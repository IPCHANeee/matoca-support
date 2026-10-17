"""PRIVACY.md から matoca/privacy.html を生成する。

ポリシーの原文は PRIVACY.md ひとつだけにして、公開ページはそこから作る。
文面を直すときは PRIVACY.md を編集して、このスクリプトを実行する。

    python3 tools/build_privacy.py
"""

import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "PRIVACY.md"
OUTPUT = ROOT / "matoca" / "privacy.html"

TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Matoca プライバシーポリシー</title>
<meta name="description" content="Matoca（まとまるカレンダー・タスク）のプライバシーポリシー。取得する情報、保存場所、Googleユーザーデータの取り扱い（Limited Use）について。">
<link rel="stylesheet" href="/assets/style.css">
</head>
<body>
<header class="site">
  <div class="wrap">
    <a class="home" href="/">あいぴー</a>
    <nav><a href="/matoca/">Matoca</a><a href="/matoca/privacy.html">プライバシーポリシー</a></nav>
  </div>
</header>

<main class="wrap">
{body}
</main>

<footer class="site">
  <div class="wrap">
    <p><a href="/matoca/">Matoca サポート</a> &middot; <a href="/">あいぴー</a></p>
    <p>&copy; 2026 あいぴー</p>
  </div>
</footer>
</body>
</html>
"""


BREAK = "\u0000BR\u0000"  # 行末の半角スペース2つ（markdownの改行）を一旦退避する印

# メールアドレスは半角英数のみ。日本語が直前にくっついていても巻き込まない。
EMAIL = re.compile(r"(?<![A-Za-z0-9.@_+-])([A-Za-z0-9._+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]+)")


def inline(text: str) -> str:
    """行内の記法（リンク・強調・コード・メールアドレス）をHTMLへ。先にエスケープする。"""
    out = html.escape(text)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = EMAIL.sub(r'<a href="mailto:\1">\1</a>', out)
    return out.replace(BREAK, "<br>")


def join(parts: list[str]) -> str:
    """折り返された行をつなぐ。日本語は詰めて、英数字との境目にだけ空白を入れる。"""
    joined = ""
    for part in parts:
        if joined and not joined.endswith(BREAK):
            left, right = joined[-1], part[0]
            if (left.isascii() and left.isalnum()) != (right.isascii() and right.isalnum()):
                joined += " "
        joined += part
    return joined


def cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def convert(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    buffer: list[str] = []  # 折り返された本文行（日本語なので空白を挟まず連結する）
    i = 0

    def flush() -> None:
        if buffer:
            out.append("<p>" + inline(join(buffer)) + "</p>")
            buffer.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if line.endswith("  ") and stripped:
            stripped += BREAK

        if not stripped:
            flush()
            i += 1
            continue

        if stripped.startswith("## "):
            flush()
            out.append("<h2>" + inline(stripped[3:]) + "</h2>")
            i += 1
            continue

        if stripped.startswith("# "):
            flush()
            out.append("<h1>" + inline(stripped[2:]) + "</h1>")
            i += 1
            continue

        if stripped.startswith("|"):
            flush()
            head = cells(lines[i])
            i += 2  # ヘッダ行と区切り行
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            out.append("<table>")
            out.append("<tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr>")
            for row in rows:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
            out.append("</table>")
            continue

        if stripped.startswith("- "):
            flush()
            items: list[str] = []
            while i < len(lines) and (
                lines[i].strip().startswith("- ") or (lines[i].startswith("  ") and lines[i].strip())
            ):
                if lines[i].strip().startswith("- "):
                    items.append(lines[i].strip()[2:])
                else:
                    items[-1] = join([items[-1], lines[i].strip()])  # 折り返しの続き
                i += 1
            out.append("<ul>")
            out.extend(f"<li>{inline(item)}</li>" for item in items)
            out.append("</ul>")
            continue

        buffer.append(stripped)
        i += 1

    flush()
    return "\n".join(out)


def main() -> None:
    body = convert(SOURCE.read_text(encoding="utf-8"))
    OUTPUT.write_text(TEMPLATE.format(body=body), encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
