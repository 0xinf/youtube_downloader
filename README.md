# YouTube Downloader

A powerful command-line tool for downloading YouTube videos and audio with advanced format selection and progress tracking.

## Usage

### Console Version

```bash
# Normal mode
python3 youtube_downloader.py "VIDEO_URL"

# Verbose mode (shows all available formats / codecs and detailed information of the process)
python3 youtube_downloader.py -v "VIDEO_URL"
```

### GUI Version

```bash
python3 youtube_downloader_gui.py
```

Using the interface:
1. Enter a YouTube URL in the input field
2. Click "Fetch Info" to load video information
3. Select your desired download directory
4. Choose a format from the available options table
5. Click "Download" to start downloading
6. Use "Cancel" if you need to stop the download

## Requirements

- Python 3.6+
- FFmpeg (required for audio conversion and high-quality video processing)
- pip install -r requirements.txt

### Python Packages
```bash
pip install pytubefix
pip install tqdm
```

### FFmpeg Installation
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt-get install ffmpeg`
- **Windows**: Download from [FFmpeg official website](https://ffmpeg.org/download.html)


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

## Features

- 📹 Download videos in multiple qualities (up to 4320p+)
- 🎵 Extract audio in multiple formats (MP3/AAC)
- 📊 Real-time progress tracking
- 🔍 Detailed format information with `-v` flag
- ✨ Clean and user-friendly interface
- 📈 User-friendly graphical interface (GUI Version)
- 📊 Real-time video information display (GUI Version)
- 📈 Format selection through an interactive table (GUI Version)
- 📊 Progress bar with download status (GUI Version)
- 📁 Download size information (GUI Version)
- 🚫 Cancel download functionality (GUI Version)
- 📝 Status messages integrated in the interface (GUI Version)
- 📁 Directory selection dialog (GUI Version)
- 📈 Support for all video and audio formats (GUI Version)



## License

MIT License - feel free to use and modify as you wish!
