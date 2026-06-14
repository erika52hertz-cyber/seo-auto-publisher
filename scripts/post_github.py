"""
post_github.py - GitHub Pages（Jekyll）リポジトリに記事MDファイルをコミット
Mimosa Works / Local Navi 対応
"""
import os
import json
import base64
import requests
from datetime import datetime
from pathlib import Path

GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "")  # GitHubユーザー名

def headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

def create_jekyll_frontmatter(title, meta, date_str, keyword, lang="ja"):
    """Jekyll用フロントマターを生成"""
    return f"""---
layout: post
title: "{title.replace('"', "'")}"
date: {date_str}
description: "{meta.replace('"', "'")}"
keyword: "{keyword}"
lang: {lang}
---
"""

def commit_file_to_github(repo, file_path, content, commit_message, branch="main"):
    """GitHubリポジトリにファイルをコミット（新規 or 上書き）"""
    url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{repo}/contents/{file_path}"

    # 既存ファイルのSHAを取得（上書きの場合に必要）
    sha = None
    r = requests.get(url, headers=headers())
    if r.status_code == 200:
        sha = r.json().get("sha")

    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": commit_message,
        "content": encoded,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=headers(), json=payload)
    if r.status_code in (200, 201):
        print(f"✅ GitHub投稿成功: {repo}/{file_path}")
        return True
    else:
        print(f"❌ GitHub投稿失敗: {r.status_code} - {r.text[:200]}")
        return False

def ensure_jekyll_structure(repo, branch="main"):
    """_config.yml と _layouts/post.html が存在しなければ作成"""

    # _config.yml
    config_content = """title: Site
markdown: kramdown
permalink: /blog/:year/:month/:day/:title/
"""
    check = requests.get(
        f"{GITHUB_API}/repos/{GITHUB_OWNER}/{repo}/contents/_config.yml",
        headers=headers()
    )
    if check.status_code == 404:
        commit_file_to_github(repo, "_config.yml", config_content,
                              "Add Jekyll config", branch)

    # _layouts/post.html（最小限のレイアウト）
    post_layout = """<!DOCTYPE html>
<html lang="{{ page.lang | default: 'ja' }}">
<head>
  <meta charset="UTF-8">
  <meta name="description" content="{{ page.description }}">
  <title>{{ page.title }}</title>
</head>
<body>
  <article>
    <h1>{{ page.title }}</h1>
    <time>{{ page.date | date: "%Y年%m月%d日" }}</time>
    {{ content }}
  </article>
</body>
</html>
"""
    check = requests.get(
        f"{GITHUB_API}/repos/{GITHUB_OWNER}/{repo}/contents/_layouts/post.html",
        headers=headers()
    )
    if check.status_code == 404:
        commit_file_to_github(repo, "_layouts/post.html", post_layout,
                              "Add Jekyll post layout", branch)

def slugify(title):
    """タイトルをファイル名用スラッグに変換"""
    import re
    # 日本語はローマ字変換できないのでハッシュで代替
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[\s_-]+', '-', slug).strip('-')
    if not slug or len(slug) < 3:
        import hashlib
        slug = "post-" + hashlib.md5(title.encode()).hexdigest()[:8]
    return slug[:50]

def run(articles):
    """GitHub Pages系サービスへの投稿を実行"""
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d %H:%M:%S +0900")
    date_prefix = today.strftime("%Y-%m-%d")

    # Mimosa Works
    if articles.get("mimosa"):
        a = articles["mimosa"]
        cfg = a["config"]
        repo = cfg["github_repo"] if "github_repo" in cfg else os.environ.get("MIMOSA_REPO", "")
        branch = cfg.get("github", {}).get("branch", "main")

        if repo:
            ensure_jekyll_structure(repo, branch)

            slug = slugify(a["title"])
            filename = f"_posts/{date_prefix}-{slug}.md"
            frontmatter = create_jekyll_frontmatter(
                a["title"], a["meta"], date_str, a["keyword"]
            )
            file_content = frontmatter + "\n" + a["content"]
            commit_msg = cfg.get("github", {}).get("commit_message", "Add post").replace("{title}", a["title"])
            commit_file_to_github(repo, filename, file_content, commit_msg, branch)

    # Local Navi
    if articles.get("localnavi"):
        a = articles["localnavi"]
        cfg = a["config"]
        repo = os.environ.get("LOCALNAVI_REPO", "")
        branch = cfg.get("github", {}).get("branch", "main")
        posts_dir = a.get("extra", {}).get("posts_dir", "_posts")

        if repo:
            ensure_jekyll_structure(repo, branch)

            slug = slugify(a["title"])
            filename = f"{posts_dir}/{date_prefix}-{slug}.md"
            frontmatter = create_jekyll_frontmatter(
                a["title"], a["meta"], date_str, a["keyword"]
            )
            file_content = frontmatter + "\n" + a["content"]
            commit_msg = cfg.get("github", {}).get("commit_message", "Add post").replace("{title}", a["title"])
            commit_file_to_github(repo, filename, file_content, commit_msg, branch)

if __name__ == "__main__":
    base = Path(__file__).parent.parent
    with open(base / "generated_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    run(articles)
