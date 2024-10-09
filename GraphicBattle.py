"""Wrapper around Battle to display battles graphically as a series of PIL.Image frames"""

from io import BytesIO
from itertools import chain
from math import inf, sqrt

import matplotlib.pyplot as plt
import numpy as np
from attrs import define, Factory, field
from PIL import Image, ImageColor, ImageDraw

import Config
from Battle import DEFAULT_TERRAIN, FILE_EMPTY, FILE_SUPPORTED, FILE_VULNERABLE, FILE_WIDTH, \
                   Army, Battle, Fight, Landscape, OneWayFight, TwoWayFight, Unit


UNIT_FILE_WIDTH: float = 0.95
ATTACK_LINE_OFFSET: float = 0.2
ARROWHEAD_SIZE: float = 0.2


@define
class BattleScene:
    """Contains a list of frames showing the battle, along with methods for drawing them"""

    max_screen: tuple[int, int]
    landscape: Landscape
    min_file: int
    max_file: int
    min_pos: float
    max_pos: float

    pixel_per_pos: float = field(init=False)
    pixel_per_file: float = field(init=False)
    pixels_unit: tuple[float, float] = field(init=False)
    croped_res: tuple[int, int] = field(init=False)
    font_size: int = field(init=False)

    background: Image.Image = field(init=False, default=None)
    canvas: Image.Image = field(init=False, default=None)
    frames: list[Image.Image] = field(init=False, default=Factory(list))

    def __attrs_post_init__(self) -> None:
        num_files = 1 + self.max_file - self.min_file  # Count files, not gaps
        num_pos = 4 + self.max_pos - self.min_pos      # Including reserves and dead
        
        file_pixel_width = self.max_screen[0] / num_files
        pos_pixel_height = self.max_screen[1] / num_pos

        if pos_pixel_height * FILE_WIDTH < file_pixel_width:
            self.pixel_per_pos = pos_pixel_height
            self.pixel_per_file = self.pixel_per_pos * FILE_WIDTH
        else:
            self.pixel_per_pos = file_pixel_width / FILE_WIDTH
            self.pixel_per_file = file_pixel_width

        self.pixels_unit = UNIT_FILE_WIDTH * self.pixel_per_file, self.pixel_per_pos
        self.croped_res = int(self.pixel_per_file * num_files), int(self.pixel_per_pos * num_pos)
        self.font_size = int(self.pixel_per_pos / 2)  # Allows text to fit nicely in unit rect

        self.draw_background()

    # GETTERS
    def get_coords(self, file: float, pos: float) -> tuple[float, float]:
        """Pixel position of a point in the middle of the given file at the given position"""
        """Returns ints in float type for ease of vector manipulations later"""
        file_steps = 0.5 + file - self.min_file
        pos_steps = 2 + pos - self.min_pos
        return int(file_steps * self.pixel_per_file), int(pos_steps * self.pixel_per_pos)

    def get_fight_color(self, fight: Fight):
        if isinstance(fight, OneWayFight):
            return ImageColor.getcolor(fight.unit_A.army.color, mode="RGBA")
        else:
            cA = ImageColor.getcolor(fight.unit_A.army.color, mode="RGBA")
            cB = ImageColor.getcolor(fight.unit_B.army.color, mode="RGBA")
            return tuple((cA[j]+cB[j]) // 2 for j in range(4))

    def get_line_width(self, unit: Unit, side: int) -> int:
        # Change line thickness on edge of unit rectangle depanding on state of flanks
        state = unit.army.get_state_of_file(unit.file + side, unit.position)
        if state == FILE_EMPTY:
            return 2
        elif state == FILE_VULNERABLE:
            return 1
        elif state == FILE_SUPPORTED:
            return 3
        else:
            raise RuntimeError("Unexpected value for unit.army.file_state()")

    # BACKGROUND
    def draw_background(self) -> None:
        self.background = Image.new(mode="RGBA", size=self.croped_res, color="Gainsboro")

        for file in range(self.min_file, self.max_file + 1):
            self.draw_background_file(file)

        self.draw_background_contours()
        self.draw_background_height_labels()

    def draw_background_file(self, file: int) -> None:
        draw = ImageDraw.Draw(self.background)
        pos_prior = -inf

        file_map = self.landscape.terrain_map.get(file, {})
        if inf not in file_map:
            file_map[inf] = DEFAULT_TERRAIN

        for pos, terrain in file_map.items():
            top = self.get_coords(file-0.5, max(pos_prior, self.min_pos))
            bot = self.get_coords(file+0.5, min(pos, self.max_pos))
            draw.rectangle((*top, *bot), fill=terrain.color)
            pos_prior = pos

    def draw_background_contours(self) -> None:
        buffer = self.plot_contour_graph()
        self.draw_contour_graph_on_background(buffer)

    def plot_contour_graph(self) -> BytesIO:
        X, Y, h = self.make_vectors_for_contour_graph()
        levels = np.arange(np.min(h), np.max(h), 1)

        fig, ax = plt.subplots(frameon=False)
        ax.set_axis_off()
        fig.tight_layout()
        ax.contour(X, Y, h, colors="DimGray", linestyles="dotted", levels=levels)
        # fig.show()

        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        return buffer

    def make_vectors_for_contour_graph(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        x = np.arange(self.min_file-0.5, self.max_file+0.5, 0.05)
        y = np.arange(self.min_pos, self.max_pos, 0.05)
        X, Y = np.meshgrid(x, y)
        h = np.vectorize(self.landscape.get_height)(X, Y)
        return X, Y, h

    def draw_contour_graph_on_background(self, buffer: BytesIO) -> None:
        plot_img = Image.open(buffer)

        left, top = self.get_coords(self.min_file-0.5, self.min_pos)
        right, bot = self.get_coords(self.max_file+0.5, self.max_pos)
        plot_img = plot_img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        plot_img = plot_img.resize((int(right-left), int(bot-top)))
        self.background.paste(plot_img, (int(left), int(top)), plot_img)

    def draw_background_height_labels(self) -> None:
        draw = ImageDraw.Draw(self.background)
        for (file, pos), height in self.landscape.height_map.items():
            if self.min_pos <= pos <= self.max_pos:
                x, y = self.get_coords(file, pos)
                draw.text((x, y), f"{height}", fill="Black", font_size=self.font_size, anchor="mm")

    # FRAME
    def draw_frame(self, army_1: Army, army_2: Army, fights: list[Fight], reps: int = 1) -> None:
        self.canvas = Image.new(mode="RGBA", size=self.croped_res, color="White")
        self.canvas.paste(self.background, (0, 0))

        self.draw_battle_in_frame(army_1, army_2, fights)

        if Config.FRAME_COUNTER:
            ImageDraw.Draw(self.canvas).text((5, 5), f" {len(self.frames)}",
                                             font_size=self.font_size+8, fill="Black", anchor="lt")

        for _ in range(reps):
            self.frames.append(self.canvas)

    def draw_battle_in_frame(self, army_1: Army, army_2: Army, fights: list[Fight]) -> None:
        self.draw_all_deployed_units(army_1, army_2)
        self.draw_army_removed_units(army_1)
        self.draw_army_removed_units(army_2)
        self.draw_army_reserve_units(army_1)
        self.draw_army_reserve_units(army_2)

        for fight in fights:
            self.draw_fight(fight)

    def draw_all_deployed_units(self, army_1: Army, army_2: Army) -> None:
        for unit in chain(army_1.deployed_units, army_2.deployed_units):
            widths = self.get_line_width(unit, -1), self.get_line_width(unit, +1)
            image = self.draw_unit_image(unit, unit.army.color, widths)
            self.paste_unit_image(image, unit.file, unit.position)

    def draw_army_removed_units(self, army: Army) -> None:
        # Prevents multiple removed units being drawn on top of each other
        present: set[int] = set()
        for unit in reversed(army.removed):
            if unit.file not in present:
                present.add(unit.file)

                image = self.draw_unit_image(unit, "Gray", (FILE_EMPTY, FILE_EMPTY))
                position = unit.army.init_position - 0.01  # offset needed because of rouning errors
                position += 2 if position > 0 else -2
                self.paste_unit_image(image, unit.file, position)

    def draw_army_reserve_units(self, army: Army) -> None:
        for slot, unit in enumerate(reversed(army.reserves)):
            image = self.draw_unit_image(unit, unit.army.color, (FILE_EMPTY, FILE_EMPTY),
                                         bkgd="White")
            position = unit.army.init_position
            position += (1.0 + slot/5) if position > 0 else -(1.0 + slot/5)
            file = (self.min_file + self.max_file) / 2
            self.paste_unit_image(image, file, position)

    def draw_unit_image(self, unit: Unit, color: str, widths: tuple[float, float],
                        bkgd: str | tuple[int, int, int, int] = (255, 255, 255, 64)) -> Image.Image:
        x, y = self.pixels_unit
        image = Image.new(mode="RGBA", size=(int(x+1), int(y+2)), color=bkgd)
        draw = ImageDraw.Draw(image)
        
        # Draw Rectangle
        draw.line([(1, 1), (x-1, 1)], fill=color, width=2)  # Top
        draw.line([(1, y), (x-1, y)], fill=color, width=2)  # Bottom
        draw.line([(1, 1), (1, y)], fill=color, width=widths[0])  # Left
        draw.line([(x-1, 1), (x-1, y)], fill=color, width=widths[1])  # Right
        
        # Draw Text
        string = f"{unit.name} {100*unit.morale:.0f}%: {unit.get_eff_power():.0f}"
        draw.text((x//2, y//2), string, fill=color, font_size=self.font_size, anchor="mm")

        return image

    def paste_unit_image(self, image: Image.Image, file: float, position: float) -> None:
        centre_x, centre_y = self.get_coords(file, position)
        coord = (centre_x - self.pixels_unit[0]//2, centre_y - self.pixels_unit[1]//2)
        self.canvas.paste(image, (int(coord[0]), int(coord[1])), image)

    def draw_fight(self, fight: Fight) -> None:
        pos_A = list(self.get_coords(fight.unit_A.file, fight.unit_A.position))
        pos_B = list(self.get_coords(fight.unit_B.file, fight.unit_B.position))
        self.adjust_line_end_points(pos_A, pos_B)

        color = self.get_fight_color(fight)
        ImageDraw.Draw(self.canvas).line([*pos_A, *pos_B], fill=color, width=3)

        self.draw_arrowhead(pos_B, pos_A, color)
        if isinstance(fight, TwoWayFight):
            self.draw_arrowhead(pos_A, pos_B, color)

    def adjust_line_end_points(self, pos_A: list[float], pos_B: list[float]) -> None:
        x_offset = self.pixel_per_pos * ATTACK_LINE_OFFSET
        y_offset = FILE_WIDTH/2 * (1-ATTACK_LINE_OFFSET) * self.pixel_per_pos

        if pos_A[0] == pos_B[0] or abs(pos_A[1] - pos_B[1]) > self.pixel_per_pos:
            if pos_A[1] > pos_B[1]:
                pos_A[1] -= x_offset
                pos_B[1] += x_offset
            elif pos_A[1] < pos_B[1]:
                pos_A[1] += x_offset
                pos_B[1] -= x_offset
        else:
            if pos_A[0] > pos_B[0]:
                pos_A[0] -= y_offset
            elif pos_A[0] < pos_B[0]:
                pos_A[0] += y_offset

        if pos_A[0] > pos_B[0]:
            pos_B[0] += y_offset
        elif pos_A[0] < pos_B[0]:
            pos_B[0] -= y_offset

    def draw_arrowhead(self, pos: list[float], origin: list[float], color: tuple[int, int, int, int]
                       ) -> None:
        vec = pos[0] - origin[0], pos[1] - origin[1]
        norm_len = self.pixel_per_pos * ARROWHEAD_SIZE / sqrt(vec[0]**2 + vec[1]**2)

        back_step = vec[0]*norm_len, vec[1]*norm_len
        side_step = -vec[1]*norm_len/2, vec[0]*norm_len/2

        pos_2 = pos[0] - back_step[0] + side_step[0], pos[1] - back_step[1] + side_step[1]
        pos_3 = pos[0] - back_step[0] - side_step[0], pos[1] - back_step[1] - side_step[1]

        ImageDraw.Draw(self.canvas).polygon([*pos, *pos_2, *pos_3], fill=color)


@define
class GraphicBattle(Battle):
    """Same as parent, but draws a frame every turn and then saves them as a gif"""

    max_screen: tuple[int, int]
    gif_name: str
    battle_scene: BattleScene = field(init=False)

    def __attrs_post_init__(self) -> None:
        super().__attrs_post_init__()
        self.set_up_battle_scene()

    def set_up_battle_scene(self) -> None:
        min_file = min(min(self.army_1.file_units), min(self.army_2.file_units))
        max_file = max(max(self.army_1.file_units), max(self.army_2.file_units))
        min_pos = self.army_1.init_position - 0.5  # Space for physical size of starting units
        max_pos = self.army_2.init_position + 0.5
        self.battle_scene = \
            BattleScene(self.max_screen, self.landscape, min_file, max_file, min_pos, max_pos)

    def do_turn(self, verbosity: int) -> None:
        super().do_turn(verbosity)
        self.battle_scene.draw_frame(self.army_1, self.army_2, self.curr_fights)

    def do(self, verbosity: int) -> None:
        super().do(verbosity)
        frames = self.battle_scene.frames

        self.battle_scene.draw_frame(self.army_1, self.army_2, [], reps=len(frames)//10)
        time = max(40, 12000/len(frames))

        frames[0].save(self.gif_name+".gif", save_all=True, append_images=frames[1:], duration=time,
                       loop=True)

        print(f"Animation saved to {self.gif_name}")

    def do_to_buffer(self) -> BytesIO:
        # Version of above useful for integrating into pyscript and displaying in browser
        super().do(0)

        frames = self.battle_scene.frames
        self.battle_scene.draw_frame(self.army_1, self.army_2, [], reps=len(frames)//10)
        time = max(40, 12000/len(frames))

        stream = BytesIO()
        frames[0].save(stream, format="GIF", save_all=True, append_images=frames[1:],
                       duration=time, loop=True)
        return stream
