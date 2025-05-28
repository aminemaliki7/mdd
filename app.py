import os
import subprocess
import shutil
import re
import time
import uuid
from urllib.parse import urlparse
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)


@app.route('/')
def home():
    return render_template("media_downloader.html")

@app.route('/api-docs')
def api_docs():
    return render_template("api_docs.html")


def check_yt_dlp_installed():
    return shutil.which('yt-dlp') is not None


def download_mp3(url, output_path='youtube_audio', filename=None):
    try:
        os.makedirs(output_path, exist_ok=True)
        if not filename:
            filename = f"audio_{uuid.uuid4().hex[:8]}"
        filename = re.sub(r'[^\w\-_.]', '_', filename)
        output_file = os.path.join(output_path, f"{filename}.mp3")

        cmd = [
            'yt-dlp', '--cookies', 'cookies.txt',
            '-x', '--audio-format', 'mp3', '--audio-quality', '0',
            '-o', output_file, '--no-playlist', url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return None
        return output_file if os.path.exists(output_file) else None
    except Exception as e:
        print(f"Error: {e}")
        return None


def download_pinterest_video(url, output_path='pinterest_videos', filename=None):
    try:
        os.makedirs(output_path, exist_ok=True)
        parsed_url = urlparse(url)
        if 'pinterest' not in parsed_url.netloc:
            print("Invalid Pinterest URL")
            return None

        pin_id = re.search(r'/pin/(\d+)', url)
        pin_id = pin_id.group(1) if pin_id else uuid.uuid4().hex[:8]
        safe_filename = re.sub(r'[^\w\-_.]', '_', filename) if filename else f"pinterest_{pin_id}"
        output_filename = f"{safe_filename}.mp4"
        output_file = os.path.join(output_path, output_filename)

        cmd = ['yt-dlp', '--cookies', 'cookies.txt', '--merge-output-format', 'mp4', '-o', output_file, '--no-warnings', url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            alt_cmd = ['yt-dlp', '--cookies', 'cookies.txt', '-f', 'b', '--merge-output-format', 'mp4', '-o', output_file, url]
            alt_result = subprocess.run(alt_cmd, capture_output=True, text=True)
            if alt_result.returncode != 0:
                return None

        return output_file if os.path.exists(output_file) else None
    except Exception as e:
        print(f"Error: {e}")
        return None


def download_youtube_video(url, output_path='youtube_videos', filename=None, quality='best'):
    try:
        os.makedirs(output_path, exist_ok=True)
        parsed_url = urlparse(url)
        if 'youtube.com' not in parsed_url.netloc and 'youtu.be' not in parsed_url.netloc:
            print("Invalid YouTube URL")
            return None

        video_id = None
        if not filename:
            if 'youtube.com' in parsed_url.netloc and 'v=' in parsed_url.query:
                query_params = dict(p.split('=') for p in parsed_url.query.split('&') if '=' in p)
                video_id = query_params.get('v', '')
            elif 'youtu.be' in parsed_url.netloc:
                video_id = parsed_url.path.lstrip('/')

        safe_filename = re.sub(r'[^\w\-_.]', '_', filename) if filename else f"youtube_{video_id or uuid.uuid4().hex[:8]}"
        output_filename = f"{safe_filename}.mp4"
        output_file = os.path.join(output_path, output_filename)

        format_selection = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        if quality == '1080p':
            format_selection = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
        elif quality == '720p':
            format_selection = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
        elif quality == '480p':
            format_selection = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
        elif quality == '360p':
            format_selection = 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best'

        cmd = [
            'yt-dlp', '--cookies', 'cookies.txt',
            '-f', format_selection, '-o', output_file,
            '--merge-output-format', 'mp4', '--no-playlist', '--no-warnings', url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            alt_cmd = ['yt-dlp', '--cookies', 'cookies.txt', '-f', 'b', '-o', output_file, '--merge-output-format', 'mp4', '--no-playlist', url]
            alt_result = subprocess.run(alt_cmd, capture_output=True, text=True)
            if alt_result.returncode != 0:
                return None

        return output_file if os.path.exists(output_file) else None
    except Exception as e:
        print(f"Error downloading YouTube video: {e}")
        return None


def download_social_video(url, output_path='social_videos', filename=None):
    try:
        os.makedirs(output_path, exist_ok=True)
        filename = re.sub(r'[^\w\-_.]', '_', filename) if filename else f"social_{uuid.uuid4().hex[:8]}"
        output_file = os.path.join(output_path, f"{filename}.mp4")

        cmd = [
            'yt-dlp', '--cookies', 'cookies.txt',
            '--merge-output-format', 'mp4', '-o', output_file,
            '--no-playlist', '--no-warnings', url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("Download failed:", result.stderr)
            return None
        return output_file if os.path.exists(output_file) else None
    except Exception as e:
        print(f"Error downloading social video: {e}")
        return None


@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json()
    url = data.get("url")
    filename = data.get("filename", None)
    media_type = data.get("type", "audio")

    if media_type == "audio":
        output = download_mp3(url, 'api_audio', filename)
    elif media_type == "video":
        output = download_pinterest_video(url, 'api_video', filename)
    elif media_type == "youtube":
        quality = data.get("quality", "best")
        output = download_youtube_video(url, 'api_youtube', filename, quality)
    elif media_type == "social":
        output = download_social_video(url, 'api_social', filename)
    else:
        return jsonify({"success": False, "error": "Invalid media type."}), 400

    if output:
        return jsonify({"success": True, "file_path": output})
    return jsonify({"success": False, "error": "Download failed."}), 500
