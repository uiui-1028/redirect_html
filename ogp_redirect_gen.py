#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LinkRow:
    title: str
    url: str
    description: str
    image: str


def _is_http_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def _slugify(title: str, url: str) -> str:
    base = re.sub(r"[^\w\-]+", "-", title.strip().lower(), flags=re.UNICODE).strip("-")
    base = re.sub(r"-{2,}", "-", base)
    base = base[:48] or "link"
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"{base}-{h}"


def _render_index_html(
    *,
    title: str,
    url: str,
    description: str,
    image: str,
    canonical: str | None,
    og_url: str | None,
) -> str:
    t = html.escape(title, quote=True)
    u = html.escape(url, quote=True)
    d = html.escape(description, quote=True)
    img = html.escape(image, quote=True)
    can = html.escape(canonical, quote=True) if canonical else None
    ogu = html.escape(og_url, quote=True) if og_url else None
    og_url_tag = f'<meta property="og:url" content="{ogu}" />' if ogu else ""
    canonical_tag = f'<link rel="canonical" href="{can}" />' if can else ""

    return f"""<!doctype html>
<html lang="ja">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />

    <title>{t}</title>
    <meta name="description" content="{d}" />

    <!-- OGP -->
    <meta property="og:type" content="website" />
    <meta property="og:title" content="{t}" />
    <meta property="og:description" content="{d}" />
    <meta property="og:image" content="{img}" />
    {og_url_tag}

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{t}" />
    <meta name="twitter:description" content="{d}" />
    <meta name="twitter:image" content="{img}" />

    <!-- Bot / Indexing control -->
    <meta name="robots" content="noindex, nofollow, noarchive" />

    {canonical_tag}

    <script>
      (function () {{
        var url = "{u}";

        // OGP取得Botが meta refresh を追従してしまうケース対策:
        // meta refresh はJSで動的に追加（BotはJSを実行しない想定）。
        try {{
          var meta = document.createElement("meta");
          meta.setAttribute("http-equiv", "refresh");
          meta.setAttribute("content", "0; url=" + url);
          document.head.appendChild(meta);
        }} catch (e) {{}}

        try {{
          window.location.replace(url);
        }} catch (e) {{
          window.location.href = url;
        }}
      }})();
    </script>
  </head>
  <body>
    <noscript>
      <p>
        自動的に移動します。移動しない場合は
        <a href="{u}">こちら</a> をクリックしてください。
      </p>
    </noscript>
    <p>
      自動的に移動します。移動しない場合は
      <a href="{u}">こちら</a> をクリックしてください。
    </p>
  </body>
</html>
"""


def _read_rows(input_path: Path) -> list[LinkRow]:
    rows: list[LinkRow] = []
    with input_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = ["title", "url", "description", "image"]
        missing = [k for k in required if k not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f"CSVの列が不足しています: {', '.join(missing)}")
        for i, r in enumerate(reader, start=2):
            row = LinkRow(
                title=(r.get("title") or "").strip(),
                url=(r.get("url") or "").strip(),
                description=(r.get("description") or "").strip(),
                image=(r.get("image") or "").strip(),
            )
            if not (row.title and row.url and row.description and row.image):
                raise SystemExit(f"{input_path}:{i} 行目: 空の値があります（title/url/description/imageは必須）")
            rows.append(row)
    return rows


def _resolve_image(image_value: str, *, base_url: str) -> str:
    v = image_value.strip()
    if _is_http_url(v):
        return v
    if not base_url:
        raise SystemExit(
            "image に相対パス（例: assets/ogp.png）を使うには --base-url が必要です。"
        )
    return f"{base_url.rstrip('/')}/{v.lstrip('/')}"


def main() -> int:
    p = argparse.ArgumentParser(
        description="OGP付きリダイレクトHTMLをCSVから一括生成します（note向け）。"
    )
    p.add_argument("--input", default="links.csv", help="入力CSV（title,url,description,image）")
    p.add_argument("--out", default=".", help="出力先ディレクトリ（例: . や public）")
    p.add_argument(
        "--base-url",
        default="",
        help="公開URLのベース（例: https://uiui-1028.github.io/redirect_html）。og:url/canonicalに使用",
    )
    p.add_argument(
        "--print",
        action="store_true",
        help="生成結果（slug -> 公開URL想定）を表示する",
    )
    args = p.parse_args()

    input_path = Path(args.input)
    out_dir = Path(args.out)
    base_url = args.base_url.strip().rstrip("/")

    rows = _read_rows(input_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    mapping: list[tuple[str, str]] = []
    for row in rows:
        slug = _slugify(row.title, row.url)
        page_dir = out_dir / slug
        page_dir.mkdir(parents=True, exist_ok=True)

        canonical = f"{base_url}/{slug}/" if base_url else None
        og_url = canonical
        resolved_image = _resolve_image(row.image, base_url=base_url)

        if not _is_http_url(row.image):
            local_path = Path(row.image)
            if not local_path.exists():
                print(
                    f"WARNING: 画像ファイルが見つかりません: {row.image}（公開前に assets/ へ配置してpushしてください）"
                )

        html_text = _render_index_html(
            title=row.title,
            url=row.url,
            description=row.description,
            image=resolved_image,
            canonical=canonical,
            og_url=og_url,
        )
        (page_dir / "index.html").write_text(html_text, encoding="utf-8")
        mapping.append((slug, canonical or f"{slug}/"))

    if args.print:
        for slug, pub in mapping:
            print(f"{slug}\t{pub}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

