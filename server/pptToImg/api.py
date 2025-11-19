import os
import uuid
import shutil
import mimetypes
import json
from typing import List, Dict, Any
from urllib.parse import quote
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Query
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from pptToImg.schemas import PPTUploadResponse, ImageInfo
from pptToImg.utils import (
    get_ppt_temp_directory,
    convert_ppt_to_pdf,
    pdf_to_images
)

router = APIRouter(
    prefix="/pptToImg",
    tags=["pptToImg"]
)


# context data dir under temp root
_CONTEXT_DATA_DIR: Path = get_ppt_temp_directory() / "context_data"
_CONTEXT_DATA_DIR.mkdir(parents=True, exist_ok=True)


class ContextUpload(BaseModel):
    uuid: str
    item: Dict[str, Any]


class ContextUpdate(BaseModel):
    uuid: str
    item: Dict[str, Any]


class ContextDelete(BaseModel):
    uuid: str
    id: str


def _uuid_dir_for_context(u: str) -> Path:
    d = _CONTEXT_DATA_DIR / u
    d.mkdir(parents=True, exist_ok=True)
    return d


def _items_path_for_context(u: str) -> Path:
    return _uuid_dir_for_context(u) / "items.json"


def _load_context_items(u: str) -> List[Dict]:
    p = _items_path_for_context(u)
    if not p.exists():
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
    tmp = str(p) + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        os.replace(tmp, str(p))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存上下文数据失败: {e}")


def _find_item_index(items: List[Dict], target_id: str) -> int:
    for idx, it in enumerate(items):
        if isinstance(it, dict) and str(it.get("id")) == str(target_id):
            return idx
    return -1


@router.post(
    "/upload",
    response_model=PPTUploadResponse,
    operation_id="upload_ppt",
    summary="Upload and Convert PPT/PPTX to Images",
    description="""
    Upload a PPT/PPTX file and convert it to images.
    
    The service will:
    1. Convert PPT/PPTX to PDF using LibreOffice
    2. Render each PDF page as a PNG image
    3. Return a list of image URLs for each page
    
    Requirements:
    - LibreOffice (soffice) must be installed
    - PyMuPDF (fitz) or pdf2image + poppler recommended for PDF rendering
    
    Returns:
    - session: Unique session ID
    - count: Number of pages converted
    - images: List of image information with URLs
    """
)
async def upload_ppt(
    request: Request,
    file: UploadFile = File(..., description="PPT or PPTX file to upload")
) -> PPTUploadResponse:
    """
    Upload and convert PPT/PPTX file to images.
    
    Args:
        request: FastAPI request object (to get base URL)
        file: PPT/PPTX file to upload
    
    Returns:
        PPTUploadResponse: Conversion result with image URLs
    """
    # Validate file extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".ppt", ".pptx"}:
        raise HTTPException(
            status_code=400,
            detail="仅支持上传 .ppt 或 .pptx 文件"
        )
    
    # Get base temporary directory
    base_tmp_dir = get_ppt_temp_directory()
    
    # Create independent session directory for this upload
    session_id = uuid.uuid4().hex
    session_dir = base_tmp_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    
    # Save uploaded file
    src_path = session_dir / (file.filename or "upload.ppt")
    try:
        with open(src_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"保存上传文件失败: {e}"
        )
    
    # Convert PPT → PDF
    pdf_path = convert_ppt_to_pdf(str(src_path), str(session_dir))
    
    # Convert PDF → PNG images
    images_dir = session_dir / "images"
    img_paths = pdf_to_images(pdf_path, str(images_dir), dpi=200)
    
    # Build response data
    base_url = str(request.base_url).rstrip("/")
    items: List[ImageInfo] = []
    for i, img_path in enumerate(img_paths, start=1):
        # Build image URL using query parameter
        image_url = f"{base_url}/api/v1/pptToImg/image?path={quote(img_path)}"
        items.append(ImageInfo(
            index=i,
            url=image_url
        ))
    
    return PPTUploadResponse(
        success=True,
        session=session_id,
        count=len(img_paths),
        images=items
    )


@router.get(
    "/image",
    operation_id="get_ppt_image",
    summary="Get PPT Converted Image",
    description="""
    Retrieve a converted PPT image by its path.
    
    This endpoint serves the converted images for viewing.
    Only files within the service's temporary directory are accessible.
    """
)
async def get_image(
    path: str = Query(..., description="Image file path (must be within service temp directory)")
):
    """
    Serve a converted PPT image.
    
    Args:
        path: Local absolute path to the image file
    
    Returns:
        FileResponse: The requested image file
    """
    # Security check: only allow access to files in our temp directory
    base_tmp_dir = get_ppt_temp_directory()
    real_base = os.path.realpath(str(base_tmp_dir))
    real_path = os.path.realpath(path)
    
    if not real_path.startswith(real_base):
        raise HTTPException(
            status_code=403,
            detail="不允许访问该路径"
        )
    
    if not os.path.exists(real_path):
        raise HTTPException(
            status_code=404,
            detail="文件不存在"
        )
    
    # Determine media type
    media_type, _ = mimetypes.guess_type(real_path)
    # Default to PNG if cannot determine
    media_type = media_type or "image/png"
    
    return FileResponse(
        real_path,
        media_type=media_type
    )


@router.post("/context")
async def add_context(body: ContextUpload) -> JSONResponse:
    items = _load_context_items(body.uuid)
    if not isinstance(body.item, dict):
        raise HTTPException(status_code=400, detail="item 必须是对象")
    item_id = body.item.get("id")
    if item_id is None or not isinstance(item_id, (str, int)):
        raise HTTPException(status_code=400, detail="item.id 必须存在且为字符串或数字")
    if _find_item_index(items, str(item_id)) != -1:
        raise HTTPException(status_code=409, detail="该 uuid 下的 id 已存在，请使用更新接口")
    items.append(body.item)
    _save_context_items(body.uuid, items)
    return JSONResponse({"uuid": body.uuid, "count": len(items)})


@router.put("/context")
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
    items[idx] = body.item
    _save_context_items(body.uuid, items)
    return JSONResponse({"uuid": body.uuid, "item": body.item})


@router.delete("/context")
async def delete_context(body: ContextDelete) -> JSONResponse:
    items = _load_context_items(body.uuid)
    idx = _find_item_index(items, str(body.id))
    if idx == -1:
        raise HTTPException(status_code=404, detail="未找到待删除的数据")
    items.pop(idx)
    _save_context_items(body.uuid, items)
    return JSONResponse({"uuid": body.uuid, "deleted_id": str(body.id), "count": len(items)})


@router.get("/context/{uuid}")
def list_context(uuid: str) -> JSONResponse:
    items = _load_context_items(uuid)
    return JSONResponse({"uuid": uuid, "count": len(items), "items": items})

