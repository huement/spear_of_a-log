import asyncio
import json
import os
import re
import shutil
from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    Checkbox,
    ContentSwitcher,
    Input,
    Label,
    ProgressBar,
    RichLog,
    Select,
    TabbedContent,
)
from spear_of_a_log.kick import compose_kick_tab
from spear_of_a_log.youtube import (
    compose_youtube_tab,
    download_and_filter_transcript,
    extract_video_id,
)

# Navigates up from src/spear_of_a_log/app.py to the repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_FILE = REPO_ROOT / "kick_downloader_cache.json"

BANNER = """┏■◤◢◤◢◤◢◤◢◤◢■┳■■■■■■■■■■■■■■■■■■■■■■┳■◣◥◣◥◣◥◣◥◣◥■┓
┃▉▀▀▔▔▔▔▔▔▔▔▔┻▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔┻▔▔▔▔▔▔▔▔▔▀▀▉┃
┃▉                Šᖘ∃∆Ꞧ öƒ Å-Ⱡøg                ▉┃
┃▉▄▄▁▁▁▁▁▁▁▁▁┳▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁┳▁▁▁▁▁▁▁▁▁▄▄▉┃
┗■◣◥◣◥◣◥◣◥◣◥■┻■■■■■■■■■▶ ▽0.1.0 ◀■■■┻■◤◢◤◢◤◢◤◢◤◢■┛
"""


class ALogMachineApp(App):
    CSS = """
    Screen {
        align: center middle;
        background: $surface;
    }

    #main-box {
        width: 92;
        height: 52;
        border: heavy #00ff66;
        padding: 1 2;
        background: $surface-darken-1;
    }

    #banner {
        text-align: center;
        color: #00ff66;
        height: 6;
        content-align: center middle;
        margin-bottom: 0;
        width: 100%;
    }

    TabbedContent {
        margin-top: 0;
    }

    Tabs {
        background: $surface-darken-2;
        border-bottom: solid #00ff66;
    }

    Tab {
        color: $text-muted;
    }

    Tab.-active {
        color: #00ff66;
        text-style: bold;
    }

    .log-box {
        height: 8;
        border: solid #00ff66;
        background: black;
        margin-bottom: 1;
    }

    .field-label {
        margin-top: 1;
        text-style: bold;
        color: #00ff66;
    }

    .time-container {
        height: 3;
        margin-bottom: 1;
    }

    .time-input {
        width: 1fr;
        margin-right: 1;
    }

    .row-3col {
        height: 3;
        align: left middle;
        margin-top: 1;
    }

    .col-label {
        width: 18;
        text-style: bold;
        color: #00ff66;
        content-align: left middle;
    }

    .col-widget {
        width: 1fr;
        margin-right: 1;
    }

    .button-row {
        margin-top: 1;
        height: 3;
        width: 100%;
        align: center middle;
    }

    .button-row Button {
        width: 100%;
        margin-right: 0;
    }

    #btn-start-yt {
        display: none;
    }

    #progress-container {
        margin-top: 1;
    }

    .stat-label {
        margin-top: 1;
        color: $text;
    }

    ProgressBar .bar--complete {
        color: #00ff66;
    }
    """

    BINDINGS = [Binding("ctrl+c", "quit", "Quit", show=True)]

    def __init__(self):
        super().__init__()
        self.download_process = None
        self.cache = self.load_cache()

    def load_cache(self) -> dict:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_cache(self) -> None:
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(self.cache, f, indent=4)
        except Exception:
            pass

    def on_tabbed_content_tab_activated(
            self, event: TabbedContent.TabActivated) -> None:
        active_pane_id = event.tabbed_content.active
        btn_kick = self.query_one("#btn-start-kick", Button)
        btn_yt = self.query_one("#btn-start-yt", Button)

        if active_pane_id == "tab-kick":
            btn_kick.display = True
            btn_yt.display = False
        elif active_pane_id == "tab-youtube":
            btn_kick.display = False
            btn_yt.display = True

    def compose(self) -> ComposeResult:
        last_kick_url = self.cache.get("last_kick_url", "")
        last_yt_url = self.cache.get("last_yt_url", "")

        with Container(id="main-box"):
            yield Label(BANNER, id="banner")

            with ContentSwitcher(initial="step1"):
                # STEP 1: Dependencies
                with Vertical(id="step1", classes="step-container"):
                    yield Label("System Verification Status:",
                                classes="field-label")
                    yield RichLog(id="log-step1",
                                  classes="log-box",
                                  markup=True)

                # STEP 2: Main Tabs
                with Vertical(id="step2", classes="step-container"):
                    with TabbedContent(id="main-tabs"):
                        yield compose_kick_tab(last_kick_url)
                        yield compose_youtube_tab(last_yt_url)

                    with Horizontal(classes="button-row"):
                        yield Button(
                            "Start Kick Download",
                            id="btn-start-kick",
                            variant="primary",
                        )
                        yield Button(
                            "Start YouTube Download",
                            id="btn-start-yt",
                            variant="primary",
                        )

                # STEP 3: Progress Tracker
                with Vertical(id="step3", classes="step-container"):
                    yield RichLog(id="log-step3",
                                  classes="log-box",
                                  markup=True)
                    with Vertical(id="progress-container"):
                        yield ProgressBar(id="pbar",
                                          total=100,
                                          show_percentage=True)
                        yield Label("Progress: Initializing...",
                                    id="lbl-status",
                                    classes="stat-label")
                        yield Label("Speed / ETA: --",
                                    id="lbl-eta",
                                    classes="stat-label")

                    with Horizontal(classes="button-row"):
                        yield Button("Cancel",
                                     id="btn-cancel",
                                     variant="error")
                        yield Button("Finish",
                                     id="btn-finish",
                                     variant="success",
                                     disabled=True)

    async def on_mount(self) -> None:
        if self.cache.get("verified", False):
            self.query_one(ContentSwitcher).current = "step2"
        else:
            self.run_worker(self.verify_dependencies())

    async def verify_dependencies(self) -> None:
        log = self.query_one("#log-step1", RichLog)
        await asyncio.sleep(0.5)

        node_path = shutil.which("node")
        ytdlp_path = shutil.which("yt-dlp")
        script_file = Path(__file__).parent / "get_m3u8.js"
        script_path = str(
            script_file.resolve()) if script_file.exists() else None

        errors = False

        if node_path:
            log.write("[bold green]✔[/bold green] Node.js found")
        else:
            log.write("[bold red]✘[/bold red] Node.js missing from PATH")
            errors = True

        if script_path:
            log.write(
                "[bold green]✔[/bold green] Node script 'get_m3u8.js' found")
        else:
            log.write(
                "[bold red]✘[/bold red] 'get_m3u8.js' missing in current directory"
            )
            errors = True

        if ytdlp_path:
            log.write("[bold green]✔[/bold green] yt-dlp found")
        else:
            log.write("[bold red]✘[/bold red] yt-dlp missing from PATH")
            errors = True

        if not errors:
            self.cache["verified"] = True
            self.cache["paths"] = {
                "node": node_path,
                "yt-dlp": ytdlp_path,
                "script": script_path
            }
            self.save_cache()
            log.write(
                "\n[bold green]All dependencies verified! Proceeding...[/bold green]"
            )
            await asyncio.sleep(1.5)
            self.query_one(ContentSwitcher).current = "step2"
        else:
            log.write(
                "\n[bold red]Please resolve missing requirements above.[/bold red]"
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id in ("btn-start-kick", "btn-start-yt"):
            await self.start_download_process(
                source_tab="kick" if button_id == "btn-start-kick" else "yt")
        elif button_id == "btn-cancel":
            if self.download_process:
                self.download_process.terminate()
            self.query_one(
                "#lbl-status",
                Label).update("[bold red]Cancelled by user.[/bold red]")
            self.query_one("#btn-cancel", Button).disabled = True
            self.query_one("#btn-finish", Button).disabled = False
        elif button_id == "btn-finish":
            self.query_one("#pbar", ProgressBar).progress = 0
            self.query_one("#lbl-status",
                           Label).update("Progress: Initializing...")
            self.query_one("#lbl-eta", Label).update("Speed / ETA: --")
            self.query_one("#btn-cancel", Button).disabled = False
            self.query_one("#btn-finish", Button).disabled = True
            self.query_one(ContentSwitcher).current = "step2"

    async def start_download_process(self, source_tab: str) -> None:
        ytdlp_cmd = self.cache.get("paths", {}).get("yt-dlp", "yt-dlp")
        node_cmd = self.cache.get("paths", {}).get("node", "node")
        cmd = [ytdlp_cmd, "--newline"]

        is_full_video = False
        start_sec, end_sec = None, None

        if source_tab == "kick":
            raw_url = self.query_one("#kick-url-input", Input).value.strip()
            if raw_url:
                self.cache["last_kick_url"] = raw_url
                self.save_cache()

            url = f"https://kick.com/{raw_url.lstrip('/')}" if not raw_url.startswith(
                "http") else raw_url
            sh = self.query_one("#kick-start-h", Input).value.strip().zfill(2)
            sm = self.query_one("#kick-start-m", Input).value.strip().zfill(2)
            ss = self.query_one("#kick-start-s", Input).value.strip().zfill(2)
            eh = self.query_one("#kick-end-h", Input).value.strip().zfill(2)
            em = self.query_one("#kick-end-m", Input).value.strip().zfill(2)
            es = self.query_one("#kick-end-s", Input).value.strip().zfill(2)

            base_out = self.query_one("#kick-out-input",
                                      Input).value.strip() or "kick_clip"
            out_file = f"{base_out}_{sh}_{sm}_{ss}__{eh}_{em}_{es}.mp4"
            start_sec = int(sh) * 3600 + int(sm) * 60 + int(ss)
            end_sec = int(eh) * 3600 + int(em) * 60 + int(es)

        else:  # YOUTUBE
            url = self.query_one("#yt-url-input", Input).value.strip()
            if url:
                self.cache["last_yt_url"] = url
                self.save_cache()

            do_recode = self.query_one("#yt-recode-chk", Checkbox).value
            recode_fmt = self.query_one("#yt-recode-fmt", Select).value
            if do_recode and recode_fmt:
                cmd.extend(["--recode-video", str(recode_fmt)])

            res_val = self.query_one("#yt-res-select", Select).value
            if res_val and res_val != "max":
                cmd.extend(
                    ["-f", f"bv*[height<={res_val}]+ba/b[height<={res_val}]"])

            sh = self.query_one("#yt-start-h", Input).value.strip()
            sm = self.query_one("#yt-start-m", Input).value.strip()
            ss = self.query_one("#yt-start-s", Input).value.strip()
            eh = self.query_one("#yt-end-h", Input).value.strip()
            em = self.query_one("#yt-end-m", Input).value.strip()
            es = self.query_one("#yt-end-s", Input).value.strip()

            base_out = self.query_one("#yt-out-input",
                                      Input).value.strip() or "yt_clip"

            # Check if timestamps were provided
            if not any([sh, sm, ss, eh, em, es]):
                is_full_video = True
                out_file = f"{base_out}_full.mp4"
            else:
                sh_f, sm_f, ss_f = sh.zfill(2), sm.zfill(2), ss.zfill(2)
                eh_f, em_f, es_f = eh.zfill(2), em.zfill(2), es.zfill(2)
                out_file = f"{base_out}_{sh_f}_{sm_f}_{ss_f}__{eh_f}_{em_f}_{es_f}.mp4"
                start_sec = (int(sh or 0) * 3600) + (int(sm or 0) * 60) + int(
                    ss or 0)
                end_sec = (int(eh or 0) * 3600) + (int(em or 0) * 60) + int(
                    es or 0)

        clip_duration = max(
            1.0, float((end_sec or 0) -
                       (start_sec or 0))) if not is_full_video else 100.0

        # Switch to step 3 layout
        self.query_one(ContentSwitcher).current = "step2"
        self.query_one(ContentSwitcher).current = "step3"
        log = self.query_one("#log-step3", RichLog)
        log.clear()

        # Handle YouTube Transcript Downloading
        # Handle YouTube Transcript Downloading
        if source_tab == "yt":
            inc_transcript = self.query_one("#yt-transcript-inc",
                                            Checkbox).value
            no_video = self.query_one("#yt-transcript-novideo", Checkbox).value

            if inc_transcript or no_video:
                v_id = extract_video_id(url)
                if v_id:
                    txt_out = Path(out_file).with_suffix(
                        "").name + "_transcript.txt"
                    log.write(
                        f"[bold yellow]Fetching YouTube transcript for {v_id}...[/bold yellow]"
                    )
                    success, msg = download_and_filter_transcript(
                        v_id,
                        Path(txt_out),
                        start_sec,
                        end_sec,
                        buffer_sec=2.0)
                    log.write(f"[bold green]✔[/bold green] {msg}"
                              if success else f"[bold red]✘ {msg}[/bold red]")
                else:
                    log.write(
                        "[bold red]✘ Could not parse Video ID for transcript.[/bold red]"
                    )

            # Early exit if "No Video" is checked
            if no_video:
                pbar = self.query_one("#pbar", ProgressBar)
                lbl_status = self.query_one("#lbl-status", Label)
                lbl_eta = self.query_one("#lbl-eta", Label)

                pbar.progress = 100
                log.write(
                    "\n[bold green]✔ Transcript task completed (Video download skipped).[/bold green]"
                )
                lbl_status.update(
                    "[bold green]Transcript saved successfully![/bold green]")
                lbl_eta.update("Speed / ETA: N/A")

                self.query_one("#btn-cancel", Button).disabled = True
                self.query_one("#btn-finish", Button).disabled = False
                return

        # Prepare Stream Target
        if source_tab == "kick":
            log.write(
                "[bold green][1/2] Fetching Kick manifest via Puppeteer...[/bold green]"
            )
            proc = await asyncio.create_subprocess_exec(
                node_cmd,
                "get_m3u8.js",
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stdout, _ = await proc.communicate()
            if proc.returncode != 0 or not stdout.decode().strip():
                log.write(
                    "[bold red]Failed to retrieve Kick manifest.[/bold red]")
                self.query_one("#btn-cancel", Button).disabled = True
                self.query_one("#btn-finish", Button).disabled = False
                return
            target_stream = stdout.decode().strip()
        else:
            target_stream = url

        # Construct download section commands
        if not is_full_video and start_sec is not None and end_sec is not None:
            # Replace sh_str / eh_str formatting with fallback defaults
            sh_int, sm_int, ss_int = int(sh or 0), int(sm or 0), int(ss or 0)
            eh_int, em_int, es_int = int(eh or 0), int(em or 0), int(es or 0)
            sh_str = f"{sh_int:02d}:{sm_int:02d}:{ss_int:02d}"
            eh_str = f"{eh_int:02d}:{em_int:02d}:{es_int:02d}"
            cmd.extend(["--download-sections", f"*{sh_str}-{eh_str}"])
            log.write(
                f"[bold green]Downloading segment {sh_str} to {eh_str}...[/bold green]"
            )
        else:
            log.write("[bold green]Downloading FULL video...[/bold green]")

        cmd.extend([
            "--progress-template",
            "download:%(progress._percent_str)s|%(progress._speed_str)s|%(progress._eta_str)s|%(progress._total_bytes_estimate_str)s",
            target_stream,
            "-o",
            out_file,
        ])

        self.download_process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT)

        pbar = self.query_one("#pbar", ProgressBar)
        lbl_status = self.query_one("#lbl-status", Label)
        lbl_eta = self.query_one("#lbl-eta", Label)

        buffer = ""
        while True:
            chunk = await self.download_process.stdout.read(256)
            if not chunk:
                break

            buffer += chunk.decode(errors="ignore")
            lines = re.split(r"[\r\n]+", buffer)
            buffer = lines.pop()

            for line in lines:
                line = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", line).strip()
                if not line:
                    continue

                # 1. Handle native yt-dlp progress lines
                if line.startswith("download:"):
                    parts = line.replace("download:", "").split("|")
                    if len(parts) >= 4:
                        pct_str, speed, eta, size = [
                            p.strip() for p in parts[:4]
                        ]
                        clean_pct = pct_str.replace("%", "").strip()

                        if clean_pct not in ("NA", "N/A", "Unknown", ""):
                            try:
                                pbar.progress = float(clean_pct)
                            except ValueError:
                                pass

                        lbl_status.update(
                            f"Step: [bold green]Downloading Stream[/bold green] ({pct_str} of ~{size})"
                        )
                        lbl_eta.update(
                            f"Speed: [bold green]{speed}[/bold green] | ETA: [bold yellow]{eta}[/bold yellow]"
                        )

                # 2. Handle ffmpeg conversion & clipping progress lines
                elif "time=" in line and "fps=" in line:
                    time_match = re.search(
                        r"time=\s*(-?\d+):(\d+):(\d+(?:\.\d+)?)", line)
                    size_match = re.search(r"size=\s*(\S+)", line)
                    speed_match = re.search(r"speed=\s*(\S+)", line)

                    if time_match:
                        h, m, s = map(float, time_match.groups())
                        curr_sec = max(0.0, h * 3600 + m * 60 + s)

                        if not is_full_video and clip_duration > 0:
                            pct = min(100.0,
                                      (curr_sec / clip_duration) * 100.0)
                            pbar.progress = pct
                            lbl_status.update(
                                f"Step: [bold green]Clipping Video with FFmpeg[/bold green] ({pct:.1f}%)"
                            )
                        else:
                            lbl_status.update(
                                f"Step: [bold green]Processing Video[/bold green] ({int(curr_sec)}s processed)"
                            )

                    size_str = size_match.group(1) if size_match else "--"
                    speed_str = speed_match.group(1) if speed_match else "--"
                    lbl_eta.update(
                        f"Speed: [bold green]{speed_str}[/bold green] | Size: [bold yellow]{size_str}[/bold yellow]"
                    )
                    log.write(f"[dim]{line}[/dim]")

                # 3. Detect major pipeline stages & forward logs
                else:
                    if line.startswith("[VideoConvertor]"):
                        lbl_status.update(
                            "[bold yellow]Step: Recoding Video Format...[/bold yellow]"
                        )
                    elif line.startswith("[Merger]"):
                        lbl_status.update(
                            "[bold yellow]Step: Merging Audio & Video Tracks...[/bold yellow]"
                        )
                    elif line.startswith("[ExtractAudio]"):
                        lbl_status.update(
                            "[bold yellow]Step: Extracting Audio...[/bold yellow]"
                        )

                    log.write(f"[dim]{line}[/dim]")

        await self.download_process.wait()

        if self.download_process.returncode == 0:
            pbar.progress = 100
            log.write(
                f"\n[bold green]✔ Download Complete! Saved as '{out_file}'[/bold green]"
            )
            lbl_status.update(
                "[bold green]Download finished successfully![/bold green]")
        else:
            log.write(
                "\n[bold red]Process failed or was cancelled.[/bold red]")

        self.query_one("#btn-cancel", Button).disabled = True
        self.query_one("#btn-finish", Button).disabled = False


if __name__ == "__main__":
    app = ALogMachineApp()
    app.run()
