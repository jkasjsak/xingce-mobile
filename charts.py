# -*- coding: utf-8 -*-
"""KivyChart：对应桌面版 ChartFrame 的可复用图表控件。

设计：matplotlib 用 Agg 后端渲染出 PNG → 放进 Kivy Scatter 控件，
- 单指拖动平移、双指捏合缩放（对应桌面版拖拽平移/缩放）；
- 「🔄 重置」恢复默认视角（对应桌面版 reset_view，极坐标回到完整圈）；
- 「💾 存图」导出 PNG 到下载目录。
这样把所有图表交互统一在移动端手势下，且视觉与桌面版一致。
"""
import io
import os
import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp
from kivy.utils import platform as kplatform

from core import CN_FONT, C

DPI = 85

# matplotlib 中文与负号
if CN_FONT:
    plt.rcParams["font.sans-serif"] = [CN_FONT]
else:
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "WenQuanYi Micro Hei"]
plt.rcParams["axes.unicode_minus"] = False


def _cn_font_name():
    return CN_FONT if CN_FONT else "Roboto"


class KivyChart(BoxLayout):
    def __init__(self, figsize=(7.0, 4.0), export=True, **kw):
        # size_hint_y=None + 固定高度：放进滚动盒后各图表独立占位、不再叠在一起
        super().__init__(orientation="vertical", size_hint_y=None, height=dp(360), **kw)
        self.figsize = figsize
        self.fig = None
        self._scatter = Scatter(
            do_rotation=False,
            do_scale=True,
            scale_min=0.6,
            scale_max=4.0,
            size_hint=(1, 1),
        )
        self._img = Image()
        self._scatter.add_widget(self._img)
        self.add_widget(self._scatter)
        if export:
            bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8), padding=dp(2))
            btn_reset = Button(
                text="🔄 重置",
                size_hint=(None, 1),
                width=dp(120),
                font_name=_cn_font_name(),
                background_color=C("accent_soft"),
                color=C("accent"),
            )
            btn_reset.bind(on_press=lambda *a: self.reset_view())
            btn_save = Button(
                text="💾 存图",
                size_hint=(None, 1),
                width=dp(120),
                font_name=_cn_font_name(),
                background_color=C("surface_alt"),
                color=C("success"),
            )
            btn_save.bind(on_press=lambda *a: self.save_image())
            hint = Label(
                text="单指拖动 · 双指缩放",
                size_hint=(1, 1),
                font_name=_cn_font_name(),
                color=C("muted"),
                halign="right",
            )
            bar.add_widget(btn_reset)
            bar.add_widget(btn_save)
            bar.add_widget(hint)
            self.add_widget(bar)

    def set_figure(self, fig):
        self.fig = fig
        self._render()

    def _render(self):
        if self.fig is None:
            return
        buf = io.BytesIO()
        try:
            self.fig.savefig(
                buf, format="png", dpi=DPI, bbox_inches="tight",
                transparent=True, facecolor="none",
            )
        except Exception:
            return
        buf.seek(0)
        try:
            ci = CoreImage(buf, ext="png")
            self._img.texture = ci.texture
            self._scatter.transform.identity()
            self._scatter.scale = 1.0
            self._scatter.pos = (0, 0)
            self._scatter.rotation = 0
        except Exception:
            pass
        finally:
            try:
                import matplotlib.pyplot as plt
                plt.close(self.fig)
            except Exception:
                pass

    def reset_view(self):
        try:
            self._scatter.transform.identity()
            self._scatter.scale = 1.0
            self._scatter.pos = (0, 0)
            self._scatter.rotation = 0
        except Exception:
            pass

    def save_image(self):
        if self.fig is None:
            return
        from kivy.app import App

        if kplatform == "android":
            d = "/sdcard/Download"
        else:
            d = os.path.expanduser("~/Downloads")
        os.makedirs(d, exist_ok=True)
        fn = os.path.join(d, f"行测图表_{datetime.datetime.now():%Y%m%d_%H%M%S}.png")
        try:
            self.fig.savefig(fn, dpi=110, bbox_inches="tight", facecolor="white")
            App.get_running_app().toast(f"已存图：{fn}")
        except Exception:
            App.get_running_app().toast("存图失败")
