# -*- coding: utf-8 -*-
"""共享工具：格式化、配色、考试计时控制器（行为与原桌面版 timer_state 完全一致）。

移植说明：原桌面版把计时状态放在 App.timer_state 并用 tkinter after 驱动；
此处改为 TimerController（纯 Python，不依赖 Tk），由 Kivy Clock 在页面可见时驱动显示。
"""
import os
import datetime

ACCENT = "#2F6FED"
RED = "#e5534b"
GREEN = "#22a06b"
ORANGE = "#E0922B"


def find_font():
    """中文显示字体：桌面优先系统微软雅黑；手机打包需把字体放到 fonts/msyh.ttf。"""
    candidates = [
        os.path.join(os.path.dirname(__file__), "fonts", "msyh.ttf"),
        r"C:\Windows\Fonts\msyh.ttf",
        r"C:\Windows\Fonts\msyh.ttc",
        "/system/fonts/NotoSansCJK-Regular.ttc",
        "/system/fonts/NotoSansSC-Regular.otf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return ""


CN_FONT = find_font()


def pct(x):
    if x is None:
        return "—"
    return f"{x * 100:.1f}%"


def fmt_elapsed(sec):
    if sec is None:
        return "00:00:00"
    sec = int(sec)
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def fmt_dur(minutes):
    if minutes is None:
        return ""
    m = int(minutes)
    s = int(round((minutes - m) * 60))
    return f"{m}分{s:02d}秒"


def chart_colors():
    """浅色主题配色，对应桌面版 light 主题。"""
    return {
        "bg": "#ffffff",
        "text": "#1f2733",
        "muted": "#5b6b82",
        "grid": "#e6e9ee",
        "line": "#2F6FED",
        "accent": ACCENT,
    }


class TimerController:
    """考试计时控制器：开始/暂停/继续/结束/重置，跨页面保留，并持久化到数据文件。"""

    def __init__(self, store):
        self.store = store
        self.state = {
            "start": None,
            "seg_start": None,
            "end": None,
            "running": False,
            "paused": False,
            "accum": 0.0,
        }
        try:
            r = store.get_timer()
            if isinstance(r, dict):
                for k in self.state:
                    if k in r:
                        self.state[k] = r[k]
        except Exception:
            pass

    def _persist(self):
        try:
            self.store.set_timer(self.state)
        except Exception:
            pass

    def start(self):
        now = datetime.datetime.now()
        self.state["start"] = now
        self.state["seg_start"] = now
        self.state["end"] = None
        self.state["running"] = True
        self.state["paused"] = False
        self.state["accum"] = 0.0
        self._persist()

    def pause(self):
        if not self.state["start"] or self.state["end"]:
            return
        now = datetime.datetime.now()
        self.state["accum"] += (now - self.state["seg_start"]).total_seconds()
        self.state["running"] = False
        self.state["paused"] = True
        self._persist()

    def resume(self):
        if not self.state.get("paused"):
            return
        self.state["seg_start"] = datetime.datetime.now()
        self.state["running"] = True
        self.state["paused"] = False
        self._persist()

    def stop(self):
        if not self.state["start"]:
            return None
        now = datetime.datetime.now()
        if self.state["paused"]:
            total = self.state["accum"]
        else:
            total = self.state["accum"] + (now - self.state["seg_start"]).total_seconds()
        self.state["end"] = now
        self.state["running"] = False
        self.state["paused"] = False
        self.state["accum"] = total
        self._persist()
        return total

    def reset(self):
        self.state = {
            "start": None,
            "seg_start": None,
            "end": None,
            "running": False,
            "paused": False,
            "accum": 0.0,
        }
        self._persist()

    def elapsed(self, now=None):
        now = now or datetime.datetime.now()
        if not self.state["start"]:
            return 0.0
        if self.state["paused"]:
            return self.state["accum"]
        if self.state["end"]:
            return self.state["accum"] + (self.state["end"] - self.state["seg_start"]).total_seconds()
        return self.state["accum"] + (now - self.state["seg_start"]).total_seconds()


# ---- 清新扁平化配色（hex，供 Kivy UI 统一使用）----
COLORS = {
    "bg": "#F4F6FA",          # 极浅灰蓝白背景
    "surface": "#FFFFFF",      # 卡片表面
    "surface_alt": "#F7F9FC",  # 次级表面
    "text": "#1F2733",         # 主文字
    "muted": "#5B6B82",        # 次要文字
    "accent": "#2F6FED",       # 强调蓝
    "accent_soft": "#E8F0FE",  # 强调蓝浅底
    "success": "#22A06B",
    "warning": "#E0922B",
    "danger": "#E5534B",
    "border": "#E3E8F0",       # 边框/分隔
}


def hex2rgb(h, alpha=1.0):
    """#RRGGBB -> (r,g,b,a) 0~1，供 Kivy 颜色使用。"""
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (r, g, b, alpha)


def C(name, alpha=1.0):
    return hex2rgb(COLORS[name], alpha)
