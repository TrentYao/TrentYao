from pathlib import Path

import numpy as np
import pygame as pg


# --------------------------------------------------
# Settings
# --------------------------------------------------

FPS = 60

WIDTH = 700
HEIGHT = 800

X_GAP = 6
Y_GAP = 12

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Animation timing, measured in seconds.
PRINT_LINE_TIME = 0.07
PRINT_HOLD_TIME = 0.5

ROTATE_DURATION = 6.0

ERASE_LINE_TIME = 0.05
BLANK_HOLD_TIME = 0.4


# --------------------------------------------------
# File path
# --------------------------------------------------

# main.py is assumed to be inside:
# TrentYao/scripts/main.py
#
# The ASCII file is assumed to be inside:
# TrentYao/asciiArt/secondCard.txt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TXT_PATH = PROJECT_ROOT / "asciiArt" / "secondCard.txt"


# --------------------------------------------------
# Load ASCII card
# --------------------------------------------------

def load_ascii_file(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find the ASCII card file:\n{path}"
        )

    lines = path.read_text(encoding="utf-8").splitlines()

    if not lines:
        raise ValueError(
            f"The ASCII card file is empty:\n{path}"
        )

    map_width = max(len(line) for line in lines)
    map_height = len(lines)

    # Make every line the same width.
    padded_lines = [
        line.ljust(map_width)
        for line in lines
    ]

    characters = "".join(padded_lines)

    return characters, map_width, map_height


# --------------------------------------------------
# Card object
# --------------------------------------------------

class CardObject:
    def __init__(self):
        self.nodes = np.zeros((0, 4), dtype=float)
        self.original_nodes = np.zeros((0, 4), dtype=float)

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
        Rotate from the original coordinates rather than repeatedly
        rotating already-rotated coordinates.
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

        pg.display.set_caption("ASCII 3D CARD")

        self.background = BLACK
        self.surfaces = {}

        # A monospaced font keeps ASCII artwork aligned.
        self.font = pg.font.SysFont(
            "consolas",
            10,
        )

        # Render each unique character only once.
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

        card_pixel_width = self.map_width * X_GAP
        card_pixel_height = self.map_height * Y_GAP

        start_x = (
            self.width / 2
            - card_pixel_width / 2
        )

        start_y = (
            self.height / 2
            - card_pixel_height / 2
        )

        for surface in self.surfaces.values():
            for index, node in enumerate(surface.nodes):
                if index >= len(self.characters):
                    break

                row = index // self.map_width

                # Only display rows belonging to the current phase.
                if not (
                    first_visible_row
                    <= row
                    < last_visible_row
                ):
                    continue

                character = self.characters[index]

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
            surface.set_rotation(combined_matrix)

    def reset(self):
        for surface in self.surfaces.values():
            surface.reset()


# --------------------------------------------------
# Create card coordinates
# --------------------------------------------------

def create_card_nodes(map_width, map_height):
    nodes = []

    for row in range(map_height):
        y = Y_GAP * row

        for column in range(map_width):
            x = X_GAP * column
            z = 0

            nodes.append((x, y, z))

    return np.array(nodes, dtype=float)


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

    phase = "printing"
    phase_time = 0.0

    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        phase_time += dt

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        first_visible_row = 0
        last_visible_row = map_height

        # ------------------------------------------
        # Phase 1: print from top to bottom
        # ------------------------------------------

        if phase == "printing":
            rows_visible = (
                int(phase_time / PRINT_LINE_TIME)
                + 1
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

            # Absolute rotation calculated from the
            # card's original position.
            angle_x = progress * 2 * np.pi
            angle_y = progress * 4 * np.pi
            angle_z = progress * 2 * np.pi

            projection.set_rotation(
                angle_x,
                angle_y,
                angle_z,
            )

            if phase_time >= ROTATE_DURATION:
                # Return to the flat position before erasing.
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

        projection.display(
            first_visible_row,
            last_visible_row,
        )

        pg.display.flip()

    pg.quit()


if __name__ == "__main__":
    main()