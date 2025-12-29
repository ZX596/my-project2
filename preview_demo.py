"""
Streamlit 预览演示
- 支持图片、PDF首页预览
- 支持Base64编码展示
"""
import streamlit as st
import os
from image_processor import process_image, image_to_base64, resize_image
from PIL import Image
from pdf_converter import pdf_first_page_to_image, pdf_bytes_to_image
from werkzeug.utils import secure_filename
import requests
from io import BytesIO

st.title('证书图片/PDF预览演示')

# 使用与脚本同目录下的 sample_certificates 文件夹
BASE_DIR = os.path.dirname(__file__)
sample_dir = os.path.join(BASE_DIR, 'sample_certificates')
flask_uploads_dir = os.path.join(BASE_DIR, 'uploads')

# 如果目录不存在则创建并提示用户添加样本文件
if not os.path.exists(sample_dir):
    os.makedirs(sample_dir, exist_ok=True)
    st.info(f'已创建样本目录：{sample_dir}。请将图片或 PDF 放入该目录，然后刷新页面。')
    st.stop()

# 列出目录下的文件并筛选支持的类型
files = sorted(os.listdir(sample_dir)) if os.path.exists(sample_dir) else []
img_files = [f for f in files if f.lower().endswith(('png', 'jpg', 'jpeg'))]
pdf_files = [f for f in files if f.lower().endswith('pdf')]

# 数据源：固定使用 Flask 上传目录（移除 sample_certificates 选项）
data_source = 'flask_uploads'

if data_source == 'sample_certificates':
    options = img_files + pdf_files
    if not options:
        st.warning('样本目录中没有找到支持的文件（PNG/JPG/JPEG/PDF）。请将样本文件放入目录后重试，或使用上传控件上传样本。')
        st.stop()

    file_option = st.selectbox('选择样本文件', options)
    file_path = os.path.join(sample_dir, file_option)

else:
    # Flask uploads 目录下按用户目录组织：uploads/<user_id>/*
    if not os.path.exists(flask_uploads_dir):
        st.warning('Flask 上传目录不存在：{0}'.format(flask_uploads_dir))
        st.stop()

    user_dirs = sorted([d for d in os.listdir(flask_uploads_dir) if os.path.isdir(os.path.join(flask_uploads_dir, d))])
    if not user_dirs:
        st.warning('Flask 上传目录中没有用户子目录（uploads/<user_id>）。请先在 Flask 应用中上传文件以创建用户目录。')
        st.stop()

    selected_user = st.selectbox('选择用户目录', user_dirs)
    user_dir_path = os.path.join(flask_uploads_dir, selected_user)
    user_files = sorted([f for f in os.listdir(user_dir_path) if f.lower().endswith(('png','jpg','jpeg','pdf'))])
    if not user_files:
        st.warning(f'用户 {selected_user} 目录下没有支持的文件。')
        st.stop()

    file_option = st.selectbox('选择用户文件', user_files)
    file_path = os.path.join(user_dir_path, file_option)

    # 支持通过 query 参数直接从 Flask 获取文件并预览
    qp = st.experimental_get_query_params()
    file_url = qp.get('file_url', [None])[0]

    # 如果 URL 参数存在，优先通过远程 URL 展示并退出页面后续流程
    if file_url:
        st.info('正在从 Flask 获取共享文件...')
        try:
            resp = requests.get(file_url, timeout=10)
            resp.raise_for_status()
            ctype = resp.headers.get('content-type', '')
            if 'image' in ctype:
                img = Image.open(BytesIO(resp.content))
                img = img.convert('RGB')
                img = resize_image(img)
                st.image(img, caption='远程图片预览', use_column_width=True)
                st.text_area('Base64编码', image_to_base64(img, format='PNG'), height=150)
                st.stop()
            elif 'pdf' in ctype or file_url.lower().endswith('.pdf'):
                img = pdf_bytes_to_image(resp.content)
                st.image(img, caption='远程 PDF 首页预览', use_column_width=True)
                st.text_area('Base64编码', image_to_base64(img, format='PNG'), height=150)
                st.stop()
            else:
                st.error(f'不支持的远程内容类型: {ctype}')
                st.stop()
        except Exception as e:
            st.error(f'从远程获取文件失败: {e}')
            st.stop()

# 上传器：允许一次上传多个样本文件，保存到 sample_certificates
uploaded = st.file_uploader('上传样本文件（PNG/JPG/JPEG/PDF），可多选', type=['png', 'jpg', 'jpeg', 'pdf'], accept_multiple_files=True)
if uploaded:
    saved = []
    for uf in uploaded:
        name = secure_filename(uf.name)
        dest = os.path.join(sample_dir, name)
        try:
            with open(dest, 'wb') as f_out:
                f_out.write(uf.read())
            saved.append(name)
        except Exception as e:
            st.error(f'保存文件 {name} 失败: {e}')

    if saved:
        st.success(f'已保存 {len(saved)} 个文件: {", ".join(saved)}')
        st.experimental_rerun()

if file_option.lower().endswith(('png', 'jpg', 'jpeg')):
    image, img_b64 = process_image(file_path)
    st.image(image, caption='图片预览', use_column_width=True)
    st.text_area('Base64编码', img_b64, height=150)
elif file_option.lower().endswith('pdf'):
    image = pdf_first_page_to_image(file_path)
    st.image(image, caption='PDF首页预览', use_column_width=True)
    from image_processor import image_to_base64
    img_b64 = image_to_base64(image, format='PNG')
    st.text_area('Base64编码', img_b64, height=150)
