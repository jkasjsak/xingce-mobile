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

# ---- 崩溃自报：捕获导入/启动期异常并显示在屏幕上，避免“直接闪退无提示” ----
import traceback as _tb

_CRASH_PATH = None


def _crash_path():
    global _CRASH_PATH
    if _CRASH_PATH is None:
        try:
            _CRASH_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xingce_crash.log")
        except Exception:
            _CRASH_PATH = os.path.join(os.getcwd(), "xingce_crash.log")
    return _CRASH_PATH


def _write_crash(text):
    try:
        with open(_crash_path(), "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass


def _excepthook(et, ev, tb):
    text = "".join(_tb.format_exception(et, ev, tb))
    _write_crash("=== Python 未捕获异常 ===\n" + text)
    try:
        sys.__excepthook__(et, ev, tb)
    except Exception:
        pass


sys.excepthook = _excepthook

# 原生崩溃（C 层 segfault，如 SDL_ttf/numpy）也会把栈写到 logcat，便于定位
try:
    import faulthandler
    faulthandler.enable()
except Exception:
    pass

_IMPORT_ERROR = None  # 各屏/图表导入期异常，build() 时显示到屏幕

# 所有「导入期」代码统一保护：任何一处（core / kivy / data_store / ui / 9 个屏）
# 在安卓上失败都不再直接闪退无提示，而是记录并在 build() 显示到屏幕。
# （#21/#30 长期闪退根因未知，先让 Python 层错误可见；原生崩溃仍需 adb logcat）
try:
    from core import TimerController, C, CN_FONT, VERSION
    # 必须在导入任何 kivy 控件之前设置全局默认字体，否则 TextInput 的 IME 候选词、
    # 以及未显式指定 font_name 的控件仍会用 Roboto（无中文字形）→ 中文乱码（#11）。
    # CN_FONT 是打包进 assets 的纯 TrueType（glyf），Kivy/SDL2 可稳定渲染。
    from kivy.config import Config
    if CN_FONT:
        # 必须是「逗号分隔的字符串」，不能传 list：Kivy 在导入 kivy.core.text 时会
        # 对 default_font 调 .split(',')，传 list 会在启动时 AttributeError 直接闪退。
        Config.set("kivy", "default_font", f"{CN_FONT},Roboto,DejaVuSans")
    from kivy.app import App
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.scrollview import ScrollView
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.metrics import dp
    from kivy.utils import platform as kivy_platform

    from data_store import DataStore, get_base_dir, PAPER_TYPES
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
except Exception as _e:
    # 导入期异常（如 matplotlib / 某屏语法或运行期错误）不再让整 app 秒退，
    # 而是记录后在 build() 显示到屏幕，便于定位（#21 闪退根因未知，先暴露出来）
    _IMPORT_ERROR = "%s: %s\n%s" % (type(_e).__name__, _e, _tb.format_exc())

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
        # 导入期异常（如 matplotlib / 某屏）已在 main 顶部捕获，这里直接显示，
        # 避免“直接闪退无提示”（#21 闪退根因未知，先暴露出来）
        if _IMPORT_ERROR is not None:
            return self._error_screen("导入失败：\n" + _IMPORT_ERROR)
        try:
            return self._build_ui()
        except Exception:
            return self._error_screen("启动构建失败：\n" + _tb.format_exc())

    def _build_ui(self):
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
            try:
                screen = self._make_screen(name)
                self.sm.add_widget(screen)
            except Exception:
                return self._error_screen("构建屏幕 %s 失败：\n%s" % (name, _tb.format_exc()))
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

    def _error_screen(self, msg):
        """启动期异常可视化：让用户在屏幕上直接看到报错，便于定位（不再“直接闪退无提示”）。"""
        from kivy.uix.screenmanager import ScreenManager, Screen
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.label import Label
        _write_crash(msg)
        sm = ScreenManager()
        sc = Screen(name="error")
        sv = ScrollView(size_hint=(1, 1))
        # 用 Kivy 内置 Roboto，避免依赖自定义字体导致二次崩溃
        lb = Label(
            text="行测APP启动失败\n\n" + msg,
            font_name="Roboto", font_size=dp(13),
            color=(0.85, 0.15, 0.15, 1),
            size_hint_y=None, text_size=(dp(360), None),
            halign="left", valign="top",
        )
        lb.bind(texture_size=lb.setter("height"))
        sv.add_widget(lb)
        sc.add_widget(sv)
        sm.add_widget(sc)
        return sm

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

    def refresh_all(self, exclude=None):
        """数据变更后刷新相关屏。

        只重建「已经构建过」的屏（未访问的屏首次进入时会自构建，无需提前重建），
        并用 Clock 错峰调度，避免一次同步重建全部图表导致切页卡顿（#8 #9）。
        默认跳过：计时屏（无数据依赖、误建会启其 Clock）；
        趋势/诊断/对比三屏本就在进入时整屏重建，无需在此预重建
        → 省下 3 次 matplotlib 重绘，进一步去卡顿（#8 #9，A）。
        """
        exc = set(exclude or ["timer", "trends", "modules", "compare"])
        for n, _ in NAV:
            if n in exc:
                continue
            scr = self.sm.get_screen(n)
            if scr and getattr(scr, "_built", False):
                Clock.schedule_once(lambda dt, s=scr: s.rebuild(), 0)

    def on_resume(self):
        """App 从锁屏/后台恢复：若在计时屏，重启计时刷新（#13 锁屏后继续计时）。"""
        scr = self.sm.current_screen
        if scr and getattr(scr, "name", None) == "timer" and hasattr(scr, "_start_clock"):
            scr._start_clock()
        return True

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
    try:
        XingceApp().run()
    except Exception:
        # run() 内未捕获的顶层异常：写文件，便于回看（屏幕型异常已由 build() 拦截）
        _write_crash("=== run() 顶层异常 ===\n" + _tb.format_exc())
        raise
