# YouTube Downloader

A powerful command-line tool for downloading YouTube videos and audio with advanced format selection and progress tracking.

## Features

- 📹 Download videos in multiple qualities (up to 1080p+)
- 🎵 Extract audio in multiple formats (MP3/AAC)
- 📊 Real-time progress tracking
- 🔍 Detailed format information with `-v` flag
- ✨ Clean and user-friendly interface

## Requirements

- Python 3.6+
- FFmpeg (required for audio conversion and high-quality video processing)

### Python Packages
```bash
pip install pytubefix
pip install tqdm
```

### FFmpeg Installation
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt-get install ffmpeg`
- **Windows**: Download from [FFmpeg official website](https://ffmpeg.org/download.html)

## Usage

1. Clone the repository:
```bash
git clone https://github.com/0xinf/youtube_downloader.git
cd youtube_downloader
```

2. Run the script:
```bash
# Normal mode
python youtube_downloader.py "VIDEO_URL"

# Verbose mode (shows all available formats and detailed information)
python youtube_downloader.py -v "VIDEO_URL"
```

3. Select your desired format from the list and enjoy!

## Example Output

```
📡 Getting video information...
Title: Example Video
Channel: Example Channel
Length: 10:30
Views: 1,234,567

Available formats:
----------------------------------------
#   Type         Quality    Format   Size     
----------------------------------------
1   Video        1080p+     mp4      150 MB
2   Video        1080p      mp4      120 MB
3   Video        720p       mp4      80 MB
4   Audio only   160kbps    mp3      12 MB
5   Audio only   160kbps    aac      12 MB
----------------------------------------
```

## License

MIT License - feel free to use and modify as you wish!
