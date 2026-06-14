"""
notify.py - 生成した記事をメール or Slack で通知（note手動投稿用）
"""
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

def send_slack(webhook_url, message):
    payload = json.dumps({"text": message}).encode("utf-8")
    req = urllib.request.Request(webhook_url, data=payload,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return r.status == 200

def send_email_via_gmail_smtp(to_email, subject, body):
    """Gmail SMTPで送信（環境変数: GMAIL_USER, GMAIL_APP_PASSWORD）"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "")

    if not gmail_user or not gmail_password:
        print("⚠️ Gmail設定がありません。Slack通知のみ実行します。")
        return False

    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
    return True

def build_note_draft(articles):
    """note投稿用の下書きサマリーを作成"""
    today = datetime.now().strftime("%Y年%m月%d日")
    lines = [f"📝 {today} の自動生成記事サマリー（note投稿候補）\n"]
    lines.append("=" * 50)

    service_names = {
        "fromzero": "FromZERO Work",
        "mimosa": "Mimosa Works",
        "localnavi": "Local Navi",
        "nishiki": "錦 NISHIKI",
    }

    for key, name in service_names.items():
        a = articles.get(key)
        if not a:
            continue
        lines.append(f"\n【{name}】")
        lines.append(f"タイトル: {a.get('title', 'N/A')}")
        lines.append(f"キーワード: {a.get('keyword', 'N/A')}")
        lines.append(f"メタ: {a.get('meta', 'N/A')}")
        lines.append("")
        # 本文の冒頭200字
        content_preview = a.get("content", "")[:200].replace("\n", " ")
        lines.append(f"本文冒頭: {content_preview}...")
        lines.append("-" * 40)

    lines.append("\n💡 上記からnoteに投稿する記事を選んでください。")
    lines.append("本文全文はGitHubの generated_articles.json を参照してください。")
    return "\n".join(lines)

def run(articles):
    slack_webhook = os.environ.get("SLACK_WEBHOOK_URL", "")
    notify_email = os.environ.get("NOTIFY_EMAIL", "")

    message = build_note_draft(articles)
    print(message)  # GitHub Actionsのログにも出力

    # Slack通知
    if slack_webhook:
        success = send_slack(slack_webhook, message)
        print("✅ Slack通知送信完了" if success else "❌ Slack通知失敗")

    # メール通知
    if notify_email:
        today = datetime.now().strftime("%Y/%m/%d")
        try:
            success = send_email_via_gmail_smtp(
                to_email=notify_email,
                subject=f"【SEO自動生成】{today} の記事サマリー",
                body=message
            )
            print("✅ メール通知送信完了" if success else "❌ メール通知失敗")
        except Exception as e:
            print(f"❌ メール通知エラー: {e}")

if __name__ == "__main__":
    base = Path(__file__).parent.parent
    with open(base / "generated_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    run(articles)
