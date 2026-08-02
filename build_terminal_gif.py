from __future__ import annotations

from pathlib import Path
from typing import Iterator

from PIL import Image, ImageDraw, ImageFont, ImageOps


# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------

# build_terminal_gif.py should be in the root TrentYao folder.
ROOT = Path(__file__).resolve().parent

SOURCE_GIF = ROOT / "assets" / "card-animation.gif"
OUTPUT_GIF = ROOT / "assets" / "windows-matrix-profile.gif"


# -----------------------------------------------------------------------------
# Edit your profile text here
# -----------------------------------------------------------------------------

PROFILE = {
    "name": "Trent Yao",
    "role": "CS Student",
    "location": "San Jose State University",
    "focus": "coming soon",
    "status": "Learning",
    "languages": "Python, JavaScript, Java, HTML, CSS, FXML",
    "tools": "Git, VS Code, Pygame CE, JavaFX",
    "contact": "ty18662@gmail.com",
    "bio": [
        "coming soon",
    ],
}


# -----------------------------------------------------------------------------
# Output controls
# -----------------------------------------------------------------------------

CANVAS_SIZE = (1100, 700)

# left, top, right, bottom
GIF_PANEL_BOX = (42, 105, 432, 665)

# Use 1 to keep every source GIF frame.
# Use 2 to keep every second frame and reduce file size.
FRAME_STEP = 2

MIN_FRAME_DURATION_MS = 40


# Matrix-green Windows Terminal colors
BG = "#020805"
TITLE_BAR = "#111711"
PANEL = "#031009"

GREEN = "#00FF41"
GREEN_SOFT = "#74FF96"
GREEN_DIM = "#2E6C3D"
WHITE_GREEN = "#D8FFE2"

RED_CLOSE = "#7A2020"


# -----------------------------------------------------------------------------
# Fonts
# -----------------------------------------------------------------------------

def load_font(
    size: int,
    bold: bool = False,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Use Windows fonts when available, with fallback fonts."""

    if bold:
        candidates = [
            Path(r"C:\Windows\Fonts\consolab.ttf"),
            Path(r"C:\Windows\Fonts\segoeuib.ttf"),
            Path(
                "/usr/share/fonts/truetype/"
                "dejavu/DejaVuSansMono-Bold.ttf"
            ),
        ]
    else:
        candidates = [
            Path(r"C:\Windows\Fonts\consola.ttf"),
            Path(r"C:\Windows\Fonts\segoeui.ttf"),
            Path(
                "/usr/share/fonts/truetype/"
                "dejavu/DejaVuSansMono.ttf"
            ),
        ]

    for font_path in candidates:
        if font_path.exists():
            return ImageFont.truetype(
                str(font_path),
                size=size,
            )

    return ImageFont.load_default()


FONT_SMALL = load_font(13)
FONT_BODY = load_font(16)
FONT_BODY_BOLD = load_font(16, bold=True)
FONT_HEADER = load_font(20, bold=True)
FONT_TITLE = load_font(15, bold=True)


# -----------------------------------------------------------------------------
# Draw the Windows Terminal layout
# -----------------------------------------------------------------------------

def rounded_border(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
) -> None:
    draw.rounded_rectangle(
        box,
        radius=18,
        fill=BG,
        outline=GREEN,
        width=2,
    )

    inner = (
        box[0] + 4,
        box[1] + 4,
        box[2] - 4,
        box[3] - 4,
    )

    draw.rounded_rectangle(
        inner,
        radius=15,
        outline=GREEN_DIM,
        width=1,
    )


def draw_windows_icon(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
) -> None:
    gap = 2
    size = 9

    for row in range(2):
        for column in range(2):
            left = x + column * (size + gap)
            top = y + row * (size + gap)

            draw.rectangle(
                (
                    left,
                    top,
                    left + size,
                    top + size,
                ),
                fill=GREEN,
            )


def draw_caption_buttons(
    draw: ImageDraw.ImageDraw,
) -> None:
    # Minimize
    draw.rectangle(
        (948, 20, 994, 76),
        fill=TITLE_BAR,
    )

    draw.line(
        (962, 50, 979, 50),
        fill=WHITE_GREEN,
        width=2,
    )

    # Maximize
    draw.rectangle(
        (994, 20, 1040, 76),
        fill=TITLE_BAR,
    )

    draw.rectangle(
        (1008, 40, 1025, 55),
        outline=WHITE_GREEN,
        width=2,
    )

    # Close
    draw.rectangle(
        (1040, 20, 1080, 76),
        fill=RED_CLOSE,
    )

    draw.line(
        (1052, 40, 1068, 56),
        fill="white",
        width=2,
    )

    draw.line(
        (1068, 40, 1052, 56),
        fill="white",
        width=2,
    )


def draw_label_value(
    draw: ImageDraw.ImageDraw,
    y: int,
    label: str,
    value: str,
    left: int = 500,
    right: int = 1040,
) -> None:
    draw.text(
        (left, y),
        label,
        fill=GREEN,
        font=FONT_BODY,
    )

    value_box = draw.textbbox(
        (0, 0),
        value,
        font=FONT_BODY_BOLD,
    )

    value_width = value_box[2] - value_box[0]
    value_x = right - value_width

    dots_start = left + 120
    dots_end = max(
        dots_start,
        value_x - 12,
    )

    dot_width = max(
        0,
        dots_end - dots_start,
    )

    dot_count = max(
        0,
        dot_width // 9,
    )

    draw.text(
        (dots_start, y),
        "." * dot_count,
        fill=GREEN_DIM,
        font=FONT_BODY,
    )

    draw.text(
        (value_x, y),
        value,
        fill=WHITE_GREEN,
        font=FONT_BODY_BOLD,
    )


def make_terminal_background() -> Image.Image:
    canvas = Image.new(
        "RGBA",
        CANVAS_SIZE,
        BG,
    )

    draw = ImageDraw.Draw(canvas)

    # Main terminal window
    rounded_border(
        draw,
        (18, 18, 1082, 682),
    )

    # Title bar
    draw.rounded_rectangle(
        (20, 20, 1080, 77),
        radius=15,
        fill=TITLE_BAR,
    )

    draw.rectangle(
        (20, 58, 1080, 77),
        fill=TITLE_BAR,
    )

    draw.line(
        (20, 77, 1080, 77),
        fill=GREEN_DIM,
        width=1,
    )

    draw_windows_icon(
        draw,
        40,
        37,
    )

    draw.text(
        (72, 34),
        "Windows Terminal - PowerShell",
        fill=WHITE_GREEN,
        font=FONT_TITLE,
    )

    draw.text(
        (72, 54),
        r"C:\Users\Trent\github\profile",
        fill=GREEN_SOFT,
        font=FONT_SMALL,
    )

    draw_caption_buttons(draw)

    # Left card panel
    gx1, gy1, gx2, gy2 = GIF_PANEL_BOX

    draw.rounded_rectangle(
        (gx1, gy1, gx2, gy2),
        radius=10,
        fill=PANEL,
        outline=GREEN_DIM,
        width=2,
    )

    draw.text(
        (gx1 + 16, gy1 + 13),
        "VISUAL.CARD",
        fill=GREEN,
        font=FONT_SMALL,
    )

    draw.line(
        (
            gx1 + 115,
            gy1 + 21,
            gx2 - 14,
            gy1 + 21,
        ),
        fill=GREEN_DIM,
        width=1,
    )

    # Right information panel
    draw.text(
        (500, 108),
        "SYSTEM.INFO",
        fill=GREEN,
        font=FONT_HEADER,
    )

    draw.line(
        (650, 123, 1010, 123),
        fill=GREEN_DIM,
        width=1,
    )

    draw.ellipse(
        (1024, 118, 1032, 126),
        fill=GREEN,
    )

    draw.text(
        (1040, 111),
        "LIVE",
        fill=GREEN_SOFT,
        font=FONT_SMALL,
    )

    y = 158

    for label, key in [
        ("Name", "name"),
        ("Role", "role"),
        ("Location", "location"),
        ("Focus", "focus"),
        ("Status", "status"),
    ]:
        draw_label_value(
            draw,
            y,
            label,
            PROFILE[key],
        )

        y += 35

    draw.text(
        (500, 355),
        "ABOUT.ME",
        fill=GREEN,
        font=FONT_HEADER,
    )

    draw.line(
        (620, 370, 1038, 370),
        fill=GREEN_DIM,
        width=1,
    )

    y = 398

    for line in PROFILE["bio"]:
        draw.text(
            (504, y),
            f"> {line}",
            fill=WHITE_GREEN,
            font=FONT_BODY,
        )

        y += 31

    draw.text(
        (500, 535),
        "STACK.CONNECT",
        fill=GREEN,
        font=FONT_HEADER,
    )

    draw.line(
        (665, 550, 1038, 550),
        fill=GREEN_DIM,
        width=1,
    )

    draw_label_value(
        draw,
        568,
        "Languages",
        PROFILE["languages"],
    )

    draw_label_value(
        draw,
        596,
        "Tools",
        PROFILE["tools"],
    )

    draw_label_value(
        draw,
        624,
        "Contact",
        PROFILE["contact"],
    )

    # PowerShell prompt
    draw.text(
        (42, 665),
        r"PS C:\Users\Trent> .\profile.exe --live",
        fill=GREEN_SOFT,
        font=FONT_SMALL,
    )

    return canvas


# -----------------------------------------------------------------------------
# Process the card GIF
# -----------------------------------------------------------------------------

def fit_frame(
    frame: Image.Image,
    box: tuple[int, int, int, int],
) -> Image.Image:
    """Resize a source frame to fit inside the card panel."""

    left, top, right, bottom = box

    # Leave room for the VISUAL.CARD heading.
    target_size = (
        right - left - 24,
        bottom - top - 52,
    )

    rgba_frame = frame.convert("RGBA")

    # Force the frame to have an opaque background.
    # This prevents transparency or GIF disposal metadata
    # from making the card disappear.
    opaque_frame = Image.new(
        "RGBA",
        rgba_frame.size,
        (0, 0, 0, 255),
    )

    opaque_frame.alpha_composite(
        rgba_frame
    )

    return ImageOps.contain(
        opaque_frame,
        target_size,
        method=Image.Resampling.LANCZOS,
    )


def iter_source_frames(
    source: Image.Image,
) -> Iterator[tuple[Image.Image, int]]:
    """
    Read and copy fully composed GIF frames.

    Each frame is copied immediately after source.seek().
    This prevents every output frame from becoming the
    same blank or final frame.
    """

    total_frames = int(
        getattr(source, "n_frames", 1)
    )

    default_duration = int(
        source.info.get("duration", 50)
        or 50
    )

    for index in range(
        0,
        total_frames,
        FRAME_STEP,
    ):
        source.seek(index)

        # Copy the current frame immediately.
        frame = (
            source
            .convert("RGBA")
            .copy()
        )

        combined_duration = 0

        # Combine the durations of skipped frames.
        for duration_index in range(
            index,
            min(
                index + FRAME_STEP,
                total_frames,
            ),
        ):
            source.seek(duration_index)

            frame_duration = int(
                source.info.get(
                    "duration",
                    default_duration,
                )
                or default_duration
            )

            combined_duration += frame_duration

        yield (
            frame,
            max(
                MIN_FRAME_DURATION_MS,
                combined_duration,
            ),
        )


# -----------------------------------------------------------------------------
# Create the combined Matrix terminal GIF
# -----------------------------------------------------------------------------

def build_profile_gif() -> None:
    print(f"Input GIF: {SOURCE_GIF}")
    print(f"Input exists: {SOURCE_GIF.exists()}")
    print(f"Output GIF: {OUTPUT_GIF}")

    if not SOURCE_GIF.exists():
        raise FileNotFoundError(
            "Place your existing card animation here:\n"
            f"{SOURCE_GIF}"
        )

    terminal = make_terminal_background()

    output_frames: list[Image.Image] = []
    durations: list[int] = []

    gx1, gy1, gx2, gy2 = GIF_PANEL_BOX

    with Image.open(SOURCE_GIF) as source:
        print(
            "Source frames:",
            getattr(source, "n_frames", 1),
        )

        print(
            "Source size:",
            source.size,
        )

        for frame, duration in iter_source_frames(
            source
        ):
            composed = terminal.copy()

            fitted = fit_frame(
                frame,
                GIF_PANEL_BOX,
            )

            panel_width = gx2 - gx1
            panel_height = gy2 - (gy1 + 42)

            x = (
                gx1
                + (panel_width - fitted.width) // 2
            )

            y = (
                gy1
                + 42
                + (panel_height - fitted.height) // 2
            )

            # Put the card GIF frame inside the terminal.
            composed.alpha_composite(
                fitted,
                dest=(x, y),
            )

            # Save complete RGB frames.
            # This avoids per-frame palette problems.
            output_frames.append(
                composed.convert("RGB")
            )

            durations.append(duration)

    if not output_frames:
        raise RuntimeError(
            "No frames were read from the source GIF."
        )

    OUTPUT_GIF.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_frames[0].save(
        OUTPUT_GIF,
        save_all=True,
        append_images=output_frames[1:],
        duration=durations,
        loop=0,
        disposal=1,
        optimize=False,
    )

    print(f"Created: {OUTPUT_GIF}")
    print(f"Frames: {len(output_frames)}")


if __name__ == "__main__":
    build_profile_gif()
