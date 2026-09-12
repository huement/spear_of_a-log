from textual.containers import Horizontal
from textual.widgets import Input, Label, TabPane

def compose_kick_tab(last_kick_url: str = "") -> TabPane:
    """Generates the Kick UI Tab Pane."""
    return TabPane(
        "KICK",
        Label("Kick Video URL or VOD ID:", classes="field-label"),
        Input(
            value=last_kick_url,
            placeholder="kinocasinogaming/videos/01a026df-75b0-75e8-9e92-d9c1b5f7663f",
            id="kick-url-input",
        ),
        Label("Start Time (HH : MM : SS):", classes="field-label"),
        Horizontal(
            Input(value="00", placeholder="HH", id="kick-start-h", classes="time-input", max_length=2),
            Input(value="00", placeholder="MM", id="kick-start-m", classes="time-input", max_length=2),
            Input(value="00", placeholder="SS", id="kick-start-s", classes="time-input", max_length=2),
            classes="time-container",
        ),
        Label("End Time (HH : MM : SS):", classes="field-label"),
        Horizontal(
            Input(value="00", placeholder="HH", id="kick-end-h", classes="time-input", max_length=2),
            Input(value="01", placeholder="MM", id="kick-end-m", classes="time-input", max_length=2),
            Input(value="30", placeholder="SS", id="kick-end-s", classes="time-input", max_length=2),
            classes="time-container",
        ),
        Label("Output Filename (text only):", classes="field-label"),
        Input(value="kick_clip", placeholder="e.g. kick_clip", id="kick-out-input"),
        id="tab-kick",
    )