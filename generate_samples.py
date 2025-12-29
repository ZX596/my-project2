"""
生成测试证书图片和 PDF 的脚本。
运行后会在 sample_certificates 目录下生成若干示例文件。
依赖: Pillow
运行:
    python generate_samples.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

BASE_DIR = os.path.dirname(__file__)
OUT_DIR = os.path.join(BASE_DIR, 'sample_certificates')
os.makedirs(OUT_DIR, exist_ok=True)

def make_image(path, text, size=(1200, 800), bg=(255, 255, 240)):
    img = Image.new('RGB', size, color=bg)
    draw = ImageDraw.Draw(img)
    try:
        # 尝试加载系统常规字体
        font = ImageFont.truetype('arial.ttf', 60)
    except Exception:
        font = ImageFont.load_default()
    w, h = draw.textsize(text, font=font)
    draw.text(((size[0]-w)/2, (size[1]-h)/2), text, fill=(20,20,60), font=font)
    img.save(path)
    print('Saved', path)
    return img

if __name__ == '__main__':
    img1 = make_image(os.path.join(OUT_DIR, 'certificate1.png'), '示例证书 1')
    img2 = make_image(os.path.join(OUT_DIR, 'certificate2.jpg'), '示例证书 2')
    img3 = make_image(os.path.join(OUT_DIR, 'certificate3.jpeg'), '示例证书 3')

    # 生成 PDF（由图片转换）
    pdf_path = os.path.join(OUT_DIR, 'certificate_sample.pdf')
    try:
        rgb = img1.convert('RGB')
        rgb.save(pdf_path, save_all=True)
        print('Saved', pdf_path)
    except Exception as e:
        print('生成 PDF 失败:', e)

    print('\n生成完成。你现在可以重新运行 streamlit 演示或者直接在 sample_certificates 目录查看示例文件。')