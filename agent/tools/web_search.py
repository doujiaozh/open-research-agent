import httpx

import re

from bs4 import BeautifulSoup

from urllib.parse import quote



STOP = set(["最新", "进展", "研究", "消息", "动态", "新闻", "信息", "报告",

            "分析", "解读", "观察", "深度", "相关", "有关", "关于", "数据",

            "中国", "全球", "市场", "产业", "行业", "领域", "方面", "情况",

            "问题", "内容", "全部", "百度", "百科", "知乎", "新浪", "腾讯",

            "搜狐", "网易", "今日", "头条"])



TECH_KEYWORDS = set([

    "2026", "2025", "2024", "量产", "产能", "成本", "技术", "路线",

    "中科院", "宁德时代", "比亚迪", "丰田", "三星", "国轩", "赣锋", "清陶",

    "硫化物", "氧化物", "聚合物", "能量密度", "电解质", "产业链",

    "政策", "专利", "投资", "生产", "装车", "上市", "材料", "研发",

    "电芯", "负极", "正极", "充电", "续航", "锂电",

])



UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0"

HDRS = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"}





def _core_terms(query):

    terms = []

    for w in re.findall(r"[\u4e00-\u9fa5]{2,8}", query):

        if w in STOP:

            continue

        terms.append(w)

    return terms





def _has_core(text, core_terms):

    """核心词必须出现完整词 或 前 3 字"""

    for t in core_terms:

        if t in text:

            return True

        if len(t) >= 3 and t[:3] in text:

            return True

    return False





def _strict_match(title, snippet, core_terms):

    """严格: 必须有核心词(完整/前3字) 且 有技术关键词"""

    if not core_terms:

        return False

    text = title + " " + snippet

    if not _has_core(text, core_terms):

        return False

    for kw in TECH_KEYWORDS:

        if kw in text:

            return True

    return False





def _loose_match(title, snippet, core_terms):

    """宽松: 只要有核心词"""

    if not core_terms:

        return True

    text = title + " " + snippet

    return _has_core(text, core_terms)





def _try_baidu(query, top_k=5):

    try:

        url = "https://www.baidu.com/s?wd=" + quote(query) + "&rn=20"

        r = httpx.Client(timeout=20, follow_redirects=True).get(url, headers=HDRS)

        if r.status_code != 200:

            return []

        core_terms = _core_terms(query)

        soup = BeautifulSoup(r.text, "html.parser")

        out = []

        seen = set()

        for h3 in soup.find_all("h3"):

            if len(out) >= top_k:

                break

            a = h3.find("a")

            if not a:

                continue

            title = a.get_text(strip=True)

            href = a.get("href", "")

            if not title or not href or href in seen:

                continue

            seen.add(href)

            parent = h3.find_parent("div")

            snippet = ""

            if parent:

                sp = parent.find("span", class_=re.compile(r"content|abstract"))

                if not sp:

                    sp = parent.find("span")

                if sp:

                    snippet = sp.get_text(strip=True)[:200]

            if not _loose_match(title, snippet, core_terms):

                continue

            out.append("- " + title + "\n  " + href + "\n  " + snippet)

        return out

    except Exception:

        return []





def _try_bing_strict(query, top_k=5):

    try:

        url = "https://cn.bing.com/search?q=" + quote(query) + "&mkt=zh-CN"

        r = httpx.Client(timeout=20, follow_redirects=True).get(url, headers=HDRS)

        if r.status_code != 200:

            return []

        core_terms = _core_terms(query)

        soup = BeautifulSoup(r.text, "html.parser")

        out = []

        for li in soup.select("li.b_algo"):

            if len(out) >= top_k:

                break

            h2 = li.find("h2")

            if not h2:

                continue

            a = h2.find("a")

            if not a:

                continue

            title = a.get_text(strip=True)

            href = a.get("href", "")

            p = li.find("p")

            snippet = p.get_text(strip=True) if p else ""

            if not _strict_match(title, snippet, core_terms):

                continue

            out.append("- " + title + "\n  " + href + "\n  " + snippet)

        return out

    except Exception:

        return []





def web_search(query, top_k=5):

    baidu = _try_baidu(query, top_k)

    if len(baidu) >= top_k:

        return "\n".join(baidu)

    bing = _try_bing_strict(query, top_k - len(baidu))

    combined = baidu + bing

    if not combined:

        return "无结果"

    out = "\n".join(combined)

    if bing and len(baidu) < top_k:

        out += "\n[百度 " + str(len(baidu)) + " 条 + Bing 严格 " + str(len(bing)) + " 条]"

    return out

