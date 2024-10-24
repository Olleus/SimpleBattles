"""Wrapper around Battle to display battles graphically as a series of PIL.Image frames"""
from io import BytesIO
from math import inf, sqrt

import matplotlib.pyplot as plt
import numpy as np
from attrs import define, Factory, field
from PIL import Image, ImageColor, ImageDraw

from Config import FRAME_COUNTER, FRAME_MS
from Battle import Battle
from Geography import DEFAULT_TERRAIN, Landscape
from Globals import FILE_WIDTH, FILE_EMPTY, FILE_SUPPORTED, FILE_VULNERABLE, Stance, BattleOutcome
from Unit import Army, Unit

UNIT_FILE_WIDTH: float = 0.95
ATTACK_LINE_OFFSET: float = 0.2
ARROWHEAD_SIZE: float = 0.2
STANCE_ICON_FRAC: float = 1 / 7


@define
class Scene:
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
        num_pos = 4 + self.max_pos - self.min_pos      # Including space for reserves and dead
        
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
        self.font_size = int(self.pixel_per_pos / 2.2)  # Allows text to fit nicely in unit rect

        self.draw_background()

    # GETTERS
    def get_coords(self, file: float, pos: float) -> tuple[float, float]:
        """Pixel position of a point in the middle of the given file at the given position"""
        """Returns ints in float type for ease of vector manipulations later"""
        file_steps = 0.5 + file - self.min_file
        pos_steps = 2 + pos - self.min_pos
        return int(file_steps * self.pixel_per_file), int(pos_steps * self.pixel_per_pos)

    def get_line_width(self, morale_gain: float) -> int:
        if morale_gain >= FILE_SUPPORTED:
            return 4
        elif morale_gain > 0:
            return 3
        elif morale_gain == FILE_EMPTY:
            return 2
        elif morale_gain > FILE_VULNERABLE:
            return 1
        else:
            return 0

    def get_blended_color(self, color_1: str, color_2: str) -> tuple[int, ...]:
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
        if len(levels) <= 3:
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
        del self.canvas

    def draw_unit_image(self, unit: Unit, color: str, flanks: tuple[float, float],
                        power: float, morale: float, bkgd_color=(255, 255, 255, 64)) -> Image.Image:
        x, y = self.pixels_unit
        image = Image.new(mode="RGBA", size=(int(x+2), int(y+2)), color=bkgd_color)
        draw = ImageDraw.Draw(image)

        # Draw Rectangle
        draw.line([(1, 1), (x-1, 1)], fill=color, width=2)
        draw.line([(1, y), (x-1, y)], fill=color, width=2)
        draw.line([(1, 1), (1, y)], fill=color, width=int(self.get_line_width(flanks[0])))
        draw.line([(x-1, 1), (x-1, y)], fill=color, width=int(self.get_line_width(flanks[1]))) 
        
        # Draw Text
        string = f"{unit.name} {100*morale:.0f}% ({power:.0f})"
        draw.text((x//2, y//2), string, fill=color, font_size=self.font_size, anchor="mm")

        # Draw Stance
        self.draw_stance_poligon(draw, unit, color)
        return image

    def draw_stance_poligon(self, draw: ImageDraw.ImageDraw, unit: Unit, color: str) -> None:
        r = self.pixel_per_pos * STANCE_ICON_FRAC

        if unit.stance is Stance.AGGR:
            draw.regular_polygon((4+r, 2+r, r), 3, rotation=60, fill=color, width=0)
        elif unit.stance is Stance.NEUT:
            draw.regular_polygon((4+r, 2+r, r), 4, fill=color, width=0)
        elif unit.stance is Stance.DEFN:
            draw.regular_polygon((4+r, 4+r, r), 6, fill=color, width=0)

    def paste_unit_image(self, image: Image.Image, file: float | None, position: float) -> None:
        file = (self.min_file + self.max_file) / 2 if file is None else file
        centre_x, centre_y = self.get_coords(file, position)
        coord = (centre_x - self.pixels_unit[0]//2, centre_y - self.pixels_unit[1]//2)
        self.canvas.paste(image, (int(coord[0]), int(coord[1])), image)

    def draw_fight(self, unit_A: Unit, unit_B: Unit, color: str | tuple[int, ...], both: bool
                   ) -> None:
        pos_A = list(self.get_coords(unit_A.file, unit_A.position))
        pos_B = list(self.get_coords(unit_B.file, unit_B.position))
        self.adjust_line_end_points(pos_A, pos_B)

        ImageDraw.Draw(self.canvas).line([*pos_A, *pos_B], fill=color, width=3)

        self.draw_arrowhead(pos_B, pos_A, color)
        if both:
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

    def draw_arrowhead(self, pos: list[float], origin: list[float], color: str | tuple[int, ...]
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
    """Same as parent, but draws a frame every turn and then saves them as a gif
        GOOD PRACTICE TO CALL GARBAGE COLLECTOR - gc.collect(2) -
        AFTER CLASS IS DONE TO FREE UP MEMORY NEUTER"""
    max_screen: tuple[int, int]
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
        self.scene = Scene(self.max_screen, self.landscape, min_file, max_file, min_pos, max_pos)

    def do_turn(self, verbosity: int) -> None:
        super().do_turn(verbosity)
        self.draw_frame()

    def draw_frame(self) -> None:
        self.scene.init_draw_frame()

        self.draw_deployed_units(self.army_1)
        self.draw_deployed_units(self.army_2)
        self.draw_removed_units(self.army_1)
        self.draw_removed_units(self.army_2)
        self.draw_reserve_units(self.army_1)
        self.draw_reserve_units(self.army_2)

        for unit_A, unit_B in self.fight_pairs.two_way_pairs:
            color = self.scene.get_blended_color(self.army_1.color, self.army_2.color)
            self.scene.draw_fight(unit_A, unit_B, color, True)

        for unit_A, unit_B in self.fight_pairs.one_way_pairs:
            color_name = self.get_army_deployed_in(unit_A).color
            self.scene.draw_fight(unit_A, unit_B, color_name, False)

        self.scene.fini_draw_frame()

    def draw_deployed_units(self, army: Army) -> None:
        for unit in army.deployed_units:
            power = self.get_max_eff_power(unit)
            morale = self.get_eff_morale(unit)
            flanks = (self.get_morale_from_supporting_file(unit, unit.file - 1),
                      self.get_morale_from_supporting_file(unit, unit.file + 1))
            image = self.scene.draw_unit_image(unit, army.color, flanks, power, morale)
            self.scene.paste_unit_image(image, unit.file, unit.position)

    def draw_removed_units(self, army: Army) -> None:
        # Prevents multiple removed units being drawn on top of each other
        present: set[int] = set()
        for unit in reversed(army.removed):
            if unit.file not in present:
                present.add(unit.file)

                image = self.scene.draw_unit_image(unit, "Gray", (FILE_EMPTY, FILE_EMPTY),
                                                   unit.power, unit.morale)
                position = unit.init_pos - 0.01  # offset needed because of rouning errors
                position += 2 if position > 0 else -2
                self.scene.paste_unit_image(image, unit.file, position)

    def draw_reserve_units(self, army: Army) -> None:
        for slot, unit in enumerate(reversed(army.reserves)):
            image = self.scene.draw_unit_image(unit, army.color, (FILE_EMPTY, FILE_EMPTY),
                                               unit.power, unit.morale, bkgd_color="White")
            position = unit.init_pos
            position += (1.0 + slot/5) if position > 0 else -(1.0 + slot/5)
            self.scene.paste_unit_image(image, None, position)

    def do(self, verbosity: int) -> BattleOutcome:
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
