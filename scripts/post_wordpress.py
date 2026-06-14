"""
post_wordpress.py - WordPress REST APIで記事を自動投稿する
FromZERO Work と 錦NISHIKI の両方に対応
"""
import os
import json
import base64
import requests
from datetime import datetime
from pathlib import Path

def post_to_wordpress(wp_url, wp_user, wp_password, title, content, meta_description,
                      status="publish", category_name=None, tags=None, lang=None):
    """WordPress REST APIで記事を投稿"""

    # 認証ヘッダー（アプリケーションパスワード）
    credentials = base64.b64encode(f"{wp_user}:{wp_password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }

    # カテゴリIDを取得（なければ作成）
    category_id = None
    if category_name:
        category_id = get_or_create_term(wp_url, headers, "categories", category_name)

    # タグIDを取得（なければ作成）
    tag_ids = []
    if tags:
        for tag in tags:
            tag_id = get_or_create_term(wp_url, headers, "tags", tag)
            if tag_id:
                tag_ids.append(tag_id)

    # 記事データ
    post_data = {
        "title": title,
        "content": markdown_to_html(content),
        "status": status,
        "excerpt": meta_description,
    }
    if category_id:
        post_data["categories"] = [category_id]
    if tag_ids:
        post_data["tags"] = tag_ids

    # 投稿
    endpoint = f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts"
    response = requests.post(endpoint, headers=headers, json=post_data)

    if response.status_code in (200, 201):
        post = response.json()
        print(f"✅ WP投稿成功: {post['link']}")
        return post
    else:
        print(f"❌ WP投稿失敗: {response.status_code} - {response.text[:200]}")
        return None

def get_or_create_term(wp_url, headers, taxonomy, name):
    """カテゴリ・タグをIDで取得、なければ作成"""
    endpoint = f"{wp_url.rstrip('/')}/wp-json/wp/v2/{taxonomy}"

    # 既存を検索
    r = requests.get(endpoint, headers=headers, params={"search": name})
    if r.status_code == 200 and r.json():
        return r.json()[0]["id"]

    # 新規作成
    r = requests.post(endpoint, headers=headers, json={"name": name})
    if r.status_code in (200, 201):
        return r.json()["id"]
    return None

def markdown_to_html(md_text):
    """マークダウンをHTMLに変換（簡易版）"""
    try:
        import markdown
        return markdown.markdown(md_text, extensions=["extra", "toc"])
    except ImportError:
        # markdownライブラリがない場合は簡易変換
        lines = md_text.split("\n")
        html_lines = []
        for line in lines:
            if line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.strip() == "":
                html_lines.append("<br>")
            else:
                html_lines.append(f"<p>{line}</p>")
        return "\n".join(html_lines)

def run(articles):
    """WordPress系サービスへの投稿を実行"""

    # FromZERO Work
    if articles.get("fromzero"):
        a = articles["fromzero"]
        cfg = a["config"]
        wp_cfg = cfg.get("wordpress", {})
        tags = wp_cfg.get("tags", [])

        post_to_wordpress(
            wp_url=os.environ["FROMZERO_WP_URL"],
            wp_user=os.environ["FROMZERO_WP_USER"],
            wp_password=os.environ["FROMZERO_WP_APP_PASSWORD"],
            title=a["title"],
            content=a["content"],
            meta_description=a["meta"],
            status=wp_cfg.get("post_status", "publish"),
            category_name=wp_cfg.get("category", "SEOブログ"),
            tags=tags
        )

    # 錦 NISHIKI
    if articles.get("nishiki"):
        a = articles["nishiki"]
        cfg = a["config"]
        wp_cfg = cfg.get("wordpress", {})
        lang = a.get("lang", "ja")

        category_name = wp_cfg.get("categories", {}).get(lang, "ブログ")
        tags = wp_cfg.get(f"tags_{lang}", [])

        post_to_wordpress(
            wp_url=os.environ["NISHIKI_WP_URL"],
            wp_user=os.environ["NISHIKI_WP_USER"],
            wp_password=os.environ["NISHIKI_WP_APP_PASSWORD"],
            title=a["title"],
            content=a["content"],
            meta_description=a["meta"],
            status=wp_cfg.get("post_status", "publish"),
            category_name=category_name,
            tags=tags,
            lang=lang
        )

if __name__ == "__main__":
    base = Path(__file__).parent.parent
    with open(base / "generated_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    run(articles)
