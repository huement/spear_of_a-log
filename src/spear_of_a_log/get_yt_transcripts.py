import argparse
import re
import sys
from pathlib import Path
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(input_str: str) -> Optional[str]:
    """Extracts YouTube 11-character video ID from raw ID or full URL."""
    input_str = input_str.strip()
    if re.match(r"^[0-9A-Za-z_-]{11}$", input_str):
        return input_str

    match = re.search(r"(?:v=|\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})", input_str)
    return match.group(1) if match else None


def fetch_full_transcript(video_id: str, out_path: Path) -> bool:
    """Fetches full transcript for a video ID and saves it with timecodes."""
    try:
        api = YouTubeTranscriptApi()

        if hasattr(api, "fetch"):
            fetched = api.fetch(video_id)
            if hasattr(fetched, "to_raw_data"):
                transcript_list = fetched.to_raw_data()
            else:
                transcript_list = [
                    {
                        "text": getattr(item, "text", item.get("text") if isinstance(item, dict) else ""),
                        "start": getattr(item, "start", item.get("start") if isinstance(item, dict) else 0),
                        "duration": getattr(item, "duration", item.get("duration") if isinstance(item, dict) else 0),
                    }
                    for item in fetched
                ]
        elif hasattr(api, "get_transcript"):
            transcript_list = api.get_transcript(video_id)
        else:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

    except Exception as e:
        print(f"  ❌ Error fetching transcript for {video_id}: {e}")
        return False

    if not transcript_list:
        print(f"  ❌ No transcript entries returned for {video_id}")
        return False

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            for entry in transcript_list:
                t = int(entry["start"])
                m, s = divmod(t, 60)
                h, m = divmod(m, 60)
                timecode = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
                f.write(f"[{timecode}] {entry['text']}\n")
        print(f"  ✔ Saved: {out_path}")
        return True
    except Exception as e:
        print(f"  ❌ Failed writing file {out_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fetch full YouTube transcripts for multiple video IDs or URLs."
    )
    parser.add_argument(
        "--list",
        "-l",
        required=True,
        help="Comma-separated list of YouTube video IDs or URLs (e.g. ID_1,ID_2,https://youtube.com/watch?v=ID_3)",
    )
    parser.add_argument(
        "--output_dir",
        "--output-dir",
        "-o",
        default="transcripts",
        help="Directory to save transcript text files (default: 'transcripts')",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_items = [item.strip() for item in args.list.split(",") if item.strip()]

    if not raw_items:
        print("Error: No valid video IDs or URLs provided.")
        sys.exit(1)

    print(f"Processing {len(raw_items)} item(s) -> Output directory: '{output_dir}'")

    success_count = 0
    for raw_item in raw_items:
        video_id = extract_video_id(raw_item)
        if not video_id:
            print(f"  ❌ Invalid Video ID/URL skipped: '{raw_item}'")
            continue

        out_path = output_dir / f"{video_id}_transcript.txt"
        if fetch_full_transcript(video_id, out_path):
            success_count += 1

    print(f"\nCompleted: {success_count}/{len(raw_items)} transcript(s) saved successfully.")


if __name__ == "__main__":
    main()