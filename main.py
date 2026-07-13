import streamlit as st
import json
import os
import re
from datetime import datetime
from utils.file_parser import parse_document
from utils.ai_api import generate_exam_paper, correct_exam_paper
from utils.ocr_engine import image_to_text

st.set_page_config(
    page_title="AI文档双模式学习系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
WRONG_QUESTIONS_FILE = os.path.join(DATA_DIR, "wrong_questions.json")
EXAM_HISTORY_FILE = os.path.join(DATA_DIR, "exam_history.json")
os.makedirs(DATA_DIR, exist_ok=True)

# ========== 多语言字典 ==========
L10N = {
    "zh": {
        "app_title": "AI智能学习考试系统",
        "login": "登录",
        "register": "注册",
        "username": "用户名",
        "password": "密码",
        "confirm_password": "确认密码",
        "login_btn": "登 录",
        "register_btn": "注 册",
        "welcome_back": "欢迎回来，{}！",
        "register_success": "注册成功！请登录",
        "user_exists": "用户名已存在",
        "pwd_mismatch": "两次密码不一致",
        "pwd_length": "密码长度至少6位",
        "fill_all": "请填写完整信息",
        "wrong_cred": "用户名或密码错误",
        "profile": "个人中心",
        "upload": "上传文档",
        "theme_setting": "主题设置",
        "apply_theme": "应用主题",
        "wrong_book": "错题本",
        "exam_history": "考试记录",
        "no_wrong": "暂无错题，继续保持！",
        "no_history": "暂无考试记录",
        "logout": "退出登录",
        "recite_mode": "背诵检查模式",
        "exam_mode": "知识练习",
        "submit_paper": "提交试卷",
        "score_report": "考试成绩单",
        "total_score": "总分",
        "correct_count": "正确题数",
        "time_used": "用时",
        "minutes": "分钟",
        "add_wrong": "加入错题本",
        "added_wrong": "已加入错题本",
        "delete_wrong": "删除此错题",
        "question_types": "选择题型配置",
        "single_choice": "单选题",
        "true_false": "判断题",
        "fill_blank": "填空题",
        "short_answer": "简答题",
        "num_questions": "每种题型数量",
        "generate_paper": "生成试卷",
        "upload_file": "上传学习资料（支持 PDF / Word / TXT / Markdown）",
        "parsing": "正在解析文档...",
        "parse_done": "✅ 文档解析完成：{}（共{}字符）",
        "select_mode": "选择学习模式",
        "recite_scope": "背诵范围",
        "full_text": "全文背诵",
        "paragraph": "段落背诵",
        "choose_paragraph": "选择背诵段落",
        "search_paragraph": "🔍 搜索段落内容（可选）",
        "search_placeholder": "输入关键词筛选...",
        "select_para_btn": "选择第 {} 段",
        "reference_text": "参考文本",
        "recording_hint": "💡 点击录音后朗读，录音结束后可回听对比",
        "start_recording": "🎙️ 点击开始录音",
        "playback": "🔊 你的录音回放",
        "self_eval": "自我评价",
        "eval_good": "😊 很好（90分）",
        "eval_ok": "😐 还行（70分）",
        "eval_poor": "😞 不太熟（50分）",
        "recite_text_display": "📖 背诵内容",
        "hide_text_mode": "🙈 隐藏文本背诵",
        "show_text_mode": "📖 显示文本背诵",
        "answer_method": "答题方式（任选其一）：",
        "keyboard_input": "键盘输入",
        "photo_input": "拍照手写",
        "enter_answer": "请输入答案",
        "upload_photo": "上传答案照片",
        "ocr_recognizing": "OCR识别中...",
        "ocr_result": "识别结果：{}",
        "ocr_fail": "OCR功能未启用，请使用键盘输入",
        "unanswered": "未作答",
        "correct": "正确",
        "wrong": "错误",
        "analysis": "解析",
        "score": "得分",
        "comment": "评价",
        "detail": "详解",
        "reference_answer": "参考答案",
        "wrong_book_empty": "🎉 暂无错题，继续保持！",
        "filter_by_doc": "按文档筛选错题",
        "all_docs": "全部",
        "delete_confirm": "已删除",
        "exam_record": "考试记录",
        "exam_time": "考试时间",
        "question_type_label": "题型",
        "register_time": "注册时间",
        "language": "语言",
        "chinese": "中文",
        "english": "English",
        "background_mode": "背景模式",
        "bg_white": "白色",
        "bg_black": "黑色",
        "bg_custom_color": "自定义颜色",
        "pick_color": "选取颜色",
        "back_to_upload": "返回出题页面",
    },
    "en": {
        "app_title": "AI Smart Learning & Exam System",
        "login": "Login",
        "register": "Register",
        "username": "Username",
        "password": "Password",
        "confirm_password": "Confirm Password",
        "login_btn": "Login",
        "register_btn": "Register",
        "welcome_back": "Welcome back, {}!",
        "register_success": "Registration successful! Please login.",
        "user_exists": "Username already exists",
        "pwd_mismatch": "Passwords do not match",
        "pwd_length": "Password must be at least 6 characters",
        "fill_all": "Please fill in all fields",
        "wrong_cred": "Incorrect username or password",
        "profile": "Profile",
        "upload": "Upload Document",
        "theme_setting": "Theme Settings",
        "apply_theme": "Apply Theme",
        "wrong_book": "Wrong Question Book",
        "exam_history": "Exam History",
        "no_wrong": "No wrong questions yet. Keep going!",
        "no_history": "No exam records yet.",
        "logout": "Logout",
        "recite_mode": "Recitation Check",
        "exam_mode": "Knowledge Practice",
        "submit_paper": "Submit Paper",
        "score_report": "Score Report",
        "total_score": "Total Score",
        "correct_count": "Correct",
        "time_used": "Time Used",
        "minutes": "min",
        "add_wrong": "Add to Wrong Book",
        "added_wrong": "Added to wrong book",
        "delete_wrong": "Delete this question",
        "question_types": "Select Question Types",
        "single_choice": "Single Choice",
        "true_false": "True/False",
        "fill_blank": "Fill in the Blank",
        "short_answer": "Short Answer",
        "num_questions": "Number per type",
        "generate_paper": "Generate Paper",
        "upload_file": "Upload study material (PDF / Word / TXT / Markdown)",
        "parsing": "Parsing document...",
        "parse_done": "✅ Document parsed: {} ({} chars)",
        "select_mode": "Select Learning Mode",
        "recite_scope": "Recite Scope",
        "full_text": "Full Text",
        "paragraph": "Paragraph",
        "choose_paragraph": "Choose a paragraph to recite",
        "search_paragraph": "🔍 Search paragraphs (optional)",
        "search_placeholder": "Enter keyword to filter...",
        "select_para_btn": "Select paragraph {}",
        "reference_text": "Reference Text",
        "recording_hint": "💡 Click to record, then playback to compare.",
        "start_recording": "🎙️ Click to start recording",
        "playback": "🔊 Your recording playback",
        "self_eval": "Self Evaluation",
        "eval_good": "😊 Good (90 points)",
        "eval_ok": "😐 Okay (70 points)",
        "eval_poor": "😞 Not good (50 points)",
        "recite_text_display": "📖 Recitation Text",
        "hide_text_mode": "🙈 Hide text",
        "show_text_mode": "📖 Show text",
        "answer_method": "Answer method (choose one):",
        "keyboard_input": "Keyboard",
        "photo_input": "Photo handwriting",
        "enter_answer": "Enter your answer",
        "upload_photo": "Upload answer photo",
        "ocr_recognizing": "OCR recognizing...",
        "ocr_result": "Result: {}",
        "ocr_fail": "OCR not available, please use keyboard.",
        "unanswered": "Not answered",
        "correct": "Correct",
        "wrong": "Wrong",
        "analysis": "Analysis",
        "score": "Score",
        "comment": "Comment",
        "detail": "Details",
        "reference_answer": "Reference Answer",
        "wrong_book_empty": "🎉 No wrong questions. Keep it up!",
        "filter_by_doc": "Filter by document",
        "all_docs": "All",
        "delete_confirm": "Deleted",
        "exam_record": "Exam Record",
        "exam_time": "Exam time",
        "question_type_label": "Types",
        "register_time": "Register time",
        "language": "Language",
        "chinese": "中文",
        "english": "English",
        "background_mode": "Background Mode",
        "bg_white": "White",
        "bg_black": "Black",
        "bg_custom_color": "Custom Color",
        "pick_color": "Pick a color",
        "back_to_upload": "Back to Upload",
    }
}

def t(key):
    lang = st.session_state.get("lang", "zh")
    return L10N.get(lang, L10N["zh"]).get(key, key)

# ========== 工具函数 ==========
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

# ========== 主题系统 ==========
THEMES = {
    "极简深蓝": {"primary": "#1e3a8a", "secondary": "#3b82f6", "bg": "#e0e7ff", "card": "#ffffff", "text": "#1e293b", "accent": "#93c5fd"},
    "清新淡绿": {"primary": "#065f46", "secondary": "#10b981", "bg": "#d1fae5", "card": "#ffffff", "text": "#064e3b", "accent": "#6ee7b7"},
    "科技暗紫": {"primary": "#5b21b6", "secondary": "#8b5cf6", "bg": "#ede9fe", "card": "#ffffff", "text": "#2e1065", "accent": "#c4b5fd"},
    "温暖浅橙": {"primary": "#c2410c", "secondary": "#f97316", "bg": "#ffedd5", "card": "#ffffff", "text": "#431407", "accent": "#fdba74"},
    "高级灰": {"primary": "#374151", "secondary": "#6b7280", "bg": "#f3f4f6", "card": "#ffffff", "text": "#111827", "accent": "#9ca3af"}
}

def set_background_style():
    theme_name = st.session_state.get("current_bg", "极简深蓝")
    theme = THEMES.get(theme_name, THEMES["极简深蓝"])
    bg_mode = st.session_state.get("background_mode", "white")
    custom_color = st.session_state.get("bg_custom_color", "#000000")
    if bg_mode == "white":
        bg_color = "#ffffff"
    elif bg_mode == "black":
        bg_color = "#000000"
    else:
        bg_color = custom_color
    bg_style = f"background: {bg_color};"
    css = f"""
    <style>
    .stApp {{ {bg_style} }}
    .stApp > div {{ background-color: rgba(255,255,255,0.95); border-radius: 10px; padding: 20px; }}
    h1,h2,h3,h4,h5,h6 {{ color: {theme['primary']} !important; }}
    .stButton > button {{ background-color: {theme['primary']} !important; color: white !important; border-radius: 8px !important; border: none !important; }}
    .stButton > button:hover {{ background-color: {theme['secondary']} !important; color: white !important; }}
    .stSidebar .sidebar-content {{ background-color: {theme['card']} !important; }}
    .stProgress > div > div {{ background-color: {theme['primary']} !important; }}
    .stMetric .stMetricValue {{ color: {theme['primary']} !important; }}
    .stExpander {{ border-left: 4px solid {theme['primary']} !important; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ========== 认证页面 ==========
def auth_page():
    tab_login, tab_register = st.tabs([f"🔐 {t('login')}", f"✍️ {t('register')}"])
    users = load_json(USERS_FILE)
    with tab_login:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            uname = st.text_input(t("username"), key="login_user")
            pwd = st.text_input(t("password"), type="password", key="login_pwd")
            if st.button(t("login_btn"), use_container_width=True, type="primary"):
                if not uname or not pwd:
                    st.error(t("fill_all"))
                    return
                for user in users:
                    if user["username"] == uname and user["password"] == pwd:
                        st.session_state["username"] = uname
                        st.session_state["current_bg"] = user.get("bg", "极简深蓝")
                        st.session_state["bg_history"] = user.get("bg_history", [])
                        st.session_state["background_mode"] = user.get("background_mode", "white")
                        st.session_state["bg_custom_color"] = user.get("bg_custom_color", "#000000")
                        st.success(t("welcome_back").format(uname))
                        st.rerun()
                st.error(t("wrong_cred"))
    with tab_register:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            uname_r = st.text_input(t("username"), key="reg_user")
            pwd_r = st.text_input(t("password"), type="password", key="reg_pwd")
            pwd_confirm = st.text_input(t("confirm_password"), type="password", key="reg_pwd_confirm")
            if st.button(t("register_btn"), use_container_width=True, type="primary"):
                if not uname_r or not pwd_r:
                    st.error(t("fill_all"))
                    return
                if pwd_r != pwd_confirm:
                    st.error(t("pwd_mismatch"))
                    return
                if len(pwd_r) < 6:
                    st.error(t("pwd_length"))
                    return
                for u in users:
                    if u["username"] == uname_r:
                        st.warning(t("user_exists"))
                        return
                new_user = {
                    "username": uname_r,
                    "password": pwd_r,
                    "bg": "极简深蓝",
                    "bg_history": [],
                    "background_mode": "white",
                    "bg_custom_color": "#000000",
                    "register_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                users.append(new_user)
                save_json(USERS_FILE, users)
                st.success(t("register_success"))

# ========== 个人中心 ==========
def profile_page():
    st.markdown(f"<h2 style='color: #1e3a8a;'>👤 {t('profile')}</h2>", unsafe_allow_html=True)
    username = st.session_state["username"]
    users = load_json(USERS_FILE)
    user_data = next((u for u in users if u["username"] == username), None)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; color: white; text-align: center;'>
            <h3>{username}</h3>
            <p>{t('register_time')}：{user_data.get('register_time', '未知')}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.subheader(f"🎨 {t('theme_setting')}")
        bg_select = st.selectbox(t("theme_setting"), list(THEMES.keys()))
        if st.button(t("apply_theme"), use_container_width=True):
            st.session_state["current_bg"] = bg_select
            hist = user_data.get("bg_history", [])
            if bg_select not in hist:
                hist.append(bg_select)
                user_data["bg_history"] = hist[-5:]
            user_data["bg"] = bg_select
            save_json(USERS_FILE, users)
            st.success(t("apply_theme"))
            st.rerun()
        st.subheader(f"🖼️ {t('background_mode')}")
        bg_opts = [t("bg_white"), t("bg_black"), t("bg_custom_color")]
        current_mode = st.session_state.get("background_mode", "white")
        mode_map = {"white": 0, "black": 1, "custom": 2}
        idx = mode_map.get(current_mode, 0)
        selected = st.radio(t("background_mode"), bg_opts, index=idx, key="bg_radio")
        if selected == t("bg_custom_color"):
            current_color = st.session_state.get("bg_custom_color", "#000000")
            new_color = st.color_picker(t("pick_color"), value=current_color, key="color_picker")
            if new_color != current_color:
                st.session_state["bg_custom_color"] = new_color
                user_data["bg_custom_color"] = new_color
                save_json(USERS_FILE, users)
                if st.session_state.get("background_mode") != "custom":
                    st.session_state["background_mode"] = "custom"
                    user_data["background_mode"] = "custom"
                    save_json(USERS_FILE, users)
                st.rerun()
            if st.session_state.get("background_mode") != "custom":
                st.session_state["background_mode"] = "custom"
                user_data["background_mode"] = "custom"
                save_json(USERS_FILE, users)
                st.rerun()
        else:
            mode_key = "white" if selected == t("bg_white") else "black"
            if st.session_state.get("background_mode") != mode_key:
                st.session_state["background_mode"] = mode_key
                user_data["background_mode"] = mode_key
                save_json(USERS_FILE, users)
                st.rerun()
    st.divider()
    tab_wrong, tab_history = st.tabs([f"📒 {t('wrong_book')}", f"📊 {t('exam_history')}"])
    with tab_wrong:
        st.subheader(f"📒 {t('wrong_book')}")
        wrong_all = load_json(WRONG_QUESTIONS_FILE)
        user_wrong = [w for w in wrong_all if w["username"] == username]
        if user_wrong:
            doc_list = sorted(list({item["doc_name"] for item in user_wrong}))
            sel_doc = st.selectbox(t("filter_by_doc"), [t("all_docs")] + doc_list)
            filtered_wrong = user_wrong
            if sel_doc != t("all_docs"):
                filtered_wrong = [w for w in user_wrong if w["doc_name"] == sel_doc]
            st.info(f"{t('wrong_book')}：共 {len(filtered_wrong)} 题")
            for idx, item in enumerate(filtered_wrong, 1):
                with st.expander(f"❌ 第{idx}题 - {item['question'][:50]}..."):
                    st.markdown(f"**{t('question_types')}：** {item['question']}")
                    st.markdown(f"**{t('wrong_book')}：** <span style='color: red;'>{item['user_ans']}</span>", unsafe_allow_html=True)
                    st.markdown(f"**{t('reference_answer')}：** <span style='color: green;'>{item['correct_ans']}</span>", unsafe_allow_html=True)
                    st.markdown(f"**{t('analysis')}：** {item['analysis']}")
                    st.caption(f"文档：{item['doc_name']} | 时间：{item.get('time', '未知')}")
                    if st.button(f"{t('delete_wrong')}", key=f"del_{idx}_{item['question'][:20]}"):
                        wrong_all.remove(item)
                        save_json(WRONG_QUESTIONS_FILE, wrong_all)
                        st.success(t("delete_confirm"))
                        st.rerun()
        else:
            st.success(t("wrong_book_empty"))
    with tab_history:
        st.subheader(f"📊 {t('exam_history')}")
        history_all = load_json(EXAM_HISTORY_FILE)
        user_history = [h for h in history_all if h["username"] == username]
        if user_history:
            st.info(f"{t('exam_history')}：共 {len(user_history)} 次")
            for idx, record in enumerate(reversed(user_history), 1):
                with st.expander(f"📝 {record['doc_name']} - {record.get('score', 0)}{t('total_score')}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(t("total_score"), f"{record.get('score', 0)}")
                    with col2:
                        st.metric(t("correct_count"), f"{record.get('accuracy', 0)}%")
                    with col3:
                        st.metric(t("time_used"), f"{record.get('duration', 0)}{t('minutes')}")
                    st.caption(f"{t('exam_time')}：{record.get('exam_time', '未知')}")
                    st.caption(f"{t('question_type_label')}：{', '.join(record.get('types', []))}")
        else:
            st.info(t("no_history"))
    st.divider()
    if st.button(f"🚪 {t('logout')}", use_container_width=True, type="secondary"):
        st.session_state.clear()
        st.rerun()

# ========== 智能段落分割 ==========
def smart_split_paragraphs(content):
    raw_paragraphs = re.split(r'\n\s*\n', content)
    paragraphs = []
    for i, para in enumerate(raw_paragraphs):
        text = para.strip().replace('\n', ' ')
        if len(text) < 10:
            continue
        preview = text[:60] + "..." if len(text) > 60 else text
        paragraphs.append({
            "index": i + 1,
            "full_text": text,
            "preview": preview,
            "char_count": len(text)
        })
    return paragraphs

# ========== 背诵模式（修复搜索：全文任意位置匹配）==========
def recite_mode(doc_name, content):
    st.markdown(f"<h3 style='color: #059669;'>🎤 {t('recite_mode')}</h3>", unsafe_allow_html=True)

    paragraphs = smart_split_paragraphs(content)
    if not paragraphs:
        st.warning("文档内容过短，无法分段背诵")
        return

    st.markdown(f"### 📝 {t('choose_paragraph')}")

    # 搜索框（固定 key 保留输入）
    search = st.text_input(
        t("search_paragraph"),
        placeholder=t("search_placeholder"),
        key="search_para_input"
    )

    # 改进的过滤逻辑：忽略大小写，同时检查 full_text 和 preview
    filtered = paragraphs
    if search:
        search_lower = search.lower()
        filtered = [
            p for p in paragraphs
            if search_lower in p["full_text"].lower() or search_lower in p["preview"].lower()
        ]
        if not filtered:
            st.warning("没有找到包含该关键词的段落，请尝试其他词")

    selected_paragraph = None
    cols_per_row = 2
    for i in range(0, len(filtered), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i + j
            if idx < len(filtered):
                para = filtered[idx]
                with cols[j]:
                    st.markdown(f"""
                    <div style='border: 2px solid #e0e0e0; border-radius: 10px; 
                                padding: 15px; margin: 5px 0; background: #f9fafb;'>
                        <p style='font-size: 14px; color: #333;'>{para['preview']}</p>
                        <p style='font-size: 12px; color: #666;'>{para['char_count']} 字</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(t("select_para_btn").format(para['index']), key=f"sel_{para['index']}"):
                        selected_paragraph = para["full_text"]
                        st.rerun()

    if selected_paragraph:
        st.markdown("---")
        st.markdown(f"### {t('recite_text_display')}")
        mode = st.radio("模式", [t("show_text_mode"), t("hide_text_mode")], horizontal=True)
        if mode == t("show_text_mode"):
            st.text_area("原文", selected_paragraph, height=200, disabled=True)
        else:
            st.info("文本已隐藏，请尝试背诵")

        st.info(t("recording_hint"))
        audio = st.audio_input(t("start_recording"))

        if audio:
            st.audio(audio, format="audio/wav")
            st.markdown(f"### {t('self_eval')}")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(t("eval_good"), use_container_width=True):
                    st.success("继续保持！")
            with col2:
                if st.button(t("eval_ok"), use_container_width=True):
                    st.info("还需努力！")
            with col3:
                if st.button(t("eval_poor"), use_container_width=True):
                    st.warning("多读几遍！")
    else:
        st.info("👆 请选择一个段落开始背诵")

# ========== 考试界面（无防作弊，未作答强制0分）==========
def exam_interface(doc_name, content, question_types, num_per_type):
    st.markdown(f"<h3 style='color: #dc2626;'>📝 {t('exam_mode')}</h3>", unsafe_allow_html=True)

    if "paper" not in st.session_state:
        with st.spinner(t("parsing")):
            st.session_state["paper"] = generate_exam_paper(content, question_types, num_per_type)
            st.session_state["exam_start_time"] = datetime.now()

    paper = st.session_state["paper"]

    if "exam_result" in st.session_state:
        display_exam_result(doc_name)
        return

    user_answers = {}
    for idx, q in enumerate(paper):
        st.markdown("---")
        st.markdown(f"**<span style='font-size: 18px; color: #1e3a8a;'>第{idx + 1}题 [{q['type']}]</span>**", unsafe_allow_html=True)
        st.markdown(f"**{q['question']}**")
        q_type = q["type"]

        if q_type in ["单选题", "判断题"]:
            opts = q.get("options", [])
            choice = st.radio(
                t("single_choice") if q_type == "单选题" else t("true_false"),
                opts, key=f"q_{idx}", label_visibility="collapsed", index=None
            )
            if choice:
                if q_type == "单选题":
                    user_answers[idx] = re.sub(r'^[\d]\.\s*', '', choice)
                else:
                    user_answers[idx] = choice
            else:
                user_answers[idx] = ""
        elif q_type == "填空题":
            st.markdown(f"**{t('answer_method')}**")
            tab_txt, tab_photo = st.tabs([t("keyboard_input"), t("photo_input")])
            with tab_txt:
                txt_ans = st.text_input(t("enter_answer"), key=f"txt_{idx}")
            with tab_photo:
                photo_ans = st.file_uploader(t("upload_photo"), type=["jpg", "png", "jpeg"], key=f"photo_{idx}")
                ocr_text = ""
                if photo_ans:
                    with st.spinner(t("ocr_recognizing")):
                        ocr_text = image_to_text(photo_ans)
                    st.success(t("ocr_result").format(ocr_text))
            user_answers[idx] = txt_ans if txt_ans else ocr_text
        elif q_type == "简答题":
            st.markdown(f"**{t('answer_method')}**")
            tab_txt, tab_photo = st.tabs([t("keyboard_input"), t("photo_input")])
            with tab_txt:
                txt_ans = st.text_area(t("enter_answer"), height=150, key=f"txt_{idx}")
            with tab_photo:
                photo_ans = st.file_uploader(t("upload_photo"), type=["jpg", "png", "jpeg"], key=f"photo_{idx}")
                ocr_text = ""
                if photo_ans:
                    with st.spinner(t("ocr_recognizing")):
                        ocr_text = image_to_text(photo_ans)
                    st.success(t("ocr_result").format(ocr_text))
            user_answers[idx] = txt_ans if txt_ans else ocr_text

    st.session_state["temp_answers"] = user_answers
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(f"✅ {t('submit_paper')}", use_container_width=True, type="primary"):
            with st.spinner(t("parsing")):
                result = correct_exam_paper(paper, user_answers)
                for i, res in enumerate(result):
                    if user_answers.get(i, "").strip() == "":
                        res["is_correct"] = False
                        if "得分：" in res.get("display", ""):
                            res["display"] = re.sub(r'得分：\d+', '得分：0', res["display"])
                        res["display"] = res.get("display", "").replace("✅", "❌")
                st.session_state["exam_result"] = result
                save_exam_result(doc_name, question_types, paper, user_answers, result)
            st.rerun()

def display_exam_result(doc_name):
    st.divider()
    st.markdown(f"<h3 style='color: #059669;'>📊 {t('score_report')}</h3>", unsafe_allow_html=True)
    result = st.session_state["exam_result"]
    paper = st.session_state.get("paper", [])
    user_answers = st.session_state.get("temp_answers", {})
    total = len(result)
    total_score = 0
    for item in result:
        disp = item["display"]
        score_match = re.search(r'得分：(\d+)', disp)
        if score_match:
            total_score += int(score_match.group(1))
        else:
            if item["is_correct"]:
                total_score += 100
    avg_score = int(total_score / total) if total > 0 else 0
    correct = sum(1 for r in result if r.get("is_correct", False))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(t("total_score"), f"{avg_score}分")
    with col2:
        st.metric(t("correct_count"), f"{correct}/{total}")
    with col3:
        start_time = st.session_state.get("exam_start_time", datetime.now())
        duration = int((datetime.now() - start_time).total_seconds() / 60)
        st.metric(t("time_used"), f"{duration}{t('minutes')}")
    st.progress(avg_score / 100)

    for idx, item in enumerate(result):
        is_correct = item.get("is_correct", False)
        if user_answers.get(idx, "").strip() == "" and is_correct:
            is_correct = False
            item["display"] = item.get("display", "").replace("✅", "❌")
        icon = "✅" if is_correct else "❌"
        with st.expander(f"{icon} 第{idx + 1}题"):
            st.markdown(item.get("display", ""))
            if not is_correct and paper:
                if st.button(f"{t('add_wrong')}", key=f"save_result_{idx}"):
                    wrong_all = load_json(WRONG_QUESTIONS_FILE)
                    wrong_all.append({
                        "username": st.session_state["username"],
                        "doc_name": doc_name,
                        "question": paper[idx]["question"],
                        "user_ans": user_answers.get(idx, ""),
                        "correct_ans": paper[idx]["answer"],
                        "analysis": paper[idx].get("analysis", ""),
                        "reference": paper[idx].get("reference", ""),
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    save_json(WRONG_QUESTIONS_FILE, wrong_all)
                    st.success(t("added_wrong"))
    if st.button(f"🔙 {t('back_to_upload')}", use_container_width=True):
        for key in ["paper", "exam_result", "temp_answers"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

def save_exam_result(doc_name, types, paper, user_answers, result):
    history = load_json(EXAM_HISTORY_FILE)
    total = len(result)
    total_score = 0
    correct = 0
    for r in result:
        if r["is_correct"]:
            correct += 1
        disp = r["display"]
        score_match = re.search(r'得分：(\d+)', disp)
        if score_match:
            total_score += int(score_match.group(1))
    avg_score = int(total_score / total) if total > 0 else 0
    start_time = st.session_state.get("exam_start_time", datetime.now())
    duration = int((datetime.now() - start_time).total_seconds() / 60)
    record = {
        "username": st.session_state["username"],
        "doc_name": doc_name,
        "types": types,
        "total_questions": total,
        "correct_count": correct,
        "score": avg_score,
        "accuracy": avg_score,
        "duration": duration,
        "exam_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "details": [
            {
                "question": paper[i]["question"],
                "user_answer": user_answers.get(i, ""),
                "correct_answer": paper[i]["answer"],
                "is_correct": r.get("is_correct", False),
                "grading": r.get("display", "")
            }
            for i, r in enumerate(result)
        ]
    }
    history.append(record)
    save_json(EXAM_HISTORY_FILE, history)

# ========== 主函数 ==========
def main():
    if "lang" not in st.session_state: st.session_state.lang = "zh"
    if "background_mode" not in st.session_state: st.session_state["background_mode"] = "white"
    if "bg_custom_color" not in st.session_state: st.session_state["bg_custom_color"] = "#000000"

    col1, col2 = st.columns([7, 1])
    with col1:
        st.markdown(f"<h1 style='margin:0;'>{t('app_title')}</h1>", unsafe_allow_html=True)
    with col2:
        lang_opts = [t("chinese"), t("english")]
        current_lang = "zh" if st.session_state.lang == "zh" else "en"
        idx = 0 if current_lang == "zh" else 1
        choice = st.selectbox(t("language"), lang_opts, index=idx, key="lang_selector")
        if choice == t("chinese") and st.session_state.lang != "zh":
            st.session_state.lang = "zh"; st.rerun()
        elif choice == t("english") and st.session_state.lang != "en":
            st.session_state.lang = "en"; st.rerun()

    if "username" not in st.session_state:
        auth_page()
        return

    set_background_style()
    st.sidebar.markdown(f"### 👤 {st.session_state['username']}")
    page = st.sidebar.radio(t("upload"), [f"📁 {t('upload')}", f"👤 {t('profile')}"])

    if page == f"📁 {t('upload')}":
        st.markdown(f"<h2 style='color: #1e3a8a;'>📁 {t('upload')}</h2>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(t("upload_file"), type=["pdf", "docx", "txt", "md"])
        if not uploaded_file:
            st.info("👆 " + t("upload_file"))
            return
        doc_name = uploaded_file.name
        if "uploaded_content" not in st.session_state or st.session_state.get("current_doc") != doc_name:
            with st.spinner(t("parsing")):
                content = parse_document(uploaded_file)
                st.session_state["uploaded_content"] = content
                st.session_state["current_doc"] = doc_name
        content = st.session_state["uploaded_content"]
        st.success(t("parse_done").format(doc_name, len(content)))
        mode = st.radio(t("select_mode"), [f"🎤 {t('recite_mode')}", f"📝 {t('exam_mode')}"])
        if mode == f"🎤 {t('recite_mode')}":
            recite_mode(doc_name, content)
        else:
            st.markdown(f"<h4 style='color: #6d28d9;'>{t('question_types')}</h4>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            q_types = []
            with col1:
                if st.checkbox(t("single_choice"), value=True): q_types.append("单选题")
            with col2:
                if st.checkbox(t("true_false"), value=True): q_types.append("判断题")
            with col3:
                if st.checkbox(t("fill_blank"), value=True): q_types.append("填空题")
            with col4:
                if st.checkbox(t("short_answer"), value=True): q_types.append("简答题")
            num_questions = st.slider(t("num_questions"), min_value=1, max_value=10, value=3)
            if st.button(f"🚀 {t('generate_paper')}", use_container_width=True, type="primary") and q_types:
                for key in ["paper", "exam_result", "temp_answers"]:
                    if key in st.session_state: del st.session_state[key]
                st.session_state["exam_doc"] = doc_name
                st.session_state["exam_content"] = content
                st.session_state["exam_types"] = q_types
                st.session_state["num_questions"] = num_questions
                st.rerun()
        if "exam_doc" in st.session_state and "exam_content" in st.session_state:
            exam_interface(
                st.session_state["exam_doc"],
                st.session_state["exam_content"],
                st.session_state.get("exam_types", ["单选题"]),
                st.session_state["num_questions"]
            )
    else:
        profile_page()

if __name__ == "__main__":
    main()
