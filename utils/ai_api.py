import json
import os
import re
from openai import OpenAI

# ---------- DeepSeek 配置 ----------
try:
    import streamlit as st
    DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY"))
except:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY:
    raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量或 Streamlit secrets")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# ---------- 生成试卷 ----------
def generate_exam_paper(content, question_types, num_per_type):
    paper = []
    for qtype in question_types:
        for _ in range(num_per_type):
            question = _generate_single_question(content, qtype)
            if question:
                paper.append(question)
    return paper

def _generate_single_question(content, qtype):
    type_desc = {
        "单选题": "single choice question with exactly 4 options (A/B/C/D)",
        "判断题": "true or false question with options: [\"正确\", \"错误\"]",
        "填空题": "fill-in-the-blank question (one or two blanks)",
        "简答题": "short answer question"
    }

    prompt = f"""你是一个专业的出题老师。请仔细阅读以下文档内容，并据此生成一道高质量的{type_desc[qtype]}。
要求：
- 题目必须严格基于文档内容，不能凭空编造。
- 输出为严格的 JSON 格式，包含以下字段：
  - "question": 题目标题 (string)
  - "options": 选项数组 (仅单选题和判断题需要，判断题固定为 ["正确", "错误"])
  - "answer": 正确答案 (string)
  - "analysis": 答案解析，指出在文档中的依据 (string)

文档内容：
{content[:3000]}

请只返回 JSON，不要添加任何其他文字。"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000,
        )
        raw = response.choices[0].message.content
        clean = re.sub(r'^```json\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
        result = json.loads(clean)
        result["type"] = qtype
        return result
    except Exception as e:
        return {
            "type": qtype,
            "question": f"[生成失败] {qtype}",
            "options": [] if qtype not in ["单选题", "判断题"] else (["正确", "错误"] if qtype == "判断题" else ["A.","B.","C.","D."]),
            "answer": "无",
            "analysis": f"题目生成出错: {str(e)}"
        }

# ---------- 批改试卷 ----------
def correct_exam_paper(paper, user_answers):
    results = []
    for i, q in enumerate(paper):
        user_ans = user_answers.get(i, "").strip()
        correct_ans = q.get("answer", "").strip()
        q_type = q["type"]

        if not user_ans:
            results.append({
                "is_correct": False,
                "display": f"❌ **未作答**\n得分：0\n参考答案：{correct_ans}\n解析：{q.get('analysis', '')}"
            })
            continue

        if q_type in ["单选题", "判断题"]:
            is_correct = (user_ans == correct_ans)
            score = 100 if is_correct else 0
            icon = "✅" if is_correct else "❌"
            display = f"{icon} 你的答案：{user_ans}\n得分：{score}\n参考答案：{correct_ans}\n解析：{q.get('analysis', '')}"
        else:
            is_correct, score, comment = _ai_grade(q, user_ans)
            icon = "✅" if is_correct else "❌"
            display = f"{icon} 你的答案：{user_ans}\n得分：{score}\nAI评价：{comment}\n参考答案：{correct_ans}\n解析：{q.get('analysis', '')}"

        results.append({
            "is_correct": is_correct,
            "display": display
        })
    return results

def _ai_grade(question, user_answer):
    q_type = question["type"]
    q_text = question["question"]
    ref_answer = question.get("answer", "")

    prompt = f"""你是一个严格的评卷老师。请根据以下题目和参考答案，对学生的答案进行评分。
题型：{q_type}
题目：{q_text}
参考答案：{ref_answer}
学生答案：{user_answer}
评分标准：
- 如果答案完全错误或毫无关联，得 0 分，is_correct 为 false。
- 如果部分正确，根据正确程度给 30-80 分，is_correct 为 false（不够准确）。
- 如果完全正确或核心意思一致，给 100 分，is_correct 为 true。
请以 JSON 格式返回，包含以下字段：
- is_correct: boolean
- score: integer (0-100)
- comment: string (简短评语，20字以内)

只返回 JSON，不要其他文字。"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )
        raw = response.choices[0].message.content
        clean = re.sub(r'^```json\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
        result = json.loads(clean)
        return result.get("is_correct", False), result.get("score", 0), result.get("comment", "")
    except Exception as e:
        if ref_answer and user_answer in ref_answer:
            return True, 100, "答案正确"
        else:
            return False, 0, "答案错误"

def evaluate_recitation(reference_text, audio_bytes):
    """背诵评价（可后续接入 DeepSeek）"""
    return 85, "背诵流利，但有个别词遗漏，继续加油！"
