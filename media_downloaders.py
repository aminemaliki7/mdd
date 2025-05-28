import os
import subprocess
import shutil
import re
import time
import uuid
from urllib.parse import urlparse
from flask import Flask, request, jsonify

app = Flask(__name__)


def check_yt_dlp_installed():
    return shutil.which('yt-dlp') is not None


def detect_platform(url):
    """Detect which platform the URL belongs to"""
    parsed_url = urlparse(url.lower())
    domain = parsed_url.netloc.lower()
    
    if any(x in domain for x in ['youtube.com', 'youtu.be', 'm.youtube.com']):
        return 'youtube'
    elif any(x in domain for x in ['instagram.com', 'www.instagram.com']):
        return 'instagram'
    elif any(x in domain for x in ['pinterest.com', 'www.pinterest.com', 'pin.it']):
        return 'pinterest'
    elif any(x in domain for x in ['tiktok.com', 'www.tiktok.com', 'vm.tiktok.com']):
        return 'tiktok'
    elif any(x in domain for x in ['twitter.com', 'x.com', 't.co']):
        return 'twitter'
    elif any(x in domain for x in ['facebook.com', 'fb.com', 'fb.watch']):
        return 'facebook'
    else:
        return 'generic'


def get_platform_specific_args(platform):
    """Get platform-specific arguments for yt-dlp"""
    base_args = [
        '--no-warnings',
        '--no-playlist',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    platform_args = {
        'youtube': [
            '--extractor-args', 'youtube:skip=dash,hls',
            '--no-check-certificate',
            # Remove cookies for now, add alternative methods
        ],
        'instagram': [
            '--extractor-args', 'instagram:include_stories=false',
            # Instagram often needs cookies, but let's try without first
        ],
        'pinterest': [
            '--referer', 'https://www.pinterest.com/',
        ],
        'tiktok': [
            '--referer', 'https://www.tiktok.com/',
        ],
        'twitter': [
            '--referer', 'https://twitter.com/',
        ],
        'facebook': [
            '--referer', 'https://www.facebook.com/',
        ],
        'generic': []
    }
    
    return base_args + platform_args.get(platform, platform_args['generic'])


def download_mp3(url, output_path='youtube_audio', filename=None):
    """Download audio with platform-specific handling"""
    try:
        os.makedirs(output_path, exist_ok=True)
        platform = detect_platform(url)
        
        if not filename:
            filename = f"audio_{uuid.uuid4().hex[:8]}"
        filename = re.sub(r'[^\w\-_.]', '_', filename)
        output_file = os.path.join(output_path, f"{filename}.mp3")

        platform_args = get_platform_specific_args(platform)
        
        strategies = []
        
        if platform == 'youtube':
            # YouTube-specific strategies
            strategies = [
                # Strategy 1: Try without cookies first
                [
                    'yt-dlp',
                    '-x', '--audio-format', 'mp3', '--audio-quality', '0',
                    '-o', output_file,
                ] + platform_args + [url],
                
                # Strategy 2: Try with browser cookies
                [
                    'yt-dlp', '--cookies-from-browser', 'chrome',
                    '-x', '--audio-format', 'mp3', '--audio-quality', '0',
                    '-o', output_file, '--no-playlist',
                    url
                ],
                
                # Strategy 3: Simple fallback
                [
                    'yt-dlp',
                    '-x', '--audio-format', 'mp3',
                    '-f', 'worst/best',
                    '-o', output_file,
                    url
                ]
            ]
        
        elif platform == 'instagram':
            # Instagram-specific strategies
            strategies = [
                # Strategy 1: Try with browser cookies first (Instagram usually needs auth)
                [
                    'yt-dlp', '--cookies-from-browser', 'chrome',
                    '-x', '--audio-format', 'mp3', '--audio-quality', '0',
                    '-o', output_file,
                ] + platform_args + [url],
                
                # Strategy 2: Try without cookies
                [
                    'yt-dlp',
                    '-x', '--audio-format', 'mp3', '--audio-quality', '0',
                    '-o', output_file,
                ] + platform_args + [url],
            ]
        
        else:
            # For Pinterest, TikTok, and others (these usually work without cookies)
            strategies = [
                [
                    'yt-dlp',
                    '-x', '--audio-format', 'mp3', '--audio-quality', '0',
                    '-o', output_file,
                ] + platform_args + [url]
            ]
        
        # Try each strategy
        for i, cmd in enumerate(strategies):
            try:
                print(f"Trying audio download strategy {i+1} for {platform}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode == 0 and os.path.exists(output_file):
                    print(f"Success with strategy {i+1}")
                    return output_file
                else:
                    print(f"Strategy {i+1} failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                print(f"Strategy {i+1} timeout")
                continue
            except Exception as e:
                print(f"Strategy {i+1} error: {e}")
                continue
        
        return None
    except Exception as e:
        print(f"Error in download_mp3: {e}")
        return None


def download_pinterest_video(url, output_path='pinterest_videos', filename=None):
    """Pinterest video download (usually works fine)"""
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

        platform_args = get_platform_specific_args('pinterest')
        
        cmd = [
            'yt-dlp', 
            '--merge-output-format', 'mp4', 
            '-o', output_file,
        ] + platform_args + [url]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            # Fallback
            alt_cmd = [
                'yt-dlp', 
                '-f', 'best[ext=mp4]/best', 
                '--merge-output-format', 'mp4', 
                '-o', output_file, 
                url
            ]
            alt_result = subprocess.run(alt_cmd, capture_output=True, text=True, timeout=300)
            if alt_result.returncode != 0:
                print(f"Pinterest download failed: {alt_result.stderr}")
                return None

        return output_file if os.path.exists(output_file) else None
    except Exception as e:
        print(f"Error downloading Pinterest video: {e}")
        return None


def download_youtube_video(url, output_path='youtube_videos', filename=None, quality='best'):
    """YouTube video download with multiple fallback strategies"""
    try:
        os.makedirs(output_path, exist_ok=True)
        platform = detect_platform(url)
        
        if platform != 'youtube':
            print("Invalid YouTube URL")
            return None

        video_id = None
        parsed_url = urlparse(url)
        if not filename:
            if 'youtube.com' in parsed_url.netloc and 'v=' in parsed_url.query:
                query_params = dict(p.split('=') for p in parsed_url.query.split('&') if '=' in p)
                video_id = query_params.get('v', '')
            elif 'youtu.be' in parsed_url.netloc:
                video_id = parsed_url.path.lstrip('/')

        safe_filename = re.sub(r'[^\w\-_.]', '_', filename) if filename else f"youtube_{video_id or uuid.uuid4().hex[:8]}"
        output_filename = f"{safe_filename}.mp4"
        output_file = os.path.join(output_path, output_filename)

        # Format selection based on quality
        format_selections = {
            '1080p': 'best[height<=1080][ext=mp4]/best[height<=1080]/best',
            '720p': 'best[height<=720][ext=mp4]/best[height<=720]/best',
            '480p': 'best[height<=480][ext=mp4]/best[height<=480]/best',
            '360p': 'best[height<=360][ext=mp4]/best[height<=360]/best',
            'best': 'best[ext=mp4]/best'
        }
        format_selection = format_selections.get(quality, format_selections['best'])

        platform_args = get_platform_specific_args('youtube')
        
        strategies = [
            # Strategy 1: No cookies, specified quality
            [
                'yt-dlp',
                '-f', format_selection,
                '-o', output_file,
                '--merge-output-format', 'mp4',
            ] + platform_args + [url],
            
            # Strategy 2: Browser cookies
            [
                'yt-dlp', '--cookies-from-browser', 'chrome',
                '-f', format_selection,
                '-o', output_file,
                '--merge-output-format', 'mp4',
                '--no-playlist',
                url
            ],
            
            # Strategy 3: Lower quality fallback
            [
                'yt-dlp',
                '-f', 'worst[ext=mp4]/worst/best',
                '-o', output_file,
                '--merge-output-format', 'mp4',
                '--no-playlist',
                url
            ]
        ]
        
        for i, cmd in enumerate(strategies):
            try:
                print(f"Trying YouTube video strategy {i+1}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode == 0 and os.path.exists(output_file):
                    print(f"YouTube download success with strategy {i+1}")
                    return output_file
                else:
                    print(f"Strategy {i+1} failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                print(f"Strategy {i+1} timeout")
                continue
            except Exception as e:
                print(f"Strategy {i+1} error: {e}")
                continue
        
        return None
    except Exception as e:
        print(f"Error downloading YouTube video: {e}")
        return None


def download_social_video(url, output_path='social_videos', filename=None):
    """Download social media videos with platform detection"""
    try:
        os.makedirs(output_path, exist_ok=True)
        platform = detect_platform(url)
        
        filename = re.sub(r'[^\w\-_.]', '_', filename) if filename else f"social_{platform}_{uuid.uuid4().hex[:8]}"
        output_file = os.path.join(output_path, f"{filename}.mp4")

        platform_args = get_platform_specific_args(platform)
        
        strategies = []
        
        if platform == 'instagram':
            # Instagram needs special handling
            strategies = [
                # Try with browser cookies first
                [
                    'yt-dlp', '--cookies-from-browser', 'chrome',
                    '--merge-output-format', 'mp4',
                    '-o', output_file,
                ] + platform_args + [url],
                
                # Try without cookies
                [
                    'yt-dlp',
                    '--merge-output-format', 'mp4',
                    '-o', output_file,
                ] + platform_args + [url]
            ]
        else:
            # TikTok, Twitter, etc. usually work without cookies
            strategies = [
                [
                    'yt-dlp',
                    '--merge-output-format', 'mp4',
                    '-o', output_file,
                ] + platform_args + [url]
            ]
        
        for i, cmd in enumerate(strategies):
            try:
                print(f"Trying {platform} download strategy {i+1}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode == 0 and os.path.exists(output_file):
                    print(f"{platform} download success with strategy {i+1}")
                    return output_file
                else:
                    print(f"Strategy {i+1} failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                print(f"Strategy {i+1} timeout")
                continue
            except Exception as e:
                print(f"Strategy {i+1} error: {e}")
                continue
        
        return None
    except Exception as e:
        print(f"Error downloading social video: {e}")
        return None