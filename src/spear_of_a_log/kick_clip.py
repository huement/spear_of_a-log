import sys
import subprocess
import json
import re
from curl_cffi import requests

def get_kick_m3u8(video_url):
    parts = video_url.rstrip('/').split('/')
    video_id = parts[-1]

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    # 1. Query Direct Kick Video Endpoint
    try:
        api_url = f"https://kick.com/api/v1/video/{video_id}"
        response = requests.get(api_url, impersonate="chrome", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "source" in data and data["source"]:
                return data["source"]
            if "video" in data and "source" in data["video"]:
                return data["video"]["source"]
    except Exception:
        pass

    # 2. Fallback: Parse Direct Page HTML
    try:
        response = requests.get(video_url, impersonate="chrome", headers=headers, timeout=10)
        if response.status_code == 200:
            # Check for direct m3u8 URL pattern
            m3u8_match = re.search(r'https://[^\s"\']*?master\.m3u8[^\s"\']*', response.text)
            if m3u8_match:
                return m3u8_match.group(0).replace('\\/', '/')

            # Parse NEXT_DATA JSON blob
            next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', response.text)
            if next_data_match:
                next_data = json.loads(next_data_match.group(1))
                def find_source(obj):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if k == 'source' and isinstance(v, str) and '.m3u8' in v:
                                return v
                            res = find_source(v)
                            if res: return res
                    elif isinstance(obj, list):
                        for item in obj:
                            res = find_source(item)
                            if res: return res
                    return None
                
                src = find_source(next_data)
                if src:
                    return src
    except Exception:
        pass

    raise Exception(f"Could not retrieve .m3u8 stream source for video ID: {video_id}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 kick_clip.py <kick_url> <start_time> <end_time> [output_file]")
        sys.exit(1)

    url = sys.argv[1]
    start = sys.argv[2]
    end = sys.argv[3]
    out = sys.argv[4] if len(sys.argv) > 4 else "clip.mp4"

    print("[1/2] Fetching direct .m3u8 manifest from Kick...")
    m3u8_url = get_kick_m3u8(url)
    print(f"Found stream: {m3u8_url}")

    print("[2/2] Downloading segment using yt-dlp...")
    cmd = [
        "yt-dlp",
        "--download-sections", f"*{start}-{end}",
        m3u8_url,
        "-o", out
    ]
    subprocess.run(cmd)
