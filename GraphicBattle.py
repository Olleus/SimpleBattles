import math

from attrs import define, Factory, field
from PIL import Image, ImageColor, ImageDraw

from Battle import FILE_WIDTH, FILE_EMPTY, FILE_VULNERABLE, FILE_SUPPORTED, DEFAULT_TERRAIN, \
                   Landscape, Unit, Fight, OneWayFight, Battle


UNIT_FILE_WIDTH: float = 0.95
ATTACK_LINE_OFFSET: float = 0.2
ARROWHEAD_SIZE: float = 0.2


@define
class BattleScene:
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

    background: Image.Image = field(init=False, default=None)
    canvas: Image.Image = field(init=False, default=None)
    frames: list[Image.Image] = field(init=False, default=Factory(list))

    def __attrs_post_init__(self) -> None:
        # Count files, not gaps
        file_pixel_width = self.max_screen[0] / (1 + self.max_file - self.min_file)
        # Inc fleeing row
        pos_pixel_height = self.max_screen[0] / (2 + self.max_pos - self.min_pos)

        if pos_pixel_height * FILE_WIDTH < file_pixel_width:
            self.pixel_per_pos = pos_pixel_height
            self.pixel_per_file = self.pixel_per_pos * FILE_WIDTH
        else:
            self.pixel_per_pos = file_pixel_width / FILE_WIDTH
            self.pixel_per_file = file_pixel_width

        self.pixels_unit = UNIT_FILE_WIDTH * self.pixel_per_file, self.pixel_per_pos

        self.croped_res = (int(self.pixel_per_file * (1 + self.max_file - self.min_file)),
                           int(self.pixel_per_pos * (2 + self.max_pos - self.min_pos)))

        self.draw_background()

    def coord_position(self, file: float, pos: float) -> tuple[float, float]:
        """Pixel position of a point in the middle of the given file at the given position"""
        file_steps = 0.5 + file - self.min_file
        pos_steps = 1 + pos - self.min_pos
        return int(file_steps * self.pixel_per_file), int(pos_steps * self.pixel_per_pos)

    def draw_background(self) -> None:
        self.background = Image.new(mode="RGBA", size=self.croped_res, color="Gainsboro")

        for file in range(self.min_file, self.max_file + 1):
            self.draw_background_file(file)

    def draw_background_file(self, file: int) -> None:
        draw = ImageDraw.Draw(self.background)
        pos_prior = -math.inf

        file_map = self.landscape.terrain_map.get(file, {})
        if math.inf not in file_map:
            file_map[math.inf] = DEFAULT_TERRAIN

        for pos, terrain in file_map.items():
            top = self.coord_position(file-0.5, max(pos_prior, self.min_pos))
            bot = self.coord_position(file+0.5, min(pos, self.max_pos))
            draw.rectangle((*top, *bot), fill=terrain.color)
            pos_prior = pos

        # for pos, terrain in file_map:
        #     pos_top = self.min_pos if pos_prior < self.min_pos else (pos + pos_prior) / 2
        #     pos_prior = pos
        #     draw.rectangle((*self.coord_position(file-0.5, pos_top), *corner), fill=terrain.color)

    def draw_frame(self, units: list[Unit], fights: list[Fight], reps: int = 1) -> None:
        self.draw_fresh_canvas()

        for unit in units:
            self.draw_unit(unit)

        for fight in fights:
            self.draw_fight(fight)

        for _ in range(reps):
            self.frames.append(self.canvas)

    def draw_fresh_canvas(self) -> None:
        self.canvas = Image.new(mode="RGBA", size=self.croped_res, color="white")
        self.canvas.paste(self.background, (0, 0))

        ImageDraw.Draw(self.canvas).text(
                            (0, 5), f" {len(self.frames)}", font_size=24, fill="black", anchor="lt")

    def draw_unit(self, unit: Unit) -> None:
        # Preliminaries
        x, y = self.pixels_unit
        image = Image.new(mode="RGBA", size=(int(x+1), int(y+2)))
        draw = ImageDraw.Draw(image)
        color = "Gray" if unit.defeated else unit.army.color
        
        # Draw Rectangle
        draw.line([(1, 1), (x-1, 1)], fill=color, width=2)  # Top
        draw.line([(1, y), (x-1, y)], fill=color, width=2)  # Bottom
        draw.line([(1, 1), (1, y)], fill=color, width=self.unit_width(unit, -1))  # Left
        draw.line([(x-1, 1), (x-1, y)], fill=color, width=self.unit_width(unit, +1))  # Right
        
        # Draw Text
        string = f"{unit.name} ({unit.eff_power():.0f}) {100*unit.morale:.0f}%"
        draw.text((x//2, y//2), string, fill=color, font_size=14, anchor="mm")

        self.paste_unit(unit, image)

    def unit_width(self, unit: Unit, side: int) -> int:
        # Change line thickness on edge of unit rectangle depanding on state of flanks
        if unit.defeated:
            return 2

        state = unit.army.file_state(unit.file + side, unit.position)
        if state == FILE_EMPTY:
            return 2
        elif state == FILE_VULNERABLE:
            return 1
        elif state == FILE_SUPPORTED:
            return 3
        else:
            raise RuntimeError("Unexpected value for unit.army.file_state()")

    def paste_unit(self, unit: Unit, image: Image.Image) -> None:
        if unit.defeated:
            position = unit.army.init_position
            position += 1 if position > 0 else -1
        else:
            position = unit.position

        centre_x, centre_y = self.coord_position(unit.file, position)
        coord = (centre_x - self.pixels_unit[0]//2, centre_y - self.pixels_unit[1]//2)
        self.canvas.paste(image, (int(coord[0]), int(coord[1])), image)

    def draw_fight(self, fight: Fight) -> None:
        pos_A = list(self.coord_position(fight.unit_A.file, fight.unit_A.position))
        pos_B = list(self.coord_position(fight.unit_B.file, fight.unit_B.position))
        self.adjust_line_end_points(pos_A, pos_B)

        color = self.fight_color(fight)
        ImageDraw.Draw(self.canvas).line([*pos_A, *pos_B], fill=color, width=3)

        self.draw_arrowhead(pos_B, pos_A, color)
        if not isinstance(fight, OneWayFight):
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

    def fight_color(self, fight: Fight):
        if isinstance(fight, OneWayFight):
            return ImageColor.getcolor(fight.unit_A.army.color, mode="RGBA")
        else:
            cA = ImageColor.getcolor(fight.unit_A.army.color, mode="RGBA")
            cB = ImageColor.getcolor(fight.unit_B.army.color, mode="RGBA")
            return tuple((cA[j]+cB[j]) // 2 for j in range(4))

    def draw_arrowhead(self, pos: list[float], origin: list[float], color: tuple[int, int, int, int]
                       ) -> None:
        vec = pos[0] - origin[0], pos[1] - origin[1]
        norm_len = self.pixel_per_pos * ARROWHEAD_SIZE / math.sqrt(vec[0]**2 + vec[1]**2)

        back_step = vec[0]*norm_len, vec[1]*norm_len
        side_step = -vec[1]*norm_len/2, vec[0]*norm_len/2

        pos_2 = pos[0] - back_step[0] + side_step[0], pos[1] - back_step[1] + side_step[1]
        pos_3 = pos[0] - back_step[0] - side_step[0], pos[1] - back_step[1] - side_step[1]

        ImageDraw.Draw(self.canvas).polygon([*pos, *pos_2, *pos_3], fill=color)


@define
class GraphicBattle(Battle):
    """Same as parent, but draws a frame every turn and then animates them"""
    max_screen: tuple[int, int]
    gif_name: str
    battle_scene: BattleScene = field(init=False)

    def __attrs_post_init__(self) -> None:
        super().__attrs_post_init__()
        self.set_up_battle_scene()

    def set_up_battle_scene(self) -> None:
        min_file = min(min(self.army_1.file_units), min(self.army_2.file_units))
        max_file = max(max(self.army_1.file_units), max(self.army_2.file_units))
        min_pos = self.army_1.init_position - 0.5  # Space for starting units
        max_pos = self.army_2.init_position + 0.5
        self.battle_scene = \
            BattleScene(self.max_screen, self.landscape, min_file, max_file, min_pos, max_pos)

    def do_turn(self, verbosity: int) -> None:
        super().do_turn(verbosity)
        units = list(self.army_1.units) + list(self.army_2.units)
        self.battle_scene.draw_frame(units, self.curr_fights)

    def do(self, verbosity: int) -> None:
        super().do(verbosity)

        # Hold the final result frame long enough to see
        units = list(self.army_1.units) + list(self.army_2.units)
        self.battle_scene.draw_frame(units, [], reps=len(self.battle_scene.frames)//10)

        print(self.gif_name)

        self.battle_scene.frames[0].save(
            self.gif_name+".gif", save_all=True, append_images=self.battle_scene.frames[1:],
            optimize=False, duration=10000/len(self.battle_scene.frames), loop=True)
