import os
import time
import feedparser
import requests
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

RSS_URL = "https://rss.arxiv.org/rss/cs.AI"

def summarize_text(client, title, summary, max_retries=6):
    """Geminiを使ってニュースを要約する（503混雑時は指数バックオフで待機）"""
    prompt = f"""
以下の最新AI関連ニュースを、日本の学生・研究者向けに日本語で要約してください。

タイトル: {title}
内容: {summary}

【出力フォーマット】
・何が新しいのか（1行）
・心理学や実社会、技術への影響・意義（1行）
・重要ポイント（1行）
"""
    # エラー時は 5秒, 10秒, 20秒, 40秒... と待機時間を増やして再試行
    wait_time = 5
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"一時的な混雑またはエラー ({e})。{wait_time}秒待機して再試行します (試行 {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
                wait_time *= 2  # 待機時間を倍に伸ばす
                continue
            raise e

def send_discord(content):
    """Discordのチャンネルに通知を送信"""
    payload = {"content": content}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    response.raise_for_status()

def main():
    client = genai.Client(api_key=GEMINI_API_KEY)
    feed = feedparser.parse(RSS_URL)
    
    # 最新の3件を処理
    entries = feed.entries[:3]
    
    for i, entry in enumerate(entries, 1):
        title = entry.title
        link = entry.link
        description = entry.get("summary", "")
        
        print(f"[{i}/3] 記事を要約中: {title[:30]}...")
        summary = summarize_text(client, title, description)
        
        message = f"**【最新AIニュース】**\n**{title}**\n{link}\n\n{summary}\n-------------------"
        send_discord(message)
        print(f"[{i}/3] Discord送信完了")
        
        # 連続リクエストによる負荷を避けるため5秒インターバル
        time.sleep(5)

if __name__ == "__main__":
    main()
