import os
import time
import feedparser
import requests
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

RSS_URL = "https://rss.arxiv.org/rss/cs.AI"

def get_available_flash_model(client):
    """利用可能なモデル一覧から最適なFlashモデルを自動検出する"""
    try:
        available_models = [m.name for m in client.models.list()]
        # flashを含み、generateContentに対応するモデルを探す
        flash_models = [m for m in available_models if "flash" in m.lower()]
        if flash_models:
            chosen = flash_models[0]
            print(f"自動選択されたモデル: {chosen}")
            return chosen
    except Exception as e:
        print(f"モデル一覧取得失敗 ({e})。デフォルトを試行します。")
    return "gemini-2.0-flash"

def summarize_text(client, model_name, title, summary, max_retries=5):
    """Geminiを使ってニュースを要約する（混雑時はリトライ）"""
    prompt = f"""
以下の最新AI関連ニュースを、日本の学生・研究者向けに日本語で要約してください。

タイトル: {title}
内容: {summary}

【出力フォーマット】
・何が新しいのか（1行）
・心理学や実社会、技術への影響・意義（1行）
・重要ポイント（1行）
"""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 10 * (attempt + 1)
                print(f"一時エラー ({e})。{wait_time}秒待機して再試行します...")
                time.sleep(wait_time)
                continue
            raise e

def send_discord(content):
    """Discordのチャンネルに通知を送信"""
    payload = {"content": content}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    response.raise_for_status()

def main():
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # 確実に使えるモデルを自動で特定
    model_name = get_available_flash_model(client)
    
    feed = feedparser.parse(RSS_URL)
    entries = feed.entries[:3]
    
    for entry in entries:
        title = entry.title
        link = entry.link
        description = entry.get("summary", "")
        
        summary = summarize_text(client, model_name, title, description)
        
        message = f"**【最新AIニュース】**\n**{title}**\n{link}\n\n{summary}\n-------------------"
        send_discord(message)
        time.sleep(3)

if __name__ == "__main__":
    main()
