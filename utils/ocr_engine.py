try:
    import easyocr

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("警告：easyocr未安装，拍照答题功能将不可用")

reader = None


def get_reader():
    global reader
    if reader is None and OCR_AVAILABLE:
        try:
            reader = easyocr.Reader(["ch_sim", "en"], gpu=False)
        except Exception as e:
            print(f"OCR引擎初始化失败：{e}")
    return reader


def image_to_text(image_file):
    if not image_file:
        return ""

    if not OCR_AVAILABLE:
        return "OCR功能未启用，请使用键盘输入"

    try:
        ocr_reader = get_reader()
        if not ocr_reader:
            return "OCR引擎加载失败"

        image_bytes = image_file.read()
        results = ocr_reader.readtext(image_bytes, detail=0, paragraph=True)

        text = " ".join(results)
        return text.strip()

    except Exception as e:
        print(f"OCR识别失败：{e}")
        return f"识别失败：{str(e)}"
