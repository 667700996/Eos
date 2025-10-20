"""타자 연습 기반의 간단한 보스전 게임 (tkinter GUI).

애국가 1~4절 가사를 모두 입력하면 보스를 쓰러뜨릴 수 있고,
틀리는 즉시 플레이어가 피해를 입습니다.
"""

import time
import tkinter as tk
from tkinter import ttk, font


ANTHEM_LINES = [
    "동해 물과 백두산이 마르고 닳도록",
    "하느님이 보우하사 우리나라 만세",
    "무궁화 삼천리 화려 강산",
    "대한 사람 대한으로 길이 보전하세",
    "남산 위에 저 소나무 철갑을 두른 듯",
    "바람 서리 불변함은 우리 기상일세",
    "무궁화 삼천리 화려 강산",
    "대한 사람 대한으로 길이 보전하세",
    "가을 하늘 공활한데 높고 구름 없이",
    "밝은 달은 우리 가슴 일편단심일세",
    "무궁화 삼천리 화려 강산",
    "대한 사람 대한으로 길이 보전하세",
    "이 기상과 이 마음으로 충성을 다하여",
    "괴로우나 즐거우나 나라 사랑하세",
    "무궁화 삼천리 화려 강산",
    "대한 사람 대한으로 길이 보전하세",
]


class TypingBattleGame:
    CANVAS_WIDTH = 520
    CANVAS_HEIGHT = 220

    PLAYER_POS = (40, 140, 100, 200)
    BOSS_POS = (410, 40, 510, 140)

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("한컴 타자 - 애국가 보스전")
        self.root.resizable(False, False)

        style = ttk.Style()
        style.configure("Info.TLabel", font=("Nanum Gothic", 14, "bold"))
        style.configure("Status.TLabel", font=("Nanum Gothic", 11))
        style.configure("Small.TLabel", font=("Nanum Gothic", 10))

        self._prepare_assets()
        self._build_state()
        self._build_widgets()
        self._reset_game_state()
        self._start_timer()

    def _prepare_assets(self) -> None:
        self.display_text = "\n".join(ANTHEM_LINES)
        self.text_chars = [ch for line in ANTHEM_LINES for ch in line]

        self.total_chars = len(self.text_chars)
        self.boss_damage_per_hit = 100.0 / float(self.total_chars)

        self.char_meta = []
        for line_idx, line in enumerate(ANTHEM_LINES):
            for pos_in_line, _ch in enumerate(line):
                self.char_meta.append((line_idx, pos_in_line))

    def _build_state(self) -> None:
        self.boss_hp = 100.0
        self.current_index = 0
        self.current_line_index = 0
        self.game_over = False
        self.start_time = None

        self.correct_inputs = 0
        self.total_inputs = 0
        self.wpm = 0.0

        self.ignore_entry_update = False

    def _build_widgets(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.grid(row=0, column=0, sticky="nsew")

        self.line_font = font.Font(family="Nanum Gothic", size=20, weight="bold")
        self.bottom_font = font.Font(family="Nanum Gothic", size=18, weight="bold")
        self.bar_font = font.Font(family="Nanum Gothic", size=11, weight="bold")

        top_frame = ttk.Frame(container)
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=1)
        top_frame.columnconfigure(2, weight=1)

        self.timer_label = ttk.Label(top_frame, text="시간 - 0.00초", style="Info.TLabel", anchor="w")
        self.timer_label.grid(row=0, column=0, sticky="w")

        self.boss_hp_label = ttk.Label(
            top_frame,
            text=f"보스 체력 - {self.total_chars - self.current_index}/{self.total_chars} (100.0%)",
            style="Info.TLabel",
            anchor="center",
        )
        self.boss_hp_label.grid(row=0, column=1, sticky="n")

        self.status_label = ttk.Label(
            top_frame,
            text="한 글자씩 정확하게 입력하면 보스에게 미사일이 발사됩니다!",
            style="Status.TLabel",
            anchor="e",
        )
        self.status_label.grid(row=0, column=2, sticky="e")

        bar_frame = ttk.Frame(container, padding=(0, 10, 0, 0))
        bar_frame.grid(row=1, column=0, sticky="ew")
        bar_frame.columnconfigure(0, weight=1)
        bar_frame.columnconfigure(1, weight=1)

        self.BAR_WIDTH = 200
        self.BAR_HEIGHT = 20

        self.accuracy_canvas = tk.Canvas(
            bar_frame,
            width=self.BAR_WIDTH,
            height=self.BAR_HEIGHT,
            bg="#0f172a",
            highlightthickness=0,
        )
        self.accuracy_canvas.grid(row=0, column=0, padx=(0, 12), sticky="w")
        self.accuracy_canvas.create_rectangle(
            1,
            1,
            self.BAR_WIDTH - 1,
            self.BAR_HEIGHT - 1,
            outline="#475569",
            width=2,
        )
        self.accuracy_bar_fill = self.accuracy_canvas.create_rectangle(
            2,
            2,
            2,
            self.BAR_HEIGHT - 2,
            fill="#fb7185",
            width=0,
        )
        self.accuracy_bar_text = self.accuracy_canvas.create_text(
            self.BAR_WIDTH / 2,
            self.BAR_HEIGHT / 2,
            text="오차 0.0%",
            fill="#f8fafc",
            font=self.bar_font,
        )

        self.wpm_canvas = tk.Canvas(
            bar_frame,
            width=self.BAR_WIDTH,
            height=self.BAR_HEIGHT,
            bg="#0f172a",
            highlightthickness=0,
        )
        self.wpm_canvas.grid(row=0, column=1, padx=(12, 0), sticky="e")
        self.wpm_canvas.create_rectangle(
            1,
            1,
            self.BAR_WIDTH - 1,
            self.BAR_HEIGHT - 1,
            outline="#475569",
            width=2,
        )
        self.wpm_bar_fill = self.wpm_canvas.create_rectangle(
            2,
            2,
            2,
            self.BAR_HEIGHT - 2,
            fill="#38bdf8",
            width=0,
        )
        self.wpm_bar_text = self.wpm_canvas.create_text(
            self.BAR_WIDTH / 2,
            self.BAR_HEIGHT / 2,
            text="000",
            fill="#f8fafc",
            font=self.bar_font,
        )

        self.canvas = tk.Canvas(
            container,
            width=self.CANVAS_WIDTH,
            height=self.CANVAS_HEIGHT,
            bg="#1f1b2d",
            highlightthickness=0,
        )
        self.canvas.grid(row=2, column=0, sticky="ew", pady=(12, 12))

        self.player_circle = self.canvas.create_oval(
            self.PLAYER_POS[0],
            self.PLAYER_POS[1],
            self.PLAYER_POS[2],
            self.PLAYER_POS[3],
            fill="#7dd3fc",
            outline="#0891b2",
            width=4,
        )
        self.player_label = self.canvas.create_text(
            (self.PLAYER_POS[0] + self.PLAYER_POS[2]) // 2,
            self.PLAYER_POS[1] - 12,
            text="플레이어",
            fill="#bae6fd",
            font=("Nanum Gothic", 10, "bold"),
        )
        self.boss_circle = self.canvas.create_oval(
            self.BOSS_POS[0],
            self.BOSS_POS[1],
            self.BOSS_POS[2],
            self.BOSS_POS[3],
            fill="#f97316",
            outline="#ea580c",
            width=5,
        )
        self.boss_label = self.canvas.create_text(
            (self.BOSS_POS[0] + self.BOSS_POS[2]) // 2,
            self.BOSS_POS[3] + 12,
            text="보스",
            fill="#ffedd5",
            font=("Nanum Gothic", 10, "bold"),
        )

        typing_frame = ttk.Frame(container, padding=(0, 8))
        typing_frame.grid(row=3, column=0, sticky="ew")
        typing_frame.columnconfigure(0, weight=1)

        self.current_line_display = tk.Text(
            typing_frame,
            width=40,
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
        self.current_line_display.grid(row=0, column=0, sticky="ew")

        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(
            container,
            width=16,
            textvariable=self.entry_var,
            font=self.line_font,
        )
        self.entry.place(x=-1000, y=-1000)
        self.entry.focus_set()

        self.entry_var.trace_add("write", self._on_entry_change)

        button_frame = ttk.Frame(container, padding=(0, 4))
        button_frame.grid(row=4, column=0, sticky="e")

        self.reset_button = ttk.Button(button_frame, text="다시 시작", command=self._reset_game_state)
        self.reset_button.grid(row=0, column=0, padx=8)

    def _reset_game_state(self) -> None:
        self._build_state()
        self._update_stat_labels()
        self._update_wpm(0.0)
        self.status_label.configure(text="타자를 시작하면 전투가 진행됩니다!")

        self._update_line_display()

        self.entry.configure(state="normal")
        self.ignore_entry_update = True
        self.entry_var.set("")
        self.ignore_entry_update = False
        self.entry.focus_set()

        self.canvas.itemconfig(self.player_circle, fill="#7dd3fc")
        self.canvas.itemconfig(self.player_circle, outline="#0891b2")
        self.canvas.itemconfig(self.boss_circle, fill="#f97316")
        self.canvas.itemconfig(self.boss_circle, outline="#ea580c")

        self.start_time = time.perf_counter()
        if not hasattr(self, "_timer_running"):
            self._timer_running = True
        self.game_over = False

    def _start_timer(self) -> None:
        self._timer_running = True
        self._update_timer()

    def _update_timer(self) -> None:
        elapsed = 0.0 if self.start_time is None else time.perf_counter() - self.start_time
        self.timer_label.configure(text=f"시간 - {elapsed:0.2f}초")
        self._update_wpm(elapsed)
        self.root.after(50, self._update_timer)

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

        self.total_inputs += 1

        if ch == expected:
            self.correct_inputs += 1
            self._handle_correct_input()
            return True
        else:
            self._handle_wrong_input(ch, expected)
            return True

    def _handle_correct_input(self) -> None:
        if self.current_index < self.total_chars:
            previous_line_idx = self.char_meta[self.current_index][0]
            previous_line_text = ANTHEM_LINES[previous_line_idx]
        else:
            previous_line_idx = len(ANTHEM_LINES) - 1
            previous_line_text = ANTHEM_LINES[previous_line_idx]

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
        self.status_label.configure(
            text=f"틀렸습니다! 입력 - '{ch}' / 목표 - '{expected}'"
        )

        self._update_line_display(wrong_char=ch)

    def _update_stat_labels(self) -> None:
        remaining_hits = self.total_chars - self.current_index
        boss_percent = max(0.0, self.boss_hp)
        self.boss_hp_label.configure(
            text=f"보스 체력 - {remaining_hits}/{self.total_chars} ({boss_percent:0.1f}%)"
        )
        accuracy = 100.0 if self.total_inputs == 0 else (self.correct_inputs / self.total_inputs) * 100.0
        self._draw_accuracy_bar(accuracy)

    def _update_wpm(self, elapsed: float) -> None:
        if elapsed <= 0.0:
            self.wpm = 0.0
        else:
            characters_per_minute = (self.correct_inputs / elapsed) * 60.0
            self.wpm = characters_per_minute
        self._draw_wpm_bar(self.wpm)

    def _draw_accuracy_bar(self, accuracy: float) -> None:
        error = max(0.0, 100.0 - accuracy)
        fraction = min(error / 100.0, 1.0)
        fill_width = 2 + (self.BAR_WIDTH - 4) * fraction
        self.accuracy_canvas.coords(
            self.accuracy_bar_fill,
            2,
            2,
            fill_width,
            self.BAR_HEIGHT - 2,
        )
        self.accuracy_canvas.itemconfig(
            self.accuracy_bar_text,
            text=f"오차 {error:0.1f}%",
        )

    def _draw_wpm_bar(self, wpm: float) -> None:
        capped = min(max(wpm, 0.0), 800.0)
        fraction = capped / 800.0
        fill_width = 2 + (self.BAR_WIDTH - 4) * fraction
        self.wpm_canvas.coords(
            self.wpm_bar_fill,
            2,
            2,
            fill_width,
            self.BAR_HEIGHT - 2,
        )
        self.wpm_canvas.itemconfig(
            self.wpm_bar_text,
            text=f"{int(round(capped)):03d}",
        )

    def _get_line_state(self) -> tuple[int, str, int, str]:
        if self.current_index >= self.total_chars:
            idx = len(ANTHEM_LINES) - 1
            typed_len = len(ANTHEM_LINES[idx])
            next_line = ""
        else:
            idx, typed_len = self.char_meta[self.current_index]
            next_line = ANTHEM_LINES[idx + 1] if idx + 1 < len(ANTHEM_LINES) else ""
        return idx, ANTHEM_LINES[idx], typed_len, next_line

    def _update_line_display(
        self,
        wrong_char: str | None = None,
        line_override: str | None = None,
        typed_len_override: int | None = None,
    ) -> None:
        line_idx, current_line, typed_len, _ = self._get_line_state()
        self.current_line_index = line_idx

        if line_override is not None:
            current_line = line_override
        if typed_len_override is not None:
            typed_len = typed_len_override

        self.current_line_display.configure(state="normal")
        self.current_line_display.delete("1.0", "end")
        self.current_line_display.insert("1.0", current_line)
        self.current_line_display.insert("end", "\n")

        bottom_chars = [" "] * len(current_line)
        for idx in range(min(typed_len, len(current_line))):
            bottom_chars[idx] = current_line[idx]
        if wrong_char and typed_len < len(bottom_chars):
            bottom_chars[typed_len] = wrong_char
        self.current_line_display.insert("end", "".join(bottom_chars))

        self.current_line_display.tag_remove("typed", "1.0", "2.0")
        self.current_line_display.tag_remove("current", "1.0", "2.0")
        self.current_line_display.tag_remove("pending", "1.0", "2.0")
        self.current_line_display.tag_remove("bottom_line", "2.0", "3.0")
        self.current_line_display.tag_remove("bottom_typed", "2.0", "3.0")
        self.current_line_display.tag_remove("bottom_wrong", "2.0", "3.0")
        self.current_line_display.tag_remove("transition_old", "1.0", "3.0")

        self.current_line_display.tag_add("align", "1.0", "2.0")
        self.current_line_display.tag_add("align", "2.0", "3.0")
        self.current_line_display.tag_add("bottom_line", "2.0", "3.0")

        if typed_len > 0:
            self.current_line_display.tag_add("typed", "1.0", f"1.0 + {typed_len}c")
            self.current_line_display.tag_add("bottom_typed", "2.0", f"2.0 + {typed_len}c")

        if typed_len < len(current_line):
            self.current_line_display.tag_add(
                "current", f"1.0 + {typed_len}c", f"1.0 + {typed_len + 1}c"
            )
            self.current_line_display.tag_add(
                "pending", f"1.0 + {typed_len + 1}c", "1.0 lineend"
            )

        if wrong_char and typed_len < len(current_line):
            self.current_line_display.tag_add(
                "bottom_wrong",
                f"2.0 + {typed_len}c",
                f"2.0 + {typed_len + 1}c",
            )

        self.current_line_display.configure(state="disabled")

    def _animate_missile(self) -> None:
        start_x = (self.PLAYER_POS[0] + self.PLAYER_POS[2]) // 2
        start_y = (self.PLAYER_POS[1] + self.PLAYER_POS[3]) // 2
        missile_radius = 6
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

        control1 = (
            start_x + max(40, (target_x - start_x) * 0.25),
            start_y - 90,
        )
        control2 = (
            target_x - max(40, (target_x - start_x) * 0.2),
            target_y + 80,
        )

        steps = 48

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
            eased = t ** 2.2
            x, y = bezier_point(eased)
            self.canvas.coords(
                missile,
                x - missile_radius,
                y - missile_radius,
                x + missile_radius,
                y + missile_radius,
            )
            self.root.after(18, move, step + 1)

        move()

    def _line_transition_animation(self, previous_line_text: str) -> None:
        if self.current_index >= self.total_chars:
            self._update_line_display()
            return

        _, next_line_text, _, _ = self._get_line_state()

        self.current_line_display.configure(state="normal")
        self.current_line_display.delete("1.0", "end")
        self.current_line_display.insert("1.0", previous_line_text)
        self.current_line_display.insert("end", "\n")
        self.current_line_display.insert("end", next_line_text)
        self.current_line_display.insert("end", "\n")
        self.current_line_display.insert("end", " " * len(next_line_text))

        self.current_line_display.tag_remove("typed", "1.0", "end")
        self.current_line_display.tag_remove("current", "1.0", "end")
        self.current_line_display.tag_remove("pending", "1.0", "end")
        self.current_line_display.tag_remove("bottom_line", "1.0", "end")
        self.current_line_display.tag_remove("bottom_typed", "1.0", "end")
        self.current_line_display.tag_remove("bottom_wrong", "1.0", "end")
        self.current_line_display.tag_remove("align", "1.0", "end")

        self.current_line_display.tag_add("align", "1.0", "3.0")
        self.current_line_display.tag_add("transition_old", "1.0", "1.0 lineend")
        self.current_line_display.tag_add("bottom_line", "3.0", "3.0 lineend")

        self.current_line_display.configure(state="disabled")

        def finalize() -> None:
            if self.game_over:
                return
            self._update_line_display()

        self.root.after(220, finalize)

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

        original_color = "#f97316"
        hit_color = "#fbbf24"

        self.canvas.itemconfig(self.boss_circle, fill=hit_color)
        self.root.after(120, lambda: self.canvas.itemconfig(self.boss_circle, fill=original_color))

    def _flash_player(self) -> None:
        original_color = "#7dd3fc"
        hit_color = "#f87171"

        self.canvas.itemconfig(self.player_circle, fill=hit_color)
        self.root.after(150, lambda: self.canvas.itemconfig(self.player_circle, fill=original_color))

    def _finish_game(self, victory: bool) -> None:
        self.game_over = True
        self.entry.configure(state="disabled")
        elapsed = (
            time.perf_counter() - self.start_time if self.start_time is not None else 0.0
        )

        if victory:
            self.status_label.configure(
                text=f"승리! 총 소요 시간 {elapsed:0.2f}초 - 정확한 타자 실력입니다!"
            )
            self.canvas.itemconfig(self.boss_circle, fill="#22c55e")

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    root = tk.Tk()
    game = TypingBattleGame(root)
    game.run()


if __name__ == "__main__":
    main()
