import os

def write_file(path, content):
    try:
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return "已写入 " + path + " (" + str(len(content)) + " 字符)"
    except Exception as e:
        return "写入失败: " + str(e)