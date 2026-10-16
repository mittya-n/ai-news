import os
import time
import feedparser
import requests
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

RSS_URL = "https://rss.arxiv.org/rss/cs.AI"

def summarize_text(client, title, summary, max_retries=6):
    """Geminiを使ってニュースを中学生でもわかるレベルに噛み砕いて要約する"""
    prompt = f"""
以下の最新AI研究について、専門用語を一切使わず、日常会話レベルのわかりやすい日本語で解説してください。
工学的な数式や専門用語は、身近な例え話に置き換えてください。

論文タイトル: {title}
元の内容: {summary}

【出力フォーマット】
💡 ざっくり言うと？
（この研究が解決したい悩みやテーマを、身近な言葉で1行）

🚀 ここが新しい・すごい！
（今までできなかった何ができるようになったのかを1〜2行）

🌱 私たちの生活や社会、心にどう影響する？
（教育、仕事、人間関係、メンタルなど、人間の生活への影響を1行）
"""
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
                print(f"一時的な混雑またはエラー ({e})。{wait_time}秒待機して再試行します...")
                time.sleep(wait_time)
                wait_time *= 2
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
