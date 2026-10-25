"""Check active local links, all six note entries and available paper assets."""

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.paper_catalog import PAPERS, artifact

ARCHIVE_PARTS = {"sources", "upstream", "reruns", ".git", ".build", "__pycache__"}


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.ids.update([attrs["id"]] if "id" in attrs else [])
        for key in ("href", "src"):
            if key in attrs:
                self.links.append(attrs[key])


def local_links(path):
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".html":
        parser = Links()
        parser.feed(text)
        return parser.links
    if path.suffix == ".css":
        return [value.strip("\"' ") for value in re.findall(r"url\(([^)]+)\)", text)]
    if path.suffix == ".tex":
        return re.findall(r"\\(?:input|includegraphics)(?:\[[^\]]*\])?\{([^}]+)\}", text)
    if path.suffix == ".md":
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        return re.findall(r"\]\(([^)\s]+)\)", text)
    return []


def check(root, site=False):
    root = root.resolve()
    failures, count = [], 0
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in (".html", ".md", ".css", ".tex"):
            continue
        if ARCHIVE_PARTS.intersection(path.relative_to(root).parts):
            continue
        for link in local_links(path):
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            target = (root if parsed.path.startswith("/") else path.parent) / unquote(parsed.path.lstrip("/"))
            target = target.resolve()
            if path.suffix == ".tex" and not target.exists() and not target.suffix:
                target = target.with_suffix(".tex")
            count += 1
            if not target.exists():
                failures.append(f"{path.relative_to(root)}: {link}")
                continue
            if parsed.fragment and target.suffix == ".html":
                parser = Links()
                parser.feed(target.read_text(encoding="utf-8"))
                if unquote(parsed.fragment) not in parser.ids:
                    failures.append(f"{path.relative_to(root)}: missing fragment {link}")
    home = (root / "index.html").read_text(encoding="utf-8")
    if home.count('class="series-card"') != len(PAPERS):
        failures.append(f"index.html: expected exactly {len(PAPERS)} note cards")
    for path in [root / "index.html", *root.glob("*.html"), *root.glob("notes/*/*.html")]:
        text = path.read_text(encoding="utf-8")
        parser = Links()
        parser.feed(text)
        if any(paper["stem"] + ".html" in urlsplit(link).path
               for paper in PAPERS if not paper["published"] for link in parser.links):
            failures.append(f"{path.relative_to(root)}: link to unavailable draft HTML")
    if site:
        for paper in PAPERS:
            for extension in (".pdf", ".tex"):
                if not (root / "notes" / paper["folder"] / (paper["stem"] + extension)).is_file():
                    failures.append(f"missing canonical paper asset: {paper['stem']}{extension}")
            if not paper["published"] and (root / "notes" / paper["folder"] / (paper["stem"] + ".html")).exists():
                failures.append("unexpected draft HTML: " + paper["stem"])
            if paper["published"]:
                for extension in (".html", ".pdf", ".tex"):
                    if not (root / (paper["stem"] + extension)).is_file():
                        failures.append("missing legacy route: " + paper["stem"] + extension)
    else:
        for paper in PAPERS:
            if not paper["published"] and artifact(paper, ".html").exists():
                failures.append(f"Note {paper['number']} HTML should not exist")
    if failures:
        print("\n".join(failures))
        raise SystemExit(f"{len(failures)} broken or forbidden links")
    print(f"Checked {count} active local links/assets; {len(PAPERS)} note entries, "
          f"{sum(p['published'] for p in PAPERS)} HTML papers; draft status respected.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, help="Check a prepared deployment directory, including legacy downloads.")
    args = parser.parse_args()
    check(args.site or ROOT, site=args.site is not None)
