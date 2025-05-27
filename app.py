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

app = Flask(__name__)
app.secret_key = "simple_tts_generator"


@app.route('/')
def home():
    return render_template('media_downloader.html')


@app.route('/download-audio', methods=['POST'])
def download_audio():
    url = request.form.get('url', '').strip()
    custom_filename = request.form.get('filename', '').strip()

    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})

    if not check_yt_dlp_installed():
        return jsonify({'success': False, 'error': 'yt-dlp is not installed.'})

    download_id = str(uuid.uuid4())

    try:
        audio_folder = os.path.join('downloads', 'audio')
        os.makedirs(audio_folder, exist_ok=True)

        output_file = download_mp3(url, audio_folder, custom_filename)

        if not output_file:
            return jsonify({'success': False, 'error': 'Failed to download audio.'})

        filename = os.path.basename(output_file)
        app.media_downloads = getattr(app, 'media_downloads', {})
        app.media_downloads[download_id] = {
            'id': download_id,
            'type': 'audio',
            'url': url,
            'file_path': output_file,
            'filename': filename,
            'timestamp': time.time()
        }

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

@app.route('/download-video', methods=['POST'])
def download_video():
    url = request.form.get('url', '').strip()
    custom_filename = request.form.get('filename', '').strip()

    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})

    if not check_yt_dlp_installed():
        return jsonify({'success': False, 'error': 'yt-dlp is not installed.'})

    download_id = str(uuid.uuid4())

    try:
        video_folder = os.path.join('downloads', 'video')
        os.makedirs(video_folder, exist_ok=True)

        output_file = download_pinterest_video(url, video_folder, custom_filename)

        if not output_file:
            return jsonify({'success': False, 'error': 'Failed to download video.'})

        filename = os.path.basename(output_file)
        app.media_downloads = getattr(app, 'media_downloads', {})
        app.media_downloads[download_id] = {
            'id': download_id,
            'type': 'video',
            'url': url,
            'file_path': output_file,
            'filename': filename,
            'timestamp': time.time()
        }

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

@app.route('/download-social', methods=['POST'])
def download_social():
    url = request.form.get('url', '').strip()
    custom_filename = request.form.get('filename', '').strip()

    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})

    if not check_yt_dlp_installed():
        return jsonify({'success': False, 'error': 'yt-dlp is not installed.'})

    download_id = str(uuid.uuid4())

    try:
        social_folder = os.path.join('downloads', 'social')
        os.makedirs(social_folder, exist_ok=True)

        output_file = download_social_video(url, social_folder, custom_filename)

        if not output_file:
            return jsonify({'success': False, 'error': 'Failed to download video.'})

        filename = os.path.basename(output_file)
        app.media_downloads = getattr(app, 'media_downloads', {})
        app.media_downloads[download_id] = {
            'id': download_id,
            'type': 'social',
            'url': url,
            'file_path': output_file,
            'filename': filename,
            'timestamp': time.time()
        }

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

@app.route('/download-youtube', methods=['POST'])
def download_youtube():
    url = request.form.get('url', '').strip()
    custom_filename = request.form.get('filename', '').strip()
    quality = request.form.get('quality', 'best').strip()

    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})

    if not check_yt_dlp_installed():
        return jsonify({'success': False, 'error': 'yt-dlp is not installed.'})

    download_id = str(uuid.uuid4())

    try:
        youtube_folder = os.path.join('downloads', 'youtube')
        os.makedirs(youtube_folder, exist_ok=True)

        output_file = download_youtube_video(url, youtube_folder, custom_filename, quality)

        if not output_file:
            return jsonify({'success': False, 'error': 'Failed to download video.'})

        filename = os.path.basename(output_file)
        app.media_downloads = getattr(app, 'media_downloads', {})
        app.media_downloads[download_id] = {
            'id': download_id,
            'type': 'youtube',
            'url': url,
            'file_path': output_file,
            'filename': filename,
            'quality': quality,
            'timestamp': time.time()
        }

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

if __name__ == '__main__':
    app.run(debug=True)