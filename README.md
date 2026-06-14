# SEO Auto Publisher

5サービスのSEO記事を毎日自動生成・自動投稿するシステム。

## 対象サービス

| サービス | CMS | 言語 |
|---------|-----|------|
| FromZERO Work | WordPress | 日本語 |
| 錦 NISHIKI | WordPress | 日本語 + 英語 |
| Mimosa Works | GitHub Pages (Jekyll) | 日本語 |
| Local Navi | GitHub Pages (Jekyll) | 日本語 |
| SKINN | Shopify（後日追加） | 日本語 |

---

## セットアップ手順

### 1. このリポジトリをGitHubにプッシュ

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_NAME/seo-auto-publisher.git
git push -u origin main
```

### 2. GitHub Secretsを登録

GitHubリポジトリの Settings → Secrets and variables → Actions → New repository secret

| Secret名 | 値 | 取得方法 |
|---------|---|---------|
| `ANTHROPIC_API_KEY` | sk-ant-... | console.anthropic.com |
| `FROMZERO_WP_URL` | https://work.fromzero.jp | そのまま |
| `FROMZERO_WP_USER` | WPのユーザー名 | WP管理画面のプロフィール |
| `FROMZERO_WP_APP_PASSWORD` | xxxx xxxx xxxx | WP管理画面→アプリパスワード |
| `NISHIKI_WP_URL` | https://nishiki-domain.com | そのまま |
| `NISHIKI_WP_USER` | WPのユーザー名 | WP管理画面のプロフィール |
| `NISHIKI_WP_APP_PASSWORD` | xxxx xxxx xxxx | WP管理画面→アプリパスワード |
| `GITHUB_OWNER` | GitHubユーザー名 | GitHubプロフィール |
| `MIMOSA_REPO` | mimosaworks.com | リポジトリ名 |
| `LOCALNAVI_REPO` | localnavi-repo名 | リポジトリ名 |
| `NOTIFY_EMAIL` | your@email.com | 通知を受け取るメールアドレス |
| `GMAIL_USER` | gmail@gmail.com | Gmailアドレス（任意） |
| `GMAIL_APP_PASSWORD` | xxxx xxxx | Gmail→アプリパスワード（任意） |
| `SLACK_WEBHOOK_URL` | https://hooks.slack... | Slack設定（任意） |

### 3. 動作確認（手動実行）

GitHub → Actions タブ → "Daily SEO Article Publisher" → "Run workflow"

### 4. 自動実行の確認

毎朝 JST 06:00 に自動実行されます。
Actions タブでログを確認できます。

---

## ファイル構成

```
seo-auto-publisher/
├── config/
│   ├── fromzero.yaml      # FromZERO キーワード設定
│   ├── mimosa.yaml        # Mimosa Works キーワード設定
│   ├── localnavi.yaml     # Local Navi 業種×地域マトリクス
│   └── nishiki.yaml       # 錦NISHIKI キーワード設定（日英）
│
├── prompts/
│   ├── fromzero_prompt.md
│   ├── mimosa_prompt.md
│   ├── localnavi_prompt.md
│   └── nishiki_prompt.md
│
├── scripts/
│   ├── generate.py        # Claude APIで記事生成
│   ├── post_wordpress.py  # WordPress投稿（FromZERO + NISHIKI）
│   ├── post_github.py     # GitHub Pages投稿（Mimosa + LocalNavi）
│   └── notify.py          # note用通知
│
└── .github/workflows/
    └── daily_publish.yml  # 毎朝6時自動実行
```

---

## カスタマイズ

### キーワードを追加する
各 `config/*.yaml` の `keywords` セクションにキーワードを追加するだけ。

### 記事を下書きにしたい
`config/fromzero.yaml` の `post_status: "draft"` に変更。

### Local Naviの新業種を有効化する
`config/localnavi.yaml` の該当業種の `active: false` を `active: true` に変更。

### SKINNを追加する（Shopify公開後）
1. `config/skinn.yaml` を作成
2. `prompts/skinn_prompt.md` を作成
3. `scripts/post_shopify.py` を作成
4. `daily_publish.yml` にShopify投稿ステップを追加
