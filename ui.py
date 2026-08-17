# -*- coding: utf-8 -*-
"""Kivy UI 基础组件：自适应滚动容器、卡片、标题、空状态提示。

对应桌面版 self.card / self.header / self.empty_hint。
所有容器用 size_hint_y=None + height 绑定 minimum_height，内容变化时自动撑高。
"""
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
from core import CN_FONT, ACCENT


def cn():
    return CN_FONT if CN_FONT else "Roboto"


def make_scroll():
    sv = ScrollView(size_hint=(1, 1), do_scroll_x=False)
    box = BoxLayout(orientation="vertical", size_hint_y=None, padding=dp(12), spacing=dp(10))
    box.bind(minimum_height=box.setter("height"))
    sv.add_widget(box)
    return sv, box


class Card(BoxLayout):
    def __init__(self, title=None, **kw):
        super().__init__(orientation="vertical", size_hint_y=None, padding=dp(12), spacing=dp(6), **kw)
        self.bind(minimum_height=self.setter("height"))
        if title:
            tl = Label(
                text=title, font_name=cn(), font_size=dp(15), bold=True,
                color=(0.18, 0.43, 0.93, 1), size_hint_y=None, height=dp(26), halign="left",
            )
            self.add_widget(tl)


def header(parent, title, sub=""):
    box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(54), padding=(dp(2), 0))
    box.add_widget(Label(
        text=title, font_name=cn(), font_size=dp(20), bold=True,
        color=(0.12, 0.15, 0.2, 1), size_hint_y=None, height=dp(30), halign="left",
    ))
    if sub:
        box.add_widget(Label(
            text=sub, font_name=cn(), font_size=dp(13),
            color=(0.36, 0.4, 0.45, 1), size_hint_y=None, height=dp(20), halign="left",
        ))
    parent.add_widget(box)


def empty_hint(parent, msg="暂无数据"):
    parent.add_widget(Label(
        text=msg, font_name=cn(), font_size=dp(14),
        color=(0.48, 0.52, 0.58, 1), size_hint_y=None, height=dp(44), halign="left",
    ))


def paper_spinner(values, current, callback):
    """卷型筛选下拉（用于趋势/诊断/对比等屏）。current 为空串表示「全部」。"""
    sp = Spinner(
        text=current or "全部卷型",
        values=["全部卷型"] + list(values),
        size_hint=(None, None), height=dp(36), width=dp(150),
        font_name=cn(), font_size=dp(13),
        background_color=(0.96, 0.97, 0.99, 1), color=(0.2, 0.24, 0.3, 1),
    )
    sp.bind(text=lambda inst, txt: callback("" if txt == "全部卷型" else txt))
    return sp


def kv_button(text, on_press=None, bg=(0.18, 0.43, 0.93, 1), fg=(1, 1, 1, 1),
             size_hint=(1, None), height=dp(44), font_size=dp(15)):
    b = Button(
        text=text, size_hint=size_hint, height=height, font_name=cn(),
        font_size=font_size, background_color=bg, color=fg,
    )
    if on_press:
        b.bind(on_press=on_press)
    return b
