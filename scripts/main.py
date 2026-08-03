from pathlib import Path

import numpy as np
import pygame as pg
from PIL import Image


# ==================================================
# Window settings
# ==================================================

FPS = 60

WIDTH = 700
HEIGHT = 800

# Character spacing
X_GAP = 8
Y_GAP = 16

# Smaller margin makes the card appear larger.
SAFE_MARGIN = 30


# ==================================================
# Font settings
# ==================================================

FONT_NAME = "consolas"
FONT_SIZE = 14
FONT_BOLD = True


# ==================================================
# Colors
# ==================================================

BLACK = (0, 0, 0)

# Bright card border
WHITE = (255, 255, 255)

# Bright Matrix green for text and symbols
CARD_GREEN = (90, 255, 125)

# Glow colors
GREEN_GLOW = (0, 150, 50)
WHITE_GLOW = (125, 125, 125)

GLOW_ALPHA = 170


# ==================================================
# Animation timing
# ==================================================

PRINT_LINE_TIME = 0.07
PRINT_HOLD_TIME = 0.5

ROTATE_DURATION = 16.0

ERASE_LINE_TIME = 0.05
BLANK_HOLD_TIME = 0.4


# ==================================================
# GIF settings
# ==================================================

GIF_FPS = 20

GIF_SIZE = (525, 600)

CAPTURE_EVERY = max(
    1,
    round(FPS / GIF_FPS),
)


# ==================================================
# Project paths
# ==================================================

# Expected structure:
#
# TrentYao/
# ├── assets/
# │   └── card-animation.gif
# ├── asciiArt/
# │   └── secondCard.txt
# └── scripts/
#     └── main.py

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TXT_PATH = (
    PROJECT_ROOT
    / "asciiArt"
    / "secondCard.txt"
)

GIF_PATH = (
    PROJECT_ROOT
    / "assets"
    / "card-animation.gif"
)


# ==================================================
# Load the ASCII-art file
# ==================================================

def load_ascii_file(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            "Could not find the ASCII-art file:\n"
            f"{path}"
        )

    lines = path.read_text(
        encoding="utf-8"
    ).splitlines()

    if not lines:
        raise ValueError(
            "The ASCII-art file is empty:\n"
            f"{path}"
        )

    map_width = max(
        len(line)
        for line in lines
    )

    map_height = len(lines)

    # Make every row the same width.
    padded_lines = [
        line.ljust(map_width)
        for line in lines
    ]

    characters = "".join(
        padded_lines
    )

    return (
        characters,
        padded_lines,
        map_width,
        map_height,
    )


# ==================================================
# Card coordinate object
# ==================================================

class CardObject:
    def __init__(self):
        self.nodes = np.zeros(
            (0, 4),
            dtype=float,
        )

        self.original_nodes = np.zeros(
            (0, 4),
            dtype=float,
        )

    def add_nodes(self, node_array):
        ones_column = np.ones(
            (len(node_array), 1),
            dtype=float,
        )

        nodes_with_ones = np.hstack(
            (
                node_array,
                ones_column,
            )
        )

        self.nodes = nodes_with_ones.copy()
        self.original_nodes = nodes_with_ones.copy()

    def set_rotation(self, matrix):
        """
        Rotate from the original card coordinates so small
        calculation errors do not accumulate over time.
        """

        center = self.original_nodes.mean(
            axis=0,
            keepdims=True,
        )

        self.nodes = (
            (self.original_nodes - center)
            @ matrix.T
            + center
        )

    def reset(self):
        self.nodes = self.original_nodes.copy()


# ==================================================
# Projection and rendering
# ==================================================

class Projection:
    def __init__(
        self,
        width,
        height,
        characters,
        lines,
        map_width,
        map_height,
    ):
        self.width = width
        self.height = height

        self.characters = characters
        self.lines = lines

        self.map_width = map_width
        self.map_height = map_height

        self.screen = pg.display.set_mode(
            (width, height)
        )

        pg.display.set_caption(
            "ASCII 3D CARD"
        )

        self.background = BLACK
        self.surfaces = {}

        # Bold monospaced font for clearer ASCII art.
        self.font = pg.font.SysFont(
            FONT_NAME,
            FONT_SIZE,
            bold=FONT_BOLD,
        )

        # Original dimensions of the card.
        self.card_width = (
            max(0, self.map_width - 1)
            * X_GAP
        )

        self.card_height = (
            max(0, self.map_height - 1)
            * Y_GAP
        )

        # The diagonal is the maximum size the card may occupy
        # while rotating around its center.
        card_diagonal = np.hypot(
            self.card_width,
            self.card_height,
        )

        available_width = max(
            1,
            self.width - SAFE_MARGIN * 2,
        )

        available_height = max(
            1,
            self.height - SAFE_MARGIN * 2,
        )

        if card_diagonal > 0:
            self.card_scale = min(
                1.0,
                available_width / card_diagonal,
                available_height / card_diagonal,
            )
        else:
            self.card_scale = 1.0

        self.card_center_x = (
            self.card_width / 2
        )

        self.card_center_y = (
            self.card_height / 2
        )

        print(
            f"Card display scale: "
            f"{self.card_scale:.3f}"
        )

        # Cache normal characters and glow characters.
        self.character_surfaces = {}
        self.glow_surfaces = {}

        # Border positions remain white.
        self.border_positions = set()

        self.find_border_positions()

        print(
            f"Detected {len(self.border_positions)} "
            "white border characters."
        )

    def add_surface(
        self,
        name,
        surface,
    ):
        self.surfaces[name] = surface

    def find_border_positions(self):
        """
        Detect the outer card border.

        The border stays white. Text, hearts, corner symbols,
        and other content inside the card become green.
        """

        border_glyphs = {
            "-",
            "|",
            "+",
            "_",
            "/",
            "\\",
            "=",
            "*",
            "│",
            "─",
            "┌",
            "┐",
            "└",
            "┘",
            "╭",
            "╮",
            "╰",
            "╯",
            "═",
            "║",
            "╔",
            "╗",
            "╚",
            "╝",
        }

        nonempty_rows = [
            row
            for row, line in enumerate(self.lines)
            if line.strip()
        ]

        if not nonempty_rows:
            return

        top_row = min(nonempty_rows)
        bottom_row = max(nonempty_rows)

        for row, line in enumerate(self.lines):
            visible_columns = [
                column
                for column, character in enumerate(line)
                if character != " "
            ]

            if not visible_columns:
                continue

            left_edge = min(visible_columns)
            right_edge = max(visible_columns)

            # Outermost characters on each row.
            self.border_positions.add(
                (row, left_edge)
            )

            self.border_positions.add(
                (row, right_edge)
            )

            # Entire top and bottom rows are border.
            if row == top_row or row == bottom_row:
                for column in visible_columns:
                    self.border_positions.add(
                        (row, column)
                    )

                continue

            visible_characters = [
                line[column]
                for column in visible_columns
            ]

            # Rows containing only border symbols are also
            # considered part of the border.
            if all(
                character in border_glyphs
                for character in visible_characters
            ):
                for column in visible_columns:
                    self.border_positions.add(
                        (row, column)
                    )

                continue

            # Detect connected border symbols from the left.
            for column in visible_columns:
                character = line[column]

                if character in border_glyphs:
                    self.border_positions.add(
                        (row, column)
                    )
                else:
                    break

            # Detect connected border symbols from the right.
            for column in reversed(visible_columns):
                character = line[column]

                if character in border_glyphs:
                    self.border_positions.add(
                        (row, column)
                    )
                else:
                    break

    def get_character_color(self, index):
        row = index // self.map_width
        column = index % self.map_width

        if (row, column) in self.border_positions:
            return WHITE

        return CARD_GREEN

    def scale_text_surface(self, surface):
        """
        Scale the character using regular scaling so it stays
        sharper than smooth scaling.
        """

        if self.card_scale >= 0.999:
            return surface

        scaled_width = max(
            1,
            round(
                surface.get_width()
                * self.card_scale
            ),
        )

        scaled_height = max(
            1,
            round(
                surface.get_height()
                * self.card_scale
            ),
        )

        return pg.transform.scale(
            surface,
            (
                scaled_width,
                scaled_height,
            ),
        )

    def get_character_surface(
        self,
        character,
        color,
    ):
        cache_key = (
            character,
            color,
        )

        if cache_key not in self.character_surfaces:
            original_surface = self.font.render(
                character,
                True,
                color,
            )

            text_surface = self.scale_text_surface(
                original_surface
            )

            self.character_surfaces[cache_key] = (
                text_surface
            )

        return self.character_surfaces[cache_key]

    def get_glow_surface(
        self,
        character,
        color,
    ):
        cache_key = (
            character,
            color,
        )

        if cache_key not in self.glow_surfaces:
            original_surface = self.font.render(
                character,
                True,
                color,
            )

            glow_surface = self.scale_text_surface(
                original_surface
            )

            glow_surface.set_alpha(
                GLOW_ALPHA
            )

            self.glow_surfaces[cache_key] = (
                glow_surface
            )

        return self.glow_surfaces[cache_key]

    def display(
        self,
        first_visible_row=0,
        last_visible_row=None,
    ):
        self.screen.fill(
            self.background
        )

        if last_visible_row is None:
            last_visible_row = self.map_height

        screen_center_x = self.width / 2
        screen_center_y = self.height / 2

        for surface in self.surfaces.values():
            for index, node in enumerate(
                surface.nodes
            ):
                if index >= len(self.characters):
                    break

                row = index // self.map_width

                if not (
                    first_visible_row
                    <= row
                    < last_visible_row
                ):
                    continue

                character = self.characters[index]

                if character == " ":
                    continue

                color = self.get_character_color(
                    index
                )

                text_surface = (
                    self.get_character_surface(
                        character,
                        color,
                    )
                )

                # Keep the card centered during rotation.
                x = (
                    screen_center_x
                    + (
                        node[0]
                        - self.card_center_x
                    )
                    * self.card_scale
                    - text_surface.get_width() / 2
                )

                y = (
                    screen_center_y
                    + (
                        node[1]
                        - self.card_center_y
                    )
                    * self.card_scale
                    - text_surface.get_height() / 2
                )

                draw_x = int(x)
                draw_y = int(y)

                if color == WHITE:
                    glow_color = WHITE_GLOW
                else:
                    glow_color = GREEN_GLOW

                glow_surface = (
                    self.get_glow_surface(
                        character,
                        glow_color,
                    )
                )

                # Draw a glow around the character.
                glow_offsets = (
                    (-2, 0),
                    (2, 0),
                    (0, -2),
                    (0, 2),
                    (-1, -1),
                    (1, -1),
                    (-1, 1),
                    (1, 1),
                )

                for offset_x, offset_y in glow_offsets:
                    self.screen.blit(
                        glow_surface,
                        (
                            draw_x + offset_x,
                            draw_y + offset_y,
                        ),
                    )

                # Draw the bright character on top.
                self.screen.blit(
                    text_surface,
                    (
                        draw_x,
                        draw_y,
                    ),
                )

    def set_rotation(
        self,
        angle_x,
        angle_y,
        angle_z,
    ):
        cx = np.cos(angle_x)
        sx = np.sin(angle_x)

        cy = np.cos(angle_y)
        sy = np.sin(angle_y)

        cz = np.cos(angle_z)
        sz = np.sin(angle_z)

        rotate_x = np.array([
            [1, 0, 0, 0],
            [0, cx, -sx, 0],
            [0, sx, cx, 0],
            [0, 0, 0, 1],
        ])

        rotate_y = np.array([
            [cy, 0, sy, 0],
            [0, 1, 0, 0],
            [-sy, 0, cy, 0],
            [0, 0, 0, 1],
        ])

        rotate_z = np.array([
            [cz, -sz, 0, 0],
            [sz, cz, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ])

        combined_matrix = (
            rotate_z
            @ rotate_y
            @ rotate_x
        )

        for surface in self.surfaces.values():
            surface.set_rotation(
                combined_matrix
            )

    def reset(self):
        for surface in self.surfaces.values():
            surface.reset()


# ==================================================
# Create one coordinate per ASCII character
# ==================================================

def create_card_nodes(
    map_width,
    map_height,
):
    nodes = []

    for row in range(map_height):
        y = Y_GAP * row

        for column in range(map_width):
            x = X_GAP * column
            z = 0

            nodes.append(
                (x, y, z)
            )

    return np.array(
        nodes,
        dtype=float,
    )


# ==================================================
# Capture one GIF frame
# ==================================================

def capture_gif_frame(screen):
    # Regular scaling keeps the ASCII characters sharper.
    resized_surface = pg.transform.scale(
        screen,
        GIF_SIZE,
    )

    image_bytes = pg.image.tobytes(
        resized_surface,
        "RGB",
    )

    return Image.frombytes(
        "RGB",
        resized_surface.get_size(),
        image_bytes,
    )


# ==================================================
# Save the animated GIF
# ==================================================

def save_animation(
    frames,
    output_path,
    fps,
):
    if not frames:
        print(
            "No GIF frames were recorded."
        )
        return

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        f"Saving {len(frames)} GIF frames..."
    )

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=round(
            1000 / fps
        ),
        loop=0,
        disposal=1,
        optimize=False,
    )

    print(
        "\nBright card GIF successfully saved to:\n"
        f"{output_path.resolve()}\n"
    )


# ==================================================
# Main animation
# ==================================================

def main():
    pg.init()

    clock = pg.time.Clock()

    (
        card_ascii,
        ascii_lines,
        map_width,
        map_height,
    ) = load_ascii_file(
        TXT_PATH
    )

    projection = Projection(
        WIDTH,
        HEIGHT,
        card_ascii,
        ascii_lines,
        map_width,
        map_height,
    )

    card = CardObject()

    card.add_nodes(
        create_card_nodes(
            map_width,
            map_height,
        )
    )

    projection.add_surface(
        "card",
        card,
    )

    phase = "printing"
    phase_time = 0.0

    recorded_frames = []
    frame_counter = 0
    recording = True

    print(
        "Recording the first complete animation cycle."
    )

    print(
        "Keep the Pygame window open until the GIF is saved."
    )

    print(
        "\nThe GIF will be saved to:\n"
        f"{GIF_PATH.resolve()}\n"
    )

    running = True

    while running:
        dt = (
            clock.tick(FPS)
            / 1000.0
        )

        phase_time += dt
        cycle_finished = False

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

            if (
                event.type == pg.KEYDOWN
                and event.key == pg.K_ESCAPE
            ):
                running = False

        first_visible_row = 0
        last_visible_row = map_height

        # ------------------------------------------
        # Phase 1: print the card
        # ------------------------------------------

        if phase == "printing":
            rows_visible = int(
                phase_time
                / PRINT_LINE_TIME
            )

            rows_visible = min(
                rows_visible,
                map_height,
            )

            first_visible_row = 0
            last_visible_row = rows_visible

            print_duration = (
                map_height
                * PRINT_LINE_TIME
                + PRINT_HOLD_TIME
            )

            if phase_time >= print_duration:
                projection.reset()

                phase = "rotating"
                phase_time = 0.0

        # ------------------------------------------
        # Phase 2: rotate the card
        # ------------------------------------------

        elif phase == "rotating":
            first_visible_row = 0
            last_visible_row = map_height

            progress = min(
                phase_time
                / ROTATE_DURATION,
                1.0,
            )

            angle_x = (
                progress
                * 2
                * np.pi
            )

            angle_y = (
                progress
                * 4
                * np.pi
            )

            angle_z = (
                progress
                * 2
                * np.pi
            )

            projection.set_rotation(
                angle_x,
                angle_y,
                angle_z,
            )

            if phase_time >= ROTATE_DURATION:
                projection.reset()

                phase = "erasing"
                phase_time = 0.0

        # ------------------------------------------
        # Phase 3: erase the card
        # ------------------------------------------

        elif phase == "erasing":
            rows_removed = int(
                phase_time
                / ERASE_LINE_TIME
            )

            rows_removed = min(
                rows_removed,
                map_height,
            )

            first_visible_row = rows_removed
            last_visible_row = map_height

            erase_duration = (
                map_height
                * ERASE_LINE_TIME
                + BLANK_HOLD_TIME
            )

            if phase_time >= erase_duration:
                projection.reset()

                phase = "printing"
                phase_time = 0.0

                cycle_finished = True

        projection.display(
            first_visible_row,
            last_visible_row,
        )

        pg.display.flip()

        # Record only the first complete cycle.
        if (
            recording
            and frame_counter % CAPTURE_EVERY == 0
        ):
            recorded_frames.append(
                capture_gif_frame(
                    projection.screen
                )
            )

        if recording and cycle_finished:
            save_animation(
                recorded_frames,
                GIF_PATH,
                GIF_FPS,
            )

            recording = False
            recorded_frames.clear()

            pg.display.set_caption(
                "ASCII 3D CARD - GIF SAVED"
            )

        frame_counter += 1

    pg.quit()


if __name__ == "__main__":
    main()