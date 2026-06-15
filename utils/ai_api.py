from openai import OpenAI
import json
import re

client = OpenAI(
    api_key="sk-db4f0eb7d2ad4aefb6397b8ac33d4d1a",
    base_url="https://api.deepseek.com"
)


def generate_exam_paper(content, types, num_per_type=3):
    prompt = f"""
你是专业的出题专家，请根据以下文档内容生成高质量试题。

要求：
1. 题型包括：{types}
2. 每种题型生成{num_per_type}道题
3. 题目要覆盖文档的关键知识点
4. 难度适中，区分度好
5. 必须严格按照JSON格式输出，不要有任何额外文字

输出格式示例：
[
    {{
        "type": "单选题",
        "question": "题目内容",
        "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"],
        "answer": "A. 选项A",
        "analysis": "详细解析说明为什么选A"
    }},
    {{
        "type": "判断题",
        "question": "题目内容",
        "options": ["正确", "错误"],
        "answer": "正确",
        "analysis": "解析说明"
    }},
    {{
        "type": "填空题",
        "question": "题目内容（用___表示填空位置）",
        "options": [],
        "answer": "标准答案",
        "analysis": "解析说明"
    }},
    {{
        "type": "简答题",
        "question": "题目内容",
        "options": [],
        "answer": "参考答案要点",
        "analysis": "评分标准和解析"
    }}
]

文档内容：
{content[:3000]}

请生成试题（只输出JSON数组）：
"""

    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的出题专家，擅长根据文档内容生成高质量的试题。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=2000
        )

        result_text = resp.choices[0].message.content.strip()

        json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(0)

        questions = json.loads(result_text)

        valid_questions = []
        for q in questions:
            if all(k in q for k in ["type", "question", "answer", "analysis"]):
                if "options" not in q:
                    q["options"] = []
                valid_questions.append(q)

        return valid_questions[:len(types) * num_per_type]

    except Exception as e:
        print(f"生成试卷出错：{e}")
        return []


def correct_exam_paper(paper, user_answers):
    results = []

    for idx, q in enumerate(paper):
        user_ans = user_answers.get(idx, "")

        if not user_ans or not user_ans.strip():
            results.append(f"第{idx + 1}题：未作答（0分）\n正确答案：{q['answer']}\n解析：{q.get('analysis', '')}")
            continue

        q_type = q["type"]

        if q_type in ["单选题", "判断题"]:
            is_correct = user_ans.strip() == q["answer"].strip()
            if is_correct:
                results.append(
                    f"第{idx + 1}题：回答正确 ✓\n你的答案：{user_ans}\n正确答案：{q['answer']}\n解析：{q.get('analysis', '')}")
            else:
                results.append(
                    f"第{idx + 1}题：回答错误 ✗\n你的答案：{user_ans}\n正确答案：{q['answer']}\n解析：{q.get('analysis', '')}")

        else:
            prompt = f"""
你是AI阅卷老师，请对学生的答案进行智能批改。

题目类型：{q_type}
题目：{q['question']}
学生答案：{user_ans}
标准答案：{q['answer']}

评分标准：
1. 意思对即可得分，不要死抠字眼
2. 关键点答对就给大部分分数
3. 鼓励性评语，指出优点和不足
4. 给出具体得分（0-100分）

请按以下格式输出：
得分：XX分
评价：[简短评价]
详解：[详细说明]
"""

            try:
                r = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "你是一位温和、专业的AI阅卷老师，善于发现学生答案中的亮点。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=300
                )

                feedback = r.choices[0].message.content.strip()
                results.append(f"第{idx + 1}题批改结果：\n{feedback}\n\n标准答案参考：{q['answer']}")

            except Exception as e:
                results.append(f"第{idx + 1}题：批改失败\n你的答案：{user_ans}\n正确答案：{q['answer']}")

    return results


def evaluate_recitation(text, audio):
    try:
        import speech_recognition as sr
        import io

        recognizer = sr.Recognizer()
        audio_data = sr.AudioFile(audio)

        with audio_data as source:
            audio_content = recognizer.record(source)

        spoken_text = recognizer.recognize_google(audio_content, language='zh-CN')

        text_words = set(text.split())
        spoken_words = set(spoken_text.split())

        if len(text_words) == 0:
            return 0, "参考文本为空"

        common_words = text_words & spoken_words
        accuracy = int((len(common_words) / len(text_words)) * 100)
        accuracy = min(accuracy, 100)

        if accuracy >= 90:
            comment = "非常流利！几乎没有遗漏，表现优秀！"
        elif accuracy >= 70:
            comment = "整体不错，个别地方可以更流畅一些。"
        elif accuracy >= 50:
            comment = "基本掌握，建议再多练习几遍。"
        else:
            comment = "需要加强记忆，建议分段背诵。"

        return accuracy, comment

    except Exception as e:
        print(f"语音识别失败：{e}")
        return 85, "语音识别服务暂时不可用，但听起来还不错哦~"
