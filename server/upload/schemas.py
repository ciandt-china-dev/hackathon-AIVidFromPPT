from pydantic import BaseModel, Field
from typing import Optional

class UploadResponse(BaseModel):
    """File upload response"""
    success: bool = Field(
        description="Whether the upload was successful"
    )
    filename: str = Field(
        description="Name of the uploaded file"
    )
    file_path: str = Field(
        description="Relative path to the uploaded file"
    )
    file_url: str = Field(
        description="URL to access the uploaded file"
    )
    file_size: int = Field(
        description="Size of the uploaded file in bytes"
    )
    file_type: str = Field(
        description="MIME type of the uploaded file"
    )
    upload_time: str = Field(
        description="Timestamp of the upload"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "filename": "example.jpg",
                "file_path": "uploads/2025/10/27/example.jpg",
                "file_url": "http://localhost:8000/api/v1/upload/files/2025/10/27/example.jpg",
                "file_size": 1024000,
                "file_type": "image/jpeg",
                "upload_time": "2025-10-27 10:30:45"
            }
        }


class FileInfo(BaseModel):
    """File information"""
    filename: str = Field(
        description="Name of the file"
    )
    file_path: str = Field(
        description="Relative path to the file"
    )
    file_url: str = Field(
        description="URL to access the file"
    )
    file_size: int = Field(
        description="Size of the file in bytes"
    )
    file_type: str = Field(
        description="MIME type of the file"
    )
    upload_time: str = Field(
        description="Upload timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "example.jpg",
                "file_path": "uploads/2025/10/27/example.jpg",
                "file_url": "http://localhost:8000/api/v1/upload/files/2025/10/27/example.jpg",
                "file_size": 1024000,
                "file_type": "image/jpeg",
                "upload_time": "2025-10-27 10:30:45"
            }
        }


class DeleteResponse(BaseModel):
    """File deletion response"""
    success: bool = Field(
        description="Whether the deletion was successful"
    )
    message: str = Field(
        description="Response message"
    )
    filename: str = Field(
        description="Name of the deleted file"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "File deleted successfully",
                "filename": "example.jpg"
            }
        }

