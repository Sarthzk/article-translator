# Article Translator

A small command-line tool that takes an article — from a URL, a text file, a PDF, or just raw text — and translates it into English.

Source language is auto-detected, so it works with pretty much any language Google Translate supports.

## Setup

```bash
git clone https://github.com/Sarthzk/article-translator.git
cd article-translator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

Translate an article from a URL:

```bash
python translator.py "https://example.com/some-article"
```

Translate a text file:

```bash
python translator.py article.txt
```

Translate a PDF:

```bash
python translator.py article.pdf
```

Translate raw text directly:

```bash
python translator.py "Bonjour le monde, ceci est un article."
```

Pipe text in via stdin:

```bash
cat article.txt | python translator.py
```

Save the output to a file instead of printing it:

```bash
python translator.py article.txt -o translated.txt
```

## Notes

- Long articles are automatically split into chunks under the hood, translated, and stitched back together.
- Scanned/image-only PDFs won't work since there's no text to extract (no OCR here).
- If you didn't activate the venv, you can run it directly with `./venv/bin/python translator.py ...` instead.
