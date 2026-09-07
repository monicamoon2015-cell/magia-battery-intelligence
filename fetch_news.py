import feedparser, json, re, html
from datetime import datetime, timezone
from urllib.parse import quote_plus
from pathlib import Path

# category, query
QUERIES = [
    # 고객사 / 파트너 - 한국어
    ("customer", 'CATL 배터리'),
    ("customer", 'BYD 배터리'),
    ("customer", '"LG에너지솔루션" 배터리'),
    ("customer", '"LG화학" 배터리'),
    ("customer", '"포스코퓨처엠" 배터리'),
    ("customer", '에코프로 배터리'),
    ("customer", '엘앤에프 배터리'),
    ("customer", '"엘앤에프플러스"'),
    ("customer", '삼성SDI 배터리'),
    ("customer", 'SK온 배터리'),

    # 고객사 / 파트너 - 영어
    ("customer", 'CATL battery'),
    ("customer", 'BYD battery'),
    ("customer", '"LG Energy Solution" battery'),
    ("customer", '"LG Chem" battery'),
    ("customer", '"POSCO Future M" battery'),
    ("customer", 'EcoPro battery'),
    ("customer", '"L&F" battery'),

    # 소재 / 시장 - 한국어
    ("material", 'LFP 배터리'),
    ("material", 'NCM 양극재'),
    ("material", '리튬 배터리'),
    ("material", '니켈 배터리'),
    ("material", '핵심광물 배터리'),
    ("material", '양극재 배터리'),
    ("material", '전구체 배터리'),

    # 소재 / 시장 - 영어
    ("material", 'LFP battery'),
    ("material", 'NCM cathode battery'),
    ("material", 'lithium battery'),
    ("material", '"critical minerals" battery'),

    # 품질 / 이물 - 한국어
    ("quality", '자성이물 배터리'),
    ("quality", '금속이물 배터리'),
    ("quality", '배터리 품질검사'),
    ("quality", '배터리 이물검사'),
    ("quality", '양극재 오염 품질'),
    ("quality", '배터리 SEM EDS'),

    # 품질 / 이물 - 영어
    ("quality", '"magnetic impurity" battery'),
    ("quality", '"metallic impurity" battery'),
    ("quality", '"quality control" battery manufacturing'),
    ("quality", 'contamination battery cathode'),

    # SNE Research
    ("sne", '"SNE리서치" 배터리'),
    ("sne", '"SNE Research" battery'),
]

def google_news_rss(q, lang="ko"):
    if lang == "ko":
        return f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=ko&gl=KR&ceid=KR:ko"
    return f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=en-US&gl=US&ceid=US:en"

def clean_title(title):
    return re.sub(r"\s+", " ", html.unescape(title or "")).strip()

def source_from_entry(e):
    src = getattr(e, "source", None)
    if isinstance(src, dict):
        return src.get("title","")
    return ""

def tag(text):
    t=text.lower()
    checks=[
        ("CATL",["catl"]),
        ("BYD",["byd"]),
        ("POSCO",["posco","포스코"]),
        ("LG",["lg energy","lg chem","lg에너지솔루션","lg화학"]),
        ("L&F",["l&f","엘앤에프"]),
        ("EcoPro",["ecopro","에코프로"]),
        ("Samsung SDI",["samsung sdi","삼성sdi"]),
        ("SK On",["sk on","sk온"]),
        ("SNE Research",["sne research","sne리서치"]),
        ("LFP",["lfp","lithium iron phosphate","인산철"]),
        ("NCM",["ncm"]),
        ("Lithium",["lithium","리튬"]),
        ("Critical Minerals",["critical mineral","critical minerals","핵심광물","광물"]),
        ("Quality",["quality","품질","contamination","오염","이물"]),
        ("Magnetic Impurity",["magnetic impurity","metallic impurity","자성이물","금속이물"])
    ]
    out=[]
    for name,keys in checks:
        if any(k in t for k in keys):
            out.append(name)
    return out[:7]

articles=[]
seen=set()

for category,q in QUERIES:
    # 한국어 쿼리는 한국 뉴스 우선
    is_korean = bool(re.search(r"[가-힣]", q))
    feeds = []
    if is_korean:
        feeds.append(("KR", google_news_rss(q, "ko")))
    else:
        # 영어 키워드는 한국/영문 둘 다 검색
        feeds.append(("KR", google_news_rss(q, "ko")))
        feeds.append(("EN", google_news_rss(q, "en")))

    for market, url in feeds:
        feed=feedparser.parse(url)
        for e in feed.entries[:15]:
            title=clean_title(getattr(e,"title",""))
            link=getattr(e,"link","")
            if not title or not link:
                continue

            # 제목 기준 중복 제거
            key=re.sub(r"\s+"," ",title.lower()).strip()
            if key in seen:
                continue
            seen.add(key)

            published=getattr(e,"published","")
            source=source_from_entry(e)
            tags=tag(title+" "+source)
            cats={category}

            if any(x in tags for x in ["CATL","BYD","POSCO","LG","L&F","EcoPro","Samsung SDI","SK On"]):
                cats.add("customer")
            if any(x in tags for x in ["LFP","NCM","Lithium","Critical Minerals"]):
                cats.add("material")
            if any(x in tags for x in ["Quality","Magnetic Impurity"]):
                cats.add("quality")
            if "SNE Research" in tags:
                cats.add("sne")

            articles.append({
                "title":title,
                "url":link,
                "source":source,
                "published":published,
                "category":category,
                "categories":sorted(cats),
                "tags":tags,
                "market":market
            })

# 한국 뉴스가 위로 오도록 정렬
articles.sort(key=lambda x: (0 if x.get("market")=="KR" else 1, x.get("published","")), reverse=False)

# 최대 300건
articles=articles[:300]

payload={
    "updated_at":datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    "articles":articles
}
Path("data.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
print("saved",len(articles),"articles")
