import os


def parse_document(uploaded_file):
    """
    解析上传的文件，返回文本内容。
    支持：.txt, .md, .pdf, .docx
    """
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()

    if file_extension in ['.txt', '.md']:
        return uploaded_file.getvalue().decode('utf-8', errors='ignore')

    elif file_extension == '.pdf':
        try:
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text() + '\n'
            return text
        except ImportError:
            return "❌ 需要安装 PyPDF2 库：pip install PyPDF2"

    elif file_extension == '.docx':
        try:
            import docx
            doc = docx.Document(uploaded_file)
            text = '\n'.join([para.text for para in doc.paragraphs])
            return text
        except ImportError:
            return "❌ 需要安装 python-docx 库：pip install python-docx"

    else:
        return f"不支持的文件格式：{file_extension}"
