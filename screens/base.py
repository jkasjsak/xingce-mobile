# -*- coding: utf-8 -*-
"""Screen 基类：进入时懒加载构建一次并缓存复用（对应桌面版 grid 缓存复用）。

app.set_paper_filter / app.invalidate 需要强制刷新时调用 screen.rebuild()。
"""
from kivy.uix.screenmanager import Screen
from kivy.app import App
from ui import make_scroll


class BaseScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._built = False
        self.box = None

    def on_enter(self):
        if not self._built:
            sv, box = make_scroll()
            self.box = box
            self.add_widget(sv)
            self.build(box)
            self._built = True

    def rebuild(self):
        self.clear_widgets()
        self._built = False
        self.on_enter()

    def build(self, box):
        raise NotImplementedError

    def app(self):
        return App.get_running_app()
