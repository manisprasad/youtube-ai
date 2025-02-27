import os
import json
import webvtt
from flask import Flask, request, jsonify
import yt_dlp

def format_timestamp(timestamp):
    """Convert WebVTT timestamp to hh:mm:ss or mm:ss format."""
    parts = timestamp.split('.')  # Remove milliseconds if present
    time_parts = parts[0].split(':')

    # Convert to integer for proper formatting
    time_parts = list(map(int, time_parts))

    if len(time_parts) == 3:  # hh:mm:ss format
        return f"{time_parts[0]:02}:{time_parts[1]:02}:{time_parts[2]:02}"
    elif len(time_parts) == 2:  # mm:ss format
        return f"{time_parts[0]:02}:{time_parts[1]:02}"
    return timestamp  # Fallback in case of unexpected format

app = Flask(__name__)

def get_auto_generated_captions(video_url):
    """Fetch auto-generated captions from a YouTube video."""
    ydl_opts = {
        "writeautomaticsub": True,
        "skip_download": True,
        "outtmpl": "captions.%(ext)s",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        auto_subtitles = info.get("automatic_captions", {})

        print("Auto subtitles available:", auto_subtitles.keys())  # Debugging

        # Prioritize English if available, otherwise take the first available language
        lang = "en" if "en" in auto_subtitles else next(iter(auto_subtitles), None)

        if lang:
            caption_filename = f"captions.{lang}.vtt"
            print(f"Expected caption filename: {caption_filename}")

            if os.path.exists(caption_filename):
                captions = []
                for caption in webvtt.read(caption_filename):
                    captions.append({
                        "start": format_timestamp(caption.start),
                        "end": format_timestamp(caption.end),
                        "text": caption.text
                    })
                    print("Extracted caption:", caption.text)  # Debugging
                return captions

    print("Caption file NOT found!")  # Debugging
    return []


@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/about')
def about():
    return 'About'


@app.route("/api/getCaptions", methods=["GET"])
def get_captions():
    """API endpoint to get YouTube video captions."""
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    captions = get_auto_generated_captions(url)
    if captions:
        return jsonify({"captions": captions}), 200
    else:
        return jsonify({"error": "Captions not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)
