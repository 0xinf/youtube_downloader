#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog
import threading
from pathlib import Path
import sys
import os
import json
from datetime import datetime, timedelta
import subprocess
import pytubefix
from tqdm import tqdm
import ssl
import certifi

# Configure SSL context to use certifi's certificates
ssl._create_default_https_context = ssl._create_unverified_context

class YouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        
        # Set window size
        window_width = 1280
        window_height = 1000
        
        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Calculate position coordinates
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set window size and position
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.configure(bg="#f0f0f0")
        
        # Prevent window resizing
        self.root.resizable(True, True)
        
        # Lift window to top
        self.root.lift()
        self.root.focus_force()
        
        # Config file
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        self.config = self.load_config()
        
        # Style configuration
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TButton", padding=8, font=("Helvetica", 11))
        self.style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 11))
        self.style.configure("Header.TLabel", font=("Helvetica", 18, "bold"))
        
        self.create_widgets()
        self.streams = []
        self.yt = None
        self.downloading = False
        self.download_thread = None
        self.cancel_download = False
        
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'download_dir': os.path.expanduser('~/Downloads')}
        
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # URL Entry section
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(url_frame, text="YouTube URL:", font=("Helvetica", 13)).pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(url_frame, width=80, font=("Helvetica", 11))
        self.url_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        self.fetch_btn = ttk.Button(url_frame, text="Get Video Info", command=self.fetch_video_info)
        self.fetch_btn.pack(side=tk.LEFT)
        
        # Download Directory section
        dir_frame = ttk.Frame(main_frame)
        dir_frame.pack(fill=tk.X, pady=(0, 25))
        
        ttk.Label(dir_frame, text="Download Folder:", font=("Helvetica", 13)).pack(side=tk.LEFT)
        self.dir_entry = ttk.Entry(dir_frame, width=80, font=("Helvetica", 11))
        self.dir_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.dir_entry.insert(0, self.config['download_dir'])
        
        self.dir_btn = ttk.Button(dir_frame, text="Browse", command=self.choose_directory)
        self.dir_btn.pack(side=tk.LEFT)
        
        # Video info section
        self.info_frame = ttk.LabelFrame(main_frame, text="Video Information", padding="15")
        self.info_frame.pack(fill=tk.X, pady=(0, 25))
        
        self.title_label = ttk.Label(self.info_frame, text="", wraplength=1200)
        self.title_label.pack(fill=tk.X)
        self.channel_label = ttk.Label(self.info_frame, text="")
        self.channel_label.pack(fill=tk.X)
        self.length_label = ttk.Label(self.info_frame, text="")
        self.length_label.pack(fill=tk.X)
        
        # Formats section
        formats_frame = ttk.LabelFrame(main_frame, text="Available Formats", padding="15")
        formats_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 25))
        
        # Treeview for formats
        columns = ("Type", "Quality", "Format", "Size")
        self.tree = ttk.Treeview(formats_frame, columns=columns, show="headings", selectmode="browse", height=12)
        
        self.tree.heading("Type", text="Type")
        self.tree.heading("Quality", text="Quality")
        self.tree.heading("Format", text="Format")
        self.tree.heading("Size", text="Size")
        
        self.tree.column("Type", width=200)
        self.tree.column("Quality", width=150)
        self.tree.column("Format", width=150)
        self.tree.column("Size", width=150)
        
        scrollbar = ttk.Scrollbar(formats_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Message section
        message_frame = ttk.Frame(main_frame)
        message_frame.pack(fill=tk.X, pady=(0, 25))
        
        self.message_label = ttk.Label(message_frame, text="", wraplength=1200, justify=tk.LEFT)
        self.message_label.pack(fill=tk.X)
        
        # Download section
        download_frame = ttk.Frame(main_frame)
        download_frame.pack(fill=tk.X, pady=25)
        
        button_frame = ttk.Frame(download_frame)
        button_frame.pack(side=tk.LEFT)
        
        self.download_btn = ttk.Button(button_frame, text="Download", command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel_download_action, state="disabled")
        self.cancel_btn.pack(side=tk.LEFT)
        
        progress_frame = ttk.Frame(download_frame)
        progress_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(side=tk.TOP, fill=tk.X)
        
        status_frame = ttk.Frame(progress_frame)
        status_frame.pack(side=tk.TOP, fill=tk.X, pady=(5, 0))
        
        self.status_label = ttk.Label(status_frame, text="")
        self.status_label.pack(side=tk.LEFT)
        
        self.download_size_label = ttk.Label(status_frame, text="")
        self.download_size_label.pack(side=tk.RIGHT)
        
    def choose_directory(self):
        directory = filedialog.askdirectory(
            initialdir=self.config['download_dir'],
            title="Choose Download Directory"
        )
        if directory:
            self.config['download_dir'] = directory
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            self.save_config()
            
    def fetch_video_info(self):
        url = self.url_entry.get().strip()
        if not url:
            self.show_message("Please enter a YouTube URL", is_error=True)
            return
            
        self.fetch_btn.configure(state="disabled")
        self.status_label.configure(text="Fetching video info...")
        self.message_label.configure(text="")
        
        def fetch():
            try:
                self.yt = pytubefix.YouTube(url)
                self.root.after(0, self.update_video_info)
                self.root.after(0, self.update_formats)
                self.root.after(0, lambda: self.status_label.configure(text=""))
                self.root.after(0, lambda: self.show_message("Video information loaded successfully"))
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self.show_message(error_msg, is_error=True))
            finally:
                self.root.after(0, lambda: self.fetch_btn.configure(state="normal"))
        
        threading.Thread(target=fetch, daemon=True).start()
        
    def update_video_info(self):
        self.title_label.configure(text=f"Title: {self.yt.title}")
        self.channel_label.configure(text=f"Channel: {self.yt.author}")
        length = str(timedelta(seconds=self.yt.length))
        self.length_label.configure(text=f"Length: {length}")
        
    def update_formats(self):
        # Clear previous entries
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Get all streams
        video_streams = []
        
        # Get all video streams and sort them by resolution
        all_video_streams = self.yt.streams.filter(type="video").order_by('resolution').desc()
        
        # Get best audio stream for combining with video
        audio_streams = self.yt.streams.filter(only_audio=True).order_by('abr').desc()
        best_audio = audio_streams.first() if audio_streams else None
        
        # Process each video stream
        seen_resolutions = set()
        for stream in all_video_streams:
            # Skip duplicates of same resolution
            if stream.resolution in seen_resolutions:
                continue
                
            seen_resolutions.add(stream.resolution)
            
            # Check if it's 1080p or higher
            is_hd = False
            if stream.resolution:
                try:
                    # Extract numeric value from resolution (e.g., "1080p" -> 1080)
                    res_value = int(stream.resolution[:-1])
                    is_hd = res_value >= 1080
                except ValueError:
                    pass
            
            # If it's an adaptive stream (no audio), we'll need to combine it
            if not stream.is_progressive:
                size = self.get_size_str(stream.filesize + (best_audio.filesize if best_audio else 0))
                video_streams.append({
                    'stream': stream,
                    'audio_stream': best_audio,
                    'is_adaptive': True,
                    'values': (
                        f"Video{' (High Quality)' if is_hd else ''}",
                        stream.resolution,
                        "mp4",
                        size
                    )
                })
            else:
                size = self.get_size_str(stream.filesize)
                video_streams.append({
                    'stream': stream,
                    'audio_stream': None,
                    'is_adaptive': False,
                    'values': (
                        f"Video{' (High Quality)' if is_hd else ''}",
                        stream.resolution,
                        stream.mime_type.split('/')[-1],
                        size
                    )
                })
        
        # Store all streams for later use
        self.streams = []
        
        # Add video streams to treeview
        for stream_data in video_streams:
            self.streams.append(stream_data)
            self.tree.insert("", "end", values=stream_data['values'])
            
        # Add audio streams
        for stream in audio_streams:
            size = self.get_size_str(stream.filesize)
            # Add virtual MP3 option
            self.streams.append({'stream': stream, 'audio_stream': None, 'is_adaptive': False})
            self.tree.insert("", "end", values=(
                "Audio (MP3)",
                f"{stream.abr}",
                "mp3",
                size
            ))
            # Add virtual AAC option
            self.streams.append({'stream': stream, 'audio_stream': None, 'is_adaptive': False})
            self.tree.insert("", "end", values=(
                "Audio (AAC)",
                f"{stream.abr}",
                "aac",
                size
            ))
        
    def get_size_str(self, bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} GB"
        
    def cancel_download_action(self):
        if self.downloading and self.download_thread and self.download_thread.is_alive():
            self.cancel_download = True
            self.status_label.configure(text="Canceling download...")
            self.cancel_btn.configure(state="disabled")
    
    def start_download(self):
        if not self.yt or not self.streams:
            self.show_message("Please fetch video information first", is_error=True)
            return
            
        selection = self.tree.selection()
        if not selection:
            self.show_message("Please select a format to download", is_error=True)
            return
            
        # Get download directory from entry
        download_dir = self.dir_entry.get()
        if not os.path.exists(download_dir):
            try:
                os.makedirs(download_dir)
            except Exception as e:
                self.show_message(f"Could not create download directory: {str(e)}", is_error=True)
                return
        
        self.download_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.status_label.configure(text="Starting download...")
        self.progress_var.set(0)
        self.cancel_download = False
        self.message_label.configure(text="")
        
        # Get selected format index
        all_items = self.tree.get_children()
        format_idx = all_items.index(selection[0])
        
        # Start download in a separate thread
        self.downloading = True
        self.download_thread = threading.Thread(
            target=self.download_selected_format,
            args=(format_idx, download_dir)
        )
        self.download_thread.start()
        
    def show_message(self, message, is_error=False):
        if is_error:
            self.message_label.configure(
                text=f"❌ Error: {message}",
                foreground="red"
            )
        else:
            self.message_label.configure(
                text=f"✅ {message}",
                foreground="white",
                background="green"
            )
        
        # Programar la limpieza del mensaje después de 5 segundos
        self.root.after(5000, lambda: self.message_label.configure(
            text="",
            foreground="black",
            background=self.root.cget("background")
        ))
    
    def show_success(self):
        self.show_message("Download completed successfully!")
        
    def show_error(self, error_msg):
        self.show_message(error_msg, is_error=True)
    
    def reset_download_state(self):
        self.downloading = False
        self.download_thread = None
        self.cancel_download = False
        self.download_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.status_label.configure(text="")
        self.progress_var.set(0)
        self.download_size_label.configure(text="")
        
    def download_selected_format(self, format_idx, download_dir):
        try:
            stream_data = self.streams[format_idx]
            stream = stream_data['stream']
            format_type = self.tree.item(self.tree.get_children()[format_idx])['values'][0]
            
            if format_type.startswith("Audio"):
                self.download_audio(stream, download_dir, format_type)
            else:
                if stream_data['is_adaptive']:
                    self.download_adaptive_video(stream_data, download_dir)
                else:
                    self.download_video(stream, download_dir)
                    
            self.root.after(0, self.show_success)
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.show_error(error_msg))
        finally:
            self.root.after(0, self.reset_download_state)
            
    def download_video(self, stream, download_dir):
        filename = stream.default_filename
        filepath = os.path.join(download_dir, filename)
        
        def on_progress(stream, chunk, bytes_remaining):
            if self.cancel_download:
                raise Exception("Download cancelled by user")
                
            total_size = stream.filesize
            bytes_downloaded = total_size - bytes_remaining
            percentage = (bytes_downloaded / total_size) * 100
            downloaded_mb = bytes_downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            self.root.after(0, lambda: self.update_progress(percentage, downloaded_mb, total_mb))
        
        self.yt.register_on_progress_callback(on_progress)
        stream.download(output_path=download_dir, filename=filename)
        
    def download_adaptive_video(self, stream_data, download_dir):
        video_stream = stream_data['stream']
        audio_stream = stream_data['audio_stream']
        
        # Calculate total size
        total_size = video_stream.filesize + (audio_stream.filesize if audio_stream else 0)
        total_mb = total_size / (1024 * 1024)
        
        try:
            # Download video
            def on_video_progress(stream, chunk, bytes_remaining):
                if self.cancel_download:
                    raise Exception("Download cancelled by user")
                    
                bytes_downloaded = stream.filesize - bytes_remaining
                percentage = (bytes_downloaded / total_size) * 40  # First 40%
                downloaded_mb = bytes_downloaded / (1024 * 1024)
                self.root.after(0, lambda: self.update_progress(percentage, downloaded_mb, total_mb))
            
            self.root.after(0, lambda: self.status_label.configure(text="Downloading video..."))
            self.yt.register_on_progress_callback(on_video_progress)
            video_file = os.path.join(download_dir, "temp_video")
            video_stream.download(output_path=download_dir, filename="temp_video")
            
            if self.cancel_download:
                raise Exception("Download cancelled by user")
            
            # Download audio
            def on_audio_progress(stream, chunk, bytes_remaining):
                if self.cancel_download:
                    raise Exception("Download cancelled by user")
                    
                video_size = video_stream.filesize
                audio_downloaded = stream.filesize - bytes_remaining
                total_downloaded = video_size + audio_downloaded
                percentage = (total_downloaded / total_size) * 70  # Up to 70%
                downloaded_mb = total_downloaded / (1024 * 1024)
                self.root.after(0, lambda: self.update_progress(percentage, downloaded_mb, total_mb))
            
            self.root.after(0, lambda: self.status_label.configure(text="Downloading audio..."))
            self.yt.register_on_progress_callback(on_audio_progress)
            audio_file = os.path.join(download_dir, "temp_audio")
            audio_stream.download(output_path=download_dir, filename="temp_audio")
            
            if self.cancel_download:
                raise Exception("Download cancelled by user")
            
            # Combine video and audio
            self.root.after(0, lambda: self.status_label.configure(text="Combining video and audio..."))
            self.root.after(0, lambda: self.download_size_label.configure(text=f"{total_mb:.1f}MB / {total_mb:.1f}MB"))
            
            # Create final filename
            final_filename = f"{self.yt.title} ({video_stream.resolution}).mp4"
            final_filename = "".join(c for c in final_filename if c.isalnum() or c in (' ', '-', '_', '.'))
            final_path = os.path.join(download_dir, final_filename)
            
            # Combine using ffmpeg
            cmd = [
                'ffmpeg',
                '-i', video_file,
                '-i', audio_file,
                '-c:v', 'copy',
                '-c:a', 'aac',
                final_path,
                '-y'
            ]
            
            process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
            process.wait()
            
            # Clean up temp files
            os.remove(video_file)
            os.remove(audio_file)
            
            self.progress_var.set(100)
            
        except Exception as e:
            if "Download cancelled by user" in str(e):
                self.root.after(0, lambda: self.status_label.configure(text="Download cancelled"))
                self.root.after(0, lambda: self.reset_download_state())
                # Clean up temporary files
                for temp_file in [video_file, audio_file]:
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                return
            raise e
            
    def download_audio(self, stream, download_dir, format_type):
        temp_file = os.path.join(download_dir, "temp_audio")
        format_ext = "mp3" if "MP3" in format_type else "aac"
        final_filename = f"{self.yt.title}.{format_ext}"
        final_path = os.path.join(download_dir, final_filename)
        
        # Register progress callback before downloading
        def on_progress(stream, chunk, bytes_remaining):
            if self.cancel_download:
                raise Exception("Download cancelled by user")
                
            total_size = stream.filesize
            bytes_downloaded = total_size - bytes_remaining
            percentage = (bytes_downloaded / total_size) * 50  # First 50% for download
            downloaded_mb = bytes_downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            self.root.after(0, lambda: self.update_progress(percentage, downloaded_mb, total_mb))
        
        # Register the callback
        self.yt.register_on_progress_callback(on_progress)
        
        # Download audio stream
        stream.download(output_path=download_dir, filename="temp_audio")
        
        # Convert to desired format
        self.root.after(0, lambda: self.status_label.configure(text="Converting audio..."))
        
        if format_ext == "mp3":
            cmd = [
                'ffmpeg', '-i', temp_file,
                '-codec:a', 'libmp3lame',
                '-q:a', '2',
                final_path,
                '-y'
            ]
        else:
            cmd = [
                'ffmpeg', '-i', temp_file,
                '-c:a', 'aac',
                '-b:a', '192k',
                final_path,
                '-y'
            ]
            
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
        process.wait()
        
        # Clean up temp file
        os.remove(temp_file)
        
        # Set progress to 100%
        self.root.after(0, lambda: self.progress_var.set(100))
        
    def update_progress(self, percentage, downloaded_mb, total_mb):
        self.progress_var.set(percentage)
        self.download_size_label.configure(text=f"{downloaded_mb:.1f}MB / {total_mb:.1f}MB")

def main():
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
