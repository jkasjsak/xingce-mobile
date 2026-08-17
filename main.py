# -*- coding: utf-8 -*-
"""行测模考分析 · 手机版（Kivy）。

把桌面版（customtkinter + matplotlib）的全部功能移植到手机端：
- 数据层 data_store.py 原样复用（算分 / 估分 / 备份 / 计时持久化，纯 Python）；
- 视图层用 Kivy 重写，图表沿用 matplotlib(Agg) → KivyChart 手势控件；
- 9 个视图：总览 / 录入 / 计时 / 趋势 / 模块诊断 / 对比 / 目标 / 数据 / 记录。

运行（桌面调试）：python main.py
打包安卓：buildozer android debug  （需 buildozer.spec 与本机 Android SDK）
"""
import os
import sys

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import platform as kivy_platform

from data_store import DataStore, get_base_dir, PAPER_TYPES
from core import ACCENT, TimerController, C
from ui import make_scroll, cn

import screens.overview as overview
import screens.add as add
import screens.timer as timer
import screens.trends as trends
import screens.modules as modules
import screens.compare as compare
import screens.goals as goals
import screens.data as data
import screens.exams as exams

NAV = [
    ("overview", "总览"),
    ("add", "录入"),
    ("timer", "计时"),
    ("trends", "趋势"),
    ("modules", "诊断"),
    ("compare", "对比"),
    ("goals", "目标"),
    ("data", "数据"),
    ("exams", "记录"),
]


class XingceApp(App):
    def build(self):
        # 手机端让窗口自动撑满整屏（绝不可写死 Window.size，否则会缩成左下角小方块）；
        # 仅桌面调试时用固定尺寸方便预览。
        if kivy_platform != "android":
            Window.size = (400, 800)
        Window.clearcolor = C("bg")  # 清新浅色背景（根治整体发黑）
        Window.softinput_mode = "below_target"

        base = get_base_dir()
        self.data_path = os.path.join(base, "xingce_mobile_data.json")
        self.store = DataStore(path=self.data_path)
        self.timer = TimerController(self.store)
        self.paper_filter = None  # None = 全部卷型
        self.edit_eid = None      # 录入页编辑态：待编辑考试 id

        root = FloatLayout()
        content = BoxLayout(orientation="vertical")

        # 屏幕管理
        self.sm = __import__("kivy.uix.screenmanager", fromlist=["ScreenManager"]).ScreenManager()
        for name, _ in NAV:
            screen = self._make_screen(name)
            self.sm.add_widget(screen)
        content.add_widget(self.sm)

        # 底部导航（横向滚动，9 个按钮）
        nav = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(2))
        nav_sv = ScrollView(size_hint=(1, None), height=dp(54), do_scroll_y=False,
                            do_scroll_x=True)
        nav_box = BoxLayout(size_hint_x=None, height=dp(54), spacing=dp(2), padding=dp(2))
        nav_box.bind(minimum_width=nav_box.setter("width"))
        self.nav_buttons = {}
        for name, label in NAV:
            b = Button(
                text=label, size_hint=(None, 1), width=dp(66),
                font_name=cn(), font_size=dp(14),
                background_color=C("surface_alt"), color=C("text"),
                on_press=lambda *a, n=name: self.go(n),
            )
            self.nav_buttons[name] = b
            nav_box.add_widget(b)
        nav_sv.add_widget(nav_box)
        nav.add_widget(nav_sv)
        content.add_widget(nav)

        root.add_widget(content)
        self.root = root
        self._highlight("overview")
        return root

    def _make_screen(self, name):
        mapping = {
            "overview": overview.OverviewScreen,
            "add": add.AddScreen,
            "timer": timer.TimerScreen,
            "trends": trends.TrendsScreen,
            "modules": modules.ModulesScreen,
            "compare": compare.CompareScreen,
            "goals": goals.GoalsScreen,
            "data": data.DataScreen,
            "exams": exams.ExamsScreen,
        }
        return mapping[name](name=name)

    # ---- 导航 ----
    def go(self, name):
        self.sm.current = name
        self._highlight(name)

    def _highlight(self, name):
        for n, b in self.nav_buttons.items():
            if n == name:
                b.background_color = C("accent")
                b.color = (1, 1, 1, 1)
            else:
                b.background_color = C("surface_alt")
                b.color = C("text")

    # ---- 数据变更后刷新相关屏 ----
    def refresh(self, *names):
        for n in names:
            scr = self.sm.get_screen(n)
            if scr:
                scr.rebuild()

    def refresh_all(self):
        self.refresh(*[n for n, _ in NAV])

    # ---- 录入编辑态 ----
    def open_add(self, eid=None):
        self.edit_eid = eid
        self.go("add")

    # ---- 轻量 toast ----
    def toast(self, msg, dur=2.0):
        from kivy.uix.label import Label
        from kivy.clock import Clock
        from kivy.graphics import Color, Rectangle
        lb = Label(
            text=msg, font_name=cn(), font_size=dp(14),
            size_hint=(None, None),
            size=(max(dp(140), len(msg) * dp(13) + dp(24)), dp(40)),
            color=(0.12, 0.14, 0.17, 1),
        )
        with lb.canvas.before:
            Color(0.96, 0.97, 0.99, 0.97)
            Rectangle(pos=lb.pos, size=lb.size)
        lb.pos_hint = {"center_x": 0.5, "y": 0.06}
        self.root.add_widget(lb)
        Clock.schedule_once(lambda dt: lb.canvas.before.clear(), dur)
        Clock.schedule_once(lambda dt: self.root.remove_widget(lb), dur)


if __name__ == "__main__":
    XingceApp().run()
