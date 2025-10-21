"""타자 연습 기반의 간단한 보스전 게임 (tkinter GUI).

주어진 전곡 가사를 모두 입력하면 보스를 쓰러뜨릴 수 있고,
틀리는 즉시 플레이어가 피해를 입습니다.
"""

import random
import tkinter as tk
from tkinter import ttk, font


LYRICS_LINES = [
    "싱싱 다정한 내 친구",
    "아기 강아지 쿠키루",
    "어렵고 힘들 때면",
    "쿠키루를 불러주세요 싱싱",
    "달려라 신나게",
    "날아라 내일을",
    "우리 세상 우리 친구",
    "아기 쿠키루",
]


class TypingBattleGame:
    CANVAS_WIDTH = 420
    CANVAS_HEIGHT = 120

    PLAYER_POS = (40, 20, 120, 100)
    BOSS_POS = (300, 20, 380, 100)

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Eos")
        self.root.resizable(False, False)

        style = ttk.Style()
        style.configure("Info.TLabel", font=("Nanum Gothic", 14, "bold"))
        style.configure("Status.TLabel", font=("Nanum Gothic", 11))
        style.configure("Small.TLabel", font=("Nanum Gothic", 10))

        self._prepare_assets()
        self._build_state()
        self._build_widgets()
        self._reset_game_state()

    def _prepare_assets(self) -> None:
        self.display_text = "\n".join(LYRICS_LINES)
        self.text_chars = [ch for line in LYRICS_LINES for ch in line]

        self.total_chars = len(self.text_chars)
        self.boss_damage_per_hit = 100.0 / float(self.total_chars)

        self.char_meta = []
        for line_idx, line in enumerate(LYRICS_LINES):
            for pos_in_line, _ch in enumerate(line):
                self.char_meta.append((line_idx, pos_in_line))

    def _build_state(self) -> None:
        self.boss_hp = 100.0
        self.prev_boss_percent = 100.0
        self.current_index = 0
        self.current_line_index = 0
        self.game_over = False
        self.await_restart = False
        self.ignore_entry_update = False
        self.player_base_coords = None
        self.boss_base_coords = None
        self.player_label_base = None
        self.boss_label_base = None
        self.player_offset = (0.0, 0.0)
        self.boss_offset = (0.0, 0.0)
        self._jiggle_job = None

    def _build_widgets(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.grid(row=0, column=0, sticky="nsew")

        self.line_font = font.Font(family="Nanum Gothic", size=13, weight="bold")
        self.bottom_font = font.Font(family="Nanum Gothic", size=14, weight="bold")

        hp_frame = ttk.Frame(container, padding=(0, 0, 0, 6))
        hp_frame.grid(row=0, column=0, sticky="ew")
        hp_frame.columnconfigure(0, weight=1)

        self.HP_BAR_WIDTH = self.CANVAS_WIDTH
        self.HP_BAR_HEIGHT = 22
        self.hp_canvas = tk.Canvas(
            hp_frame,
            width=self.HP_BAR_WIDTH,
            height=self.HP_BAR_HEIGHT,
            bg="#111827",
            highlightthickness=0,
        )
        self.hp_canvas.grid(row=0, column=0, sticky="ew")
        self.hp_canvas.create_rectangle(
            1,
            1,
            self.HP_BAR_WIDTH - 1,
            self.HP_BAR_HEIGHT - 1,
            outline="#991b1b",
            width=2,
        )
        self.hp_bar_fill = self.hp_canvas.create_rectangle(
            2,
            2,
            self.HP_BAR_WIDTH - 2,
            self.HP_BAR_HEIGHT - 2,
            fill="#ef4444",
            width=0,
        )
        self.hp_percent_text = self.hp_canvas.create_text(
            self.HP_BAR_WIDTH / 2,
            self.HP_BAR_HEIGHT / 2,
            text="보스 체력 100.0%",
            fill="#fee2e2",
            font=("Nanum Gothic", 12, "bold"),
        )

        self.canvas = tk.Canvas(
            container,
            width=self.CANVAS_WIDTH,
            height=self.CANVAS_HEIGHT,
            bg="#1f1b2d",
            highlightthickness=0,
        )
        self.canvas.grid(row=1, column=0, sticky="ew", pady=(6, 14))

        self.player_circle = self.canvas.create_oval(
            self.PLAYER_POS[0],
            self.PLAYER_POS[1],
            self.PLAYER_POS[2],
            self.PLAYER_POS[3],
            fill="#172554",
            outline="#1d4ed8",
            width=4,
        )
        self.player_label = self.canvas.create_text(
            (self.PLAYER_POS[0] + self.PLAYER_POS[2]) / 2,
            (self.PLAYER_POS[1] + self.PLAYER_POS[3]) / 2,
            text="플레이어",
            fill="#bfdbfe",
            font=("Nanum Gothic", 12, "bold"),
        )
        self.boss_circle = self.canvas.create_oval(
            self.BOSS_POS[0],
            self.BOSS_POS[1],
            self.BOSS_POS[2],
            self.BOSS_POS[3],
            fill="#450a0a",
            outline="#dc2626",
            width=5,
        )
        self.boss_label = self.canvas.create_text(
            (self.BOSS_POS[0] + self.BOSS_POS[2]) / 2,
            (self.BOSS_POS[1] + self.BOSS_POS[3]) / 2,
            text="보스",
            fill="#fecaca",
            font=("Nanum Gothic", 12, "bold"),
        )

        self.player_base_coords = self.canvas.coords(self.player_circle)
        self.boss_base_coords = self.canvas.coords(self.boss_circle)
        self.player_label_base = self.canvas.coords(self.player_label)
        self.boss_label_base = self.canvas.coords(self.boss_label)

        typing_frame = ttk.Frame(container, padding=(0, 8))
        typing_frame.grid(row=2, column=0, sticky="ew")
        typing_frame.columnconfigure(0, weight=1)

        self.current_line_display = tk.Text(
            typing_frame,
            width=34,
            height=3,
            font=self.line_font,
            bg="#111025",
            fg="#f4f4f5",
            relief="flat",
            wrap="char",
        )
        self.current_line_display.tag_configure("typed", foreground="#34d399")
        self.current_line_display.tag_configure("current", foreground="#facc15")
        self.current_line_display.tag_configure("pending", foreground="#a5b4fc")
        self.current_line_display.tag_configure("align", justify="center")
        self.current_line_display.tag_configure("bottom_line", font=self.bottom_font, foreground="#fef08a")
        self.current_line_display.tag_configure("bottom_typed", foreground="#facc15")
        self.current_line_display.tag_configure("bottom_wrong", foreground="#f87171")
        self.current_line_display.tag_configure("transition_old", foreground="#94a3b8")
        self.current_line_display.configure(state="disabled")
        self.current_line_display.grid(row=0, column=0, sticky="ew", padx=0)

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(
            self.root,
            textvariable=self.entry_var,
            font=self.line_font,
        )
        self.entry.place(x=-1000, y=-1000, width=10, height=10)
        self.entry.focus_set()

        self.entry_var.trace_add("write", self._on_entry_change)
        self.root.bind("<space>", self._on_space_press)

        info_frame = ttk.Frame(container, padding=(0, 4, 0, 0))
        info_frame.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        info_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(1, weight=1)

        self.result_label = ttk.Label(
            info_frame,
            text="",
            style="Status.TLabel",
            anchor="e",
        )
        self.result_label.grid(row=0, column=1, sticky="e")

        button_frame = ttk.Frame(container, padding=(0, 4))
        button_frame.grid(row=4, column=0, sticky="e")

        self.reset_button = ttk.Button(button_frame, text="다시 시작", command=self._reset_game_state)
        self.reset_button.grid(row=0, column=0, padx=8)

    def _reset_game_state(self) -> None:
        self._build_state()
        self._update_stat_labels()
        self.result_label.configure(text="")

        self._update_line_display()

        self.entry.configure(state="normal")
        self.ignore_entry_update = True
        self.entry_var.set("")
        self.ignore_entry_update = False
        self.entry.focus_set()
        self.await_restart = False

        self.canvas.itemconfig(self.player_circle, fill="#172554")
        self.canvas.itemconfig(self.player_circle, outline="#1d4ed8")
        self.canvas.itemconfig(self.boss_circle, fill="#450a0a")
        self.canvas.itemconfig(self.boss_circle, outline="#dc2626")

        self.player_offset = (0.0, 0.0)
        self.boss_offset = (0.0, 0.0)
        self._apply_entity_offsets(self.player_offset, self.boss_offset)
        self.game_over = False
        self._schedule_jiggle()

    def _on_entry_change(self, *_args) -> None:
        if self.ignore_entry_update or self.game_over:
            return

        new_text = self.entry_var.get()
        if not new_text:
            return

        processed_any = False
        for ch in new_text:
            if self._process_input_char(ch):
                processed_any = True
            if self.game_over:
                break

        if processed_any:
            self.ignore_entry_update = True
            self.entry_var.set("")
            self.ignore_entry_update = False

    def _on_space_press(self, _event: tk.Event) -> None:
        if self.await_restart:
            self._reset_game_state()
            return "break"

    def _process_input_char(self, ch: str) -> bool:
        if not ch or ch == "\r" or ch == "\n":
            return False

        expected = self.text_chars[self.current_index] if self.current_index < self.total_chars else None
        if expected is None:
            return False

        if self._is_composing_char(ch):
            return False

        if ch.strip() == "" and expected != " ":
            return False

        if ch == expected:
            self._handle_correct_input()
            return True
        else:
            self._handle_wrong_input(ch, expected)
            return True

    def _handle_correct_input(self) -> None:
        if self.current_index < self.total_chars:
            previous_line_idx = self.char_meta[self.current_index][0]
            previous_line_text = LYRICS_LINES[previous_line_idx]
        else:
            previous_line_idx = len(LYRICS_LINES) - 1
            previous_line_text = LYRICS_LINES[previous_line_idx]

        self.current_index += 1
        self.boss_hp = max(0.0, self.boss_hp - self.boss_damage_per_hit)
        self._update_stat_labels()

        line_changed = False
        if self.current_index < self.total_chars:
            current_line_idx = self.char_meta[self.current_index][0]
            line_changed = current_line_idx != previous_line_idx
        else:
            current_line_idx = previous_line_idx

        if line_changed:
            self._update_line_display(
                line_override=previous_line_text,
                typed_len_override=len(previous_line_text),
            )
            self.current_line_index = current_line_idx
            self._line_transition_animation(previous_line_text)
        else:
            self._update_line_display()

        self._animate_missile()

        if self.current_index >= self.total_chars:
            self._finish_game(victory=True)

    def _handle_wrong_input(self, ch: str, expected: str) -> None:
        self._update_stat_labels()
        self._flash_player()
        self._update_line_display(wrong_char=ch)

    def _update_stat_labels(self) -> None:
        boss_percent = max(0.0, self.boss_hp)
        self._draw_hp_bar(boss_percent)

    def _draw_hp_bar(self, boss_percent: float) -> None:
        proportion = boss_percent / 100.0
        proportion = max(0.0, min(1.0, proportion))
        fill_width = 2 + (self.HP_BAR_WIDTH - 4) * proportion
        self.hp_canvas.coords(
            self.hp_bar_fill,
            2,
            2,
            fill_width,
            self.HP_BAR_HEIGHT - 2,
        )
        self.hp_canvas.itemconfig(
            self.hp_percent_text,
            text=f"보스 체력 {boss_percent:0.1f}%",
        )
        if boss_percent < self.prev_boss_percent and not self.game_over:
            self._flash_hp_bar()
        self.prev_boss_percent = boss_percent

    def _flash_hp_bar(self) -> None:
        original_fill = "#ef4444"
        flash_fill = "#fca5a5"
        self.hp_canvas.itemconfig(self.hp_bar_fill, fill=flash_fill)
        self.hp_canvas.after(120, lambda: self.hp_canvas.itemconfig(self.hp_bar_fill, fill=original_fill))
    def _get_line_state(self) -> tuple[int, str, int, str]:
        if self.current_index >= self.total_chars:
            idx = len(LYRICS_LINES) - 1
            typed_len = len(LYRICS_LINES[idx])
            next_line = ""
        else:
            idx, typed_len = self.char_meta[self.current_index]
            next_line = LYRICS_LINES[idx + 1] if idx + 1 < len(LYRICS_LINES) else ""
        return idx, LYRICS_LINES[idx], typed_len, next_line

    def _update_line_display(
        self,
        wrong_char=None,
        line_override=None,
        typed_len_override=None,
    ) -> None:
        line_idx, current_line, typed_len, _ = self._get_line_state()
        self.current_line_index = line_idx

        if line_override is not None:
            current_line = line_override
        if typed_len_override is not None:
            typed_len = typed_len_override

        canvas = self.current_line_display
        canvas.configure(state="normal")
        canvas.delete("1.0", "end")
        canvas.insert("1.0", current_line)
        canvas.insert("end", "\n")

        bottom_chars = [" " for _ in current_line]
        for idx in range(min(typed_len, len(current_line))):
            bottom_chars[idx] = current_line[idx]
        if wrong_char and typed_len < len(bottom_chars):
            bottom_chars[typed_len] = wrong_char
        canvas.insert("end", "".join(bottom_chars))

        canvas.tag_remove("typed", "1.0", "end")
        canvas.tag_remove("current", "1.0", "end")
        canvas.tag_remove("pending", "1.0", "end")
        canvas.tag_remove("bottom_line", "1.0", "end")
        canvas.tag_remove("bottom_typed", "1.0", "end")
        canvas.tag_remove("bottom_wrong", "1.0", "end")
        canvas.tag_remove("align", "1.0", "end")

        canvas.tag_add("align", "1.0", "2.0")
        canvas.tag_add("align", "2.0", "3.0")
        canvas.tag_add("bottom_line", "2.0", "3.0")

        if typed_len > 0:
            canvas.tag_add("typed", "1.0", f"1.0 + {typed_len}c")
            canvas.tag_add("bottom_typed", "2.0", f"2.0 + {typed_len}c")

        if typed_len < len(current_line):
            canvas.tag_add("current", f"1.0 + {typed_len}c", f"1.0 + {typed_len + 1}c")
            canvas.tag_add("pending", f"1.0 + {typed_len + 1}c", "1.0 lineend")

        if wrong_char and typed_len < len(current_line):
            canvas.tag_add(
                "bottom_wrong",
                f"2.0 + {typed_len}c",
                f"2.0 + {typed_len + 1}c",
            )

        canvas.configure(state="disabled")

    def _apply_entity_offsets(
        self, player_offset: tuple[float, float], boss_offset: tuple[float, float]
    ) -> None:
        if self.player_base_coords and self.player_label_base:
            x1, y1, x2, y2 = self.player_base_coords
            dx, dy = player_offset
            self.canvas.coords(self.player_circle, x1 + dx, y1 + dy, x2 + dx, y2 + dy)
            px, py = self.player_label_base
            self.canvas.coords(self.player_label, px + dx, py + dy)

        if self.boss_base_coords and self.boss_label_base:
            x1, y1, x2, y2 = self.boss_base_coords
            dx, dy = boss_offset
            self.canvas.coords(self.boss_circle, x1 + dx, y1 + dy, x2 + dx, y2 + dy)
            bx, by = self.boss_label_base
            self.canvas.coords(self.boss_label, bx + dx, by + dy)

    def _schedule_jiggle(self) -> None:
        if self._jiggle_job is not None:
            self.root.after_cancel(self._jiggle_job)
            self._jiggle_job = None
        self._jiggle_job = self.root.after(520, self._jiggle_entities)

    def _jiggle_entities(self) -> None:
        if self.game_over:
            self._jiggle_job = None
            return

        max_offset = 2.0
        smoothing = 0.4

        target_player = (
            random.uniform(-max_offset, max_offset),
            random.uniform(-max_offset, max_offset),
        )
        target_boss = (
            random.uniform(-max_offset, max_offset),
            random.uniform(-max_offset, max_offset),
        )

        self.player_offset = (
            self.player_offset[0] * smoothing + target_player[0] * (1 - smoothing),
            self.player_offset[1] * smoothing + target_player[1] * (1 - smoothing),
        )
        self.boss_offset = (
            self.boss_offset[0] * smoothing + target_boss[0] * (1 - smoothing),
            self.boss_offset[1] * smoothing + target_boss[1] * (1 - smoothing),
        )

        self._apply_entity_offsets(self.player_offset, self.boss_offset)
        self._schedule_jiggle()

    def _animate_missile(self) -> None:
        start_x = (self.PLAYER_POS[0] + self.PLAYER_POS[2]) // 2
        start_y = (self.PLAYER_POS[1] + self.PLAYER_POS[3]) // 2
        missile_radius = random.randint(4, 10)
        missile = self.canvas.create_oval(
            start_x - missile_radius,
            start_y - missile_radius,
            start_x + missile_radius,
            start_y + missile_radius,
            fill="#38bdf8",
            outline="#bae6fd",
        )

        target_x = (self.BOSS_POS[0] + self.BOSS_POS[2]) // 2
        target_y = (self.BOSS_POS[1] + self.BOSS_POS[3]) // 2

        horizontal_span = target_x - start_x
        direction = 1 if horizontal_span >= 0 else -1
        span_abs = max(abs(horizontal_span), 120)

        control1 = (
            start_x + direction * span_abs * random.uniform(0.3, 1.0) * random.choice([-1, 1]),
            start_y + random.uniform(-220, 120),
        )
        control2 = (
            target_x - direction * span_abs * random.uniform(0.2, 0.9) * random.choice([-1, 1]),
            target_y + random.uniform(-120, 200),
        )

        steps = random.randint(24, 72)
        frame_delay = random.randint(8, 32)
        ease_power = random.uniform(0.8, 3.5)

        def bezier_point(t: float) -> tuple[float, float]:
            inv = 1.0 - t
            x = (
                inv ** 3 * start_x
                + 3 * inv ** 2 * t * control1[0]
                + 3 * inv * t ** 2 * control2[0]
                + t ** 3 * target_x
            )
            y = (
                inv ** 3 * start_y
                + 3 * inv ** 2 * t * control1[1]
                + 3 * inv * t ** 2 * control2[1]
                + t ** 3 * target_y
            )
            return x, y

        def move(step: int = 0) -> None:
            if step > steps or self.game_over:
                self.canvas.delete(missile)
                if not self.game_over:
                    self._flash_boss()
                return

            t = step / steps
            eased = t ** ease_power
            x, y = bezier_point(eased)
            self.canvas.coords(
                missile,
                x - missile_radius,
                y - missile_radius,
                x + missile_radius,
                y + missile_radius,
            )
            self.root.after(frame_delay, move, step + 1)

        move()

    def _line_transition_animation(self, previous_line_text) -> None:
        if self.current_index >= self.total_chars:
            self._update_line_display()
            return

        canvas = self.current_line_display
        canvas.configure(state="normal")
        canvas.delete("1.0", "end")
        canvas.insert("1.0", previous_line_text)
        canvas.insert("end", "\n")
        canvas.insert("end", " " * len(previous_line_text))

        canvas.tag_remove("typed", "1.0", "end")
        canvas.tag_remove("current", "1.0", "end")
        canvas.tag_remove("pending", "1.0", "end")
        canvas.tag_remove("bottom_line", "1.0", "end")
        canvas.tag_remove("bottom_typed", "1.0", "end")
        canvas.tag_remove("bottom_wrong", "1.0", "end")
        canvas.tag_remove("align", "1.0", "end")

        canvas.tag_add("align", "1.0", "2.0")
        canvas.tag_add("align", "2.0", "3.0")
        canvas.tag_add("bottom_line", "2.0", "3.0")
        canvas.tag_add("typed", "1.0", "1.0 lineend")

        canvas.configure(state="disabled")

        def finalize() -> None:
            if self.game_over:
                return
            self._update_line_display()

        self.root.after(160, finalize)

    def _is_composing_char(self, ch: str) -> bool:
        if not ch:
            return False
        code = ord(ch)
        return (
            0x1100 <= code <= 0x11FF
            or 0x3130 <= code <= 0x318F
            or 0xA960 <= code <= 0xA97F
            or 0xD7B0 <= code <= 0xD7FF
        )

    def _flash_boss(self) -> None:
        if self.game_over:
            return

        original_fill = "#450a0a"
        hit_fill = "#dc2626"
        self.canvas.itemconfig(self.boss_circle, fill=hit_fill)
        self.root.after(140, lambda: self.canvas.itemconfig(self.boss_circle, fill=original_fill))

    def _flash_player(self) -> None:
        original_fill = "#172554"
        hit_fill = "#2563eb"

        self.canvas.itemconfig(self.player_circle, fill=hit_fill)
        self.root.after(150, lambda: self.canvas.itemconfig(self.player_circle, fill=original_fill))

    def _finish_game(self, victory: bool) -> None:
        self.game_over = True
        self.entry.configure(state="disabled")
        self.entry_var.set("")
        if victory:
            self.result_label.configure(text="승리!")
            self.canvas.itemconfig(self.boss_circle, fill="#22c55e")
            self.await_restart = True

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    root = tk.Tk()
    game = TypingBattleGame(root)
    game.run()


if __name__ == "__main__":
    main()
