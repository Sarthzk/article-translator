#!/usr/bin/env python3
# translator.py - grabs an article (url / file / pdf / plain text) and translates it to english

import argparse
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from pypdf import PdfReader

CHUNK_LIMIT = 4500  # google translate chokes past ~5000 chars, leaving some headroom
TIMEOUT = 15
RETRIES = 3


def is_url(text):
    parsed = urlparse(text.strip())
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def fetch_article(url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ArticleTranslator/1.0)"}
    resp = requests.get(url, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    paras = [p for p in paras if p]
    if not paras:
        raise ValueError("couldn't find any readable text on that page")

    return "\n\n".join(paras)


def extract_pdf(path):
    reader = PdfReader(path)
    pages = [pg.extract_text() or "" for pg in reader.pages]
    text = "\n\n".join(p.strip() for p in pages if p.strip())
    if not text:
        raise ValueError("no text in that pdf - might be a scanned/image-only file")
    return text


def get_input_text(source):
    if is_url(source):
        return fetch_article(source)

    if source.lower().endswith(".pdf") and Path(source).is_file():
        return extract_pdf(source)

    # otherwise assume it's a path to a text file, and if that fails just
    # treat whatever was passed in as the actual text
    try:
        with open(source, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return content
    except (FileNotFoundError, IsADirectoryError, OSError):
        pass

    return source


def make_chunks(text, limit=CHUNK_LIMIT):
    paragraphs = text.split("\n\n")
    chunks = []
    buf = ""

    for para in paragraphs:
        combined = f"{buf}\n\n{para}" if buf else para

        if len(combined) <= limit:
            buf = combined
            continue

        if buf:
            chunks.append(buf)
            buf = ""

        if len(para) <= limit:
            buf = para
        else:
            # rare case - one paragraph on its own is bigger than the limit,
            # so just hard-split it
            for i in range(0, len(para), limit):
                chunks.append(para[i:i + limit])

    if buf:
        chunks.append(buf)

    return chunks


def translate_chunk(translator, chunk):
    err = None
    for attempt in range(1, RETRIES + 1):
        try:
            result = translator.translate(chunk)
            # google sometimes returns a 200 with an html error page instead
            # of actually failing, so check for that too
            if result and "That’s an error" not in result and "<html" not in result.lower():
                return result
            err = RuntimeError("translation service returned an error page")
        except Exception as e:
            err = e

        if attempt < RETRIES:
            time.sleep(1.5 * attempt)

    raise RuntimeError(f"translation failed after {RETRIES} tries: {err}")


def translate(text):
    translator = GoogleTranslator(source="auto", target="en")
    return "\n\n".join(translate_chunk(translator, c) for c in make_chunks(text))


def main():
    parser = argparse.ArgumentParser(description="Translate an article into English.")
    parser.add_argument("source", nargs="?", help="URL, file path, or raw text. Reads stdin if omitted.")
    parser.add_argument("-o", "--output", help="Write result to this file instead of printing it.")
    args = parser.parse_args()

    if args.source:
        source = args.source
    elif not sys.stdin.isatty():
        source = sys.stdin.read().strip()
    else:
        parser.error("give me a URL, file path, or some text (or pipe it in via stdin)")

    if not source:
        parser.error("no input text found")

    try:
        text = get_input_text(source)
        result = translate(text)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"saved to {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
