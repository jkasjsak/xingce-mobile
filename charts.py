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
import matplotlib.font_manager as fm

from kivy.clock import Clock
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp
from kivy.utils import platform as kplatform

from core import CN_FONT, C, is_pure_ttf

DPI = 85


def _register_cn_font():
    """把打包的纯 TrueType 注册进 matplotlib（用字体族名而非路径，否则中文字幕变方框）。"""
    if CN_FONT and is_pure_ttf(CN_FONT):
        try:
            fm.fontManager.addfont(CN_FONT)
            name = fm.FontProperties(fname=CN_FONT).get_name()
            plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
        except Exception:
            plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    else:
        plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


_register_cn_font()


def _cn_font_name():
    return CN_FONT if CN_FONT else "Roboto"


class KivyChart(BoxLayout):
    def __init__(self, figsize=(7.0, 4.0), export=True, **kw):
        # size_hint_y=None + 固定高度：放进滚动盒后各图表独立占位、不再叠在一起
        super().__init__(orientation="vertical", size_hint_y=None, height=dp(360), **kw)
        self.figsize = figsize
        self.fig = None
        self._png = None  # 已渲染的 PNG 字节，供「存图」复用（#10 存错图的根因：fig 被提前 close）
        self._scatter = Scatter(
            do_rotation=False,
            do_scale=True,
            scale_min=0.6,
            scale_max=4.0,
            size_hint=(1, 1),
        )
        self._img = Image(allow_stretch=True, keep_ratio=True)
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
        # 延后一帧渲染，避免图表创建阻塞切页（#8 #9）；屏已被销毁则跳过
        Clock.schedule_once(lambda dt: self._render(), 0)

    def _render(self):
        if self.fig is None:
            return
        # 控件已从屏幕移除（例如重建），放弃渲染
        if not self._scatter.parent:
            return
        try:
            buf = io.BytesIO()
            self.fig.savefig(
                buf, format="png", dpi=DPI, bbox_inches="tight",
                transparent=True, facecolor="none",
            )
            self._png = buf.getvalue()
            buf.seek(0)
            ci = CoreImage(buf, ext="png")
            self._img.texture = ci.texture
            self._img.size = ci.texture.size
            self._scatter.transform.identity()
            self._scatter.scale = 1.0
            self._scatter.pos = (0, 0)
            self._scatter.rotation = 0
        except Exception:
            self._png = None
        finally:
            # 渲染完即可关闭 fig（图表已转成 PNG 字节），避免反复重建造成内存累积
            try:
                plt.close(self.fig)
            except Exception:
                pass
            self.fig = None

    def reset_view(self):
        try:
            self._scatter.transform.identity()
            self._scatter.scale = 1.0
            self._scatter.pos = (0, 0)
            self._scatter.rotation = 0
        except Exception:
            pass

    def save_image(self):
        if not self._png:
            return
        from kivy.app import App

        if kplatform == "android":
            d = "/sdcard/Download"
        else:
            d = os.path.expanduser("~/Downloads")
        os.makedirs(d, exist_ok=True)
        fn = os.path.join(d, f"行测图表_{datetime.datetime.now():%Y%m%d_%H%M%S}.png")
        try:
            with open(fn, "wb") as f:
                f.write(self._png)
            App.get_running_app().toast(f"已存图：{fn}")
        except Exception:
            App.get_running_app().toast("存图失败")
