import feedparser, json, re, html
from datetime import datetime, timezone
from urllib.parse import quote_plus
from pathlib import Path

QUERIES = [
    ("customer", 'CATL battery'),
    ("customer", 'BYD battery'),
    ("customer", '"LG Energy Solution" battery'),
    ("customer", '"LG Chem" battery'),
    ("customer", '"POSCO Future M" battery'),
    ("customer", 'EcoPro battery'),
    ("customer", '"L&F" battery'),
    ("material", 'LFP battery'),
    ("material", 'NCM cathode battery'),
    ("material", 'lithium battery'),
    ("material", '"critical minerals" battery'),
    ("quality", '"magnetic impurity" battery'),
    ("quality", '"metallic impurity" battery'),
    ("quality", '"quality control" battery manufacturing'),
    ("quality", 'contamination battery cathode'),
    ("sne", '"SNE Research" battery'),
]

def google_news_rss(q):
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
        ("CATL",["catl"]),("BYD",["byd"]),("POSCO",["posco"]),("LG",["lg energy","lg chem"]),
        ("L&F",["l&f","엘앤에프"]),("EcoPro",["ecopro","에코프로"]),("SNE Research",["sne research"]),
        ("LFP",["lfp","lithium iron phosphate"]),("NCM",["ncm"]),("Lithium",["lithium","리튬"]),
        ("Critical Minerals",["critical mineral"]),("Quality",["quality","contamination","impurity"]),
        ("Magnetic Impurity",["magnetic impurity","metallic impurity"])
    ]
    out=[]
    for name,keys in checks:
        if any(k in t for k in keys): out.append(name)
    return out[:6]

articles=[]
seen=set()
for category,q in QUERIES:
    feed=feedparser.parse(google_news_rss(q))
    for e in feed.entries[:20]:
        title=clean_title(getattr(e,"title",""))
        url=getattr(e,"link","")
        if not title or not url: continue
        key=title.lower()
        if key in seen: continue
        seen.add(key)
        published=getattr(e,"published","")
        source=source_from_entry(e)
        tags=tag(title+" "+source)
        cats={category}
        if any(x in tags for x in ["CATL","BYD","POSCO","LG","L&F","EcoPro"]): cats.add("customer")
        if any(x in tags for x in ["LFP","NCM","Lithium","Critical Minerals"]): cats.add("material")
        if any(x in tags for x in ["Quality","Magnetic Impurity"]): cats.add("quality")
        if "SNE Research" in tags: cats.add("sne")
        articles.append({"title":title,"url":url,"source":source,"published":published,"category":category,"categories":sorted(cats),"tags":tags})

articles=articles[:250]
payload={"updated_at":datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),"articles":articles}
Path("data.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
print("saved",len(articles),"articles")
