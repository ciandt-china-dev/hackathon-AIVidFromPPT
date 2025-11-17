import os
import uuid
import shutil
import mimetypes
import tempfile
import subprocess
from typing import List, Dict

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Query
from fastapi.responses import JSONResponse, FileResponse
from urllib.parse import quote


"""
一个简单的服务，提供两个接口：

1) POST /upload
   - 接收 PPT/PPTX 文件上传
   - 使用本机 LibreOffice 将 PPT 转为 PDF，再将每页 PDF 渲染为 PNG 图片
   - 将每页图片保存到本地临时目录
   - 返回每页图片的序号与下载地址（第二个接口的 URL）

2) GET /image
   - 根据提供的图片地址（本地绝对路径，需在服务的临时目录内）返回图片内容

服务端口：8703

注意：
- 需要安装 LibreOffice (soffice) 以完成 PPT→PDF 转换。
- 建议安装 PyMuPDF (fitz) 用于 PDF 渲染为图片（若无，将尝试使用 pdf2image + poppler）。
"""


app = FastAPI()

# 统一的临时父目录，所有生成的图片都保存在该目录下
BASE_TMP_DIR = os.path.join(tempfile.gettempdir(), "ppt_images")
os.makedirs(BASE_TMP_DIR, exist_ok=True)


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