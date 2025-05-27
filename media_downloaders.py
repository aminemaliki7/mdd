import os
import subprocess
import shutil
import re
import time
import uuid
from urllib.parse import urlparse

def download_mp3(url, output_path='youtube_audio', filename=None):
    """
    Download audio from a video URL and save as MP3.
   
    Args:
        url (str): URL of the video
        output_path (str): Directory to save the MP3 file
        filename (str): Output filename (without extension)
   
    Returns:
        str: Path to the saved MP3 file
    """
    try:
        # Create output directory if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # Generate a unique filename if none provided
        if not filename:
            filename = f"audio_{uuid.uuid4().hex[:8]}"
        
        # Ensure filename is safe
        filename = re.sub(r'[^\w\-_.]', '_', filename)
        output_file = os.path.join(output_path, f"{filename}.mp3")
       
        print(f"Downloading audio from: {url}")
       
        # Use yt-dlp to download and convert directly to MP3
        cmd = [
            'yt-dlp',
            '-x',                    # Extract audio
            '--audio-format', 'mp3', # Convert to MP3
            '--audio-quality', '0',  # Best quality
            '-o', output_file,       # Output filename
            '--no-playlist',         # Don't download playlists
            url                      # Video URL
        ]
       
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)
       
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return None
        
        # Check if file exists
        if os.path.exists(output_file):
            print(f"Successfully downloaded: {output_file}")
            return output_file
        else:
            print("Download completed but could not locate the MP3 file.")
            return None
           
    except subprocess.CalledProcessError as e:
        print(f"Error executing yt-dlp: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return None
       
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def download_pinterest_video(url, output_path='pinterest_videos', filename=None):
    """
    Download video from a Pinterest URL and save it.
    
    Args:
        url (str): Pinterest URL of the video
        output_path (str): Directory to save the video file
        filename (str): Output filename (without extension)
    
    Returns:
        str: Path to the saved video file
    """
    try:
        # Create output directory if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # Validate Pinterest URL
        parsed_url = urlparse(url)
        if 'pinterest' not in parsed_url.netloc:
            print("Error: URL does not appear to be a Pinterest link.")
            return None
        
        # Extract pin ID for filename
        pin_id = None
        if '/pin/' in url:
            pin_id_match = re.search(r'/pin/(\d+)', url)
            if pin_id_match:
                pin_id = pin_id_match.group(1)
        
        # Set output filename
        if filename:
            filename = re.sub(r'[^\w\-_.]', '_', filename)  # Ensure filename is safe
            output_filename = f"{filename}.mp4"
        elif pin_id:
            output_filename = f"pinterest_{pin_id}.mp4"
        else:
            output_filename = f"pinterest_{uuid.uuid4().hex[:8]}.mp4"
        
        output_file = os.path.join(output_path, output_filename)
        
        # Use yt-dlp to download the Pinterest video
        cmd = [
            'yt-dlp',
            '--merge-output-format', 'mp4',  # Ensure output is MP4
            '-o', output_file,               # Output filename
            '--no-warnings',                 # Suppress warnings
            url                              # Pinterest URL
        ]
        
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Try alternate approach if first attempt fails
            alt_cmd = [
                'yt-dlp',
                '-f', 'b',          # Use best format
                '--merge-output-format', 'mp4',
                '-o', output_file,
                url
            ]
            
            alt_result = subprocess.run(alt_cmd, capture_output=True, text=True)
            
            if alt_result.returncode != 0:
                return None
        
        # Check if file was downloaded successfully
        if os.path.exists(output_file):
            print(f"Successfully downloaded: {output_file}")
            return output_file
        else:
            print("Download completed but could not locate the video file.")
            return None
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def check_yt_dlp_installed():
    """Check if yt-dlp is installed on the system"""
    return shutil.which('yt-dlp') is not None

def download_youtube_video(url, output_path='youtube_videos', filename=None, quality='best'):
    """
    Download a video from YouTube with options for quality.
    
    Args:
        url (str): YouTube URL of the video
        output_path (str): Directory to save the video file
        filename (str): Output filename (without extension)
        quality (str): Video quality - 'best', '1080p', '720p', '480p', '360p'
    
    Returns:
        str: Path to the saved video file
    """
    try:
        # Create output directory if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # Validate YouTube URL
        parsed_url = urlparse(url)
        if 'youtube.com' not in parsed_url.netloc and 'youtu.be' not in parsed_url.netloc:
            print("Error: URL does not appear to be a YouTube link.")
            return None
        
        # Extract video ID for the filename if no custom filename provided
        video_id = None
        if not filename:
            # Extract from youtube.com/watch?v=VIDEO_ID
            if 'youtube.com' in parsed_url.netloc and 'v=' in parsed_url.query:
                query_params = dict(param.split('=') for param in parsed_url.query.split('&') if '=' in param)
                video_id = query_params.get('v', '')
            # Extract from youtu.be/VIDEO_ID
            elif 'youtu.be' in parsed_url.netloc:
                video_id = parsed_url.path.lstrip('/')
        
        # Set output filename
        if filename:
            # Ensure filename is safe
            filename = re.sub(r'[^\w\-_.]', '_', filename)
            output_filename = f"{filename}.mp4"
        elif video_id:
            output_filename = f"youtube_{video_id}.mp4"
        else:
            output_filename = f"youtube_{uuid.uuid4().hex[:8]}.mp4"
        
        output_file = os.path.join(output_path, output_filename)
        
        # Map quality string to yt-dlp format selection
        format_selection = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        if quality == '1080p':
            format_selection = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
        elif quality == '720p':
            format_selection = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
        elif quality == '480p':
            format_selection = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
        elif quality == '360p':
            format_selection = 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best'
        
        # Use yt-dlp to download the YouTube video
        cmd = [
            'yt-dlp',
            '-f', format_selection,          # Format selection based on quality
            '-o', output_file,               # Output filename
            '--merge-output-format', 'mp4',  # Ensure output is MP4
            '--no-playlist',                 # Don't download playlists
            '--no-warnings',                 # Suppress warnings
            url                              # YouTube URL
        ]
        
        print(f"Downloading YouTube video: {url}")
        print(f"Quality: {quality}")
        print(f"Output: {output_file}")
        
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error downloading video: {result.stderr}")
            
            # Try alternate approach if first attempt fails
            alt_cmd = [
                'yt-dlp',
                '-f', 'best',                    # Fallback to best available format
                '-o', output_file,               # Output filename
                '--merge-output-format', 'mp4',  # Ensure output is MP4
                '--no-playlist',                 # Don't download playlists
                url                              # YouTube URL
            ]
            
            print("Attempting alternate download method...")
            alt_result = subprocess.run(alt_cmd, capture_output=True, text=True)
            
            if alt_result.returncode != 0:
                print(f"Alternate download failed: {alt_result.stderr}")
                return None
        
        # Check if file was downloaded successfully
        if os.path.exists(output_file):
            print(f"Successfully downloaded: {output_file}")
            return output_file
        else:
            print("Download completed but could not locate the video file.")
            return None
        
    except Exception as e:
        print(f"Error downloading YouTube video: {str(e)}")
        return None
def download_social_video(url, output_path='social_videos', filename=None):
    """
    Download a video from YouTube Shorts, TikTok, or Instagram using yt-dlp.
    
    Args:
        url (str): Video URL (YouTube Shorts, TikTok, Instagram Reels, etc.)
        output_path (str): Destination folder 
        filename (str): Custom filename (optional)
        
    Returns:
        str: Path to downloaded video or None if failed
    """
    try:
        # Ensure directory exists
        os.makedirs(output_path, exist_ok=True)

        # Safe filename
        if not filename:
            filename = f"social_{uuid.uuid4().hex[:8]}"
        filename = re.sub(r'[^\w\-_.]', '_', filename)
        output_file = os.path.join(output_path, f"{filename}.mp4")

        # Download command
        cmd = [
            'yt-dlp',
            '--merge-output-format', 'mp4',
            '-o', output_file,
            '--no-playlist',
            '--no-warnings',
            url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("Download failed:", result.stderr)
            return None

        return output_file if os.path.exists(output_file) else None

    except Exception as e:
        print(f"Error downloading video: {e}")
        return None


    