from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Genius API Token
GENIUS_API_TOKEN = "xmjkneZAwUrS0kjHnbOQl7e5ipwBT0P7XuKY6S6GsqUtbMgs0RD5LB09ab6SLG84"
GENIUS_BASE_URL = "https://api.genius.com"

# YouTube Data API Key
YOUTUBE_API_KEY = "AIzaSyAZzn3ATd1I4pStAZPVwBGd-noe2wZ5pmk"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def get_lyrics(song, artist=""):
    """
    Genius API থেকে লিরিক্স আনার চেষ্টা
    """
    headers = {"Authorization": f"Bearer {GENIUS_API_TOKEN}"}
    query = f"{song} {artist}".strip()

    response = requests.get(
        f"{GENIUS_BASE_URL}/search", headers=headers, params={"q": query}
    )

    if response.status_code != 200:
        return None, None, f"Genius API error: {response.status_code}"

    hits = response.json().get("response", {}).get("hits", [])
    if not hits:
        return None, None, "No results found on Genius."

    # প্রথম রেজাল্ট ধরা
    song_info = hits[0]["result"]
    lyrics_url = song_info["url"]

    try:
        # Genius পেজ থেকে লিরিক্স scrap করা
        page = requests.get(lyrics_url)
        soup = BeautifulSoup(page.text, "html.parser")
        lyrics_div = soup.find("div", class_=re.compile("^Lyrics__Root"))

        if lyrics_div:
            lyrics = lyrics_div.get_text(separator="\n")
            return lyrics.strip(), lyrics_url, None
        else:
            return None, lyrics_url, "Lyrics not found in page."
    except Exception as e:
        return None, lyrics_url, f"Scraping error: {e}"


def get_youtube_video(song, artist=""):
    """
    YouTube Data API v3 দিয়ে ভিডিও খোঁজা
    """
    query = f"{song} {artist}".strip()

    params = {
        "part": "snippet",
        "q": query,
        "key": YOUTUBE_API_KEY,
        "type": "video",
        "maxResults": 1,
    }

    response = requests.get(YOUTUBE_SEARCH_URL, params=params)

    if response.status_code != 200:
        print("YouTube API error:", response.text)
        # fallback video (Rickroll 😅)
        return "https://www.youtube.com/embed/dQw4w9WgXcQ"

    data = response.json()
    items = data.get("items", [])

    if not items:
        return "https://www.youtube.com/embed/dQw4w9WgXcQ"

    video_id = items[0]["id"]["videoId"]
    return f"https://www.youtube.com/embed/{video_id}"


@app.route("/", methods=["GET", "POST"])
def index():
    lyrics, lyrics_url, not_found_msg, video_url = None, None, None, None

    if request.method == "POST":
        song = request.form.get("song", "")
        artist = request.form.get("artist", "")

        lyrics, lyrics_url, error_msg = get_lyrics(song, artist)
        if error_msg and not lyrics:
            not_found_msg = error_msg

        video_url = get_youtube_video(song, artist)

    return render_template(
        "index.html",
        lyrics=lyrics,
        lyrics_url=lyrics_url,
        not_found_msg=not_found_msg,
        video_url=video_url,
    )


if __name__ == "__main__":
    app.run(debug=True)
