from __future__ import annotations

import html
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT_DIR = DOCS / "_prince"
PRINCE = Path(r"C:\Program Files\Prince\engine\bin\prince.exe")


CSS = """
@page {
  size: A4;
  margin: 18mm 18mm 17mm 18mm;
  @top-right {
    content: string(doc-title);
    color: #6b7280;
    font-size: 8.5pt;
  }
  @bottom-center {
    content: "智慧团建一键学 Bot 使用说明  |  第 " counter(page) " 页";
    color: #6b7280;
    font-size: 8.5pt;
  }
}

body {
  font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
  color: #202124;
  font-size: 10.5pt;
  line-height: 1.55;
}

h1 {
  string-set: doc-title content();
  color: #0b2545;
  font-size: 23pt;
  line-height: 1.2;
  margin: 0 0 12pt 0;
  padding-bottom: 8pt;
  border-bottom: 1.2pt solid #d9e2ec;
}

h2 {
  color: #2e74b5;
  font-size: 15.5pt;
  margin: 18pt 0 7pt;
  page-break-after: avoid;
}

h3 {
  color: #1f4d78;
  font-size: 12.2pt;
  margin: 12pt 0 5pt;
  page-break-after: avoid;
}

p {
  margin: 0 0 7pt 0;
}

ul, ol {
  margin: 0 0 8pt 20pt;
  padding: 0;
}

li {
  margin: 0 0 3pt 0;
}

code {
  font-family: Consolas, "Courier New", monospace;
  font-size: 9pt;
  background: #f2f4f7;
  padding: 0.5pt 2pt;
  border-radius: 2pt;
}

pre {
  font-family: Consolas, "Courier New", monospace;
  font-size: 8.7pt;
  line-height: 1.35;
  background: #f2f4f7;
  border: 0.6pt solid #d9e2ec;
  border-radius: 4pt;
  padding: 7pt 8pt;
  margin: 4pt 0 9pt 0;
  white-space: pre-wrap;
}

pre code {
  background: transparent;
  padding: 0;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 6pt 0 11pt 0;
  page-break-inside: avoid;
}

th {
  background: #e8eef5;
  color: #1f4d78;
  font-weight: 700;
}

th, td {
  border: 0.6pt solid #d9e2ec;
  padding: 5pt 6pt;
  vertical-align: top;
  font-size: 9.4pt;
  line-height: 1.42;
}

strong {
  font-weight: 700;
}

.meta {
  background: #f7fbff;
  border: 0.6pt solid #d9e2ec;
  padding: 7pt 8pt;
  margin: 0 0 12pt 0;
}
"""


def inline_md(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return text


def flush_paragraph(out: list[str], paragraph: list[str]) -> None:
    if not paragraph:
        return
    text = " ".join(line.strip() for line in paragraph).strip()
    if text:
        out.append(f"<p>{inline_md(text)}</p>")
    paragraph.clear()


def flush_list(out: list[str], list_items: list[str], ordered: bool) -> None:
    if not list_items:
        return
    tag = "ol" if ordered else "ul"
    out.append(f"<{tag}>")
    for item in list_items:
        out.append(f"<li>{inline_md(item)}</li>")
    out.append(f"</{tag}>")
    list_items.clear()


def flush_table(out: list[str], table_lines: list[str]) -> None:
    if not table_lines:
        return
    rows = []
    for line in table_lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(cells)
    if len(rows) >= 2 and all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in rows[1]):
        header = rows[0]
        body = rows[2:]
        out.append("<table>")
        out.append("<thead><tr>" + "".join(f"<th>{inline_md(c)}</th>" for c in header) + "</tr></thead>")
        out.append("<tbody>")
        for row in body:
            out.append("<tr>" + "".join(f"<td>{inline_md(c)}</td>" for c in row) + "</tr>")
        out.append("</tbody></table>")
    else:
        for line in table_lines:
            out.append(f"<p>{inline_md(line)}</p>")
    table_lines.clear()


def markdown_to_html(markdown: str, title: str) -> str:
    out: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    table_lines: list[str] = []
    in_code = False
    code_lines: list[str] = []
    ordered = False

    lines = markdown.splitlines()
    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph(out, paragraph)
            flush_list(out, list_items, ordered)
            flush_table(out, table_lines)
            if in_code:
                out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            flush_paragraph(out, paragraph)
            flush_list(out, list_items, ordered)
            flush_table(out, table_lines)
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph(out, paragraph)
            flush_list(out, list_items, ordered)
            table_lines.append(stripped)
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            flush_paragraph(out, paragraph)
            flush_list(out, list_items, ordered)
            flush_table(out, table_lines)
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline_md(heading.group(2))}</h{level}>")
            continue

        bullet = re.match(r"^-\s+(.+)$", stripped)
        if bullet:
            flush_paragraph(out, paragraph)
            flush_table(out, table_lines)
            if list_items and ordered:
                flush_list(out, list_items, ordered)
            ordered = False
            list_items.append(bullet.group(1))
            continue

        number = re.match(r"^\d+\.\s+(.+)$", stripped)
        if number:
            flush_paragraph(out, paragraph)
            flush_table(out, table_lines)
            if list_items and not ordered:
                flush_list(out, list_items, ordered)
            ordered = True
            list_items.append(number.group(1))
            continue

        flush_list(out, list_items, ordered)
        flush_table(out, table_lines)
        paragraph.append(stripped)

    flush_paragraph(out, paragraph)
    flush_list(out, list_items, ordered)
    flush_table(out, table_lines)
    if in_code:
        out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")

    body = "\n".join(out)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>
"""


def render_one(md_path: Path, pdf_path: Path) -> None:
    title = md_path.stem
    html_path = OUT_DIR / f"{md_path.stem}.html"
    html_path.write_text(markdown_to_html(md_path.read_text(encoding="utf-8"), title), encoding="utf-8")
    subprocess.run([str(PRINCE), str(html_path), "-o", str(pdf_path)], check=True)
    print(pdf_path)


def main() -> None:
    if not PRINCE.exists():
        raise FileNotFoundError(f"Prince not found: {PRINCE}")
    OUT_DIR.mkdir(exist_ok=True)
    render_one(DOCS / "管理员使用说明.md", DOCS / "管理员使用说明.pdf")
    render_one(DOCS / "普通成员使用说明.md", DOCS / "普通成员使用说明.pdf")


if __name__ == "__main__":
    main()
