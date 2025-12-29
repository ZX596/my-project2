"""
竞赛证书智能识别与管理系统 - 完整系统主程序
基于Streamlit框架开发
"""
import streamlit as st
import os
import base64
from datetime import datetime
from form_handler import (
    save_draft, submit_form, get_user_draft, get_user_submission, 
    is_before_deadline, get_deadline
)
from admin_panel import (
    view_all_submissions, export_submissions_csv, export_submissions_excel,
    get_submission_stats
)
from glm4v_api import GLM4VAPI
from info_extractor import extract_certificate_info

# 页面配置
st.set_page_config(
    page_title="竞赛证书智能识别系统",
    page_icon="🎓",
    layout="wide"
)

# 字段定义
FIELDS = [
    "学院", "竞赛项目", "学号", "学生姓名", "获奖类别",
    "获奖等级", "竞赛类型", "主办单位", "获奖时间", "指导教师"
]

# 主标题
st.title("🎓 竞赛证书智能识别与数据管理系统")
st.markdown("---")

# 用户身份选择
col1, col2 = st.columns([2, 1])
with col1:
    user_id = st.text_input("请输入学号（作为用户ID）:", placeholder="例如: 2023000000001")
with col2:
    role = st.selectbox("请选择身份:", ["普通用户", "管理员"])

if not user_id:
    st.warning("⚠️ 请输入学号后操作！")
    st.stop()

# 显示截止时间信息
deadline = get_deadline()
deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
now = datetime.now()
time_left = deadline_dt - now

if time_left.total_seconds() > 0:
    st.info(f"⏰ 截止时间: {deadline} | 剩余时间: {str(time_left).split('.')[0]}")
else:
    st.error(f"❌ 已超过截止时间: {deadline}")

# ==================== 普通用户界面 ====================
if role == "普通用户":
    st.header("📋 证书信息表单")
    
    # 图片上传与Base64显示
    uploaded_img = st.file_uploader(
        "上传证书图片（jpg/png/jpeg/pdf）", 
        type=["jpg", "jpeg", "png", "pdf"],
        help="支持JPG、PNG、JPEG和PDF格式"
    )
    
    image_base64 = ""
    if uploaded_img is not None:
        img_bytes = uploaded_img.read()
        image_base64 = base64.b64encode(img_bytes).decode("utf-8")
        
        # 显示预览
        col_preview1, col_preview2 = st.columns([2, 1])
        with col_preview1:
            if uploaded_img.type.startswith('image'):
                st.image(img_bytes, caption="证书预览", use_column_width=True)
            else:
                st.info("PDF文件预览功能开发中，请直接填写表单")
        
        with col_preview2:
            with st.expander("Base64编码预览"):
                st.text_area("Base64编码", image_base64[:200] + "..." if len(image_base64) > 200 else image_base64, 
                           height=100, disabled=True)
    
    # 检查是否已提交
    user_submission = get_user_submission(user_id)
    disabled = user_submission is not None
    
    if disabled:
        st.warning("⚠️ 您已经提交过，无法修改。")
        st.info("📄 已提交的数据:")
        st.json(user_submission)
    
    # 优先加载草稿，否则加载已提交，否则空表单
    form_data = get_user_draft(user_id) or user_submission or {field: "" for field in FIELDS}
    
    # 抽取按钮逻辑
    extract_result = None
    if uploaded_img and image_base64 and not disabled:
        if st.button("🔍 抽取信息", type="primary", use_container_width=True):
            with st.spinner("正在识别证书信息，请稍候..."):
                try:
                    api = GLM4VAPI()
                    prompt = """请从这张竞赛证书图片中提取以下信息，并以JSON格式返回：
{
    "学院": "学生所在学院",
    "竞赛项目": "竞赛项目名称",
    "学号": "13位学号",
    "学生姓名": "学生姓名",
    "获奖类别": "国家级或省级",
    "获奖等级": "一等奖、二等奖、三等奖、金奖、银奖、铜奖或优秀奖",
    "竞赛类型": "A类或B类",
    "主办单位": "主办单位名称",
    "获奖时间": "YYYY-MM-DD格式的日期",
    "指导教师": "指导教师姓名"
}

如果某个字段无法识别，请返回空字符串。请确保返回的是有效的JSON格式。"""
                    api_response = api.call_api(image_base64, prompt)
                    
                    if "error" in api_response:
                        st.error(f"❌ API调用失败: {api_response['error']}")
                        st.info("💡 提示：您可以手动填写表单")
                    else:
                        extract_result = extract_certificate_info(api_response)
                        if extract_result:
                            st.success("✅ 识别成功，已自动填充表单！")
                            form_data.update(extract_result)
                            st.rerun()
                        else:
                            st.warning("⚠️ 未能提取到有效信息，请手动填写表单")
                except Exception as e:
                    st.error(f"❌ 提取失败: {str(e)}")
                    st.info("💡 提示：您可以手动填写表单")
    
    # 表单
    with st.form("cert_form", clear_on_submit=False):
        st.subheader("✏️ 证书信息填写")
        
        # 创建两列布局
        col1, col2 = st.columns(2)
        
        inputs = {}
        with col1:
            inputs["学院"] = st.text_input(
                "学院", 
                value=form_data.get("学院", ""), 
                disabled=disabled,
                help="学生所在学院"
            )
            inputs["竞赛项目"] = st.text_input(
                "竞赛项目", 
                value=form_data.get("竞赛项目", ""), 
                disabled=disabled,
                help="竞赛项目名称"
            )
            inputs["学号"] = st.text_input(
                "学号 *", 
                value=form_data.get("学号", ""), 
                disabled=disabled,
                max_chars=13,
                help="13位学号（必填）"
            )
            inputs["学生姓名"] = st.text_input(
                "学生姓名 *", 
                value=form_data.get("学生姓名", ""), 
                disabled=disabled,
                help="学生姓名（必填）"
            )
            inputs["获奖类别"] = st.selectbox(
                "获奖类别", 
                options=["", "国家级", "省级"],
                index=0 if not form_data.get("获奖类别") else (1 if "国家级" in form_data.get("获奖类别", "") else 2),
                disabled=disabled
            )
        
        with col2:
            inputs["获奖等级"] = st.selectbox(
                "获奖等级", 
                options=["", "一等奖", "二等奖", "三等奖", "金奖", "银奖", "铜奖", "优秀奖"],
                index=0,
                disabled=disabled
            )
            # 从提取结果中匹配获奖等级
            level_text = form_data.get("获奖等级", "")
            if level_text:
                level_options = ["一等奖", "二等奖", "三等奖", "金奖", "银奖", "铜奖", "优秀奖"]
                for i, opt in enumerate(level_options):
                    if opt in level_text:
                        inputs["获奖等级"] = opt
                        break
            
            inputs["竞赛类型"] = st.selectbox(
                "竞赛类型", 
                options=["", "A类", "B类"],
                index=0 if not form_data.get("竞赛类型") else (1 if "A" in form_data.get("竞赛类型", "") else 2),
                disabled=disabled
            )
            inputs["主办单位"] = st.text_input(
                "主办单位", 
                value=form_data.get("主办单位", ""), 
                disabled=disabled
            )
            # 处理获奖时间
            award_date_value = None
            if form_data.get("获奖时间"):
                try:
                    award_date_value = datetime.strptime(form_data.get("获奖时间"), "%Y-%m-%d").date()
                except:
                    try:
                        award_date_value = datetime.strptime(form_data.get("获奖时间"), "%Y年%m月%d日").date()
                    except:
                        pass
            
            inputs["获奖时间"] = st.date_input(
                "获奖时间", 
                value=award_date_value,
                disabled=disabled
            )
            inputs["指导教师"] = st.text_input(
                "指导教师 *", 
                value=form_data.get("指导教师", ""), 
                disabled=disabled,
                help="指导教师姓名（必填）"
            )
        
        # 处理日期格式
        if inputs["获奖时间"]:
            inputs["获奖时间"] = inputs["获奖时间"].strftime("%Y-%m-%d")
        else:
            inputs["获奖时间"] = ""
        
        # 全选确认
        st.divider()
        select_all = st.checkbox("✅ 我已核实所有信息无误", disabled=disabled)
        
        # 按钮
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            save_btn = st.form_submit_button("💾 保存草稿", disabled=disabled, use_container_width=True)
        with col_btn2:
            submit_btn = st.form_submit_button("📤 批量提交", disabled=disabled or not is_before_deadline(), use_container_width=True)
        with col_btn3:
            clear_btn = st.form_submit_button("🗑️ 清空表单", disabled=disabled, use_container_width=True)
    
    # 处理表单提交
    if save_btn and not disabled:
        success, msg = save_draft(user_id, inputs)
        if success:
            st.success(f"✅ {msg}")
        else:
            st.error(f"❌ {msg}")
    
    if submit_btn and not disabled:
        if not select_all:
            st.warning("⚠️ 请勾选'我已核实所有信息无误'后再提交")
        else:
            success, msg = submit_form(user_id, inputs)
            if success:
                st.success(f"✅ {msg}")
                st.balloons()
                st.rerun()
            else:
                st.error(f"❌ {msg}")
    
    if clear_btn and not disabled:
        st.info("表单已清空")
        st.rerun()
    
    if not is_before_deadline():
        st.warning("⚠️ 已超过截止时间，无法提交。")

# ==================== 管理员界面 ====================
elif role == "管理员":
    st.header("👨‍💼 管理员面板")
    
    # 统计信息
    stats = get_submission_stats()
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("已提交记录数", stats['total_submitted'])
    with col_stat2:
        st.metric("草稿记录数", stats['total_drafts'])
    with col_stat3:
        st.metric("截止时间", stats['deadline'])
    
    st.markdown("---")
    
    # 查看所有提交数据
    st.subheader("📊 所有用户提交数据")
    all_data = view_all_submissions()
    
    if all_data:
        # 转换为DataFrame格式
        df_data = []
        for user_id_key, record in all_data.items():
            row = {"用户ID": user_id_key}
            row.update(record.get("data", {}))
            row["提交时间"] = record.get("timestamp", record.get("submitted_at", ""))
            df_data.append(row)
        
        if df_data:
            import pandas as pd
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            
            # 显示详细信息
            with st.expander("查看详细信息（JSON格式）"):
                st.json(all_data)
    else:
        st.info("暂无提交数据")
    
    st.markdown("---")
    
    # 数据导出
    st.subheader("📥 数据导出")
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        if st.button("📄 导出为CSV", use_container_width=True):
            try:
                csv_path = export_submissions_csv()
                with open(csv_path, "rb") as f:
                    st.download_button(
                        "⬇️ 下载CSV文件", 
                        f, 
                        file_name=os.path.basename(csv_path),
                        mime="text/csv"
                    )
                st.success(f"✅ CSV文件已生成: {csv_path}")
            except Exception as e:
                st.error(f"❌ 导出失败: {str(e)}")
    
    with col_exp2:
        if st.button("📊 导出为Excel", use_container_width=True):
            try:
                xlsx_path = export_submissions_excel()
                with open(xlsx_path, "rb") as f:
                    st.download_button(
                        "⬇️ 下载Excel文件", 
                        f, 
                        file_name=os.path.basename(xlsx_path),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                st.success(f"✅ Excel文件已生成: {xlsx_path}")
            except Exception as e:
                st.error(f"❌ 导出失败: {str(e)}")
    
    with col_exp3:
        if st.button("📋 查看草稿", use_container_width=True):
            from form_handler import get_all_drafts
            drafts = get_all_drafts()
            if drafts:
                st.json(drafts)
            else:
                st.info("暂无草稿数据")
