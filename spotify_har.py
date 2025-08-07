"""
🎵 SPOTIFY HAR EXTRACTOR 🎵
Extract Spotify content from HAR (HTTP Archive) files
"""

import os
import sys
import json
import re
import requests
import base64
import time
import subprocess
from typing import List, Dict, Optional, Any
from urllib.parse import unquote, urlparse, parse_qs

class SpotifyHARExtractor:
    def __init__(self):
        self.output_folder = "har_extracted"
        self.images_folder = os.path.join(self.output_folder, "images")
        self.videos_folder = os.path.join(self.output_folder, "videos")
        self.data_folder = os.path.join(self.output_folder, "data")

        for folder in [self.output_folder, self.images_folder, self.videos_folder, self.data_folder]:
            os.makedirs(folder, exist_ok=True)

        self.found_urls = set()
        self.extracted_data = {}

    def load_har_file(self, har_path: str) -> Optional[Dict]:
        """Load and parse HAR file"""
        try:
            with open(har_path, 'r', encoding='utf-8') as f:
                har_data = json.load(f)
            print(f"✅ Loaded HAR file: {har_path}")
            return har_data
        except Exception as e:
            print(f"❌ Error loading HAR file: {e}")
            return None

    def load_har_from_json_string(self, har_json: str) -> Optional[Dict]:
        """Load HAR data from JSON string"""
        try:
            har_data = json.loads(har_json)
            print("✅ Loaded HAR data from JSON string")
            return har_data
        except Exception as e:
            print(f"❌ Error parsing HAR JSON: {e}")
            return None

    def extract_spotify_images(self, har_data: Dict) -> List[Dict]:
        """Extract Spotify image URLs and data from HAR"""
        images = []

        if 'log' not in har_data or 'entries' not in har_data['log']:
            print("❌ Invalid HAR format")
            return images

        entries = har_data['log']['entries']
        print(f"🔍 Analyzing {len(entries)} HAR entries...")

        for entry in entries:
            try:
                request = entry.get('request', {})
                response = entry.get('response', {})
                url = request.get('url', '')

                if self.is_spotify_image_url(url):
                    image_info = {
                        'url': url,
                        'method': request.get('method', 'GET'),
                        'status': response.get('status', 0),
                        'content_type': self.get_content_type(response),
                        'size': response.get('bodySize', 0),
                        'timestamp': entry.get('startedDateTime', ''),
                        'headers': response.get('headers', [])
                    }

                    content = response.get('content', {})
                    if content:
                        image_info['content'] = content

                        if content.get('encoding') == 'base64' and content.get('text'):
                            try:
                                decoded_data = base64.b64decode(content['text'])
                                image_info['decoded_size'] = len(decoded_data)
                                image_info['decoded_data'] = decoded_data
                            except Exception as e:
                                print(f"⚠️  Base64 decode error for {url}: {e}")

                    images.append(image_info)
                    print(f"🖼️  Found Spotify image: {url}")

                elif self.is_spotify_video_url(url):
                    video_info = {
                        'url': url,
                        'method': request.get('method', 'GET'),
                        'status': response.get('status', 0),
                        'content_type': self.get_content_type(response),
                        'size': response.get('bodySize', 0),
                        'timestamp': entry.get('startedDateTime', ''),
                        'headers': response.get('headers', [])
                    }

                    content = response.get('content', {})
                    if content and content.get('text'):
                        video_info['content'] = content
                        if content.get('encoding') == 'base64':
                            try:
                                decoded_data = base64.b64decode(content['text'])
                                video_info['decoded_size'] = len(decoded_data)
                                video_info['decoded_data'] = decoded_data
                            except Exception as e:
                                print(f"⚠️  Base64 decode error for video {url}: {e}")

                    images.append(video_info)  
                    print(f"🎬 Found Spotify video: {url}")

                elif 'api.spotify.com' in url or 'spclient' in url:
                    self.extract_api_image_references(entry, url)

            except Exception as e:
                print(f"⚠️  Error processing entry: {e}")
                continue

        print(f"📊 Found {len(images)} Spotify media URLs")
        return images

    def is_spotify_image_url(self, url: str) -> bool:
        """Check if URL is a Spotify image CDN URL"""
        spotify_image_domains = [
            'i.scdn.co',
            'mosaic.scdn.co',
            'seed-mix-image.spotifycdn.com',
            'lineup-images.scdn.co',
            'thisis-images.scdn.co',
            'charts-images.scdn.co',
            'daily-mix.scdn.co',
            'mixed-media-images.spotifycdn.com'
        ]

        return any(domain in url for domain in spotify_image_domains)

    def is_spotify_video_url(self, url: str) -> bool:
        """Check if URL is a Spotify video/canvas URL"""
        spotify_video_domains = [
            'video-akpcw.spotifycdn.com',
            'video-fa723fc0e0b4479496acdae1c1f.spotifycdn.com',
            'canvas.scdn.co',
            'canvaz.scdn.co'
        ]

        return any(domain in url for domain in spotify_video_domains)

    def get_content_type(self, response: Dict) -> str:
        """Extract content type from response headers"""
        headers = response.get('headers', [])
        for header in headers:
            if header.get('name', '').lower() == 'content-type':
                return header.get('value', '')
        return ''

    def extract_api_image_references(self, entry: Dict, url: str):
        """Extract image references from API responses"""
        try:
            response = entry.get('response', {})
            content = response.get('content', {})

            if content.get('text'):
                text = content['text']

                if content.get('encoding') == 'base64':
                    try:
                        text = base64.b64decode(text).decode('utf-8')
                    except:
                        return

                try:
                    json_data = json.loads(text)
                    self.find_images_in_json(json_data, url)
                except:

                    self.find_image_patterns_in_text(text, url)

        except Exception as e:
            print(f"⚠️  Error extracting API references from {url}: {e}")

    def find_images_in_json(self, data: Any, source_url: str):
        """Recursively find image URLs in JSON data"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key in ['image', 'images', 'cover_art', 'avatar', 'picture', 'artwork']:
                    if isinstance(value, str) and self.is_spotify_image_url(value):
                        self.found_urls.add(value)
                        print(f"🔗 Found image reference in API: {value}")
                elif isinstance(value, (dict, list)):
                    self.find_images_in_json(value, source_url)
        elif isinstance(data, list):
            for item in data:
                self.find_images_in_json(item, source_url)

    def find_image_patterns_in_text(self, text: str, source_url: str):
        """Find image URL patterns in text"""

        patterns = [
            r'ab67616[a-f0-9]{32}',  
            r'ab6761610000[a-f0-9]{24}',  
            r'ab67616d[a-f0-9]{32}',  
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:

                image_urls = [
                    f"https://i.scdn.co/image/{match}",
                    f"https://mosaic.scdn.co/640/{match}",
                    f"https://mosaic.scdn.co/300/{match}"
                ]

                for img_url in image_urls:
                    self.found_urls.add(img_url)
                    print(f"🔗 Found image pattern: {img_url}")

    def download_media(self, media_info: Dict) -> Optional[str]:
        """Download media file from URL or use embedded data"""
        url = media_info['url']

        if 'decoded_data' in media_info:
            return self.save_embedded_media(media_info)

        try:
            print(f"📥 Downloading: {url}")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.178 Safari/537.36',
                'Referer': 'https://open.spotify.com/',
                'Accept': '*/*'
            }

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200 and len(response.content) > 100:

                content_type = response.headers.get('content-type', '').lower()
                ext = self.get_file_extension(content_type, response.content)

                filename = self.generate_filename(url, ext)

                if 'video' in content_type or ext in ['.webm', '.mp4'] or 'video-akpcw.spotifycdn.com' in url:
                    filepath = os.path.join(self.videos_folder, filename)

                    if 'webm' in url.lower() or ext == '.webm':

                        media_info['is_video_segment'] = True
                        media_info['segment_data'] = response.content

                        if 'inits' in url:
                            media_info['segment_type'] = 'init'
                        elif '/0.webm' in url or '/1.webm' in url or '/2.webm' in url:
                            media_info['segment_type'] = 'media'
                        else:
                            media_info['segment_type'] = 'unknown'

                        print(f"🎬 Video segment detected: {media_info['segment_type']}")
                else:
                    filepath = os.path.join(self.images_folder, filename)

                with open(filepath, 'wb') as f:
                    f.write(response.content)

                print(f"✅ Downloaded: {filepath} ({len(response.content)} bytes)")
                return filepath
            else:
                print(f"❌ Download failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Download error for {url}: {e}")

        return None

    def save_embedded_media(self, media_info: Dict) -> Optional[str]:
        """Save embedded media data from HAR"""
        try:
            data = media_info['decoded_data']
            url = media_info['url']
            content_type = media_info.get('content_type', '')

            ext = self.get_file_extension(content_type, data)

            filename = self.generate_filename(url, ext)

            if 'video' in content_type or ext in ['.webm', '.mp4']:
                filepath = os.path.join(self.videos_folder, filename)
            else:
                filepath = os.path.join(self.images_folder, filename)

            with open(filepath, 'wb') as f:
                f.write(data)

            print(f"✅ Saved embedded media: {filepath} ({len(data)} bytes)")
            return filepath

        except Exception as e:
            print(f"❌ Error saving embedded media: {e}")
            return None

    def get_file_extension(self, content_type: str, data: bytes) -> str:
        """Determine file extension from content type or data"""

        if 'jpeg' in content_type or 'jpg' in content_type:
            return '.jpg'
        elif 'png' in content_type:
            return '.png'
        elif 'gif' in content_type:
            return '.gif'
        elif 'webp' in content_type:
            return '.webp'
        elif 'webm' in content_type:
            return '.webm'
        elif 'mp4' in content_type:
            return '.mp4'

        if data.startswith(b'\xFF\xD8\xFF'):
            return '.jpg'
        elif data.startswith(b'\x89PNG'):
            return '.png'
        elif data.startswith(b'GIF8'):
            return '.gif'
        elif data.startswith(b'RIFF') and b'WEBP' in data[:20]:
            return '.webp'
        elif data.startswith(b'\x1a\x45\xdf\xa3'):  
            return '.webm'
        elif data.startswith(b'\x00\x00\x00') and b'ftyp' in data[:20]:
            return '.mp4'

        return '.bin'  

    def generate_filename(self, url: str, ext: str) -> str:
        """Generate a safe filename from URL"""

        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')

        if path_parts and path_parts[-1]:
            base_name = path_parts[-1]

            if '.' in base_name:
                base_name = base_name.rsplit('.', 1)[0]
        else:
            base_name = f"spotify_media_{int(time.time())}"

        safe_name = re.sub(r'[^\w\-_.]', '_', base_name)
        return f"{safe_name}{ext}"

    def save_analysis_report(self, har_data: Dict, extracted_media: List[Dict]) -> str:
        """Save detailed analysis report"""
        report_file = os.path.join(self.data_folder, f"har_analysis_{int(time.time())}.json")

        clean_media = []
        for media in extracted_media:
            clean_item = {}
            for key, value in media.items():
                if key in ['segment_data', 'decoded_data']:

                    clean_item[f"{key}_size"] = len(value) if value else 0
                elif isinstance(value, bytes):
                    clean_item[f"{key}_size"] = len(value)
                else:
                    clean_item[key] = value
            clean_media.append(clean_item)

        analysis = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'har_info': {
                'version': har_data.get('log', {}).get('version', ''),
                'creator': har_data.get('log', {}).get('creator', {}),
                'total_entries': len(har_data.get('log', {}).get('entries', []))
            },
            'extraction_summary': {
                'total_media_found': len(extracted_media),
                'images': len([m for m in extracted_media if 'image' in m.get('content_type', '')]),
                'videos': len([m for m in extracted_media if 'video' in m.get('content_type', '')]),
                'unique_urls': len(self.found_urls)
            },
            'extracted_media': clean_media,
            'found_urls': list(self.found_urls)
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        print(f"📊 Analysis report saved: {report_file}")
        return report_file

    def process_har_file(self, har_path: str) -> Dict:
        """Process a HAR file and extract all Spotify content"""
        print(f"🎵 Processing HAR file: {har_path}")

        har_data = self.load_har_file(har_path)
        if not har_data:
            return {'success': False, 'error': 'Failed to load HAR file'}

        return self.process_har_data(har_data)

    def combine_webm_segments(self, extracted_media: List[Dict]) -> List[str]:
        """Combine WebM segments into playable videos"""
        combined_videos = []

        segment_groups = {}

        for media_info in extracted_media:
            if media_info.get('is_video_segment') and 'video-akpcw.spotifycdn.com' in media_info['url']:
                url = media_info['url']

                import re
                source_match = re.search(r'sources/([a-f0-9]+)/', url)
                profile_match = re.search(r'profiles/(\d+)/', url)

                if source_match and profile_match:
                    source_id = source_match.group(1)
                    profile_id = profile_match.group(1)
                    group_key = f"{source_id}_profile_{profile_id}"

                    if group_key not in segment_groups:
                        segment_groups[group_key] = {'init': None, 'segments': []}

                    if media_info.get('segment_type') == 'init':
                        segment_groups[group_key]['init'] = media_info
                    else:
                        segment_groups[group_key]['segments'].append(media_info)

        print(f"🎬 Found {len(segment_groups)} video segment groups")

        for group_key, group_data in segment_groups.items():
            try:
                print(f"🔧 Combining segments for {group_key}...")

                init_segment = group_data['init']
                media_segments = sorted(group_data['segments'], 
                                      key=lambda x: self.extract_segment_number(x['url']))

                if init_segment and media_segments:

                    combined_data = init_segment['segment_data']

                    for segment in media_segments:
                        combined_data += segment['segment_data']

                    output_filename = f"spotify_canvas_{group_key}.webm"
                    output_path = os.path.join(self.videos_folder, output_filename)

                    with open(output_path, 'wb') as f:
                        f.write(combined_data)

                    print(f"✅ Combined video saved: {output_path} ({len(combined_data)} bytes)")
                    combined_videos.append(output_path)

                    mp4_path = self.convert_to_mp4(output_path)
                    if mp4_path:
                        combined_videos.append(mp4_path)

            except Exception as e:
                print(f"❌ Error combining segments for {group_key}: {e}")

        return combined_videos

    def extract_segment_number(self, url: str) -> int:
        """Extract segment number from URL for proper ordering"""
        import re
        match = re.search(r'/(\d+)\.webm', url)
        return int(match.group(1)) if match else 0

    def convert_to_mp4(self, webm_path: str) -> Optional[str]:
        """Convert WebM to MP4 using ffmpeg if available"""
        try:
            import subprocess

            mp4_path = webm_path.replace('.webm', '.mp4')

            result = subprocess.run([
                'ffmpeg', '-i', webm_path, '-c:v', 'libx264', '-c:a', 'aac', 
                '-movflags', '+faststart', mp4_path, '-y'
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0 and os.path.exists(mp4_path):
                print(f"✅ Converted to MP4: {mp4_path}")
                return mp4_path
            else:
                print(f"⚠️  FFmpeg conversion failed: {result.stderr}")

        except FileNotFoundError:
            print("⚠️  FFmpeg not found - install it to convert WebM to MP4")
        except Exception as e:
            print(f"⚠️  Conversion error: {e}")

        return None

    def process_har_data(self, har_data: Dict) -> Dict:
        """Process HAR data and extract all Spotify content"""
        print("🔍 Analyzing HAR data for Spotify content...")

        extracted_media = self.extract_spotify_images(har_data)

        downloaded_files = []
        for media_info in extracted_media:
            filepath = self.download_media(media_info)
            if filepath:
                downloaded_files.append(filepath)

        combined_videos = self.combine_webm_segments(extracted_media)
        downloaded_files.extend(combined_videos)

        for url in self.found_urls:
            if url not in [m['url'] for m in extracted_media]:
                try:
                    media_info = {'url': url, 'content_type': 'image/jpeg'}
                    filepath = self.download_media(media_info)
                    if filepath:
                        downloaded_files.append(filepath)
                except Exception as e:
                    print(f"⚠️  Error downloading {url}: {e}")

        report_file = self.save_analysis_report(har_data, extracted_media)

        results = {
            'success': True,
            'total_media_found': len(extracted_media),
            'downloaded_files': downloaded_files,
            'combined_videos': len(combined_videos),
            'report_file': report_file,
            'output_folder': self.output_folder
        }

        return results

def main():
    print("🎵📊 SPOTIFY HAR EXTRACTOR 📊🎵")
    print("=" * 60)
    print("Extract Spotify content from HAR (HTTP Archive) files")

    extractor = SpotifyHARExtractor()

    if len(sys.argv) > 1:
        har_file = sys.argv[1]
        if os.path.exists(har_file):
            results = extractor.process_har_file(har_file)
        else:
            print(f"❌ HAR file not found: {har_file}")
            return
    else:

        print("\n📁 HAR FILE INPUT:")
        print("1. Drag and drop a .har file here")
        print("2. Or enter the full path to a .har file")
        print("3. Or paste HAR JSON data directly")

        user_input = input("\n🎯 Enter HAR file path or paste JSON: ").strip()

        if not user_input:
            print("❌ No input provided")
            return

        if os.path.exists(user_input):
            results = extractor.process_har_file(user_input)
        elif user_input.startswith('{') and user_input.endswith('}'):

            har_data = extractor.load_har_from_json_string(user_input)
            if har_data:
                results = extractor.process_har_data(har_data)
            else:
                print("❌ Invalid JSON data")
                return
        else:
            print("❌ Invalid input - not a valid file path or JSON")
            return

    if results['success']:
        print(f"\n🎉 EXTRACTION COMPLETE!")
        print("=" * 60)
        print(f"📊 Total media found: {results['total_media_found']}")
        print(f"📥 Files downloaded: {len(results['downloaded_files'])}")
        print(f"📁 Output folder: {results['output_folder']}")
        print(f"📊 Analysis report: {results['report_file']}")

        if results['downloaded_files']:
            print(f"\n📋 Downloaded files:")
            for filepath in results['downloaded_files']:
                print(f"  ✅ {filepath}")

        print(f"\n💡 Check the '{results['output_folder']}' folder for all extracted content!")
    else:
        print(f"❌ Extraction failed: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()