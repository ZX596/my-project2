"""
PDF转图片模块（提取首页）
"""
"""
PDF转图片模块（提取首页）
支持：PyMuPDF(fitz) 或 pdf2image(需安装 poppler)
如果两者都未安装，会抛出提示性的 ImportError。
"""
import io
from PIL import Image
from pdf2image import convert_from_bytes

_HAVE_FITZ = False
_HAVE_PDF2IMAGE = False

try:
    import fitz  # PyMuPDF
    _HAVE_FITZ = True
except Exception:
    _HAVE_FITZ = False

try:
    from pdf2image import convert_from_path
    _HAVE_PDF2IMAGE = True
except Exception:
    _HAVE_PDF2IMAGE = False

def pdf_first_page_to_image(pdf_path, dpi=150):
    """将PDF首页转换为PIL图片对象。

    优先使用 PyMuPDF(fitz)，若未安装则尝试使用 pdf2image（需要系统安装 poppler）。
    """
    if _HAVE_FITZ:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=dpi)
        img_data = pix.tobytes('png')
        image = Image.open(io.BytesIO(img_data))
        return image

    if _HAVE_PDF2IMAGE:
        pages = convert_from_path(pdf_path, dpi=dpi, first_page=1, last_page=1)
        if pages:
            return pages[0]
        raise RuntimeError('无法从 PDF 中提取页面')

    # 两者都不可用，抛出明确错误以便用户安装依赖
    raise ImportError(
        "缺少依赖：请安装 'PyMuPDF'（pip install pymupdf）或 'pdf2image'（pip install pdf2image）并在系统上安装 poppler。\n"
        "Windows 用户可从 https://blog.alivate.com.au/poppler-windows/ 下载 poppler。"
    )


def pdf_bytes_to_image(pdf_bytes, dpi=150):
    """将 PDF 二进制数据的首页转换为 PIL 图片对象。"""
    if _HAVE_FITZ:
        # PyMuPDF 支持从内存打开
        doc = fitz.open(stream=pdf_bytes, filetype='pdf')
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=dpi)
        img_data = pix.tobytes('png')
        image = Image.open(io.BytesIO(img_data))
        return image

    if _HAVE_PDF2IMAGE:
        pages = convert_from_bytes(pdf_bytes, dpi=dpi, first_page=1, last_page=1)
        if pages:
            return pages[0]
        raise RuntimeError('无法从 PDF 二进制数据中提取页面')

    raise ImportError('缺少 PDF 转换依赖（pymupdf 或 pdf2image）')
