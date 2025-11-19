import os
import uuid
import shutil
import mimetypes
import tempfile
import subprocess
import json
from typing import List, Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Query
from fastapi.responses import JSONResponse, FileResponse
from urllib.parse import quote
from pydantic import BaseModel


"""
服务文档

概述
- 提供两类能力：
  1) 文件处理：上传 PPT/PPTX → 转 PDF → 每页渲染 PNG 图片。
  2) 上下文数据：按 uuid 管理动态 item 列表，支持创建、查询、更新、删除。

运行信息
- 服务端口：8703
- 临时根目录：`tempfile.gettempdir()/ppt_images`
- 依赖：
  - 必需：LibreOffice (soffice) 用于 PPT→PDF。
  - 渲染优先：PyMuPDF (fitz)；若无则回退 pdf2image（需 poppler）。

接口列表
1) POST /upload（上传并生成图片）
   - 请求：`multipart/form-data`，字段 `file`（仅支持 .ppt/.pptx）。
   - 行为：保存上传文件 → 调用 LibreOffice 转 PDF → 将 PDF 每页渲染为 PNG → 返回每页图片的下载地址。
   - 响应示例：
     {
       "session": "<uuid>",
       "count": 10,
       "images": [{"index":1,"url":"http://host:8703/image?path=<abs>"}, ...]
     }

2) GET /image（下载生成的图片）
   - 查询参数：`path`（图片的本地绝对路径，必须位于服务临时目录内）。
   - 安全：服务会校验 `realpath(path)` 是否在临时根目录下，否则 403。

3) POST /context（创建条目）
   - 请求体：
     {
       "uuid": "<uuid>",
       "item": {"id":"<必填，字符串或数字>", "url":"...", "context":"...", ...任意扩展字段}
     }
   - 行为：在该 `uuid` 下追加一条 `item`；同一 `uuid` 下 `id` 不允许重复（返回 409）。
   - 响应：`{"uuid":"<uuid>", "count": <该 uuid 下的总条目数>}`

4) GET /context/{uuid}（查询列表）
   - 路径参数：`uuid`
   - 响应：`{"uuid":"<uuid>", "count": <数量>, "items": [ ... ]}`

5) PUT /context（更新条目）
   - 请求体：与创建相同的形状 `{ uuid, item }`，其中 `item.id` 用于定位。
   - 行为：按 `uuid + item.id` 全量替换旧条目；若不存在返回 404。
   - 响应：`{"uuid":"<uuid>", "item": { ...更新后的完整对象... }}`

6) DELETE /context（删除条目）
   - 请求体：`{"uuid":"<uuid>", "id":"<必填>"}`
   - 行为：按 `uuid + id` 删除；若不存在返回 404。
   - 响应：`{"uuid":"<uuid>", "deleted_id":"<id>", "count": <剩余数量>}`

存储与持久化
- 上下文数据存储位置：`tempfile.gettempdir()/ppt_images/context_data/<uuid>/items.json`
- 格式：一个数组，每个元素为动态对象，至少包含 `id` 字段。
- 写入采用原子替换（先写到 `.tmp` 再覆盖 `items.json`）。

示例 curl
- 创建：
  curl -X POST http://localhost:8703/context \
    -H 'Content-Type: application/json' \
    -d '{"uuid":"demo-uuid-001","item":{"id":"item-1","url":"https://example.com/resource","context":"第一条","extra":"扩展"}}'
- 查询：
  curl http://localhost:8703/context/demo-uuid-001
- 更新：
  curl -X PUT http://localhost:8703/context \
    -H 'Content-Type: application/json' \
    -d '{"uuid":"demo-uuid-001","item":{"id":"item-1","url":"https://example.com/resource-updated","context":"更新","newField":"新增"}}'
- 删除：
  curl -X DELETE http://localhost:8703/context \
    -H 'Content-Type: application/json' \
    -d '{"uuid":"demo-uuid-001","id":"item-1"}'
- 上传 PPT：
  curl -F "file=@/path/to/slides.pptx" http://localhost:8703/upload
"""


app = FastAPI()

# 统一的临时父目录，所有生成的图片都保存在该目录下
BASE_TMP_DIR = os.path.join(tempfile.gettempdir(), "ppt_images")
os.makedirs(BASE_TMP_DIR, exist_ok=True)

# 上下文数据的持久化目录
CONTEXT_DATA_DIR = os.path.join(BASE_TMP_DIR, "context_data")
os.makedirs(CONTEXT_DATA_DIR, exist_ok=True)


class ContextItem(BaseModel):
    uuid: str
    id: str
    url: str
    context: str


class ContextUpload(BaseModel):
    uuid: str
    item: Dict[str, Any]


class ContextUpdate(BaseModel):
    uuid: str
    item: Dict[str, Any]


class ContextDelete(BaseModel):
    uuid: str
    id: str


def _uuid_dir_for_context(u: str) -> str:
    d = os.path.join(CONTEXT_DATA_DIR, u)
    os.makedirs(d, exist_ok=True)
    return d


def _items_path_for_context(u: str) -> str:
    return os.path.join(_uuid_dir_for_context(u), "items.json")


def _load_context_items(u: str) -> List[Dict]:
    p = _items_path_for_context(u)
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except json.JSONDecodeError:
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取上下文数据失败: {e}")


def _save_context_items(u: str, items: List[Dict]) -> None:
    p = _items_path_for_context(u)
    tmp = p + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        os.replace(tmp, p)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存上下文数据失败: {e}")


def _find_item_index(items: List[Dict], target_id: str) -> int:
    for idx, it in enumerate(items):
        if isinstance(it, dict) and str(it.get("id")) == str(target_id):
            return idx
    return -1


def _find_soffice() -> str:
    """寻找 LibreOffice 可执行文件路径。"""
    import shutil as _sh
    # 先查 PATH
    path = _sh.which("soffice")
    if path:
        return path
    # macOS 常见安装路径
    candidates = [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/local/bin/soffice",
        "/opt/homebrew/bin/soffice",
        "/usr/bin/soffice",
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    raise FileNotFoundError("未找到 LibreOffice (soffice)，请先安装 LibreOffice 并确保可执行文件在 PATH 中。")


def convert_ppt_to_pdf(ppt_path: str, out_dir: str) -> str:
    """使用 LibreOffice 将 PPT/PPTX 转换为 PDF，返回 PDF 路径。"""
    soffice = _find_soffice()
    os.makedirs(out_dir, exist_ok=True)
    try:
        subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                out_dir,
                ppt_path,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"PPT 转 PDF 失败: {e.stderr.decode(errors='ignore')}")

    base_name = os.path.splitext(os.path.basename(ppt_path))[0]
    pdf_path = os.path.join(out_dir, f"{base_name}.pdf")
    if not os.path.exists(pdf_path):
        # 有些版本可能会输出不同命名的文件，尝试在 out_dir 内寻找最新的 pdf
        pdfs = [f for f in os.listdir(out_dir) if f.lower().endswith(".pdf")]
        if not pdfs:
            raise HTTPException(status_code=500, detail="未生成 PDF 文件，请检查 LibreOffice 配置。")
        pdf_path = os.path.join(out_dir, pdfs[0])
    return pdf_path


def pdf_to_images(pdf_path: str, output_dir: str, dpi: int = 200) -> List[str]:
    """将 PDF 每页渲染为 PNG 图片，返回图片路径列表。优先使用 PyMuPDF。"""
    os.makedirs(output_dir, exist_ok=True)

    # 优先 PyMuPDF
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_path)
        img_paths: List[str] = []
        for i in range(doc.page_count):
            page = doc.load_page(i)
            # 使用矩阵控制缩放以接近 dpi，简单倍数近似
            zoom = dpi / 72.0  # PDF 基础分辨率约为 72 dpi
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_path = os.path.join(output_dir, f"page_{i+1}.png")
            pix.save(img_path)
            img_paths.append(img_path)
        doc.close()
        return img_paths
    except ImportError:
        pass

    # 退回 pdf2image
    try:
        from pdf2image import convert_from_path

        images = convert_from_path(pdf_path, dpi=dpi)
        img_paths: List[str] = []
        for i, img in enumerate(images, start=1):
            img_path = os.path.join(output_dir, f"page_{i}.png")
            img.save(img_path, format="PNG")
            img_paths.append(img_path)
        return img_paths
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 转图片失败，请安装 PyMuPDF 或 pdf2image + poppler: {e}")


def build_image_url(request: Request, img_path: str) -> str:
    """根据请求构建图片下载地址。"""
    base = str(request.base_url).rstrip("/")
    # 将本地路径放入查询参数 path，外部调用时可直接访问该地址
    return f"{base}/image?path={quote(img_path)}"


@app.post("/context")
async def add_context(body: ContextUpload) -> JSONResponse:
    items = _load_context_items(body.uuid)
    if not isinstance(body.item, dict):
        raise HTTPException(status_code=400, detail="item 必须是对象")
    item_id = body.item.get("id")
    if item_id is None or not isinstance(item_id, (str, int)):
        raise HTTPException(status_code=400, detail="item.id 必须存在且为字符串或数字")
    # 防重复：同一 uuid 下的 id 不可重复
    if _find_item_index(items, str(item_id)) != -1:
        raise HTTPException(status_code=409, detail="该 uuid 下的 id 已存在，请使用更新接口")
    items.append(body.item)
    _save_context_items(body.uuid, items)
    return JSONResponse({"uuid": body.uuid, "count": len(items)})


@app.put("/context")
async def update_context(body: ContextUpdate) -> JSONResponse:
    items = _load_context_items(body.uuid)
    if not isinstance(body.item, dict):
        raise HTTPException(status_code=400, detail="item 必须是对象")
    item_id = body.item.get("id")
    if item_id is None:
        raise HTTPException(status_code=400, detail="item.id 必须存在")
    idx = _find_item_index(items, str(item_id))
    if idx == -1:
        raise HTTPException(status_code=404, detail="未找到待更新的数据")
    # 全量替换为新的 item（item 支持动态字段）
    items[idx] = body.item
    _save_context_items(body.uuid, items)
    return JSONResponse({"uuid": body.uuid, "item": body.item})


@app.delete("/context")
async def delete_context(body: ContextDelete) -> JSONResponse:
    items = _load_context_items(body.uuid)
    idx = _find_item_index(items, str(body.id))
    if idx == -1:
        raise HTTPException(status_code=404, detail="未找到待删除的数据")
    deleted = items.pop(idx)
    _save_context_items(body.uuid, items)
    return JSONResponse({"uuid": body.uuid, "deleted_id": str(body.id), "count": len(items)})


@app.get("/context/{uuid}")
def list_context(uuid: str) -> JSONResponse:
    items = _load_context_items(uuid)
    return JSONResponse({"uuid": uuid, "count": len(items), "items": items})


@app.post("/upload")
async def upload_ppt(file: UploadFile = File(...), request: Request = None) -> JSONResponse:
    # 校验扩展名
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".ppt", ".pptx"}:
        raise HTTPException(status_code=400, detail="仅支持上传 .ppt 或 .pptx 文件")

    # 为本次上传创建独立会话目录
    session_id = uuid.uuid4().hex
    session_dir = os.path.join(BASE_TMP_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    # 保存原始文件
    src_path = os.path.join(session_dir, file.filename)
    try:
        with open(src_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存上传文件失败: {e}")

    # PPT → PDF
    pdf_path = convert_ppt_to_pdf(src_path, session_dir)

    # PDF → 多张 PNG
    images_dir = os.path.join(session_dir, "images")
    img_paths = pdf_to_images(pdf_path, images_dir, dpi=200)

    # 构造返回数据
    items: List[Dict] = []
    for i, p in enumerate(img_paths, start=1):
        items.append({
            "index": i,
            "url": build_image_url(request, p),
        })

    return JSONResponse({
        "session": session_id,
        "count": len(img_paths),
        "images": items,
    })


@app.get("/image")
def get_image(path: str = Query(..., description="图片的本地绝对路径（必须位于服务的临时目录内）")):
    # 安全校验：仅允许访问我们生成的临时目录内文件
    real_base = os.path.realpath(BASE_TMP_DIR)
    real_path = os.path.realpath(path)
    if not real_path.startswith(real_base):
        raise HTTPException(status_code=403, detail="不允许访问该路径")
    if not os.path.exists(real_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    media_type, _ = mimetypes.guess_type(real_path)
    # 若无法识别，默认按 PNG
    media_type = media_type or "image/png"
    return FileResponse(real_path, media_type=media_type)


if __name__ == "__main__":
    import uvicorn
    # 启动服务：端口 8703
    uvicorn.run(app, host="0.0.0.0", port=8703)