from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup
import markdown


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "README.md"
DEFAULT_DIST = ROOT / "dist"
DEFAULT_HTML = DEFAULT_DIST / "integrated-assignment.html"
DEFAULT_PDF = DEFAULT_DIST / "Mustkeem_Ahmad_Integrated_Assignment.pdf"
CSS_PATH = ROOT / "styles" / "pdf.css"

EDGE_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render the assignment markdown to HTML and PDF."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Markdown source file.",
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=DEFAULT_HTML,
        help="Output HTML path.",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=DEFAULT_PDF,
        help="Output PDF path.",
    )
    parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Only generate HTML.",
    )
    return parser.parse_args()


def find_browser() -> Path:
    for candidate in EDGE_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "No supported browser found. Install Microsoft Edge or Google Chrome."
    )


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_html(markdown_text: str, source: Path) -> str:
    body = markdown.markdown(
        markdown_text,
        extensions=[
            "extra",
            "tables",
            "fenced_code",
            "sane_lists",
            "toc",
        ],
        output_format="html5",
    )

    soup = BeautifulSoup(body, "html.parser")
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and href.startswith("assets/"):
            link["href"] = href

    css = read_text(CSS_PATH)
    title = source.stem.replace("-", " ").title()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <base href="{ROOT.as_uri()}/" />
  <style>
{css}
  </style>
</head>
<body>
  <main class="document">
{str(soup)}
  </main>
</body>
</html>
"""


def write_html(output_path: Path, html: str) -> None:
    ensure_parent(output_path)
    output_path.write_text(html, encoding="utf-8")


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    ensure_parent(pdf_path)
    browser = find_browser()

    command = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=5000",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path.resolve().as_uri(),
    ]

    subprocess.run(command, check=True)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF output was not created: {pdf_path}")


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    html_path = args.html.resolve()
    pdf_path = args.pdf.resolve()

    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")
    if not CSS_PATH.exists():
        raise FileNotFoundError(f"CSS file not found: {CSS_PATH}")

    html = build_html(read_text(source), source)
    write_html(html_path, html)

    if args.skip_pdf:
        print(f"HTML generated at: {html_path}")
        return 0

    render_pdf(html_path, pdf_path)
    print(f"HTML generated at: {html_path}")
    print(f"PDF generated at: {pdf_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"Browser PDF generation failed: {exc}", file=sys.stderr)
        raise
    except Exception as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        raise
