import PyPDF2
import docx
import chardet


def parse_document(uploaded_file):
    filename = uploaded_file.name.lower()

    try:
        if filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()

        elif filename.endswith(".docx"):
            doc = docx.Document(uploaded_file)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n".join(paragraphs)

        elif filename.endswith(".txt"):
            raw_data = uploaded_file.read()
            detected = chardet.detect(raw_data)
            encoding = detected['encoding'] if detected['encoding'] else 'utf-8'
            text = raw_data.decode(encoding, errors='ignore')
            return text

        elif filename.endswith(".md"):
            raw_data = uploaded_file.read()
            detected = chardet.detect(raw_data)
            encoding = detected['encoding'] if detected['encoding'] else 'utf-8'
            text = raw_data.decode(encoding, errors='ignore')
            return text

        else:
            return "不支持的文件格式"

    except Exception as e:
        return f"文件解析失败：{str(e)}"
