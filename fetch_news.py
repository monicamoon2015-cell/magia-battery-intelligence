import feedparser, json, re, html
from datetime import datetime, timezone
from urllib.parse import quote_plus
from pathlib import Path
from email.utils import parsedate_to_datetime

QUERIES = [
    # L&F / L&F Plus 강화
    ("customer", '엘앤에프'),
    ("customer", '"엘앤에프플러스"'),
    ("customer", '"L&F"'),
    ("customer", '"L&F Plus"'),
    ("customer", '엘앤에프 LFP'),
    ("customer", '엘앤에프 양극재'),
    ("customer", '엘앤에프 투자'),
    ("customer", '엘앤에프 CB'),
    ("customer", '엘앤에프 전환사채'),
    ("customer", '엘앤에프 공급계약'),
    ("customer", '엘앤에프 수주'),
    ("customer", '엘앤에프 증설'),
    ("customer", '엘앤에프 품질'),
    ("customer", '엘앤에프플러스 LFP'),
    ("customer", '엘앤에프플러스 양극재'),

    # 주요 고객사 / 파트너
    ("customer", 'CATL 배터리'),
    ("customer", 'BYD 배터리'),
    ("customer", '"LG에너지솔루션" 배터리'),
    ("customer", '"LG화학" 배터리'),
    ("customer", '"포스코퓨처엠" 배터리'),
    ("customer", '에코프로 배터리'),
    ("customer", '삼성SDI 배터리'),
    ("customer", 'SK온 배터리'),
    ("customer", 'CATL battery'),
    ("customer", 'BYD battery'),
    ("customer", '"LG Energy Solution" battery'),
    ("customer", '"LG Chem" battery'),
    ("customer", '"POSCO Future M" battery'),
    ("customer", 'EcoPro battery'),

    # 소재 / 시장
    ("material", 'LFP 배터리'),
    ("material", 'NCM 양극재'),
    ("material", '리튬 배터리'),
    ("material", '니켈 배터리'),
    ("material", '핵심광물 배터리'),
    ("material", '양극재 배터리'),
    ("material", '전구체 배터리'),
    ("material", 'LFP battery'),
    ("material", 'NCM cathode battery'),
    ("material", 'lithium battery'),
    ("material", '"critical minerals" battery'),

    # 품질 / 이물
    ("quality", '자성이물 배터리'),
    ("quality", '금속이물 배터리'),
    ("quality", '배터리 품질검사'),
    ("quality", '배터리 이물검사'),
    ("quality", '양극재 오염 품질'),
    ("quality", '배터리 SEM EDS'),
    ("quality", '"magnetic impurity" battery'),
    ("quality", '"metallic impurity" battery'),
    ("quality", '"quality control" battery manufacturing'),
    ("quality", 'contamination battery cathode'),

    # SNE Research
    ("sne", '"SNE리서치" 배터리'),
    ("sne", '"SNE Research" battery'),
]

# 산업/사업 관련성이 높은 키워드
INDUSTRY_KEYWORDS = [
    "배터리","이차전지","양극재","음극재","전구체","lfp","ncm","nca","lmfp",
    "리튬","니켈","코발트","망간","흑연","광물","핵심광물",
    "투자","증설","공장","생산","생산능력","capa","캐파",
    "수주","공급계약","공급","계약","납품","고객사",
    "매출","영업이익","실적","적자","흑자","전환사채","cb","유상증자","자금조달",
    "품질","검사","이물","자성이물","금속이물","오염","불량",
    "기술","개발","특허","공정","자동화","sem","eds","icp",
    "시장","점유율","출하량","판매량","수요","공급망","원재료","가격",
    "정책","규제","관세","ira","crma","수출","수입",
    "battery","cathode","anode","precursor","lithium","nickel","cobalt",
    "investment","plant","factory","production","capacity","supply","contract",
    "order","revenue","profit","earnings","quality","inspection","contamination",
    "technology","patent","market","share","shipment","demand","supply chain"
]

# CSR / 홍보성 기사 제외 키워드
EXCLUDE_KEYWORDS = [
    "봉사","봉사활동","자원봉사","기부","기탁","후원","사회공헌","장학금",
    "지역사회","지역 상생","상생협력 행사","캠페인","환경정화","플로깅",
    "헌혈","임직원 행사","임직원 봉사","체육대회","가족행사","문화행사",
    "나눔","성금","물품 지원","연탄","김장","복지관","취약계층",
    "csr","volunteer","volunteering","donation","charity","sponsorship",
    "community service","scholarship","social contribution"
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

def is_industry_relevant(text):
    t = text.lower()

    # CSR성 기사면 우선 제외
    if any(k.lower() in t for k in EXCLUDE_KEYWORDS):
        return False

    # 산업 관련 키워드가 하나 이상 있으면 포함
    return any(k.lower() in t for k in INDUSTRY_KEYWORDS)

def tag(text):
    t=text.lower()
    checks=[
        ("CATL",["catl"]),
        ("BYD",["byd"]),
        ("POSCO",["posco","포스코"]),
        ("LG",["lg energy","lg chem","lg에너지솔루션","lg화학"]),
        ("L&F Plus",["l&f plus","엘앤에프플러스"]),
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
        ("Magnetic Impurity",["magnetic impurity","metallic impurity","자성이물","금속이물"]),
        ("Investment",["투자","investment","cb","전환사채","유상증자","증설"]),
        ("Supply / Order",["공급계약","수주","공급","order","contract"]),
        ("Market",["시장","점유율","출하량","수요","market","share","shipment","demand"]),
        ("Policy",["정책","규제","관세","ira","crma","policy","regulation","tariff"])
    ]
    out=[]
    for name,keys in checks:
        if any(k in t for k in keys):
            out.append(name)
    return out[:8]

articles=[]
seen=set()

for category,q in QUERIES:
    is_korean = bool(re.search(r"[가-힣]", q))
    feeds = []

    if is_korean:
        feeds.append(("KR", google_news_rss(q, "ko")))
    else:
        feeds.append(("KR", google_news_rss(q, "ko")))
        feeds.append(("EN", google_news_rss(q, "en")))

    for market, url in feeds:
        feed = feedparser.parse(url)
        limit = 25 if ("엘앤에프" in q or "L&F" in q) else 15

        for e in feed.entries[:limit]:
            title = clean_title(getattr(e, "title", ""))
            link = getattr(e, "link", "")
            if not title or not link:
                continue

            source = source_from_entry(e)
            combined = title + " " + source

            # 산업 관련성 필터
            if not is_industry_relevant(combined):
                continue

            key = re.sub(r"\s+"," ",title.lower()).strip()
            if key in seen:
                continue
            seen.add(key)

            published = getattr(e, "published", "")
            tags = tag(combined)
            cats = {category}

            if any(x in tags for x in ["CATL","BYD","POSCO","LG","L&F","L&F Plus","EcoPro","Samsung SDI","SK On"]):
                cats.add("customer")
            if any(x in tags for x in ["LFP","NCM","Lithium","Critical Minerals"]):
                cats.add("material")
            if any(x in tags for x in ["Quality","Magnetic Impurity"]):
                cats.add("quality")
            if "SNE Research" in tags:
                cats.add("sne")

            articles.append({
                "title": title,
                "url": link,
                "source": source,
                "published": published,
                "category": category,
                "categories": sorted(cats),
                "tags": tags,
                "market": market
            })

def safe_date(a):
    try:
        return parsedate_to_datetime(a.get("published","")).timestamp()
    except Exception:
        return 0

# 최신 기사 우선
articles.sort(key=safe_date, reverse=True)

# 최대 350건
articles = articles[:350]

payload = {
    "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    "articles": articles
}

Path("data.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("saved", len(articles), "industry-relevant articles")
