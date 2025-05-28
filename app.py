import os
import time
import uuid
from flask import Flask, request, jsonify, send_file, session, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from media_downloaders import (
    download_mp3,
    download_pinterest_video,
    download_social_video,
    download_youtube_video,
    check_yt_dlp_installed
)
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

@app.route('/')
def home():
    return render_template('media_downloader.html')

def handle_download(url, custom_filename, folder_name, download_func, media_type, **kwargs):
    """Shared handler for all download routes."""
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})

    if not check_yt_dlp_installed():
        return jsonify({'success': False, 'error': 'yt-dlp is not installed.'})

    download_id = str(uuid.uuid4())
    try:
        folder_path = os.path.join('downloads', folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Sanitize custom filename
        custom_filename = secure_filename(custom_filename) if custom_filename else ""

        # Call the appropriate download function
        output_file = download_func(url, folder_path, custom_filename, **kwargs)

        if not output_file:
            return jsonify({'success': False, 'error': 'Failed to download.'})

        filename = os.path.basename(output_file)

        # Track metadata in app context
        app.media_downloads = getattr(app, 'media_downloads', {})
        metadata = {
            'id': download_id,
            'type': media_type,
            'url': url,
            'file_path': output_file,
            'filename': filename,
            'timestamp': time.time()
        }
        if kwargs:
            metadata.update(kwargs)

        app.media_downloads[download_id] = metadata
        session.setdefault('media_downloads', []).append(download_id)
        session.modified = True

        return jsonify({
            'success': True,
            'download_id': download_id,
            'filename': filename,
            'download_url': url_for('download_media', download_id=download_id)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download-audio', methods=['POST'])
def download_audio():
    url = request.form.get('url', '').strip()
    filename = request.form.get('filename', '').strip()
    return handle_download(url, filename, 'audio', download_mp3, 'audio')

@app.route('/download-video', methods=['POST'])
def download_video():
    url = request.form.get('url', '').strip()
    filename = request.form.get('filename', '').strip()
    return handle_download(url, filename, 'video', download_pinterest_video, 'video')

@app.route('/download-social', methods=['POST'])
def download_social():
    url = request.form.get('url', '').strip()
    filename = request.form.get('filename', '').strip()
    return handle_download(url, filename, 'social', download_social_video, 'social')

@app.route('/download-youtube', methods=['POST'])
def download_youtube():
    url = request.form.get('url', '').strip()
    filename = request.form.get('filename', '').strip()
    quality = request.form.get('quality', 'best').strip()
    return handle_download(url, filename, 'youtube', download_youtube_video, 'youtube', quality=quality)

@app.route('/download-media/<download_id>')
def download_media(download_id):
    app.media_downloads = getattr(app, 'media_downloads', {})
    download = app.media_downloads.get(download_id)

    if not download:
        return render_template('error.html', message="Download not found.")

    return send_file(
        download['file_path'],
        as_attachment=True,
        download_name=download['filename']
    )
@app.route('/api-docs')
def api_docs():
    return render_template('api_docs.html')

if __name__ == '__main__':
    app.run(debug=False)
