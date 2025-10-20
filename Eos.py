"""타자 연습 기반의 간단한 보스전 게임 (tkinter GUI).

애국가 1~4절 가사를 모두 입력하면 보스를 쓰러뜨릴 수 있고,
틀리는 즉시 플레이어가 피해를 입습니다.
"""

import math
import time
import tkinter as tk
from tkinter import ttk


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
    PLAYER_MAX_HP = 100
    WRONG_DAMAGE = 10

    CANVAS_WIDTH = 520
    CANVAS_HEIGHT = 220

    PLAYER_POS = (60, 140, 120, 200)
    BOSS_POS = (400, 40, 480, 140)

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("한컴 타자 - 애국가 보스전")
        self.root.resizable(False, False)

        style = ttk.Style()
        style.configure("Info.TLabel", font=("Nanum Gothic", 14, "bold"))
        style.configure("Status.TLabel", font=("Nanum Gothic", 11))
        style.configure("Small.TLabel", font=("Nanum Gothic", 10))

        self._build_state()
        self._build_widgets()
        self._reset_game_state()
        self._start_timer()

    def _build_state(self) -> None:
        self.display_text = "\n".join(ANTHEM_LINES)
        self.text_chars = [ch for line in ANTHEM_LINES for ch in line]

        self.display_index_map = []
        display_pointer = 0
        for line_idx, line in enumerate(ANTHEM_LINES):
            for ch in line:
                self.display_index_map.append(display_pointer)
                display_pointer += 1
            if line_idx < len(ANTHEM_LINES) - 1:
                display_pointer += 1  # newline 문자

        self.total_chars = len(self.text_chars)
        self.boss_damage_per_hit = 100.0 / float(self.total_chars)

        self.player_hp = self.PLAYER_MAX_HP
        self.boss_hp = 100.0
        self.current_index = 0
        self.game_over = False
        self.start_time = None

        self.ignore_entry_update = False

    def _build_widgets(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.grid(row=0, column=0, sticky="nsew")

        self.canvas = tk.Canvas(
            container,
            width=self.CANVAS_WIDTH,
            height=self.CANVAS_HEIGHT,
            bg="#1f1b2d",
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.player_sprite = self.canvas.create_rectangle(
            *self.PLAYER_POS, fill="#7dd3fc", outline="#0891b2", width=3
        )
        self.boss_sprite = self.canvas.create_rectangle(
            *self.BOSS_POS, fill="#f97316", outline="#ea580c", width=4
        )
        self.canvas.create_text(
            (self.PLAYER_POS[0] + self.PLAYER_POS[2]) // 2,
            self.PLAYER_POS[1] - 12,
            text="플레이어",
            fill="#bae6fd",
            font=("Nanum Gothic", 10, "bold"),
        )
        self.canvas.create_text(
            (self.BOSS_POS[0] + self.BOSS_POS[2]) // 2,
            self.BOSS_POS[3] + 12,
            text="보스",
            fill="#ffedd5",
            font=("Nanum Gothic", 10, "bold"),
        )

        info_frame = ttk.Frame(container, padding=(0, 12, 0, 0))
        info_frame.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.timer_label = ttk.Label(info_frame, text="시간: 0.00초", style="Info.TLabel")
        self.timer_label.grid(row=0, column=0, sticky="w")

        self.boss_hp_label = ttk.Label(
            info_frame,
            text=f"보스 체력: {self.total_chars - self.current_index}/{self.total_chars} (100.0%)",
            style="Info.TLabel",
        )
        self.boss_hp_label.grid(row=0, column=1, sticky="ew")

        self.player_hp_label = ttk.Label(
            info_frame,
            text=f"내 체력: {self.player_hp}/{self.PLAYER_MAX_HP}",
            style="Info.TLabel",
        )
        self.player_hp_label.grid(row=0, column=2, sticky="e")

        info_frame.columnconfigure(1, weight=1)

        self.status_label = ttk.Label(
            container,
            text="한 글자씩 정확하게 입력하면 보스에게 미사일이 발사됩니다!",
            style="Status.TLabel",
            padding=(0, 8),
        )
        self.status_label.grid(row=2, column=0, columnspan=2, sticky="w")

        self.text_widget = tk.Text(
            container,
            width=60,
            height=12,
            wrap="word",
            font=("Nanum Gothic", 12),
            bg="#111025",
            fg="#f4f4f5",
            relief="flat",
            padx=12,
            pady=12,
        )
        self.text_widget.insert("1.0", self.display_text)
        self.text_widget.configure(state="disabled")
        self.text_widget.tag_configure("typed", foreground="#34d399")
        self.text_widget.tag_configure("current", foreground="#facc15")
        self.text_widget.grid(row=3, column=0, columnspan=2, sticky="ew")

        entry_frame = ttk.Frame(container, padding=(0, 12, 0, 0))
        entry_frame.grid(row=4, column=0, sticky="w")

        entry_label = ttk.Label(entry_frame, text="입력:", style="Status.TLabel")
        entry_label.grid(row=0, column=0, sticky="w")

        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(
            entry_frame,
            width=12,
            textvariable=self.entry_var,
            font=("Nanum Gothic", 14),
        )
        self.entry.grid(row=0, column=1, padx=(8, 0))
        self.entry.focus_set()

        self.entry_var.trace_add("write", self._on_entry_change)

        button_frame = ttk.Frame(container)
        button_frame.grid(row=4, column=1, sticky="e")

        self.reset_button = ttk.Button(button_frame, text="다시 시작", command=self._reset_game_state)
        self.reset_button.grid(row=0, column=0, padx=8)

    def _reset_game_state(self) -> None:
        self._build_state()
        self._update_hp_labels()
        self.status_label.configure(text="타자를 시작하면 전투가 진행됩니다!")

        self.text_widget.configure(state="normal")
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", self.display_text)
        self.text_widget.tag_remove("typed", "1.0", "end")
        self._highlight_current_char()
        self.text_widget.configure(state="disabled")

        self.entry.configure(state="normal")
        self.ignore_entry_update = True
        self.entry_var.set("")
        self.ignore_entry_update = False
        self.entry.focus_set()

        self.canvas.itemconfig(self.player_sprite, fill="#7dd3fc")
        self.canvas.itemconfig(self.boss_sprite, fill="#f97316")

        self.start_time = time.perf_counter()
        if not hasattr(self, "_timer_running"):
            self._timer_running = True
        self.game_over = False

    def _start_timer(self) -> None:
        self._timer_running = True
        self._update_timer()

    def _update_timer(self) -> None:
        if self.start_time is None:
            elapsed = 0.0
        else:
            elapsed = time.perf_counter() - self.start_time
        self.timer_label.configure(text=f"시간: {elapsed:0.2f}초")
        self.root.after(50, self._update_timer)

    def _on_entry_change(self, *_args) -> None:
        if self.ignore_entry_update or self.game_over:
            return

        new_text = self.entry_var.get()
        if not new_text:
            return

        for ch in new_text:
            self._process_input_char(ch)
            if self.game_over:
                break

        self.ignore_entry_update = True
        self.entry_var.set("")
        self.ignore_entry_update = False

    def _process_input_char(self, ch: str) -> None:
        if not ch or ch == "\r" or ch == "\n":
            return

        expected = self.text_chars[self.current_index] if self.current_index < self.total_chars else None
        if expected is None:
            return

        if ch == expected:
            self._handle_correct_input()
        else:
            self._handle_wrong_input(ch, expected)

    def _handle_correct_input(self) -> None:
        self.current_index += 1
        self.boss_hp = max(0.0, self.boss_hp - self.boss_damage_per_hit)
        self._update_hp_labels()
        self._highlight_current_char()
        self._animate_missile()

        if self.current_index >= self.total_chars:
            self._finish_game(victory=True)

    def _handle_wrong_input(self, ch: str, expected: str) -> None:
        self.player_hp = max(0, self.player_hp - self.WRONG_DAMAGE)
        self._update_hp_labels()
        self._flash_player()
        self.status_label.configure(
            text=f"틀렸습니다! 입력: '{ch}' / 목표: '{expected}'"
        )

        if self.player_hp <= 0:
            self._finish_game(victory=False)

    def _update_hp_labels(self) -> None:
        remaining_hits = self.total_chars - self.current_index
        boss_percent = max(0.0, self.boss_hp)
        self.boss_hp_label.configure(
            text=f"보스 체력: {remaining_hits}/{self.total_chars} ({boss_percent:0.1f}%)"
        )
        self.player_hp_label.configure(
            text=f"내 체력: {self.player_hp}/{self.PLAYER_MAX_HP}"
        )

    def _highlight_current_char(self) -> None:
        self.text_widget.configure(state="normal")
        self.text_widget.tag_remove("typed", "1.0", "end")
        self.text_widget.tag_remove("current", "1.0", "end")

        if self.current_index > 0:
            last_display_index = self.display_index_map[self.current_index - 1]
            self.text_widget.tag_add("typed", "1.0", f"1.0 + {last_display_index + 1}c")

        if self.current_index < self.total_chars:
            current_display_index = self.display_index_map[self.current_index]
            self.text_widget.tag_add(
                "current",
                f"1.0 + {current_display_index}c",
                f"1.0 + {current_display_index + 1}c",
            )

        self.text_widget.configure(state="disabled")

    def _animate_missile(self) -> None:
        start_x = (self.PLAYER_POS[0] + self.PLAYER_POS[2]) // 2
        start_y = (self.PLAYER_POS[1] + self.PLAYER_POS[3]) // 2
        missile = self.canvas.create_oval(
            start_x - 6, start_y - 6, start_x + 6, start_y + 6, fill="#38bdf8", outline="#bae6fd"
        )

        target_x = (self.BOSS_POS[0] + self.BOSS_POS[2]) // 2
        target_y = (self.BOSS_POS[1] + self.BOSS_POS[3]) // 2
        steps = 20
        dx = (target_x - start_x) / steps
        dy = (target_y - start_y) / steps

        def move(step: int = 0) -> None:
            if step >= steps or self.game_over:
                self.canvas.delete(missile)
                self._flash_boss()
                return
            self.canvas.move(missile, dx, dy)
            self.root.after(20, move, step + 1)

        move()

    def _flash_boss(self) -> None:
        if self.game_over:
            return

        original_color = "#f97316"
        hit_color = "#fbbf24"

        self.canvas.itemconfig(self.boss_sprite, fill=hit_color)
        self.root.after(120, lambda: self.canvas.itemconfig(self.boss_sprite, fill=original_color))

    def _flash_player(self) -> None:
        original_color = "#7dd3fc"
        hit_color = "#f87171"

        self.canvas.itemconfig(self.player_sprite, fill=hit_color)
        self.root.after(150, lambda: self.canvas.itemconfig(self.player_sprite, fill=original_color))

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
            self.canvas.itemconfig(self.boss_sprite, fill="#22c55e")
        else:
            self.status_label.configure(
                text=f"패배... 애국가를 끝까지 지키지 못했습니다. (생존 시간 {elapsed:0.2f}초)"
            )
            self.canvas.itemconfig(self.player_sprite, fill="#ef4444")

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    root = tk.Tk()
    game = TypingBattleGame(root)
    game.run()


if __name__ == "__main__":
    main()
