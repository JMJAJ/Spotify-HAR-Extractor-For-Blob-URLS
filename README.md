# 🎵 Spotify HAR Extractor

Extract Spotify content (images, videos, canvas animations) from HAR (HTTP Archive) files captured from your browser.

## 🚀 Features

- **Image Extraction**: Download album covers, artist photos, playlist images from Spotify CDNs
- **Video/Canvas Extraction**: Extract Spotify Canvas video animations and combine WebM segments
- **API Analysis**: Parse Spotify API responses to find additional media references
- **Multiple Input Methods**: Support for HAR files, direct JSON input, or drag-and-drop
- **Automatic Conversion**: Convert WebM videos to MP4 (requires FFmpeg)
- **Detailed Reports**: Generate comprehensive analysis reports in JSON format

## 📋 Requirements

```
requests
```

### Optional Dependencies
- **FFmpeg**: For WebM to MP4 conversion (recommended)

## 🛠️ Installation

1. Clone or download the script
2. Install Python dependencies:
```bash
pip install requests
```

3. (Optional) Install FFmpeg for video conversion:
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

## 📖 Usage

### Method 1: Command Line with HAR File
```bash
python spotify_har.py path/to/your/file.(har/json)
```

### Method 2: Interactive Mode
```bash
python spotify_har.py
```
Then choose from:
- Enter path to HAR file
- Paste HAR JSON data directly
- Drag and drop HAR file

### Method 3: Import as Module
```python
from spotify_har import SpotifyHARExtractor

extractor = SpotifyHARExtractor()
results = extractor.process_har_file('your_file.har')
```

## 📁 How to Capture HAR Files

1. Open Chrome/Firefox Developer Tools (F12)
2. Go to **Network** tab
3. Navigate to Spotify Web Player
4. Browse music, playlists, artists
5. Right-click in Network tab → **Save all as HAR**

## 📂 Output Structure

```
har_extracted/
├── images/           # Album covers, artist photos, playlist images
├── videos/           # Canvas animations, video content
└── data/            # Analysis reports and metadata
```

## 🎯 Supported Spotify Content

### Image Sources
- `i.scdn.co` - Album covers and artist images
- `mosaic.scdn.co` - Playlist mosaics
- `seed-mix-image.spotifycdn.com` - Mix covers
- `lineup-images.scdn.co` - Event lineups
- `thisis-images.scdn.co` - "This Is" playlist covers
- `charts-images.scdn.co` - Chart covers
- `daily-mix.scdn.co` - Daily mix covers

### Video Sources
- `video-akpcw.spotifycdn.com` - Canvas video segments
- `canvas.scdn.co` - Canvas animations
- `canvaz.scdn.co` - Alternative canvas domain

## 🔧 Advanced Features

### WebM Segment Combination
The tool automatically detects and combines WebM video segments from Spotify Canvas:
- Identifies initialization segments
- Combines media segments in correct order
- Creates playable WebM files
- Converts to MP4 (if FFmpeg available)

### API Response Analysis
Parses Spotify API responses to find:
- Image references in JSON data
- Spotify image ID patterns
- Additional media URLs

### Content Type Detection
Automatically detects file types from:
- HTTP Content-Type headers
- File magic bytes
- URL patterns

## 📊 Analysis Reports

Each extraction generates a detailed JSON report containing:
- HAR file metadata
- Extraction statistics
- Media file information
- Found URLs and references
- Processing timestamps

## 📄 License


This project is provided as-is for educational purposes.

