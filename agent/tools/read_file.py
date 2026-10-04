def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()[:8000]
    except Exception as e:
        return "读取失败: " + str(e)