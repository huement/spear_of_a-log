import os
import re
from pathlib import Path
from typing import Optional, Tuple
from youtube_transcript_api import YouTubeTranscriptApi
from textual.containers import Horizontal
from textual.widgets import Checkbox, Input, Label, Select, TabPane


def extract_video_id(url: str) -> Optional[str]:
    """Extracts YouTube 11-character video ID from various URL formats."""
    match = re.search(r"(?:v=|\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None


def download_and_filter_transcript(
    video_id: str,
    out_path: Path,
    start_sec: Optional[float] = None,
    end_sec: Optional[float] = None,
    buffer_sec: float = 2.0,
) -> Tuple[bool, str]:
    """
    Downloads transcript for video_id. If start_sec and end_sec are provided,
    trims the transcript with a safety buffer applied to both ends.
    """
    try:
        api = YouTubeTranscriptApi()
        
        # New API method in youtube-transcript-api v1.0+
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
        # Legacy fallback
        elif hasattr(api, "get_transcript"):
            transcript_list = api.get_transcript(video_id)
        else:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

    except Exception as e:
        return False, f"Failed to retrieve transcript: {str(e)}"

    if start_sec is not None and end_sec is not None and end_sec > start_sec:
        padded_start = max(0.0, start_sec - buffer_sec)
        padded_end = end_sec + buffer_sec
        filtered = [
            entry
            for entry in transcript_list
            if (entry["start"] + entry["duration"]) >= padded_start
            and entry["start"] <= padded_end
        ]
    else:
        filtered = transcript_list

    if not filtered:
        return False, "No transcript entries found for the specified range."

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            for entry in filtered:
                t = int(entry["start"])
                m, s = divmod(t, 60)
                h, m = divmod(m, 60)
                timecode = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
                f.write(f"[{timecode}] {entry['text']}\n")
        return True, f"Saved transcript ({len(filtered)} entries) -> {out_path.name}"
    except Exception as e:
        return False, f"Failed to write transcript file: {str(e)}"


def compose_youtube_tab(last_yt_url: str = "") -> TabPane:
    """Generates the YouTube UI Tab Pane."""
    return TabPane(
        "YOUTUBE",
        Label("YouTube Video URL:", classes="field-label"),
        Input(
            value=last_yt_url,
            placeholder="https://www.youtube.com/watch?v=...",
            id="yt-url-input",
        ),
        Horizontal(
            Label("Recode Video:", classes="col-label"),
            Checkbox(value=True, id="yt-recode-chk", classes="col-widget"),
            Select(
                options=[("MP4", "mp4")],
                value="mp4",
                id="yt-recode-fmt",
                classes="col-widget",
                allow_blank=False,
            ),
            classes="row-3col",
        ),
        Horizontal(
            Label("Max Resolution:", classes="col-label"),
            Select(
                options=[
                    ("1080p", "1080"),
                    ("720p", "720"),
                    ("480p", "480"),
                    ("Best Available", "max"),
                ],
                value="720",
                id="yt-res-select",
                classes="col-widget",
                allow_blank=False,
            ),
            classes="row-3col",
        ),
        # New row with Include and No Video options
        Horizontal(
            Label("Transcript?:", classes="col-label"),
            Checkbox("Include", value=False, id="yt-transcript-inc", classes="col-widget"),
            Checkbox("No Video", value=False, id="yt-transcript-novideo", classes="col-widget"),
            classes="row-3col",
        ),
        Label("Start Time (HH : MM : SS) - [Leave blank for FULL video]:", classes="field-label"),
        Horizontal(
            Input(value="", placeholder="HH", id="yt-start-h", classes="time-input", max_length=2),
            Input(value="", placeholder="MM", id="yt-start-m", classes="time-input", max_length=2),
            Input(value="", placeholder="SS", id="yt-start-s", classes="time-input", max_length=2),
            classes="time-container",
        ),
        Label("End Time (HH : MM : SS) - [Leave blank for FULL video]:", classes="field-label"),
        Horizontal(
            Input(value="", placeholder="HH", id="yt-end-h", classes="time-input", max_length=2),
            Input(value="", placeholder="MM", id="yt-end-m", classes="time-input", max_length=2),
            Input(value="", placeholder="SS", id="yt-end-s", classes="time-input", max_length=2),
            classes="time-container",
        ),
        Label("Output Filename (text only):", classes="field-label"),
        Input(value="yt_clip", placeholder="e.g. yt_clip", id="yt-out-input"),
        id="tab-youtube",
    )