from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from upload.api import router as upload_router
from fastapi_mcp import FastApiMCP

# Create FastAPI app instance
app = FastAPI(
    title="FastAPI Project",
    description="A FastAPI project template with system monitoring and file upload capabilities",
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

@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {"message": "Welcome to FastAPI Project"}



# 文件上传API
upload_mcp = FastApiMCP(
    app,
    name="File Upload API",
    include_tags=["upload"]
)

# Mount MCP endpoints
upload_mcp.mount_http(mount_path="/upload-mcp")

if __name__ == "__main__":
    import uvicorn
    print("Server is running with multiple MCP endpoints:")
    print(" - /upload-mcp: File upload endpoints")
    uvicorn.run(app, host="0.0.0.0", port=8000) 
    # uvicorn main:app --reload --host 0.0.0.0 --port 8000