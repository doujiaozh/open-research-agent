import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote

def web_search(query, top_k=5):
    try:
        url = "https://cn.bing.com/search?q=" + quote(query) + "&mkt=zh-CN&setlang=zh-CN&ensearch=0"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            r = client.get(url, headers=headers)
        if r.status_code != 200:
            return "搜索失败 HTTP " + str(r.status_code)

        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for li in soup.select("li.b_algo")[:top_k]:
            h2 = li.find("h2")
            if not h2:
                continue
            a = h2.find("a")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a.get("href", "")
            snippet_tag = li.find("p")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            results.append("- " + title + "\n  " + href + "\n  " + snippet)
        return "\n".join(results) if results else "无结果"
    except Exception as e:
        return "搜索失败: " + str(e)