from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from upload.api import router as upload_router
from tts.api import router as tts_router
from fastapi_mcp import FastApiMCP
from pathlib import Path

# Create FastAPI app instance
app = FastAPI(
    title="FastAPI Project",
    description="A FastAPI project template with system monitoring, file upload and TTS capabilities",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router, prefix="/api/v1")
app.include_router(tts_router, prefix="/api/v1")

@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {"message": "Welcome to FastAPI Project"}


# Serve test HTML pages
@app.get("/upload/test_upload.html")
async def get_upload_test_page():
    """
    Serve upload test page
    """
    html_file = Path(__file__).parent / "upload" / "test_upload.html"
    if not html_file.exists():
        return {"error": "Test page not found"}
    return FileResponse(html_file, media_type="text/html")


@app.get("/tts/test_tts.html")
async def get_tts_test_page():
    """
    Serve TTS test page
    """
    html_file = Path(__file__).parent / "tts" / "test_tts.html"
    if not html_file.exists():
        return {"error": "Test page not found"}
    return FileResponse(html_file, media_type="text/html")



# File Upload API MCP
upload_mcp = FastApiMCP(
    app,
    name="File Upload API",
    include_tags=["upload"]
)

# TTS API MCP
tts_mcp = FastApiMCP(
    app,
    name="Text-to-Speech API",
    include_tags=["tts"]
)

# Mount MCP endpoints
upload_mcp.mount_http(mount_path="/upload-mcp")
tts_mcp.mount_http(mount_path="/tts-mcp")

if __name__ == "__main__":
    import uvicorn
    print("Server is running with multiple MCP endpoints:")
    print(" - /upload-mcp: File upload endpoints")
    print(" - /tts-mcp: Text-to-Speech endpoints")
    uvicorn.run(app, host="0.0.0.0", port=8000) 
    # uvicorn main:app --reload --host 0.0.0.0 --port 8000