import os
import feedparser
import requests
from google import genai

# 環境変数からAPIキーとWebhook URLを取得
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# 監視したいRSSフィード（例：arXiv cs.AI や公式ブログなど）
RSS_URL = "https://rss.arxiv.org/rss/cs.AI"

def summarize_text(client, title, summary):
    """Geminiを使ってニュースを3行で要約する"""
    prompt = f"""
以下の最新AI関連ニュースを、日本の学生・研究者向けに日本語で要約してください。

タイトル: {title}
内容: {summary}

【出力フォーマット】
・何が新しいのか（1行）
・心理学や実社会、技術への影響・意義（1行）
・重要ポイント（1行）
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text

def send_discord(content):
    """Discordのチャンネルに通知を送信"""
    payload = {"content": content}
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

def main():
    client = genai.Client(api_key=GEMINI_API_KEY)
    feed = feedparser.parse(RSS_URL)
    
    # 最新の3件だけを処理
    entries = feed.entries[:3]
    
    for entry in entries:
        title = entry.title
        link = entry.link
        description = entry.get("summary", "")
        
        # 要約の生成
        summary = summarize_text(client, title, description)
        
        # Discord向けメッセージの成形
        message = f"**【最新AIニュース】**\n**{title}**\n{link}\n\n{summary}\n-------------------"
        send_discord(message)

if __name__ == "__main__":
    main()
