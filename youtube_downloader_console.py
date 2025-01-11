"""
YouTube Video Downloader Script
This script allows downloading YouTube videos in various qualities, with options for:
- Downloading video and audio together (progressive download)
- Downloading high quality video and audio separately and combining them
- Viewing all available stream formats
- Selecting specific quality options
"""

from pytubefix import YouTube
import os
import re
import ssl
import sys
import time
import platform
import subprocess
import argparse
from datetime import datetime
from tqdm import tqdm

# Configure SSL to ignore certificate verification
# This is needed because sometimes YouTube's SSL certificate can cause issues
ssl._create_default_https_context = ssl._create_unverified_context

class DownloadProgress:
    def __init__(self, desc="Downloading"):
        self.pbar = None
        self.desc = desc

    def __call__(self, stream, chunk, bytes_remaining):
        if self.pbar is None:
            total_size = stream.filesize
            self.pbar = tqdm(
                total=total_size,
                unit='iB',
                unit_scale=True,
                desc=self.desc,
                bar_format='{desc}: {percentage:3.0f}%|{bar:30}{r_bar}'
            )
        
        self.pbar.update(len(chunk))

    def complete(self):
        if self.pbar is not None:
            self.pbar.close()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Download YouTube videos')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('-v', '--verbose', action='store_true',
                      help='Show detailed information about streams and processing')
    return parser.parse_args()

def process_with_progress(video_path, audio_path, output_path, verbose=False):
    """
    Process video and audio files with ffmpeg showing a progress bar
    """
    print("\n🔄 Processing files...")
    print("⚡ Combining video and audio tracks. This might take a few minutes...")
    
    # Get video information using ffprobe
    probe = subprocess.run([
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=nb_frames',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ], capture_output=True, text=True)
    
    try:
        total_frames = int(probe.stdout.strip())
    except (ValueError, AttributeError):
        # If nb_frames is not available, estimate from duration and fps
        probe = subprocess.run([
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=duration,r_frame_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ], capture_output=True, text=True)
        
        try:
            info = probe.stdout.strip().split('\n')
            duration = float(info[0])
            fps = eval(info[1])  # r_frame_rate comes as fraction like '30000/1001'
            total_frames = int(duration * float(fps))
        except (ValueError, AttributeError, IndexError):
            total_frames = 0
    
    # Start ffmpeg process
    if verbose:
        # In verbose mode, show ffmpeg output directly
        print_colored("\n📝 FFmpeg process output (merging video and audio) - You can safely ignore the following technical details:", 'cyan')
        print_colored("=" * 80, 'cyan')
        process = subprocess.Popen([
            'ffmpeg',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            output_path,
            '-y'
        ], stderr=subprocess.PIPE, universal_newlines=True)
        
        # Show ffmpeg output in real-time
        for line in process.stderr:
            print(line, end='')
        
        print_colored("=" * 80, 'cyan')
        process.wait()
        return process.returncode
    else:
        # In normal mode, show progress bar
        pbar = tqdm(total=100, desc="🎬 Processing", 
                   bar_format='{desc}: {percentage:3.0f}%|{bar:30}| {elapsed}<{remaining}')
        
        process = subprocess.Popen([
            'ffmpeg',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-progress', 'pipe:1',  # Output progress to stdout
            output_path,
            '-y'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        # Monitor progress
        frame_count = 0
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
                
            # Parse progress information
            if line.startswith('frame='):
                try:
                    frame_count = int(line.split('=')[1].strip())
                    if total_frames > 0:
                        progress = min(int((frame_count / total_frames) * 100), 100)
                        pbar.n = progress
                        pbar.refresh()
                except (ValueError, IndexError):
                    pass
        
        pbar.n = 100
        pbar.refresh()
        pbar.close()
        
        return process.returncode

def process_audio(input_path, output_path, format='mp3', verbose=False):
    """
    Convert audio to specified format
    """
    print(f"\n🎵 Converting audio to {format.upper()}...")
    
    # Get audio duration using ffprobe
    probe = subprocess.run([
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_path
    ], capture_output=True, text=True)
    
    try:
        duration = float(probe.stdout.strip())
    except (ValueError, AttributeError):
        duration = 0
    
    # Prepare ffmpeg command based on format
    if format == 'mp3':
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-codec:a', 'libmp3lame',
            '-q:a', '2',  # High quality VBR
        ]
    else:  # aac
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:a', 'aac',
            '-b:a', '192k',  # High quality AAC
        ]
    
    if verbose:
        # Show ffmpeg output in verbose mode
        print_colored("\n📝 FFmpeg process output (converting audio) - You can safely ignore the following technical details:", 'cyan')
        print_colored("=" * 80, 'cyan')
        cmd.extend([output_path, '-y'])
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
        for line in process.stderr:
            print(line, end='')
        print_colored("=" * 80, 'cyan')
        process.wait()
    else:
        # Show progress bar in normal mode
        pbar = tqdm(total=100, desc="🎵 Converting", 
                   bar_format='{desc}: {percentage:3.0f}%|{bar:30}| {elapsed}<{remaining}')
        
        cmd.extend([
            '-progress', 'pipe:1',  # Output progress to stdout
            output_path,
            '-y'
        ])
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        # Monitor progress
        time_processed = 0
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
                
            # Parse progress information
            if line.startswith('out_time_ms='):
                try:
                    time_processed = int(line.split('=')[1].strip()) / 1_000_000  # Convert microseconds to seconds
                    if duration > 0:
                        progress = min(int((time_processed / duration) * 100), 100)
                        pbar.n = progress
                        pbar.refresh()
                except (ValueError, IndexError):
                    pass
        
        pbar.n = 100
        pbar.refresh()
        pbar.close()
    
    return process.returncode

def print_colored(text, color):
    """Print text in color"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'purple': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m',
        'end': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")

def clean_filename(title):
    """
    Remove illegal characters from filename to ensure it can be saved properly
    Args:
        title (str): The original filename
    Returns:
        str: A cleaned filename safe for saving
    """
    return re.sub(r'[<>:"/\\|?*]', '', title)

def format_duration(duration):
    """
    Convert duration from seconds to HH:MM:SS format
    Args:
        duration (int): Duration in seconds
    Returns:
        str: Formatted duration string
    """
    if not duration:
        return "0:00"
    minutes = duration // 60
    seconds = duration % 60
    if minutes >= 60:
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"

def format_filesize(bytes):
    """
    Convert bytes to human readable format (B, KB, MB, GB, TB)
    Args:
        bytes (int): Size in bytes
    Returns:
        str: Formatted size string with appropriate unit
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} TB"

def print_video_info(yt):
    """
    Print basic video information in a clean format
    Args:
        yt: YouTube object containing the video information
    """
    print("\n" + "=" * 80)
    print(f"Title: {yt.title}")
    print(f"Channel: {yt.author}")
    print(f"Duration: {format_duration(yt.length)}")
    print(f"Views: {yt.views:,}")
    print("=" * 80)

def organize_streams(yt, verbose=False):
    """
    Organize streams by type and quality, removing duplicates except for 1080p
    Args:
        yt: YouTube object containing the video information
        verbose: Whether to include webm formats
    Returns:
        tuple: Lists of video and audio streams
    """
    # Get all streams and organize them
    video_streams = {}
    audio_streams = []
    best_audio = None
    
    # First, collect all video streams with their best audio counterpart
    for stream in yt.streams:
        if stream.includes_video_track:
            # Skip webm formats in non-verbose mode
            if not verbose and stream.subtype == 'webm':
                continue
                
            resolution = stream.resolution
            
            # Special handling for 1080p: keep both versions
            if resolution == "1080p":
                if "1080p_hd" not in video_streams:
                    video_streams["1080p_hd"] = stream
                elif stream.filesize < video_streams["1080p_hd"].filesize:
                    video_streams["1080p"] = stream
            elif resolution not in video_streams:
                video_streams[resolution] = stream
        elif stream.includes_audio_track and not stream.includes_video_track:
            if best_audio is None or (stream.abr and best_audio.abr and 
                  int(''.join(filter(str.isdigit, stream.abr))) > 
                  int(''.join(filter(str.isdigit, best_audio.abr)))):
                best_audio = stream
            audio_streams.append(stream)
    
    # Convert dictionary to list maintaining order
    ordered_streams = []
    resolutions = sorted(video_streams.keys(), 
                        key=lambda x: (int(''.join(filter(str.isdigit, x))), 'hd' in x.lower()),
                        reverse=True)
    
    for res in resolutions:
        ordered_streams.append(video_streams[res])
    
    # Sort audio streams by bitrate and organize them
    audio_quality = {}
    for stream in audio_streams:
        bitrate = int(''.join(filter(str.isdigit, stream.abr if stream.abr else "128")))
        key = f"{bitrate}kbps"
        if key not in audio_quality or stream.filesize < audio_quality[key].filesize:
            audio_quality[key] = stream
    
    # Sort audio streams by bitrate
    audio_streams = []
    bitrates = sorted(audio_quality.keys(), 
                     key=lambda x: int(''.join(filter(str.isdigit, x))),
                     reverse=True)
    
    for bitrate in bitrates:
        audio_streams.append(audio_quality[bitrate])
    
    # Create virtual audio streams for MP3 and AAC
    if best_audio:
        # Create MP3 and AAC options for each quality level
        virtual_streams = []
        for audio in audio_streams:
            bitrate = audio.abr if audio.abr else "160kbps"
            mp3_stream = {
                'type': 'audio',
                'subtype': 'mp3',
                'abr': bitrate,
                'filesize': audio.filesize,
                'audio_codec': 'mp3',
                'original_stream': audio
            }
            aac_stream = {
                'type': 'audio',
                'subtype': 'aac',
                'abr': bitrate,
                'filesize': audio.filesize,
                'audio_codec': 'aac',
                'original_stream': audio
            }
            virtual_streams.extend([mp3_stream, aac_stream])
        
        if verbose:
            # In verbose mode, add MP3 and AAC options after original streams
            audio_streams.extend(virtual_streams)
        else:
            # In normal mode, only show MP3 and AAC
            audio_streams = virtual_streams[:2]  # Only keep the highest quality ones
    
    return ordered_streams, audio_streams

def print_stream_options(video_streams, audio_streams, verbose=False):
    """
    Print available stream options in a clean, organized format
    Args:
        video_streams: List of video streams
        audio_streams: List of audio streams
        verbose: Show detailed codec information
    """
    print("\nAvailable formats:")
    
    # Determine column widths based on verbose mode
    if verbose:
        header = f"{'#':<3} {'Type':<12} {'Quality':<10} {'Format':<8} {'Codec':<15} {'Size':<10}"
        separator_length = 100
    else:
        header = f"{'#':<3} {'Type':<12} {'Quality':<10} {'Format':<8} {'Size':<10}"
        separator_length = 90
    
    print("-" * separator_length)
    print(header)
    print("-" * separator_length)
    
    # Print video streams
    for i, stream in enumerate(video_streams, 1):
        size = format_filesize(stream.filesize)
        quality = stream.resolution
        if quality == "1080p" and i == 1:
            quality += "+"  # Mark the higher quality version
        
        if verbose:
            codec = f"{stream.video_codec}".replace("video/", "")
            print(f"{i:<3} {'Video':<12} {quality:<10} {stream.subtype:<8} {codec:<15} {size:<10}")
        else:
            print(f"{i:<3} {'Video':<12} {quality:<10} {stream.subtype:<8} {size:<10}")
    
    # Print audio streams
    start_audio_index = len(video_streams) + 1
    for i, stream in enumerate(audio_streams, start_audio_index):
        if isinstance(stream, dict):
            # Handle virtual audio streams (MP3/AAC)
            size = format_filesize(stream['filesize'])
            quality = stream['abr']
            if verbose:
                print(f"{i:<3} {'Audio only':<12} {quality:<10} {stream['subtype']:<8} {stream['audio_codec']:<15} {size:<10}")
            else:
                print(f"{i:<3} {'Audio only':<12} {quality:<10} {stream['subtype']:<8} {size:<10}")
        else:
            # Handle original audio streams
            size = format_filesize(stream.filesize)
            quality = f"{stream.abr}" if stream.abr else "128kbps"
            if verbose:
                codec = f"{stream.audio_codec}".replace("audio/", "")
                print(f"{i:<3} {'Audio only':<12} {quality:<10} {stream.subtype:<8} {codec:<15} {size:<10}")
            else:
                print(f"{i:<3} {'Audio only':<12} {quality:<10} {stream.subtype:<8} {size:<10}")
    
    print("-" * separator_length)

def download_video(url, verbose=False):
    try:
        # Create downloads directory if it doesn't exist
        download_path = os.path.join(os.getcwd(), 'downloads')
        os.makedirs(download_path, exist_ok=True)
        
        # Initialize YouTube object and get video information
        print("\n📡 Getting video information...")
        yt = YouTube(url)
        
        # Display basic video information
        print_video_info(yt)
        
        # Organize and display available streams
        video_streams, audio_streams = organize_streams(yt, verbose)
        print_stream_options(video_streams, audio_streams, verbose)
        
        # Get user's format choice
        all_streams = video_streams + audio_streams
        while True:
            try:
                choice = input("\n🎯 Choose the format number you want to download: ")
                choice = int(choice)
                if 1 <= choice <= len(all_streams):
                    selected_stream = all_streams[choice-1]
                    break
                else:
                    print("❌ Invalid number. Try again.")
            except ValueError:
                print("❌ Please enter a valid number.")
            except KeyboardInterrupt:
                print("\n🛑 Download cancelled by user.")
                sys.exit(0)
        
        # Prepare filename and paths
        safe_title = clean_filename(yt.title)
        is_video = isinstance(selected_stream, dict) or selected_stream.includes_video_track
        
        if is_video and not isinstance(selected_stream, dict):
            print(f"\n🎥 Selected quality: {selected_stream.resolution}")
            if verbose:
                print(f"ℹ️  Video codec: {selected_stream.video_codec}")
                print(f"ℹ️  Container: {selected_stream.subtype}")
            filename = f"{safe_title}_{selected_stream.resolution}.{selected_stream.subtype}"
        else:
            if verbose:
                print(f"\n🎵 Selected quality: {selected_stream.abr}")
                print(f"ℹ️  Audio codec: {selected_stream.audio_codec}")
                print(f"ℹ️  Container: {selected_stream.subtype}")
                filename = f"{safe_title}_audio.{selected_stream.subtype}"
            else:
                # Handle virtual audio stream
                print(f"\n🎵 Selected quality: {selected_stream['abr']}")
                print(f"ℹ️  Format: {selected_stream['subtype'].upper()}")
                filename = f"{safe_title}_audio.{selected_stream['subtype']}"
        
        if isinstance(selected_stream, dict):
            print(f"📦 File size: {format_filesize(selected_stream['filesize'])}")
        else:
            print(f"📦 File size: {format_filesize(selected_stream.filesize)}")
        
        if is_video and not isinstance(selected_stream, dict) and not selected_stream.is_progressive:
            # Handle high quality format that needs separate audio download
            print("\n🚀 Starting download process...")
            print("\n📥 Downloading video and audio separately for best quality...")
            
            # Get the highest quality audio stream
            audio = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            
            if verbose:
                print(f"\nℹ️  Selected audio stream:")
                print(f"   - Bitrate: {audio.abr}")
                print(f"   - Codec: {audio.audio_codec}")
                print(f"   - Size: {format_filesize(audio.filesize)}")
            
            # Prepare filenames for temporary and final files
            video_filename = f"{safe_title}_video_temp.{selected_stream.subtype}"
            audio_filename = f"{safe_title}_audio_temp.{audio.subtype}"
            
            video_path = os.path.join(download_path, video_filename)
            audio_path = os.path.join(download_path, audio_filename)
            output_path = os.path.join(download_path, filename)
            
            try:
                # Download video with progress bar
                print()  # Add space before video progress
                video_progress = DownloadProgress("📹 Video")
                yt.register_on_progress_callback(video_progress)
                selected_stream.download(output_path=download_path, filename=video_filename)
                video_progress.complete()
                
                # Download audio with progress bar
                print()  # Add space before audio progress
                audio_progress = DownloadProgress("🎵 Audio")
                yt.register_on_progress_callback(audio_progress)
                audio.download(output_path=download_path, filename=audio_filename)
                audio_progress.complete()
                
                # Process files with progress bar
                print()  # Add space before processing
                result = process_with_progress(video_path, audio_path, output_path, verbose)
                
                if result == 0:
                    print("\n✨ Download and processing completed!")
                    print(f"📁 Saved to: {output_path}")
                    # Open downloads folder
                    print("\n🗂️  Opening downloads folder...")
                    open_file_explorer(download_path)
                else:
                    print("\n❌ Error combining video and audio")
                    sys.exit(1)
            
            finally:
                # Clean up temporary files
                if os.path.exists(video_path):
                    os.remove(video_path)
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                
        else:
            # Handle progressive format or audio-only download
            full_path = os.path.join(download_path, filename)
            temp_path = os.path.join(download_path, f"{safe_title}_temp.{selected_stream['original_stream'].subtype if isinstance(selected_stream, dict) else selected_stream.subtype}")
            
            print("\n🚀 Starting download...")
            # Determine if we're downloading video or audio
            is_video_download = isinstance(selected_stream, dict) == False and selected_stream.includes_video_track
            progress = DownloadProgress("📹 Video" if is_video_download else "🎵 Audio")
            yt.register_on_progress_callback(progress)
            
            if isinstance(selected_stream, dict):
                # Download and convert audio
                selected_stream['original_stream'].download(output_path=download_path, filename=os.path.basename(temp_path))
                progress.complete()
                
                result = process_audio(temp_path, full_path, format=selected_stream['subtype'], verbose=verbose)
                
                if result == 0:
                    os.remove(temp_path)  # Clean up temp file
                else:
                    print(f"\n❌ Error converting audio")
                    sys.exit(1)
            else:
                # Direct download
                selected_stream.download(output_path=download_path, filename=filename)
                progress.complete()
            
            print("\n✨ Download completed!")
            print(f"📁 Saved to: {full_path}")
            # Open downloads folder
            print("\n🗂️  Opening downloads folder...")
            open_file_explorer(download_path)
        
    except KeyboardInterrupt:
        print("\n\n❌ Download cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error downloading video, incorrect link")
        sys.exit(1)

def open_file_explorer(path):
    """
    Open the file explorer at the specified path
    Args:
        path (str): Path to open
    """
    if platform.system() == "Darwin":  # macOS
        subprocess.run(["open", path])
    elif platform.system() == "Windows":  # Windows
        subprocess.run(["explorer", path])
    else:  # Linux
        subprocess.run(["xdg-open", path])

def main():
    """Main entry point of the script"""
    args = parse_arguments()
    download_video(args.url, args.verbose)

if __name__ == "__main__":
    main()
