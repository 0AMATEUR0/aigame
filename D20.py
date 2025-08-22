# d100_gui.py
# 纯标准库 Tkinter GUI · D100 掷骰 · 动画 + 历史 + 优势/劣势
import random
import tkinter as tk
from datetime import datetime

ROLL_TIME_MS = 900     # 动画总时长（毫秒）
TICK_MS = 40           # 每帧间隔（毫秒）
MAX_HISTORY = 50       # 历史条数上限

class D100App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("D100 Roller · Python Tk")
        self.root.geometry("560x420")
        self.root.minsize(520, 380)

        # 主题色
        self.bg = "#0b0f16"
        self.fg = "#e7ecf2"
        self.muted = "#9aa7b4"
        self.ok = "#26d07c"
        self.bad = "#ff5d5d"

        self.root.configure(bg=self.bg)

        # 顶部标题
        title = tk.Label(root, text="D100 掷骰", font=("Segoe UI", 20, "bold"),
                         bg=self.bg, fg=self.fg)
        title.pack(pady=(10, 0))

        sub = tk.Label(root, text="动画滚动 · 历史记录 · 优势/劣势（空格=快速掷骰）",
                       font=("Segoe UI", 10), bg=self.bg, fg=self.muted)
        sub.pack(pady=(2, 10))

        # 主区域：左骰面 + 右历史
        main = tk.Frame(root, bg=self.bg)
        main.pack(fill="both", expand=True, padx=14, pady=8)

        # 左侧骰面板
        left = tk.Frame(main, bg=self._panel_bg(), highlightthickness=1,
                        highlightbackground=self._panel_border())
        left.place(relx=0.0, rely=0.0, relwidth=0.62, relheight=1.0)

        self.value_var = tk.StringVar(value="—")
        self.value_label = tk.Label(left, textvariable=self.value_var,
                                    font=("Segoe UI Black", 64),
                                    bg=self._die_bg(), fg="#ffffff",
                                    width=6, height=2)
        self.value_label.pack(padx=18, pady=16, fill="both", expand=True)

        # 控制区
        controls = tk.Frame(left, bg=self._panel_bg())
        controls.pack(pady=8)

        self.btn_roll = tk.Button(controls, text="🎲 Roll (D100)",
                                  command=self.roll_basic)
        self.btn_adv = tk.Button(controls, text="🟢 Advantage",
                                 command=self.roll_advantage)
        self.btn_dis = tk.Button(controls, text="🔴 Disadvantage",
                                 command=self.roll_disadvantage)
        self.btn_clear = tk.Button(controls, text="🧹 Clear",
                                   command=self.clear_history)

        for b in (self.btn_roll, self.btn_adv, self.btn_dis, self.btn_clear):
            b.configure(font=("Segoe UI", 10, "bold"))
            b.pack(side="left", padx=6, pady=4)

        # 右侧历史面板
        right = tk.Frame(main, bg=self._panel_bg(), highlightthickness=1,
                         highlightbackground=self._panel_border())
        right.place(relx=0.64, rely=0.0, relwidth=0.36, relheight=1.0)

        htitle = tk.Label(right, text="历史记录", font=("Segoe UI", 12, "bold"),
                          bg=self._panel_bg(), fg=self.fg)
        htitle.pack(anchor="w", padx=10, pady=(10, 6))

        self.history = tk.Listbox(right, bg=self._panel_bg(), fg=self.fg,
                                  highlightthickness=0, activestyle="none")
        self.history.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        hint = tk.Label(right, text="提示：掷出 100 会绿光庆祝；1 会红警提示。\n空格可快速掷骰。",
                        font=("Segoe UI", 9), bg=self._panel_bg(), fg=self.muted)
        hint.pack(padx=10, pady=(0, 10), anchor="w")

        # 绑定空格
        root.bind("<space>", lambda e: self.roll_basic())

        # 动画状态
        self._anim_running = False
        self._anim_after_id = None
        self._final_value = None
        self._start_ts = None

        # 初始展示
        self._set_value(50)
        self._neutral_glow()

    # ===== 样式辅助 =====
    def _panel_bg(self): return "#121a28"
    def _panel_border(self): return "#1f2a3b"
    def _die_bg(self): return "#203055"

    def _neutral_glow(self):
        self.value_label.configure(bg=self._die_bg())

    def _good_glow(self):
        self.value_label.configure(bg="#184e37")  # 绿色调背景

    def _bad_glow(self):
        self.value_label.configure(bg="#4e1a1a")  # 红色调背景

    # ===== 基础逻辑 =====
    def roll_once(self) -> int:
        return random.randint(1, 100)

    def roll_basic(self):
        if self._anim_running:  # 防抖
            return
        v = self.roll_once()
        self._animate_then_set(v, label="D100")

    def roll_advantage(self):
        if self._anim_running:
            return
        a, b = self.roll_once(), self.roll_once()
        v = max(a, b)
        self._append_history("Adv A", a)
        self._append_history("Adv B", b)
        self._animate_then_set(v, label="Adv ▶")

    def roll_disadvantage(self):
        if self._anim_running:
            return
        a, b = self.roll_once(), self.roll_once()
        v = min(a, b)
        self._append_history("Dis A", a)
        self._append_history("Dis B", b)
        self._animate_then_set(v, label="Dis ▼")

    def clear_history(self):
        self.history.delete(0, tk.END)

    # ===== 动画与历史 =====
    def _animate_then_set(self, final_value: int, label: str):
        # 启动动画：快速抖动随机数，结束后落到最终值
        self._final_value = final_value
        self._start_ts = self._now_ms()
        self._anim_running = True
        self._neutral_glow()
        self._tick()

    def _tick(self):
        elapsed = self._now_ms() - self._start_ts
        if elapsed >= ROLL_TIME_MS:
            # 动画结束，落点
            self._set_value(self._final_value)
            self._apply_glow(self._final_value)
            self._append_history(self._current_label(), self._final_value)
            self._anim_running = False
            self._anim_after_id = None
            return

        # 中间帧：显示一个抖动随机值（加速度/减速度可选，这里简单处理）
        showing = random.randint(1, 100)
        self._set_value(showing)

        # 逐帧调用
        self._anim_after_id = self.root.after(TICK_MS, self._tick)

    def _current_label(self):
        # 简单：如果历史里刚刚追加了 Adv/Dis 两条，下一条就是它们的合成
        # 实际上我们将 label 在 animate_then_set 调用时带入更好，
        # 这里简化：用 D100 / Adv ▶ / Dis ▼ 的启发式
        # ——为清晰起见，直接在 animate_then_set 里决定：
        return getattr(self, "_last_label", "D100")

    def _set_value(self, v: int):
        self.value_var.set(str(v))

    def _apply_glow(self, v: int):
        # 100: 正向庆祝；<=5: 红警；其他恢复中性
        if v == 100:
            self._good_glow()
        elif v <= 5:
            self._bad_glow()
        else:
            self._neutral_glow()

    def _append_history(self, label: str, value: int):
        timestamp = datetime.now().strftime("%H:%M:%S")
        text = f"[{timestamp}] {label:<6}  →  {value:>3}"
        # 颜色：100 绿色、1 红色，其余默认
        idx = self.history.size()
        self.history.insert(tk.END, text)
        if value == 100:
            self.history.itemconfig(idx, foreground=self.ok)
        elif value == 1:
            self.history.itemconfig(idx, foreground=self.bad)
        # 限制条数
        if self.history.size() > MAX_HISTORY:
            self.history.delete(0)

    def _animate_then_set(self, final_value: int, label: str):
        # 覆盖上一同名方法以带入 label（保持简单）
        self._final_value = final_value
        self._last_label = label
        self._start_ts = self._now_ms()
        self._anim_running = True
        self._neutral_glow()
        self._tick()

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now().timestamp() * 1000)


if __name__ == "__main__":
    root = tk.Tk()
    app = D100App(root)
    root.configure(bg="#0b0f16")
    root.mainloop()
