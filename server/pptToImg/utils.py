import os
import shutil
import subprocess
import tempfile
from typing import List
from pathlib import Path
from fastapi import HTTPException


def get_ppt_temp_directory() -> Path:
    """
    Get PPT temporary directory for storing converted images.
    Creates directory if it doesn't exist.
    
    Returns:
        Path: Path to PPT temporary directory
    """
    base_tmp_dir = Path(tempfile.gettempdir()) / "ppt_images"
    base_tmp_dir.mkdir(parents=True, exist_ok=True)
    return base_tmp_dir


def find_soffice() -> str:
    """
    Find LibreOffice executable path.
    
    Returns:
        str: Path to soffice executable
    
    Raises:
        FileNotFoundError: If LibreOffice is not found
    """
    # Check PATH first
    path = shutil.which("soffice")
    if path:
        return path
    
    # macOS common installation paths
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
    """
    Convert PPT/PPTX to PDF using LibreOffice.
    
    Args:
        ppt_path: Path to PPT/PPTX file
        out_dir: Output directory for PDF
    
    Returns:
        str: Path to generated PDF file
    
    Raises:
        HTTPException: If conversion fails
    """
    soffice = find_soffice()
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
        raise HTTPException(
            status_code=500,
            detail=f"PPT 转 PDF 失败: {e.stderr.decode(errors='ignore') if e.stderr else str(e)}"
        )
    
    base_name = os.path.splitext(os.path.basename(ppt_path))[0]
    pdf_path = os.path.join(out_dir, f"{base_name}.pdf")
    
    if not os.path.exists(pdf_path):
        # Some versions may output differently named files, try to find the latest PDF
        pdfs = [f for f in os.listdir(out_dir) if f.lower().endswith(".pdf")]
        if not pdfs:
            raise HTTPException(
                status_code=500,
                detail="未生成 PDF 文件，请检查 LibreOffice 配置。"
            )
        pdf_path = os.path.join(out_dir, pdfs[0])
    
    return pdf_path


def pdf_to_images(pdf_path: str, output_dir: str, dpi: int = 200) -> List[str]:
    """
    Convert PDF pages to PNG images.
    Prefers PyMuPDF, falls back to pdf2image.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for images
        dpi: DPI for image rendering (default: 200)
    
    Returns:
        List[str]: List of image file paths
    
    Raises:
        HTTPException: If conversion fails
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Prefer PyMuPDF
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(pdf_path)
        img_paths: List[str] = []
        for i in range(doc.page_count):
            page = doc.load_page(i)
            # Use matrix to control scaling to approximate dpi
            zoom = dpi / 72.0  # PDF base resolution is approximately 72 dpi
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_path = os.path.join(output_dir, f"page_{i+1}.png")
            pix.save(img_path)
            img_paths.append(img_path)
        doc.close()
        return img_paths
    except ImportError:
        pass
    
    # Fallback to pdf2image
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
        raise HTTPException(
            status_code=500,
            detail=f"PDF 转图片失败，请安装 PyMuPDF 或 pdf2image + poppler: {e}"
        )

