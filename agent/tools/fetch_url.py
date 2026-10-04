import httpx
from bs4 import BeautifulSoup

def fetch_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) OpenResearchAgent/0.1"
        }
        r = httpx.get(url, timeout=15, follow_redirects=True, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())
        return text[:8000]
    except Exception as e:
        return "读取失败: " + str(e)