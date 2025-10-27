from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from pathlib import Path
import os
import aiofiles
from typing import List
from upload.schemas import UploadResponse, FileInfo, DeleteResponse
from upload.utils import (
    get_current_time,
    get_upload_directory,
    generate_unique_filename,
    get_file_type,
    is_allowed_file
)

router = APIRouter(
    prefix="/upload",
    tags=["upload"]
)

# Allowed file extensions (customize as needed)
ALLOWED_EXTENSIONS = {
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico',
    # Documents
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv',
    # Videos
    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm',
    # Audio
    '.mp3', '.wav', '.ogg', '.m4a', '.flac',
    # Archives
    '.zip', '.rar', '.7z', '.tar', '.gz',
    # Other
    '.json', '.xml', '.yaml', '.yml'
}

# Maximum file size (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post(
    "/file",
    response_model=UploadResponse,
    operation_id="upload_file",
    summary="Upload a File",
    description="""
    Upload a single file (image, document, video, etc.).
    
    Supported file types:
    - Images: jpg, jpeg, png, gif, bmp, webp, svg, ico
    - Documents: pdf, doc, docx, xls, xlsx, ppt, pptx, txt, csv
    - Videos: mp4, avi, mov, wmv, flv, mkv, webm
    - Audio: mp3, wav, ogg, m4a, flac
    - Archives: zip, rar, 7z, tar, gz
    - Other: json, xml, yaml, yml
    
    Maximum file size: 50MB
    
    Returns the file URL for accessing the uploaded file.
    """
)
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="File to upload")
):
    """
    Upload a single file and return its access URL.
    
    Args:
        request: FastAPI request object (to get base URL)
        file: File to upload
    
    Returns:
        UploadResponse: Upload result with file URL
    """
    # Check if file is provided
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file extension
    if not is_allowed_file(file.filename, ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Check file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    
    # Get upload directory
    upload_dir = get_upload_directory()
    file_path = upload_dir / unique_filename
    
    # Save file
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Generate file URL
    base_url = str(request.base_url).rstrip('/')
    relative_path = str(file_path)
    file_url = f"{base_url}/api/v1/upload/files/{relative_path}"
    
    # Get file type
    file_type = get_file_type(file.filename)
    
    return UploadResponse(
        success=True,
        filename=unique_filename,
        file_path=relative_path,
        file_url=file_url,
        file_size=file_size,
        file_type=file_type,
        upload_time=get_current_time()
    )


@router.post(
    "/files",
    response_model=List[UploadResponse],
    operation_id="upload_multiple_files",
    summary="Upload Multiple Files",
    description="""
    Upload multiple files at once.
    
    Each file will be validated and saved individually.
    Returns a list of upload results with file URLs.
    """
)
async def upload_multiple_files(
    request: Request,
    files: List[UploadFile] = File(..., description="Files to upload")
):
    """
    Upload multiple files and return their access URLs.
    
    Args:
        request: FastAPI request object (to get base URL)
        files: List of files to upload
    
    Returns:
        List[UploadResponse]: List of upload results with file URLs
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    for file in files:
        try:
            result = await upload_file(request, file)
            results.append(result)
        except HTTPException as e:
            # Add error result for this file
            results.append(UploadResponse(
                success=False,
                filename=file.filename or "unknown",
                file_path="",
                file_url="",
                file_size=0,
                file_type="",
                upload_time=get_current_time()
            ))
    
    return results


@router.get(
    "/files/{file_path:path}",
    operation_id="get_uploaded_file",
    summary="Get Uploaded File",
    description="""
    Retrieve an uploaded file by its path.
    
    This endpoint serves the uploaded files for viewing or downloading.
    """
)
async def get_uploaded_file(file_path: str):
    """
    Serve an uploaded file.
    
    Args:
        file_path: Relative path to the file
    
    Returns:
        FileResponse: The requested file
    """
    full_path = Path(file_path)
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    return FileResponse(full_path)


@router.delete(
    "/file/{file_path:path}",
    response_model=DeleteResponse,
    operation_id="delete_file",
    summary="Delete Uploaded File",
    description="""
    Delete an uploaded file by its path.
    """
)
async def delete_file(file_path: str):
    """
    Delete an uploaded file.
    
    Args:
        file_path: Relative path to the file
    
    Returns:
        DeleteResponse: Deletion result
    """
    full_path = Path(file_path)
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    try:
        os.remove(full_path)
        return DeleteResponse(
            success=True,
            message="File deleted successfully",
            filename=full_path.name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.get(
    "/list",
    response_model=List[FileInfo],
    operation_id="list_uploaded_files",
    summary="List Uploaded Files",
    description="""
    List all uploaded files.
    
    Returns information about all files in the upload directory.
    Supports pagination with limit and offset parameters.
    """
)
async def list_uploaded_files(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    max_depth: int = 5
):
    """
    List all uploaded files with pagination and depth control.
    
    Args:
        request: FastAPI request object (to get base URL)
        limit: Maximum number of files to return (default: 100)
        offset: Number of files to skip (default: 0)
        max_depth: Maximum directory depth to traverse (default: 5, prevents scanning entire PVC)
    
    Returns:
        List[FileInfo]: List of file information
    """
    base_url = str(request.base_url).rstrip('/')
    # Use app-specific subdirectory to avoid scanning entire shared PVC
    upload_base = Path("uploads") / "aividfromppt"
    
    if not upload_base.exists():
        return []
    
    files_info = []
    file_count = 0
    
    # Use iterative approach with depth limit to avoid scanning entire shared volume
    def scan_directory(directory: Path, current_depth: int = 0):
        nonlocal file_count
        
        # Stop if we've collected enough files or reached max depth
        if file_count >= offset + limit or current_depth > max_depth:
            return
        
        try:
            # Only list immediate children, not recursive
            for item in directory.iterdir():
                if file_count >= offset + limit:
                    break
                    
                if item.is_file():
                    # Skip if we haven't reached offset yet
                    if file_count < offset:
                        file_count += 1
                        continue
                    
                    relative_path = str(item)
                    file_url = f"{base_url}/api/v1/upload/files/{relative_path}"
                    file_stat = item.stat()
                    
                    files_info.append(FileInfo(
                        filename=item.name,
                        file_path=relative_path,
                        file_url=file_url,
                        file_size=file_stat.st_size,
                        file_type=get_file_type(item.name),
                        upload_time=get_current_time()  # Note: using current time, could use file mtime
                    ))
                    file_count += 1
                elif item.is_dir() and current_depth < max_depth:
                    # Recursively scan subdirectories with depth limit
                    scan_directory(item, current_depth + 1)
        except (PermissionError, OSError):
            # Skip directories we can't access
            pass
    
    scan_directory(upload_base)
    
    return files_info

