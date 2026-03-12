# OGPリダイレクト（note向け）

`links.csv` に **4項目（title / url / description / image）** を書くだけで、OGP付きのリダイレクト用ページをまとめて生成します。

## 使い方（最短）

1. `links.csv` を編集（行を増やすだけ）
   - `image` は **HTTPSの画像URL** または **相対パス（例: `assets/anki.png`）** が使えます
   - 相対パスの場合、画像ファイルを `assets/` に置いて **GitHubへpush** してください（GitHub Pagesから配信されます）
2. 生成:

```bash
cd "/Users/art0/development/redirect_html"
python3 ogp_redirect_gen.py --input links.csv --out . --base-url "https://uiui-1028.github.io/redirect_html" --print
```

1. GitHubへ反映:

```bash
git add links.csv ogp_redirect_gen.py
git add */index.html
git commit -m "Generate OGP redirect pages"
git push
```

## 生成されるURL（貼る用）

`--print` を付けると、`slug -> 公開URL想定` を表示します。  
noteにはそのURLを貼ってください（反映しない時は `?v=1` などでキャッシュ回避）。

## 補足

- フォルダ名（slug）は **titleとURLから自動生成**されます（手で管理不要）。
- note等のOGP取得Botがリダイレクトを追従してしまうケースを避けるため、`meta refresh` はJSで動的に追加します。
- 画像は **1200×630（1.91:1）** が無難です（重要要素は中央寄せ推奨）。

