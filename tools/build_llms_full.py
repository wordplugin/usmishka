#!/usr/bin/env python3
"""主要ページの本文を Markdown に変換し、AI向けの /llms-full.txt を生成する。

使い方(リポジトリ直下で):
    python3 tools/build_llms_full.py

ページの文章を更新したら、このスクリプトを再実行して llms-full.txt も更新してください。
標準ライブラリのみで動作します。
"""
import datetime
import html
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://usmishka.jp"

# (ファイル, 公開URL) — llms-full.txt に収録する順番
PAGES = [
    ("index.html", "/"),
    ("kodomo.html", "/kodomo.html"),
    ("minsei.html", "/minsei.html"),
    ("bunka.html", "/bunka.html"),
    ("matching.html", "/matching.html"),
    ("wanpak.html", "/wanpak.html"),
    ("kifukinkitei.html", "/kifukinkitei.html"),
    ("en.html", "/en.html"),
    ("uk.html", "/uk.html"),
]

# 中身ごと読み飛ばす要素
SKIP_TAGS = {"script", "style", "head", "header", "footer", "nav", "noscript",
             "svg", "button", "select", "template", "iframe"}
SKIP_CLASSES = {"lightbox", "lb", "crumb", "cta-row"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "source", "track", "wbr"}
BLOCK_TAGS = {"p", "div", "section", "article", "figure", "figcaption", "ul",
              "ol", "table", "tr", "blockquote", "dl", "dt", "dd", "main", "aside"}


class MD(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []          # 完成した行
        self.buf = []          # 組み立て中の行
        self.prefix = ""       # 行頭記号(見出し・リスト)
        self.skip = 0          # スキップ中のネスト深さ
        self.stack = []        # 開いているタグ(スキップ判定用)
        self.link = None       # 処理中の <a> の href
        self.link_text = []
        self.cells = None      # 処理中の表の行
        self.cell = None
        self.title = ""
        self.in_title = False
        self.in_heading = False
        self.time_start = None
        self.last_time = None

    # --- 出力ヘルパー ---
    def flush(self):
        text = re.sub(r"[ \t　]+", " ", "".join(self.buf)).strip()
        text = re.sub(r" *\n *", "\n", text)
        if text:
            self.out.append(self.prefix + text)
        self.buf, self.prefix = [], ""

    def blank(self):
        self.flush()
        if self.out and self.out[-1] != "":
            self.out.append("")

    def emit(self, s):
        if self.cell is not None:
            self.cell.append(s)
        elif self.link is not None:
            self.link_text.append(s)
        else:
            self.buf.append(s)

    # --- パーサー ---
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.in_title = True
        if self.skip:
            if tag not in VOID_TAGS:
                self.skip += 1
            return
        classes = set((a.get("class") or "").split())
        if tag in SKIP_TAGS or classes & SKIP_CLASSES or a.get("aria-hidden") == "true":
            if tag not in VOID_TAGS:
                self.skip = 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5"):
            # 直前の <time>(年表の日付)は見出しに含める
            carry = "".join(self.buf).strip()
            dated = carry and carry == self.last_time
            if dated:
                self.buf = []
            self.blank()
            self.prefix = "#" * (int(tag[1]) + 1) + " "
            self.in_heading = True
            if dated:
                self.buf = [carry, " "]
        elif tag == "li":
            self.flush()
            self.prefix = "- "
        elif tag == "tr":
            self.flush()
            self.cells = []
        elif tag in ("td", "th") and self.cells is not None:
            self.cell = []
        elif tag in BLOCK_TAGS:
            self.blank() if tag in ("p", "section", "table", "ul", "ol", "blockquote") else self.flush()
        elif tag == "br":
            self.emit(" " if self.in_heading else "\n")
        elif tag == "a":
            href = a.get("href", "")
            if href.startswith("/"):
                href = BASE + href
            self.link = href if href.startswith(("http", "mailto:")) else ""
            self.link_text = []
        elif tag in ("em", "small", "span", "time", "b", "strong") and self.buf:
            self.emit(" ")
        if tag == "time":
            self.time_start = len(self.buf)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if self.skip:
            self.skip -= 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5"):
            self.in_heading = False
            self.blank()
        elif tag in ("td", "th") and self.cell is not None:
            self.cells.append(re.sub(r"\s+", " ", "".join(self.cell)).strip())
            self.cell = None
        elif tag == "tr" and self.cells is not None:
            row = [c for c in self.cells if c]
            if row:
                self.out.append("- " + " / ".join(row))
            self.cells = None
        elif tag == "a" and self.link is not None:
            text = re.sub(r"\s+", " ", "".join(self.link_text)).strip()
            href, self.link = self.link, None
            if text:
                self.emit(f"[{text}]({href})" if href else text)
        elif tag in ("em", "time", "b", "strong"):
            if tag == "time" and self.time_start is not None:
                self.last_time = "".join(self.buf[self.time_start:]).strip()
                self.time_start = None
            self.emit(" ")
        elif tag in BLOCK_TAGS or tag == "li":
            self.flush()

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.skip:
            return
        self.emit(data.replace("\n", " "))

    def markdown(self):
        self.flush()
        text = "\n".join(self.out)
        return re.sub(r"\n{3,}", "\n\n", text).strip()


def convert(path):
    p = MD()
    p.feed(path.read_text(encoding="utf-8"))
    return html.unescape(p.title).strip(), p.markdown()


def main():
    today = datetime.date.today().isoformat()
    parts = [
        "# 一般社団法人ウスミシュカ (Usmishka Association) — 全文",
        "",
        "> usmishka.jp の主要ページ本文を、AIアシスタント・検索エンジン向けにMarkdown化したものです。"
        "要約版は https://usmishka.jp/llms.txt をご覧ください。",
        f"> 生成日: {today} / 正式な情報は各ページのURLを出典としてください。",
        "",
    ]
    for file, url in PAGES:
        title, body = convert(ROOT / file)
        parts += ["", "---", "", f"# {title}", "", f"URL: {BASE}{url}", "", body, ""]
    out = ROOT / "llms-full.txt"
    out.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
