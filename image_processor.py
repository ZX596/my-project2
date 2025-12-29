"""
图片处理模块
- 支持图片旋转、尺寸调整、Base64编码
"""
import io
import base64
from PIL import Image, ExifTags

def load_image(image_path):
    """加载图片并自动处理方向"""
    image = Image.open(image_path)
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(image._getexif().items())
        if exif[orientation] == 3:
            image = image.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image = image.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image = image.rotate(90, expand=True)
    except Exception:
        pass
    return image

def resize_image(image, max_width=800, max_height=800):
    """调整图片尺寸，保持比例"""
    image.thumbnail((max_width, max_height))
    return image

def image_to_base64(image, format='PNG'):
    """图片转Base64编码"""
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_str

def process_image(image_path, max_width=800, max_height=800):
    """加载、旋转、缩放并转Base64"""
    image = load_image(image_path)
    image = resize_image(image, max_width, max_height)
    img_b64 = image_to_base64(image, format=image.format or 'PNG')
    return image, img_b64
