"""
Streamlit证书处理应用
- 证书预览
- 信息智能提取
- 信息核实与修改
- 保存草稿和提交
"""
import streamlit as st
import os
import sys
os.makedirs(os.path.join(os.path.dirname(__file__), 'exports'), exist_ok=True)
import requests
from io import BytesIO
from PIL import Image
from datetime import datetime
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from image_processor import process_image, image_to_base64, resize_image
from pdf_converter import pdf_first_page_to_image, pdf_bytes_to_image
from certificate_extractor import CertificateExtractor
from database import db, DatabaseManager, Certificate, SystemConfig, User
from flask import Flask

# 初始化Flask应用上下文（用于数据库操作）
def get_app():
    """获取Flask应用实例"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:%40Zhengxue111@localhost/user_auth_system'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

# 创建应用实例
flask_app = get_app()

st.set_page_config(page_title="证书信息处理", layout="wide")

# 初始化提取器
@st.cache_resource
def get_extractor():
    return CertificateExtractor()

extractor = get_extractor()

def get_file_from_url(file_url):
    """从URL获取文件"""
    try:
        resp = requests.get(file_url, timeout=10)
        resp.raise_for_status()
        return resp.content, resp.headers.get('content-type', '')
    except Exception as e:
        st.error(f'获取文件失败: {e}')
        return None, None

def process_file_to_image(file_content, content_type):
    """将文件内容转换为图片"""
    if 'image' in content_type:
        img = Image.open(BytesIO(file_content))
        img = img.convert('RGB')
        img = resize_image(img)
        return img, image_to_base64(img, format='PNG')
    elif 'pdf' in content_type or content_type == 'application/pdf':
        img = pdf_bytes_to_image(file_content)
        img = resize_image(img)
        return img, image_to_base64(img, format='PNG')
    return None, None

def main():
    st.title('🎓 竞赛证书信息处理')
    
    # 获取查询参数（Streamlit 1.28+使用query_params，旧版本使用experimental_get_query_params）
    try:
        if hasattr(st, 'query_params'):
            qp = st.query_params
            file_url = qp.get('file_url', [None])[0] if isinstance(qp.get('file_url'), list) else qp.get('file_url')
            file_id = qp.get('file_id', [None])[0] if isinstance(qp.get('file_id'), list) else qp.get('file_id')
            user_id = qp.get('user_id', [None])[0] if isinstance(qp.get('user_id'), list) else qp.get('user_id')
            submitter_role = qp.get('role', ['student'])[0] if isinstance(qp.get('role'), list) else qp.get('role', 'student')
            cert_id = qp.get('cert_id', [None])[0] if isinstance(qp.get('cert_id'), list) else qp.get('cert_id')
        else:
            qp = st.experimental_get_query_params()
            file_url = qp.get('file_url', [None])[0]
            file_id = qp.get('file_id', [None])[0]
            user_id = qp.get('user_id', [None])[0]
            submitter_role = qp.get('role', ['student'])[0]
            cert_id = qp.get('cert_id', [None])[0]
    except:
        file_url = None
        file_id = None
        user_id = None
        submitter_role = 'student'
        cert_id = None
    
    # 检查是否是编辑草稿模式
    draft_cert = None
    if cert_id:
        with flask_app.app_context():
            draft_cert = DatabaseManager.get_certificate_by_id(int(cert_id), int(user_id) if user_id else None)
            if draft_cert and draft_cert.status == 'draft':
                # 加载草稿数据到session
                if 'extracted_data' not in st.session_state:
                    st.session_state['extracted_data'] = {
                        'department': draft_cert.department or '',
                        'competition_name': draft_cert.competition_name or '',
                        'student_id': draft_cert.student_id or '',
                        'student_name': draft_cert.student_name or '',
                        'award_category': draft_cert.award_category or '',
                        'award_level': draft_cert.award_level or '',
                        'competition_type': draft_cert.competition_type or '',
                        'organizer': draft_cert.organizer or '',
                        'award_date': draft_cert.award_date.strftime('%Y-%m-%d') if draft_cert.award_date else '',
                        'advisor': draft_cert.advisor or ''
                    }
                if not file_id and draft_cert.file_id:
                    file_id = str(draft_cert.file_id)
                st.info(f'📝 正在编辑草稿 #{draft_cert.cert_id}，您可以修改任意字段后保存或提交。')
            elif draft_cert and draft_cert.status == 'submitted':
                st.error('❌ 该证书已提交，无法修改。')
                st.stop()
    
    if not file_url and not file_id and not cert_id:
        st.warning('请从Flask应用上传文件后进入此页面')
        st.stop()
    
    # 从URL获取文件
    if file_url:
        file_content, content_type = get_file_from_url(file_url)
        if not file_content:
            st.stop()
        image, image_base64 = process_file_to_image(file_content, content_type)
    else:
        # 从数据库获取文件
        with flask_app.app_context():
            from database import File
            file_record = File.query.filter_by(id=int(file_id)).first()
            if not file_record:
                st.error('文件不存在')
                st.stop()
            
            if not os.path.exists(file_record.file_path):
                st.error('文件路径不存在')
                st.stop()
            
            # 根据文件类型处理
            if file_record.file_type.lower() == 'pdf':
                image = pdf_first_page_to_image(file_record.file_path)
            else:
                image, _ = process_image(file_record.file_path)
            
            image = resize_image(image)
            image_base64 = image_to_base64(image, format='PNG')
    
    # 提前获取用户信息和角色信息（在按钮处理之前需要用到）
    with flask_app.app_context():
        if user_id:
            user = User.query.filter_by(id=int(user_id)).first()
        else:
            user = None
    
    # 根据角色设置字段是否可编辑（提前定义，供按钮处理使用）
    is_student = submitter_role == 'student'
    is_teacher = submitter_role == 'teacher'
    
    # 显示证书预览
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader('📄 证书预览')
        st.image(image, use_container_width=True)
    
    with col2:
        st.subheader('📋 操作面板')
        
        # 显示Base64编码（可折叠）
        with st.expander('Base64编码'):
            st.text_area('', image_base64, height=100, key='base64_display')
        
        # 信息提取按钮
        if st.button('🔍 提取信息', type='primary', use_container_width=True):
            with st.spinner('正在提取证书信息，请稍候...'):
                result = extractor.extract_from_image_base64(image_base64)
                
                if result['success']:
                    # 获取提取的数据
                    extracted_data = result['data']
                    
                    # 如果是学生角色，自动填充学号和姓名
                    with flask_app.app_context():
                        if user_id:
                            current_user = User.query.filter_by(id=int(user_id)).first()
                            if current_user and is_student:
                                # 自动填充学生的学号和姓名
                                if not extracted_data.get('student_id'):
                                    extracted_data['student_id'] = current_user.username if len(current_user.username) == 13 else ''
                                if not extracted_data.get('student_name'):
                                    extracted_data['student_name'] = current_user.name
                            elif current_user and is_teacher:
                                # 自动填充教师的姓名作为指导教师
                                if not extracted_data.get('advisor'):
                                    extracted_data['advisor'] = current_user.name
                    
                    st.session_state['extracted_data'] = extracted_data
                    st.session_state['extraction_method'] = result.get('extraction_method', 'glm4v')
                    st.session_state['confidence'] = result.get('confidence', 0)
                    
                    # 检查是否是模拟数据
                    if result.get('is_mock', False):
                        st.warning('⚠️ 当前使用模拟数据。请配置真实的API密钥（api_config.json）以使用实际功能。')
                        st.info('💡 提示：即使使用模拟数据，您也可以手动填写表单并提交。')
                    else:
                        st.success(f'✅ 信息提取成功！置信度: {st.session_state["confidence"]:.1f}%')
                        if is_student and user:
                            st.info(f'💡 已自动填充您的学号：{user.username} 和姓名：{user.name}')
                        elif is_teacher and user:
                            st.info(f'💡 已自动填充您的姓名作为指导教师：{user.name}')
                    
                    st.rerun()
                else:
                    error_msg = result.get("error", "未知错误")
                    st.error(f'❌ 提取失败: {error_msg}')
                    
                    # 提供手动输入选项
                    st.info('💡 提示：如果API不可用，您可以手动填写下面的表单并提交。')
    
    # 显示截止时间提醒
    with flask_app.app_context():
        deadline = DatabaseManager.get_submission_deadline()
        is_before_deadline = DatabaseManager.is_before_deadline()
        if is_before_deadline:
            days_left = (deadline - datetime.now()).days
            if days_left <= 3:
                st.warning(f'⚠️ 提交截止时间：{deadline.strftime("%Y-%m-%d %H:%M:%S")}，还剩 {days_left} 天')
        else:
            st.error(f'❌ 已超过提交截止时间：{deadline.strftime("%Y-%m-%d %H:%M:%S")}，无法提交新证书')
    
    # 信息表单（始终显示，允许手动输入）
    st.divider()
    st.subheader('✏️ 信息核实与修改')
    
    # 如果没有提取数据，初始化空数据
    if 'extracted_data' not in st.session_state:
        st.session_state['extracted_data'] = {}
        st.info('💡 您可以点击上方的"提取信息"按钮自动提取，或直接手动填写下面的表单。')
    
    extracted = st.session_state['extracted_data']
        
        # 创建表单
    with st.form('certificate_form', clear_on_submit=False):
            col1, col2 = st.columns(2)
            
            with col1:
                # 学生所在学院
                department = st.text_input(
                    '学生所在学院 *',
                    value=extracted.get('department', ''),
                    help='学生所在的学院或部门'
                )
                
                # 竞赛项目
                competition_name = st.text_input(
                    '竞赛项目 *',
                    value=extracted.get('competition_name', ''),
                    help='竞赛项目的完整名称'
                )
                
                # 学号（学生角色自动填充但可修改，教师角色可编辑）
                if is_student and user:
                    student_id = st.text_input(
                        '学号 *',
                        value=user.username if len(user.username) == 13 else extracted.get('student_id', ''),
                        help='自动填充当前登录学生的学号，可修改',
                        max_chars=13
                    )
                else:
                    student_id = st.text_input(
                        '学号 *',
                        value=extracted.get('student_id', ''),
                        help='13位学号',
                        max_chars=13
                    )
                
                # 学生姓名（学生角色自动填充但可修改，教师角色可编辑）
                if is_student and user:
                    student_name = st.text_input(
                        '学生姓名 *',
                        value=user.name if not extracted.get('student_name') else extracted.get('student_name', ''),
                        help='自动填充当前登录学生姓名，可修改'
                    )
                else:
                    student_name = st.text_input(
                        '学生姓名 *',
                        value=extracted.get('student_name', ''),
                        help='获奖学生的姓名'
                    )
                
                # 获奖类别
                award_category = st.selectbox(
                    '获奖类别',
                    options=['', '校级','国家级', '省级'],
                    index=0 if not extracted.get('award_category') else (1 if '国家级' in extracted.get('award_category', '') else 2),
                    help='国家级或省级'
                )
                
                # 获奖等级
                award_level = st.selectbox(
                    '获奖等级',
                    options=['', '一等奖', '二等奖', '三等奖', '金奖', '银奖', '铜奖', '优秀奖'],
                    index=0,
                    help='获奖等级'
                )
                
                # 从提取的数据中匹配获奖等级
                level_text = extracted.get('award_level', '').strip()
                if level_text:
                    level_options = ['一等奖', '二等奖', '三等奖', '金奖', '银奖', '铜奖', '优秀奖']
                    for i, opt in enumerate(level_options):
                        if opt in level_text:
                            award_level = opt
                            break
            
            with col2:
                # 竞赛类型
                competition_type = st.selectbox(
                    '竞赛类型',
                    options=['', 'A类', 'B类'],
                    index=0 if not extracted.get('competition_type') else (1 if 'A' in extracted.get('competition_type', '') else 2),
                    help='A类或B类'
                )
                
                # 主办单位
                organizer = st.text_input(
                    '主办单位',
                    value=extracted.get('organizer', ''),
                    help='竞赛主办单位名称'
                )
                
                # 获奖时间
                award_date_str = extracted.get('award_date')
                if award_date_str and isinstance(award_date_str, str):
                    award_date = award_date_str
                elif award_date_str:
                    award_date = award_date_str.strftime('%Y-%m-%d')
                else:
                    award_date = ''
                
                award_date = st.date_input(
                    '获奖时间',
                    value=datetime.strptime(award_date, '%Y-%m-%d').date() if award_date else None,
                    help='获奖日期'
                )
                
                # 指导教师（教师角色自动填充但可修改，学生角色可编辑）
                if is_teacher and user:
                    advisor = st.text_input(
                        '指导教师 *',
                        value=user.name if not extracted.get('advisor') else extracted.get('advisor', ''),
                        help='自动填充当前登录教师姓名，可修改'
                    )
                else:
                    advisor = st.text_input(
                        '指导教师 *',
                        value=extracted.get('advisor', ''),
                        help='指导教师的姓名'
                    )
            
            # 全选确认
            st.divider()
            select_all = st.checkbox('✅ 我已核实所有信息无误', key='select_all')
            
            # 按钮
            col_save, col_submit, col_clear = st.columns([1, 1, 1])
            
            with col_save:
                save_draft = st.form_submit_button('💾 保存草稿', use_container_width=True)
            
            with col_submit:
                submit_cert = st.form_submit_button('📤 提交', type='primary', use_container_width=True)
            
            with col_clear:
                clear_form = st.form_submit_button('🗑️ 清空', use_container_width=True)
            
            # 处理表单提交
            if save_draft or submit_cert:
                # 验证必填字段
                errors = []
                if not student_id or len(student_id) != 13:
                    errors.append('学号必须是13位数字')
                if not student_name:
                    errors.append('学生姓名不能为空')
                if not advisor:
                    errors.append('指导教师不能为空')
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # 验证user_id是否存在
                    if not user_id:
                        st.error('❌ 错误：无法获取用户ID，请重新从Flask应用进入此页面。')
                    else:
                        with flask_app.app_context():
                            # 再次验证用户是否存在
                            current_user = User.query.filter_by(id=int(user_id)).first()
                            if not current_user:
                                st.error('❌ 错误：用户不存在，请重新登录。')
                            else:
                                # 准备数据
                                cert_data = {
                                    'submitter_id': int(user_id),
                                    'submitter_role': submitter_role,
                                    'student_id': student_id,
                                    'student_name': student_name,
                                    'department': department,
                                    'competition_name': competition_name,
                                    'award_category': award_category if award_category else None,
                                    'award_level': award_level if award_level else None,
                                    'competition_type': competition_type if competition_type else None,
                                    'organizer': organizer,
                                    'award_date': award_date if award_date else None,
                                    'advisor': advisor,
                                    'file_id': int(file_id) if file_id else None,
                                    'file_path': file_url if file_url else None,
                                    'extraction_method': st.session_state.get('extraction_method', 'glm4v'),
                                    'extraction_confidence': st.session_state.get('confidence', 0),
                                    'status': 'submitted' if submit_cert else 'draft'
                                }
                                
                                if save_draft:
                                    # 保存草稿（如果是编辑草稿，则更新；否则创建新草稿）
                                    if draft_cert and draft_cert.status == 'draft':
                                        # 更新现有草稿
                                        success, message = DatabaseManager.update_certificate(
                                            draft_cert.cert_id, 
                                            int(user_id),
                                            **{k: v for k, v in cert_data.items() if k not in ['submitter_id', 'submitter_role', 'status']}
                                        )
                                        if success:
                                            st.success(f'✅ 草稿更新成功！证书ID: {draft_cert.cert_id}')
                                            st.info('💡 您可以继续编辑或稍后提交。')
                                        else:
                                            st.error(f'保存失败: {message}')
                                    else:
                                        # 创建新草稿
                                        cert, error = DatabaseManager.create_certificate(**cert_data)
                                        if cert:
                                            st.success(f'✅ 草稿保存成功！证书ID: {cert.cert_id}')
                                            st.info('💡 您可以继续编辑或稍后提交。')
                                            st.session_state.pop('extracted_data', None)
                                        else:
                                            st.error(f'保存失败: {error}')
                                
                                if submit_cert:
                                    # 检查截止时间
                                    if not DatabaseManager.is_before_deadline():
                                        deadline = DatabaseManager.get_submission_deadline()
                                        st.error(f'❌ 已超过提交截止时间 ({deadline.strftime("%Y-%m-%d %H:%M:%S")})，无法提交。')
                                        st.warning('💡 请联系管理员延长截止时间或查看系统配置。')
                                    elif not select_all:
                                        st.warning('⚠️ 请勾选"我已核实所有信息无误"后再提交')
                                    else:
                                        # 如果是编辑草稿，先更新再提交
                                        if draft_cert and draft_cert.status == 'draft':
                                            # 先更新数据
                                            success, message = DatabaseManager.update_certificate(
                                                draft_cert.cert_id, 
                                                int(user_id),
                                                **{k: v for k, v in cert_data.items() if k not in ['submitter_id', 'submitter_role', 'status']}
                                            )
                                            if success:
                                                # 然后提交
                                                success, message = DatabaseManager.submit_certificate(
                                                    draft_cert.cert_id, 
                                                    int(user_id)
                                                )
                                                if success:
                                                    st.success(f'✅ 提交成功！证书ID: {draft_cert.cert_id}，证书信息已保存。')
                                                    st.balloons()
                                                    st.session_state.pop('extracted_data', None)
                                                    
                                                    # 显示查看证书的链接
                                                    st.info(f'📋 证书ID: {draft_cert.cert_id}，您可以在Flask应用中查看已提交的证书。')
                                                    st.markdown(f'''
                                                    <div style="background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin-top: 10px;">
                                                        <h5>📌 下一步操作：</h5>
                                                        <p>1. 返回Flask应用（<a href="http://127.0.0.1:5000/certificates" target="_blank">点击这里</a>）</p>
                                                        <p>2. 在"我的证书"页面查看所有已提交的证书</p>
                                                        <p>3. 管理员可以在"证书管理"页面查看和导出所有证书</p>
                                                    </div>
                                                    ''', unsafe_allow_html=True)
                                                else:
                                                    st.error(f'提交失败: {message}')
                                            else:
                                                st.error(f'更新失败: {message}')
                                        else:
                                            # 创建新证书并直接提交
                                            cert, error = DatabaseManager.create_certificate(**cert_data)
                                            if cert:
                                                st.success(f'✅ 提交成功！证书ID: {cert.cert_id}，证书信息已保存。')
                                                st.balloons()
                                                st.session_state.pop('extracted_data', None)
                                                
                                                # 显示查看证书的链接
                                                st.info(f'📋 证书ID: {cert.cert_id}，您可以在Flask应用中查看已提交的证书。')
                                                st.markdown(f'''
                                                <div style="background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin-top: 10px;">
                                                    <h5>📌 下一步操作：</h5>
                                                    <p>1. 返回Flask应用（<a href="http://127.0.0.1:5000/certificates" target="_blank">点击这里</a>）</p>
                                                    <p>2. 在"我的证书"页面查看所有已提交的证书</p>
                                                    <p>3. 管理员可以在"证书管理"页面查看和导出所有证书</p>
                                                </div>
                                                ''', unsafe_allow_html=True)
                                            else:
                                                st.error(f'提交失败: {error}')
            
            if clear_form:
                st.session_state.pop('extracted_data', None)
                st.rerun()

if __name__ == '__main__':
    main()

