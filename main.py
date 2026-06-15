import streamlit as st
import json
import os
from datetime import datetime
from utils.file_parser import parse_document
from utils.ai_api import generate_exam_paper, correct_exam_paper, evaluate_recitation
from utils.ocr_engine import image_to_text

st.set_page_config(
    page_title="AI文档双模式学习系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
WRONG_QUESTIONS_FILE = os.path.join(DATA_DIR, "wrong_questions.json")
EXAM_HISTORY_FILE = os.path.join(DATA_DIR, "exam_history.json")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs("static/backgrounds", exist_ok=True)

DEFAULT_BACKGROUNDS = [
    "极简深蓝",
    "清新淡绿",
    "科技暗紫",
    "温暖浅橙",
    "高级灰"
]


def load_json(file_path):
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except:
        return []


def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def set_background_style():
    bg_name = st.session_state.get("current_bg", "极简深蓝")
    bg_colors = {
        "极简深蓝": "#1e3a8a",
        "清新淡绿": "#059669",
        "科技暗紫": "#6d28d9",
        "温暖浅橙": "#ea580c",
        "高级灰": "#4b5563"
    }
    color = bg_colors.get(bg_name, "#1e3a8a")

    custom_bg = f"static/backgrounds/user_{st.session_state.get('username', '')}.png"
    if os.path.exists(custom_bg):
        bg_css = f"""
        <style>
        .stApp {{
            background-image: url("file://{custom_bg}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .stApp > div {{
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            padding: 20px;
        }}
        </style>
        """
    else:
        bg_css = f"""
        <style>
        .stApp {{
            background: linear-gradient(135deg, {color} 0%, #ffffff 100%);
        }}
        .stApp > div {{
            background-color: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 20px;
        }}
        </style>
        """
    st.markdown(bg_css, unsafe_allow_html=True)


def auth_page():
    st.markdown("""
    <div style='text-align: center; padding: 40px;'>
        <h1 style='color: #1e3a8a; font-size: 48px;'>📚 AI智能学习考试系统</h1>
        <p style='color: #666; font-size: 18px;'>文档学习 + 智能出题 + 防作弊考试 + 错题本</p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔐 登录", "✍️ 注册"])
    users = load_json(USERS_FILE)

    with tab_login:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            uname = st.text_input("用户名", key="login_user")
            pwd = st.text_input("密码", type="password", key="login_pwd")

            if st.button("登 录", use_container_width=True, type="primary"):
                if not uname or not pwd:
                    st.error("请输入用户名和密码")
                    return
                for user in users:
                    if user["username"] == uname and user["password"] == pwd:
                        st.session_state["username"] = uname
                        st.session_state["current_bg"] = user.get("bg", "极简深蓝")
                        st.session_state["bg_history"] = user.get("bg_history", [])
                        st.success(f"欢迎回来，{uname}！")
                        st.rerun()
                st.error("用户名或密码错误")

    with tab_register:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            uname_r = st.text_input("设置用户名", key="reg_user")
            pwd_r = st.text_input("设置密码", type="password", key="reg_pwd")
            pwd_confirm = st.text_input("确认密码", type="password", key="reg_pwd_confirm")

            if st.button("注 册", use_container_width=True, type="primary"):
                if not uname_r or not pwd_r:
                    st.error("请填写完整信息")
                    return
                if pwd_r != pwd_confirm:
                    st.error("两次密码不一致")
                    return
                if len(pwd_r) < 6:
                    st.error("密码长度至少6位")
                    return
                for u in users:
                    if u["username"] == uname_r:
                        st.warning("用户名已存在")
                        return
                new_user = {
                    "username": uname_r,
                    "password": pwd_r,
                    "bg": "极简深蓝",
                    "bg_history": [],
                    "register_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                users.append(new_user)
                save_json(USERS_FILE, users)
                st.success("注册成功！请登录")


def profile_page():
    st.markdown("<h2 style='color: #1e3a8a;'>👤 个人中心</h2>", unsafe_allow_html=True)
    username = st.session_state["username"]
    users = load_json(USERS_FILE)
    user_data = next((u for u in users if u["username"] == username), None)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; color: white; text-align: center;'>
            <h3>{username}</h3>
            <p>注册时间：{user_data.get('register_time', '未知')}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.subheader("🎨 主题设置")
        bg_select = st.selectbox("选择主题背景", DEFAULT_BACKGROUNDS)
        if st.button("应用主题", use_container_width=True):
            st.session_state["current_bg"] = bg_select
            hist = user_data.get("bg_history", [])
            if bg_select not in hist:
                hist.append(bg_select)
                user_data["bg_history"] = hist[-5:]
            user_data["bg"] = bg_select
            save_json(USERS_FILE, users)
            st.success("主题已切换")
            st.rerun()

        up_bg = st.file_uploader("上传自定义背景图", type=["png", "jpg", "jpeg"])
        if up_bg:
            save_path = f"static/backgrounds/user_{username}.png"
            with open(save_path, "wb") as f:
                f.write(up_bg.getbuffer())
            st.session_state["current_bg"] = save_path
            st.success("自定义背景已生效")
            st.rerun()

    st.divider()

    tab_wrong, tab_history = st.tabs(["📒 错题本", "📊 考试记录"])

    with tab_wrong:
        st.subheader("📒 我的错题本")
        wrong_all = load_json(WRONG_QUESTIONS_FILE)
        user_wrong = [w for w in wrong_all if w["username"] == username]

        if user_wrong:
            doc_list = sorted(list({item["doc_name"] for item in user_wrong}))
            sel_doc = st.selectbox("按文档筛选错题", ["全部"] + doc_list)

            filtered_wrong = user_wrong
            if sel_doc != "全部":
                filtered_wrong = [w for w in user_wrong if w["doc_name"] == sel_doc]

            st.info(f"共 {len(filtered_wrong)} 道错题")

            for idx, item in enumerate(filtered_wrong, 1):
                with st.expander(f"❌ 第{idx}题 - {item['question'][:50]}..."):
                    st.markdown(f"**题目：** {item['question']}")
                    st.markdown(f"**你的答案：** <span style='color: red;'>{item['user_ans']}</span>",
                                unsafe_allow_html=True)
                    st.markdown(f"**正确答案：** <span style='color: green;'>{item['correct_ans']}</span>",
                                unsafe_allow_html=True)
                    st.markdown(f"**解析：** {item['analysis']}")
                    st.caption(f"文档：{item['doc_name']} | 时间：{item.get('time', '未知')}")

                    if st.button(f"删除此错题", key=f"del_{idx}_{item['question'][:20]}"):
                        wrong_all.remove(item)
                        save_json(WRONG_QUESTIONS_FILE, wrong_all)
                        st.success("已删除")
                        st.rerun()
        else:
            st.success("🎉 暂无错题，继续保持！")

    with tab_history:
        st.subheader("📊 历史考试记录")
        history_all = load_json(EXAM_HISTORY_FILE)
        user_history = [h for h in history_all if h["username"] == username]

        if user_history:
            st.info(f"共参加 {len(user_history)} 次考试")

            for idx, record in enumerate(reversed(user_history), 1):
                with st.expander(f"📝 {record['doc_name']} - {record.get('score', 0)}分"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("得分", f"{record.get('score', 0)}")
                    with col2:
                        st.metric("正确率", f"{record.get('accuracy', 0)}%")
                    with col3:
                        st.metric("用时", f"{record.get('duration', 0)}分钟")

                    st.caption(f"考试时间：{record.get('exam_time', '未知')}")
                    st.caption(f"题型：{', '.join(record.get('types', []))}")
        else:
            st.info("暂无考试记录")

    st.divider()
    if st.button("🚪 退出登录", use_container_width=True, type="secondary"):
        st.session_state.clear()
        st.rerun()


def recite_mode(doc_name, content):
    st.markdown("<h3 style='color: #059669;'>🎤 背诵检查模式</h3>", unsafe_allow_html=True)

    scope = st.radio("背诵范围", ["全文背诵", "段落背诵"])
    show_text = content

    if scope == "段落背诵":
        lines = content.split('\n')
        start_idx = st.number_input("起始行号", min_value=1, max_value=len(lines), value=1)
        end_idx = st.number_input("结束行号", min_value=start_idx, max_value=len(lines),
                                  value=min(start_idx + 10, len(lines)))
        show_text = '\n'.join(lines[start_idx - 1:end_idx])

    st.text_area("参考文本", show_text, height=200, disabled=True)

    st.info("💡 提示：点击录音后朗读，AI将自动评分")
    audio = st.audio_input("🎙️ 点击开始录音")

    if audio:
        if st.button("提交检查", type="primary"):
            with st.spinner("AI正在分析..."):
                score, comment = evaluate_recitation(show_text, audio)
            st.progress(score / 100)
            st.success(f"背诵准确率：{score}%")
            st.info(f"💬 AI点评：{comment}")


def exam_interface(doc_name, content, question_types):
    st.markdown("<h3 style='color: #dc2626;'>📝 智能考试系统</h3>", unsafe_allow_html=True)

    if "paper" not in st.session_state:
        with st.spinner("AI正在生成试卷..."):
            st.session_state["paper"] = generate_exam_paper(content, question_types)
            st.session_state["exam_start_time"] = datetime.now()
            st.session_state["blur_count"] = 0
    paper = st.session_state["paper"]

    blur_count = st.session_state.get("blur_count", 0)

    st.markdown(f"""
    <script>
    let blurCount = {blur_count};
    window.addEventListener('blur', function() {{
        blurCount++;
        fetch('/api/blur?count=' + blurCount);
        if (blurCount >= 3) {{
            alert('检测到切屏超过3次，系统将自动交卷！');
            document.querySelector('button[kind="primary"]').click();
        }}
    }});
    </script>
    """, unsafe_allow_html=True)

    if blur_count >= 3:
        st.error("⚠️ 检测到切屏超过3次，系统已强制交卷！")
        if "exam_result" not in st.session_state:
            user_answers = st.session_state.get("temp_answers", {})
            result = correct_exam_paper(paper, user_answers)
            st.session_state["exam_result"] = result
            save_exam_result(doc_name, question_types, paper, user_answers, result)

    st.warning(f"⚠️ 防作弊监控中 | 切屏次数：{blur_count}/3")

    user_answers = {}

    for idx, q in enumerate(paper):
        st.markdown("---")
        st.markdown(f"**<span style='font-size: 18px; color: #1e3a8a;'>第{idx + 1}题 [{q['type']}]</span>**",
                    unsafe_allow_html=True)
        st.markdown(f"**{q['question']}**")

        q_type = q["type"]

        if q_type in ["单选题", "判断题"]:
            opts = q.get("options", [])
            user_answers[idx] = st.radio("请选择答案：", opts, key=f"q_{idx}", label_visibility="collapsed")

        elif q_type == "填空题":
            st.markdown("**答题方式（任选其一）：**")
            tab_txt, tab_photo = st.tabs(["键盘输入", "拍照手写"])

            with tab_txt:
                txt_ans = st.text_input("请输入答案", key=f"txt_{idx}")

            with tab_photo:
                st.info("📸 请拍摄手写答案，确保字迹清晰")
                photo_ans = st.file_uploader("上传答案照片", type=["jpg", "png", "jpeg"], key=f"photo_{idx}")
                if photo_ans:
                    with st.spinner("OCR识别中..."):
                        ocr_text = image_to_text(photo_ans)
                    st.success(f"识别结果：{ocr_text}")
                else:
                    ocr_text = ""

            user_answers[idx] = txt_ans if txt_ans else ocr_text

        elif q_type == "简答题":
            st.markdown("**答题方式（任选其一）：**")
            tab_txt, tab_photo = st.tabs(["键盘输入", "拍照手写"])

            with tab_txt:
                txt_ans = st.text_area("请输入答案", height=150, key=f"txt_{idx}")

            with tab_photo:
                st.info("📸 请拍摄手写答案，支持多行文字")
                photo_ans = st.file_uploader("上传答案照片", type=["jpg", "png", "jpeg"], key=f"photo_{idx}")
                if photo_ans:
                    with st.spinner("OCR识别中..."):
                        ocr_text = image_to_text(photo_ans)
                    st.success(f"识别结果：{ocr_text}")
                else:
                    ocr_text = ""

            user_answers[idx] = txt_ans if txt_ans else ocr_text

    st.session_state["temp_answers"] = user_answers

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ 提交试卷", use_container_width=True, type="primary"):
            with st.spinner("AI正在批改试卷..."):
                result = correct_exam_paper(paper, user_answers)
                st.session_state["exam_result"] = result
                save_exam_result(doc_name, question_types, paper, user_answers, result)
            st.rerun()

    if "exam_result" in st.session_state:
        st.divider()
        st.markdown("<h3 style='color: #059669;'>📊 考试成绩单</h3>", unsafe_allow_html=True)

        result = st.session_state["exam_result"]
        total = len(result)
        correct = sum(1 for r in result if "正确" in r or "✓" in r or "√" in r)
        accuracy = int((correct / total) * 100) if total > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总分", f"{accuracy}分")
        with col2:
            st.metric("正确题数", f"{correct}/{total}")
        with col3:
            start_time = st.session_state.get("exam_start_time", datetime.now())
            duration = int((datetime.now() - start_time).total_seconds() / 60)
            st.metric("用时", f"{duration}分钟")

        st.progress(accuracy / 100)

        for idx, item in enumerate(result, 1):
            is_correct = "正确" in item or "✓" in item or "√" in item
            icon = "✅" if is_correct else "❌"
            with st.expander(f"{icon} 第{idx}题 - {item[:50]}..."):
                st.markdown(item)

                if not is_correct:
                    if st.button(f"加入错题本", key=f"save_{idx}"):
                        wrong_all = load_json(WRONG_QUESTIONS_FILE)
                        wrong_all.append({
                            "username": st.session_state["username"],
                            "doc_name": doc_name,
                            "question": paper[idx - 1]["question"],
                            "user_ans": user_answers.get(idx - 1, ""),
                            "correct_ans": paper[idx - 1]["answer"],
                            "analysis": paper[idx - 1].get("analysis", ""),
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        save_json(WRONG_QUESTIONS_FILE, wrong_all)
                        st.success("已加入错题本")


def save_exam_result(doc_name, types, paper, user_answers, result):
    history = load_json(EXAM_HISTORY_FILE)
    total = len(result)
    correct = sum(1 for r in result if "正确" in r or "✓" in r or "√" in r)
    accuracy = int((correct / total) * 100) if total > 0 else 0

    start_time = st.session_state.get("exam_start_time", datetime.now())
    duration = int((datetime.now() - start_time).total_seconds() / 60)

    record = {
        "username": st.session_state["username"],
        "doc_name": doc_name,
        "types": types,
        "total_questions": total,
        "correct_count": correct,
        "score": accuracy,
        "accuracy": accuracy,
        "duration": duration,
        "exam_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "details": [
            {
                "question": paper[i]["question"],
                "user_answer": user_answers.get(i, ""),
                "correct_answer": paper[i]["answer"],
                "grading": result[i]
            }
            for i in range(total)
        ]
    }
    history.append(record)
    save_json(EXAM_HISTORY_FILE, history)


def main():
    if "username" not in st.session_state:
        auth_page()
        return

    set_background_style()

    st.sidebar.markdown(f"### 👤 {st.session_state['username']}")
    page = st.sidebar.radio("导航菜单", ["📁 上传文档", "👤 个人中心"])

    if page == "📁 上传文档":
        st.markdown("<h2 style='color: #1e3a8a;'>📁 文档学习中心</h2>", unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "上传学习资料（支持 PDF / Word / TXT / Markdown）",
            type=["pdf", "docx", "txt", "md"]
        )

        if not uploaded_file:
            st.info("👆 请上传文档开始学习")
            return

        doc_name = uploaded_file.name

        if "uploaded_content" not in st.session_state or st.session_state.get("current_doc") != doc_name:
            with st.spinner("正在解析文档..."):
                content = parse_document(uploaded_file)
                st.session_state["uploaded_content"] = content
                st.session_state["current_doc"] = doc_name

        content = st.session_state["uploaded_content"]
        st.success(f"✅ 文档解析完成：{doc_name}（共{len(content)}字符）")

        mode = st.radio("选择学习模式", ["🎤 背诵检查", "📝 知识练习"])

        if mode == "🎤 背诵检查":
            recite_mode(doc_name, content)
        else:
            st.markdown("<h4 style='color: #6d28d9;'>选择题型配置</h4>", unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)
            q_types = []

            with col1:
                if st.checkbox("单选题", value=True):
                    q_types.append("单选题")
            with col2:
                if st.checkbox("判断题", value=True):
                    q_types.append("判断题")
            with col3:
                if st.checkbox("填空题", value=True):
                    q_types.append("填空题")
            with col4:
                if st.checkbox("简答题", value=True):
                    q_types.append("简答题")

            num_questions = st.slider("每种题型数量", min_value=1, max_value=10, value=3)

            if st.button("🚀 生成试卷", use_container_width=True, type="primary") and q_types:
                st.session_state["exam_doc"] = doc_name
                st.session_state["exam_content"] = content
                st.session_state["exam_types"] = q_types
                st.session_state["num_questions"] = num_questions
                if "paper" in st.session_state:
                    del st.session_state["paper"]
                if "exam_result" in st.session_state:
                    del st.session_state["exam_result"]
                st.rerun()

        if "exam_doc" in st.session_state and "exam_content" in st.session_state:
            exam_interface(
                st.session_state["exam_doc"],
                st.session_state["exam_content"],
                st.session_state.get("exam_types", ["单选题"])
            )

    elif page == "👤 个人中心":
        profile_page()


if __name__ == "__main__":
    main()
