import os
import time
import uuid
from urllib.parse import urlparse
from flask import Flask, request, jsonify, send_file, session, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from media_downloaders import (
    download_mp3,
    download_pinterest_video,
    download_social_video,
    download_youtube_video,
    check_yt_dlp_installed,
    detect_platform
)
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_platform_status_message(platform):
    """Get status message for different platforms"""
    messages = {
        'youtube': {
            'working': 'YouTube downloads may require authentication for some videos',
            'failing': 'YouTube is currently blocking downloads. Try: 1) Public videos only, 2) Wait and retry, 3) Use different quality settings'
        },
        'instagram': {
            'working': 'Instagram downloads work for public content',
            'failing': 'Instagram requires authentication. Try: 1) Public posts only, 2) Login to Instagram in your browser first'
        },
        'pinterest': {
            'working': 'Pinterest downloads are working normally',
            'failing': 'Pinterest download failed. The video may be private or unavailable'
        },
        'tiktok': {
            'working': 'TikTok downloads are working normally',
            'failing': 'TikTok download failed. The video may be private or region-blocked'
        },
        'generic': {
            'working': 'Download in progress',
            'failing': 'Download failed. Please check if the URL is valid and the content is publicly accessible'
        }
    }
    return messages.get(platform, messages['generic'])

@app.route('/')
def home():
    return render_template('media_downloader.html')

def handle_download(url, custom_filename, folder_name, download_func, media_type, **kwargs):
    """Enhanced handler with platform-specific messaging"""
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})

    if not check_yt_dlp_installed():
        return jsonify({'success': False, 'error': 'yt-dlp is not installed.'})

    # Detect platform for better error messaging
    platform = detect_platform(url)
    platform_messages = get_platform_status_message(platform)
    
    download_id = str(uuid.uuid4())
    try:
        folder_path = os.path.join('downloads', folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Sanitize custom filename
        custom_filename = secure_filename(custom_filename) if custom_filename else ""

        logger.info(f"Starting {media_type} download from {platform}: {url}")
        
        # Call the appropriate download function
        output_file = download_func(url, folder_path, custom_filename, **kwargs)

        if not output_file:
            # Platform-specific error messages
            if platform == 'youtube':
                error_msg = 'YouTube download failed. This might be due to: age restrictions, private videos, or bot detection. Try a different video or quality setting.'
            elif platform == 'instagram':
                error_msg = 'Instagram download failed. Instagram often requires authentication. Make sure the post is public and try logging into Instagram in your browser first.'
            elif platform == 'pinterest':
                error_msg = 'Pinterest download failed. The pin might be private or the video format is not supported.'
            elif platform == 'tiktok':
                error_msg = 'TikTok download failed. The video might be private, region-blocked, or have download restrictions.'
            else:
                error_msg = f'{platform_messages["failing"]}'
            
            logger.error(f"Download failed for {platform}: {url}")
            return jsonify({
                'success': False, 
                'error': error_msg,
                'platform': platform,
                'suggestion': get_platform_suggestions(platform)
            })

        filename = os.path.basename(output_file)
        logger.info(f"Download successful from {platform}: {filename}")

        # Track metadata in app context
        app.media_downloads = getattr(app, 'media_downloads', {})
        metadata = {
            'id': download_id,
            'type': media_type,
            'url': url,
            'file_path': output_file,
            'filename': filename,
            'timestamp': time.time(),
            'platform': platform
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
            'platform': platform,
            'download_url': url_for('download_media', download_id=download_id),
            'message': f'Successfully downloaded from {platform.title()}'
        })

    except Exception as e:
        error_msg = f"Download error: {str(e)}"
        logger.error(f"{platform} download error: {error_msg}")
        
        # Enhanced error handling with platform awareness
        if "Sign in to confirm" in str(e) or "cookies" in str(e).lower():
            if platform == 'youtube':
                error_msg = "YouTube requires authentication. The video may be age-restricted, private, or region-blocked."
            elif platform == 'instagram':
                error_msg = "Instagram requires login. Please log into Instagram in your browser and try again."
        elif "timeout" in str(e).lower():
            error_msg = f"{platform.title()} download timeout. The server may be slow or the file too large."
        elif "not available" in str(e).lower():
            error_msg = f"Content not available on {platform.title()}. It may be private or deleted."
        
        return jsonify({
            'success': False, 
            'error': error_msg,
            'platform': platform,
            'suggestion': get_platform_suggestions(platform)
        })

def get_platform_suggestions(platform):
    """Get helpful suggestions for each platform"""
    suggestions = {
        'youtube': [
            "Try a different video quality (360p, 480p, 720p)",
            "Make sure the video is public and not age-restricted",
            "Wait a few minutes and try again",
            "Use the direct YouTube URL (not shortened links)"
        ],
        'instagram': [
            "Make sure the post is public (not private account)",
            "Log into Instagram in your browser first",
            "Try the direct post URL",
            "Some Instagram content cannot be downloaded due to privacy settings"
        ],
        'pinterest': [
            "Make sure the pin contains a video (not just an image)",
            "Try the direct pin URL",
            "Some Pinterest videos are hosted externally and may not work"
        ],
        'tiktok': [
            "Make sure the video is public",
            "Try the direct TikTok URL (not shortened)",
            "Some videos may be region-blocked"
        ]
    }
    return suggestions.get(platform, ["Check if the URL is correct and the content is publicly available"])

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

    try:
        return send_file(
            download['file_path'],
            as_attachment=True,
            download_name=download['filename']
        )
    except FileNotFoundError:
        return render_template('error.html', message="File not found. It may have been deleted.")

@app.route('/platform-status')
def platform_status():
    """Check which platforms are working"""
    status = {
        'youtube': 'Limited (authentication issues)',
        'instagram': 'Limited (requires login)',
        'pinterest': 'Working',
        'tiktok': 'Working',
        'twitter': 'Working',
        'facebook': 'Limited'
    }
    return jsonify(status)

@app.route('/api-docs')
def api_docs():
    return render_template('api_docs.html')

@app.route('/api/download', methods=['POST'])
def api_download():
    try:
        data = request.get_json()
        url = data.get("url")
        filename = data.get("filename", None)
        media_type = data.get("type", "audio")

        if not url:
            return jsonify({"success": False, "error": "URL is required"}), 400

        platform = detect_platform(url)
        logger.info(f"API download request: {media_type} from {platform} - {url}")

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
            return jsonify({"success": False, "error": "Invalid media type. Use: audio, video, youtube, social"}), 400

        if output:
            return jsonify({
                "success": True, 
                "file_path": output,
                "platform": platform,
                "message": f"Successfully downloaded from {platform}"
            })
        else:
            platform_messages = get_platform_status_message(platform)
            return jsonify({
                "success": False, 
                "error": platform_messages["failing"],
                "platform": platform,
                "suggestions": get_platform_suggestions(platform)
            }), 500

    except Exception as e:
        logger.error(f"API download error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        "status": "healthy",
        "yt_dlp_installed": check_yt_dlp_installed(),
        "timestamp": time.time(),
        "platform_notes": {
            "youtube": "May require authentication",
            "instagram": "Requires login for some content",
            "pinterest": "Working normally",
            "tiktok": "Working normally"
        }
    })

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))