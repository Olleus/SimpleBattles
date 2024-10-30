"""Wrapper around Battle to display battles graphically as a series of PIL.Image frames"""
from io import BytesIO
from math import atan2, inf, sqrt, pi

import matplotlib.pyplot as plt
import numpy as np
from attrs import define, Factory, field
from PIL import Image, ImageColor, ImageDraw

from Config import FRAME_COUNTER, FRAME_MS
from Battle import Battle
from Geography import DEFAULT_TERRAIN, Landscape
from Globals import FILE_WIDTH, Stance, BattleOutcome
from Unit import Army, Unit

# Visual constants
UNIT_FILE_WIDTH: float = 0.95    # Width of unit relative to file
STANCE_ICON_FRAC: float = 1 / 7  # Size of the Stance icon relative to unit size
FONT_SIZE_FRAC: float = 0.45     # Font size relative to unit pixel height
HALF_ARROWHEAD_SIZE: int = 5     # Size of fight arrowhead in pixels
BORDER_WIDTH: int = 2            # Width of lines forming unit rectangles
ARROW_WIDTH: int = 3             # Width of lines for fight arrows


@define
class Scene:
    """Contains a list of frames showing the battle, along with methods for drawing them"""
    max_pixels_x: int
    landscape: Landscape
    min_file: int
    max_file: int
    min_pos: float
    max_pos: float

    drawn_file_width: float = field(init=False)
    pixel_per_pos: float = field(init=False)
    pixel_per_file: float = field(init=False)
    pixels_unit: tuple[int, int] = field(init=False)
    croped_res: tuple[int, int] = field(init=False)
    font_size: int = field(init=False)

    background: Image.Image = field(init=False, default=None)
    canvas: Image.Image = field(init=False, default=None)
    frames: list[Image.Image] = field(init=False, default=Factory(list))

    def __attrs_post_init__(self) -> None:
        num_files = 1 + self.max_file - self.min_file  # Count files, not gaps
        num_pos = 4 + self.max_pos - self.min_pos      # Including space for reserves and dead
        
        # Use "true" file width, but scale to prevent aspect ratio greater than 1x1
        if FILE_WIDTH * num_files > num_pos:
            self.drawn_file_width = FILE_WIDTH
            self.pixel_per_file = self.max_pixels_x / num_files
            self.pixel_per_pos = self.pixel_per_file / self.drawn_file_width
        else:
            self.drawn_file_width = min(num_pos / num_files, 10)
            self.pixel_per_pos = self.max_pixels_x / num_pos
            self.pixel_per_file = self.pixel_per_pos * self.drawn_file_width

        if self.drawn_file_width < 6.5:
            self.font_size = int(self.pixel_per_pos * FONT_SIZE_FRAC)
        else:
            self.font_size = int(self.pixel_per_file * FONT_SIZE_FRAC / 7)

        self.pixels_unit = int(UNIT_FILE_WIDTH * self.pixel_per_file), int(self.pixel_per_pos)
        self.croped_res = int(self.pixel_per_file * num_files), int(self.pixel_per_pos * num_pos)
        
        self.draw_background()

    # GETTERS
    def get_coords(self, file: float, pos: float) -> tuple[float, float]:
        """Pixel position of a point in the middle of the given file at the given position.
        Returns ints in float type for ease of vector manipulations in other methods"""
        file_steps = 0.5 + file - self.min_file
        pos_steps = 2 + pos - self.min_pos
        return int(file_steps * self.pixel_per_file), int(pos_steps * self.pixel_per_pos)

    def blend_colors(self, color_1: str, color_2: str) -> tuple[int, ...]:
        c1 = ImageColor.getrgb(color_1)
        c2 = ImageColor.getrgb(color_2)
        return tuple((c1[i]+c2[i]) // 2 for i in range(3))

    # BACKGROUND
    def draw_background(self) -> None:
        self.background = Image.new(mode="RGBA", size=self.croped_res, color="Gainsboro")

        for file in range(self.min_file, self.max_file + 1):
            self.draw_background_file(file)

        buffer = self.plot_contour_graph()
        self.draw_contour_graph_on_background(buffer)
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

    def plot_contour_graph(self) -> BytesIO:
        X, Y, h = self.make_vectors_for_contour_graph()
        levels = np.arange(np.min(h), np.max(h), 1)
        if len(levels) <= 4:
            levels = np.arange(np.min(h), np.max(h), 0.5)

        fig, ax = plt.subplots(frameon=False)
        ax.set_axis_off()
        fig.tight_layout()
        ax.contour(X, Y, h, colors="DimGray", linestyles="dotted", levels=levels)

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
        plot_img2 = plot_img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        plot_img3 = plot_img2.resize((int(right-left), int(bot-top)))
        self.background.paste(plot_img3, (int(left), int(top)), plot_img3)

    def draw_background_height_labels(self) -> None:
        draw = ImageDraw.Draw(self.background)
        for (file, pos), height in self.landscape.height_map.items():
            if self.min_pos <= pos <= self.max_pos:
                x, y = self.get_coords(file, pos)
                draw.text((x, y), f"{height}", fill="Black", font_size=self.font_size, anchor="mm")

    # FRAME
    def init_draw_frame(self) -> None:
        self.canvas = Image.new(mode="RGBA", size=self.croped_res, color="White")
        self.canvas.paste(self.background, (0, 0))

    def fini_draw_frame(self) -> None:
        if FRAME_COUNTER:
            ImageDraw.Draw(self.canvas).text((5, 5), f" {len(self.frames)}",
                                             font_size=self.font_size+8, fill="Black", anchor="lt")
        self.frames.append(self.canvas)

    def draw_unit_image(self, unit: Unit, color: str, pow_mod: float, morale: float,
                        bkgd_color=(255, 255, 255, 64)) -> Image.Image:
        x, y = self.pixels_unit
        image = Image.new(mode="RGBA", size=(x+1, y+1), color=bkgd_color)
        draw = ImageDraw.Draw(image)

        draw.rectangle((0, 0, x, y), outline=color, width=BORDER_WIDTH)
        
        self.draw_unit_text(draw, x, y, unit, color, pow_mod, morale)
        self.draw_stance_poligon(draw, unit, color)
        return image

    def draw_unit_text(self, draw: ImageDraw.ImageDraw, x: float, y: float, unit: Unit, color: str,
                       pow_mod: float, morale: float) -> None:
        small = self.font_size - int(0.15*self.font_size)
        name = f"{unit.name} {100*morale:.0f}%"
        str_m = f"{unit.power + pow_mod:.0f} M"
        str_r = f"{unit.pow_range + pow_mod:.0f} R" if (unit.ranged or unit.mixed) else ""

        if self.drawn_file_width < 6.5:  # Power in a column fits better when squarish
            draw.text((x//2, y//2), name+" "*6, fill=color, font_size=self.font_size, anchor="mm")
            draw.text((x-3, 4), str_m, fill=color, font_size=small, anchor="rt")
            if str_r:
                draw.text((x-4, y-4), str_r, fill=color, font_size=small, anchor="rb")

        else:  # Everything in one line fits better when long and skinny
            draw.text((x//3, y//2), name, fill=color, font_size=self.font_size, anchor="mm")
            draw.text((x-4, y//2), str_m+" "+str_r, fill=color, font_size=small, anchor="rm")

    def draw_stance_poligon(self, draw: ImageDraw.ImageDraw, unit: Unit, color: str) -> None:
        r = self.pixel_per_pos * STANCE_ICON_FRAC
        if unit.stance is Stance.AGG:
            draw.regular_polygon((3+r, 3+r, r), 3, rotation=60, fill=color, width=0)
        elif unit.stance is Stance.BAL:
            draw.regular_polygon((3+r, 3+r, r), 4, fill=color, width=0)
        elif unit.stance is Stance.DEF:
            draw.regular_polygon((4+r, 4+r, r), 6, fill=color, width=0)

    def paste_unit_image(self, image: Image.Image, file: float | None, position: float) -> None:
        file = (self.min_file + self.max_file) / 2 if file is None else file
        centre_x, centre_y = self.get_coords(file, position)
        coord = int(centre_x - self.pixels_unit[0]/2), int(centre_y - self.pixels_unit[1]/2)
        self.canvas.paste(image, coord, image)

    def draw_fight(self, unit_A: Unit, unit_B: Unit, color: str | tuple[int, ...], both: bool
                   ) -> None:
        pos_A = list(self.get_coords(unit_A.file, unit_A.position))
        pos_B = list(self.get_coords(unit_B.file, unit_B.position))
        self.adjust_line_end_points(pos_A, pos_B)
        self.draw_aa_arrow(pos_A, pos_B, color, both)

    def adjust_line_end_points(self, pos_A: list[float], pos_B: list[float]) -> None:
        close = abs(pos_A[1] - pos_B[1]) <= 0.75 * self.pixel_per_pos

        y_step = 0.2 * self.pixels_unit[1]
        if pos_A[0] == pos_B[0] or not close:
            if pos_A[1] > pos_B[1]:
                pos_A[1] -= y_step
                pos_B[1] += y_step
            elif pos_A[1] < pos_B[1]:
                pos_A[1] += y_step
                pos_B[1] -= y_step

        x_step = (0.45*self.pixels_unit[0]) if close else (0.3*self.pixels_unit[0])
        if pos_A[0] > pos_B[0]:
            pos_A[0] -= x_step
            pos_B[0] += x_step
        elif pos_A[0] < pos_B[0]:
            pos_A[0] += x_step
            pos_B[0] -= x_step

    def draw_aa_arrow(self, start: list[float], end: list[float], color: str | tuple[int, ...],
                      both: bool = False) -> None:
        """Uses existing anti-aliasing by drawing a horizontal line, then rotating it to position"""
        # COMPUTE
        vec = end[0] - start[0], end[1] - start[1]
        length = sqrt(vec[0]**2 + vec[1]**2)
        angle = -atan2(vec[1], vec[0]) * 180 / pi
        half_arrow = min(HALF_ARROWHEAD_SIZE, int(length/4))  # Prevents overlap

        # DRAW
        image = Image.new(mode="RGBA", size=(int(length), 2*half_arrow))
        draw = ImageDraw.Draw(image)
        draw.polygon([length, half_arrow,
                      length-2*half_arrow, 0,
                      length-2*half_arrow, 2*half_arrow], fill=color)
        if both:
            draw.polygon([0, half_arrow,
                          2*half_arrow, 0,
                          2*half_arrow, 2*half_arrow], fill=color)
            line_coords = [half_arrow, half_arrow, length-half_arrow, half_arrow]
        else:
            line_coords = [0, half_arrow, length-half_arrow, half_arrow]

        draw.line(line_coords, fill=color, width=ARROW_WIDTH)

        # PASTE
        rotated = image.rotate(angle, resample=Image.Resampling.BILINEAR, expand=True)
        left = min(start[0], end[0])
        top = min(start[1], end[1])
        self.canvas.paste(rotated, (int(left), int(top)), rotated)


@define
class GraphicBattle(Battle):
    """Same as parent, but draws a frame every turn and then saves them as a gif
        GOOD PRACTICE TO CALL GARBAGE COLLECTOR - gc.collect(2) -
        AFTER CLASS IS DONE TO FREE UP MEMORY BALER"""
    max_pixels_x: int
    gif_name: str
    scene: Scene = field(init=False)

    def __attrs_post_init__(self) -> None:
        super().__attrs_post_init__()
        self.set_up_scene()

    def set_up_scene(self) -> None:
        min_file = min(min(self.army_1.file_units), min(self.army_2.file_units))
        max_file = max(max(self.army_1.file_units), max(self.army_2.file_units))
        # Allowing space for physical size of starting units
        min_pos = min(x.init_pos for x in self.army_1.file_units.values()) - 0.5
        max_pos = max(x.init_pos for x in self.army_2.file_units.values()) + 0.5
        self.scene = Scene(self.max_pixels_x, self.landscape, min_file, max_file, min_pos, max_pos)

    def do_turn(self, verbosity: int) -> None:
        super().do_turn(verbosity)
        self.draw_frame()

    def draw_frame(self) -> None:
        self.scene.init_draw_frame()

        for army in (self.army_1, self.army_2):
            self.draw_deployed_units(army)
            self.draw_removed_units(army)
            self.draw_reserve_units(army)

        for unit_A, unit_B in self.fight_pairs.two_way_pairs:
            color = self.scene.blend_colors(self.army_1.color, self.army_2.color)
            self.scene.draw_fight(unit_A, unit_B, color, True)

        for unit_A, unit_B in self.fight_pairs.one_way_pairs:
            color_name = self.get_army_deployed_in(unit_A).color
            self.scene.draw_fight(unit_A, unit_B, color_name, False)

        self.scene.fini_draw_frame()

    def draw_deployed_units(self, army: Army) -> None:
        for unit in army.deployed_units:
            power_mods = self.get_power_mods(unit)
            morale = self.get_eff_morale(unit)
            image = self.scene.draw_unit_image(unit, army.color, power_mods, morale)
            self.scene.paste_unit_image(image, unit.file, unit.position)

    def draw_removed_units(self, army: Army) -> None:
        # Prevents multiple removed units being drawn on top of each other
        present: set[int] = set()
        for unit in reversed(army.removed):
            if unit.file not in present:
                present.add(unit.file)
                image = self.scene.draw_unit_image(unit, "Gray", 0, unit.morale)
                position = unit.init_pos + (2 if unit.init_pos > 0 else -1.95)
                self.scene.paste_unit_image(image, unit.file, position)

    def draw_reserve_units(self, army: Army) -> None:
        for slot, unit in enumerate(reversed(army.reserves)):
            image = self.scene.draw_unit_image(unit, army.color, 0, unit.morale, bkgd_color="White")
            position = unit.init_pos
            position += (1.0 + slot/5) if position > 0 else -(1.0 + slot/5)
            self.scene.paste_unit_image(image, None, position)

    def do(self, verbosity: int) -> BattleOutcome:
        self.draw_frame()
        winner = super().do(verbosity)
        frames = self.make_padding_frames()

        # loop=0 makes gif loop better on some platforms, even if not needed for others
        frames[0].save(self.gif_name+".gif", save_all=True, append_images=frames[1:],
                       duration=FRAME_MS, loop=0)
        if verbosity > 0:
            print(f"Animation saved to {self.gif_name}")
        return winner

    def do_to_buffer(self) -> BytesIO:
        # Version of above useful for integrating into pyscript and displaying in browser
        self.draw_frame()
        super().do(0)
        frames = self.make_padding_frames()

        stream = BytesIO()
        # loop=0 makes gif loop better on some platforms, even if not needed for others
        frames[0].save(stream, format="GIF", save_all=True, append_images=frames[1:],
                       duration=FRAME_MS, loop=0)
        return stream

    def make_padding_frames(self) -> list[Image.Image]:
        self.fight_pairs.reset()
        self.draw_frame()
        return [self.scene.frames[0]]*30 + self.scene.frames + [self.scene.frames[-1]]*60
