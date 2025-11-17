from pydantic import BaseModel, Field
from typing import List


class ImageInfo(BaseModel):
    """Image information"""
    index: int = Field(..., description="Page index (1-based)")
    url: str = Field(..., description="URL to access the image")
    
    class Config:
        json_schema_extra = {
            "example": {
                "index": 1,
                "url": "http://localhost:8000/api/v1/pptToImg/image?path=/tmp/ppt_images/abc123/images/page_1.png"
            }
        }


class PPTUploadResponse(BaseModel):
    """PPT upload and conversion response"""
    success: bool = Field(..., description="Whether the conversion was successful")
    session: str = Field(..., description="Session ID for this conversion")
    count: int = Field(..., description="Number of pages converted")
    images: List[ImageInfo] = Field(..., description="List of converted images")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "session": "abc123def456",
                "count": 5,
                "images": [
                    {
                        "index": 1,
                        "url": "http://localhost:8000/api/v1/pptToImg/image?path=/tmp/ppt_images/abc123/images/page_1.png"
                    },
                    {
                        "index": 2,
                        "url": "http://localhost:8000/api/v1/pptToImg/image?path=/tmp/ppt_images/abc123/images/page_2.png"
                    }
                ]
            }
        }

