#!/usr/bin/env python3
"""主要ページに JSON-LD 構造化データと OGP メタタグを埋め込む。

AI検索・AIアシスタント・検索エンジン・SNSが「どんな団体の、何のページか」を
機械的に正しく理解できるようにするためのもの。

使い方(リポジトリ直下で):
    python3 tools/add_structured_data.py

<!-- structured-data:start --> 〜 <!-- structured-data:end --> の間を毎回書き換えるので、
何度実行しても重複しません。団体情報(役員・住所など)が変わったら ORG を直して再実行してください。
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://usmishka.jp"
START, END = "<!-- structured-data:start -->", "<!-- structured-data:end -->"

ORG_ID = f"{BASE}/#organization"
SITE_ID = f"{BASE}/#website"
CHUJO_ID = f"{BASE}/#hideto-chujo"
KAMADA_ID = f"{BASE}/#nagaaki-kamada"

ORG = {
    "@type": "NGO",
    "@id": ORG_ID,
    "name": "一般社団法人ウスミシュカ",
    "alternateName": ["ウスミシュカ", "Usmishka Association", "Usmishka", "Асоціація «Усмішка»", "Усмішка"],
    "url": f"{BASE}/",
    "logo": {"@type": "ImageObject", "url": f"{BASE}/assets/logo.png", "width": 1032, "height": 248},
    "image": f"{BASE}/assets/gallery/2026-03-24_2036432589850837236.jpg",
    "description": "ウクライナ現地で戦争の影響を受けた子供と女性を支援し、日本とウクライナの交流を推進する非営利型一般社団法人。"
                   "支援キャラバンは100回を超え、避難搬送、病院・避難施設支援、わんぱく相撲ウクライナ大会、"
                   "ドニプロ国立大学内「ウクライナ日本センター」の運営などを行う。",
    "foundingDate": "2022-07",
    "email": "info@usmishka.jp",
    "address": {
        "@type": "PostalAddress",
        "postalCode": "761-0196",
        "addressCountry": "JP",
        "addressRegion": "香川県",
        "addressLocality": "高松市",
        "streetAddress": "牟礼町牟礼2246番地",
    },
    "areaServed": [{"@type": "Country", "name": "Ukraine"}, {"@type": "Country", "name": "Japan"}],
    "knowsAbout": ["ウクライナ人道支援", "避難搬送(エバキュエーション)", "子供の支援", "小児科病院支援",
                   "わんぱく相撲", "日本文化交流", "Humanitarian aid in Ukraine"],
    "employee": [{"@id": KAMADA_ID}, {"@id": CHUJO_ID}],
    "contactPoint": {"@type": "ContactPoint", "contactType": "お問い合わせ", "email": "info@usmishka.jp",
                     "availableLanguage": ["Japanese", "English"]},
    "potentialAction": {
        "@type": "DonateAction",
        "name": "支援金の寄付",
        "target": f"{BASE}/#donate",
        "recipient": {"@id": ORG_ID},
    },
}

PEOPLE = [
    {
        "@type": "Person",
        "@id": KAMADA_ID,
        "name": "鎌田長明",
        "jobTitle": "代表理事",
        "worksFor": {"@id": ORG_ID},
        "description": "鎌長製衡株式会社 代表取締役社長 / 公益社団法人日本青年会議所 2019年度会頭",
    },
    {
        "@type": "Person",
        "@id": CHUJO_ID,
        "name": "中條秀人",
        "alternateName": ["Pika中條秀人", "Pika中條", "Hideto Chujo", "Pika Chujo", "Хідето Чуджо"],
        "jobTitle": "理事",
        "worksFor": {"@id": ORG_ID},
        "description": "ウスミシュカの現地活動の中心。2022年5月からピカチュウ姿でウクライナ各地を回り支援を続ける。"
                       "ドニプロペトロウシク州軍政局ボランティア評議会 日本代表 / "
                       "ドニプロ国立大学内「ウクライナ日本センター・ウスミシュカ」責任者。",
        "sameAs": ["https://x.com/ChujoPika"],
    },
]

WEBSITE = {
    "@type": "WebSite",
    "@id": SITE_ID,
    "url": f"{BASE}/",
    "name": "一般社団法人ウスミシュカ",
    "alternateName": "Usmishka Association",
    "inLanguage": ["ja", "en", "uk"],
    "publisher": {"@id": ORG_ID},
}

# ファイル: (言語, og:locale, パンくず[(名前, URL or None)], ページ種別)
PAGES = {
    "index.html": ("ja", "ja_JP", None, "home"),
    "en.html": ("en", "en_US", None, "home"),
    "uk.html": ("uk", "uk_UA", None, "home"),
    "kodomo.html": ("ja", "ja_JP", [("ホーム", "/"), ("活動内容", "/#activities"), ("子供たちへの支援", None)], "page"),
    "minsei.html": ("ja", "ja_JP", [("ホーム", "/"), ("活動内容", "/#activities"), ("民生への支援", None)], "page"),
    "bunka.html": ("ja", "ja_JP", [("ホーム", "/"), ("活動内容", "/#activities"), ("文化交流", None)], "page"),
    "matching.html": ("ja", "ja_JP", [("ホーム", "/"), ("活動内容", "/#activities"), ("マッチング", None)], "page"),
    "wanpak.html": ("ja", "ja_JP", [("ホーム", "/"), ("わんぱく相撲", "/#sumo"), ("全国大会への招致", None)], "page"),
    "kifukinkitei.html": ("ja", "ja_JP", [("ホーム", "/"), ("寄付金等取扱規程", None)], "page"),
}
LOCALES = {"ja_JP", "en_US", "uk_UA"}


def first(pattern, text, default=""):
    m = re.search(pattern, text, re.S)
    return html.unescape(m.group(1)).strip() if m else default


def build(file, src):
    lang, locale, crumbs, kind = PAGES[file]
    title = first(r"<title>(.*?)</title>", src)
    desc = first(r'<meta name="description" content="([^"]*)"', src)
    url = first(r'<link rel="canonical" href="([^"]*)"', src)
    body = src.split("</header>", 1)[-1]
    img = first(r'<img[^>]*?src="([^"]+)"', body, "/assets/gallery/2026-03-24_2036432589850837236.jpg")
    img = BASE + img if img.startswith("/") else img

    page = {
        "@type": "WebPage",
        "@id": url + "#webpage",
        "url": url,
        "name": title,
        "description": desc,
        "inLanguage": lang,
        "isPartOf": {"@id": SITE_ID},
        "about": {"@id": ORG_ID},
        "publisher": {"@id": ORG_ID},
        "primaryImageOfPage": {"@type": "ImageObject", "url": img},
    }
    graph = [page, ORG, *PEOPLE, WEBSITE]
    if crumbs:
        items = []
        for i, (name, path) in enumerate(crumbs, 1):
            item = {"@type": "ListItem", "position": i, "name": name}
            item["item"] = BASE + path if path else url
            items.append(item)
        page["breadcrumb"] = {"@id": url + "#breadcrumb"}
        graph.insert(1, {"@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": items})

    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))
    ld = ld.replace("</", "<\\/")  # </script> の誤終了を防ぐ

    esc = lambda s: html.escape(s, quote=True)
    meta = [
        f'<meta property="og:type" content="{"website" if kind == "home" else "article"}">',
        '<meta property="og:site_name" content="一般社団法人ウスミシュカ">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
        f'<meta property="og:url" content="{esc(url)}">',
        f'<meta property="og:image" content="{esc(img)}">',
        f'<meta property="og:locale" content="{locale}">',
        *[f'<meta property="og:locale:alternate" content="{l}">' for l in sorted(LOCALES - {locale})
          if kind == "home"],
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">',
        '<link rel="alternate" type="text/markdown" title="AI向けサイト概要 (llms.txt)" href="/llms.txt">',
        f'<script type="application/ld+json">\n{ld}\n</script>',
    ]
    return "\n".join([START, *meta, END])


def main():
    for file in PAGES:
        path = ROOT / file
        src = path.read_text(encoding="utf-8")
        block = build(file, src)
        if START in src:
            src = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, src, flags=re.S)
        else:
            src = re.sub(r'(<link rel="canonical"[^>]*>\n)', lambda m: m.group(1) + block + "\n", src, count=1)
            if START not in src:
                raise SystemExit(f"{file}: canonical リンクが見つかりません")
        path.write_text(src, encoding="utf-8")
        print("updated", file)


if __name__ == "__main__":
    main()
