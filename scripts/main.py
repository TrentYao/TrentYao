from pathlib import Path

import numpy as np
import pygame as pg
from PIL import Image


# --------------------------------------------------
# Window and animation settings
# --------------------------------------------------

FPS = 60

WIDTH = 700
HEIGHT = 800

X_GAP = 6
Y_GAP = 12

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


# --------------------------------------------------
# Animation timing, in seconds
# --------------------------------------------------

PRINT_LINE_TIME = 0.07
PRINT_HOLD_TIME = 0.5

ROTATE_DURATION = 6.0

ERASE_LINE_TIME = 0.05
BLANK_HOLD_TIME = 0.4


# --------------------------------------------------
# GIF settings
# --------------------------------------------------

# The Pygame window runs at 60 FPS, but the GIF is
# recorded at 20 FPS to keep the file size reasonable.
GIF_FPS = 20

# Size of the saved GIF.
GIF_SIZE = (525, 600)

# Capture one frame every three Pygame frames:
# 60 FPS / 20 GIF FPS = 3
CAPTURE_EVERY = max(1, round(FPS / GIF_FPS))


# --------------------------------------------------
# Project paths
# --------------------------------------------------

# Expected project structure:
#
# TrentYao/
# ├── asciiArt/
# │   └── secondCard.txt
# ├── assets/
# │   └── card-animation.gif
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


# --------------------------------------------------
# Load the ASCII-art file
# --------------------------------------------------

def load_ascii_file(path):
    if not path.exists():
        raise FileNotFoundError(
            "Could not find the ASCII card file:\n"
            f"{path}"
        )

    lines = path.read_text(
        encoding="utf-8"
    ).splitlines()

    if not lines:
        raise ValueError(
            "The ASCII card file is empty:\n"
            f"{path}"
        )

    map_width = max(len(line) for line in lines)
    map_height = len(lines)

    # Add spaces to shorter lines so every line
    # has the same width.
    padded_lines = [
        line.ljust(map_width)
        for line in lines
    ]

    characters = "".join(padded_lines)

    return characters, map_width, map_height


# --------------------------------------------------
# Card coordinate object
# --------------------------------------------------

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
            (node_array, ones_column)
        )

        self.nodes = nodes_with_ones.copy()
        self.original_nodes = nodes_with_ones.copy()

    def set_rotation(self, matrix):
        """
        Calculate every rotation from the original card
        coordinates. This prevents rotation errors from
        accumulating over time.
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


# --------------------------------------------------
# Projection and rendering
# --------------------------------------------------

class Projection:
    def __init__(
        self,
        width,
        height,
        characters,
        map_width,
        map_height,
    ):
        self.width = width
        self.height = height

        self.characters = characters
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

        # Consolas is monospaced, which helps keep the
        # ASCII-art characters correctly aligned.
        self.font = pg.font.SysFont(
            "consolas",
            10,
        )

        # Render each unique character once instead of
        # rendering it again during every frame.
        self.character_surfaces = {
            character: self.font.render(
                character,
                True,
                WHITE,
            )
            for character in set(characters)
            if character != " "
        }

    def add_surface(self, name, surface):
        self.surfaces[name] = surface

    def display(
        self,
        first_visible_row=0,
        last_visible_row=None,
    ):
        self.screen.fill(self.background)

        if last_visible_row is None:
            last_visible_row = self.map_height

        card_pixel_width = (
            max(0, self.map_width - 1)
            * X_GAP
        )

        card_pixel_height = (
            max(0, self.map_height - 1)
            * Y_GAP
        )

        start_x = (
            self.width - card_pixel_width
        ) / 2

        start_y = (
            self.height - card_pixel_height
        ) / 2

        for surface in self.surfaces.values():
            for index, node in enumerate(
                surface.nodes
            ):
                if index >= len(self.characters):
                    break

                row = index // self.map_width

                # Hide rows that are outside the currently
                # visible section of the card.
                if not (
                    first_visible_row
                    <= row
                    < last_visible_row
                ):
                    continue

                character = self.characters[index]

                # Spaces do not need to be drawn.
                if character == " ":
                    continue

                text_surface = (
                    self.character_surfaces[character]
                )

                x = int(start_x + node[0])
                y = int(start_y + node[1])

                self.screen.blit(
                    text_surface,
                    (x, y),
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


# --------------------------------------------------
# Generate one coordinate for each ASCII character
# --------------------------------------------------

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

            nodes.append((x, y, z))

    return np.array(
        nodes,
        dtype=float,
    )


# --------------------------------------------------
# Capture one Pygame frame as a Pillow image
# --------------------------------------------------

def capture_gif_frame(screen):
    resized_surface = pg.transform.smoothscale(
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


# --------------------------------------------------
# Save all recorded frames as a GIF
# --------------------------------------------------

def save_animation(
    frames,
    output_path,
    fps,
):
    if not frames:
        print("No GIF frames were recorded.")
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
        duration=round(1000 / fps),
        loop=0,          # Repeat forever
        disposal=2,
        optimize=False,
    )

    print(
        "\nGIF successfully saved to:\n"
        f"{output_path.resolve()}\n"
    )


# --------------------------------------------------
# Main animation
# --------------------------------------------------

def main():
    pg.init()

    clock = pg.time.Clock()

    card_ascii, map_width, map_height = (
        load_ascii_file(TXT_PATH)
    )

    projection = Projection(
        WIDTH,
        HEIGHT,
        card_ascii,
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

    # Current animation phase.
    phase = "printing"
    phase_time = 0.0

    # GIF recording variables.
    recorded_frames = []
    frame_counter = 0
    recording = True

    print(
        "Recording the first complete animation cycle."
    )

    print(
        "Keep the window open until the terminal says "
        "the GIF was saved."
    )

    print(
        f"The GIF will be saved to:\n"
        f"{GIF_PATH.resolve()}\n"
    )

    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        phase_time += dt

        # This becomes True after one complete
        # print -> rotate -> erase sequence.
        cycle_finished = False

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        first_visible_row = 0
        last_visible_row = map_height

        # ------------------------------------------
        # Phase 1: print from top to bottom
        # ------------------------------------------

        if phase == "printing":
            rows_visible = int(
                phase_time / PRINT_LINE_TIME
            )

            rows_visible = min(
                rows_visible,
                map_height,
            )

            first_visible_row = 0
            last_visible_row = rows_visible

            print_duration = (
                map_height * PRINT_LINE_TIME
                + PRINT_HOLD_TIME
            )

            if phase_time >= print_duration:
                projection.reset()

                phase = "rotating"
                phase_time = 0.0

        # ------------------------------------------
        # Phase 2: rotate the complete card
        # ------------------------------------------

        elif phase == "rotating":
            first_visible_row = 0
            last_visible_row = map_height

            progress = min(
                phase_time / ROTATE_DURATION,
                1.0,
            )

            # Complete whole rotations so the card returns
            # to its original position before erasing.
            angle_x = progress * 2 * np.pi
            angle_y = progress * 4 * np.pi
            angle_z = progress * 2 * np.pi

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
        # Phase 3: erase from top to bottom
        # ------------------------------------------

        elif phase == "erasing":
            rows_removed = int(
                phase_time / ERASE_LINE_TIME
            )

            rows_removed = min(
                rows_removed,
                map_height,
            )

            first_visible_row = rows_removed
            last_visible_row = map_height

            erase_duration = (
                map_height * ERASE_LINE_TIME
                + BLANK_HOLD_TIME
            )

            if phase_time >= erase_duration:
                projection.reset()

                phase = "printing"
                phase_time = 0.0

                cycle_finished = True

        # Draw the current frame.
        projection.display(
            first_visible_row,
            last_visible_row,
        )

        pg.display.flip()

        # ------------------------------------------
        # Record the first complete cycle
        # ------------------------------------------

        if (
            recording
            and frame_counter % CAPTURE_EVERY == 0
        ):
            recorded_frames.append(
                capture_gif_frame(
                    projection.screen
                )
            )

        # Save immediately after the first sequence ends.
        if recording and cycle_finished:
            save_animation(
                recorded_frames,
                GIF_PATH,
                GIF_FPS,
            )

            recording = False
            recorded_frames.clear()

            # Update the window title after saving.
            pg.display.set_caption(
                "ASCII 3D CARD - GIF SAVED"
            )

        frame_counter += 1

    pg.quit()


if __name__ == "__main__":
    main()