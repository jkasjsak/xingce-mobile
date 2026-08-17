# -*- coding: utf-8 -*-
"""考试对比：选取最近 N 场，按模块分组对比正确率。"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.metrics import dp

from ui import make_scroll, header, Card, empty_hint, cn
from core import ACCENT
from charts import KivyChart
from screens.base import BaseScreen


class CompareScreen(BaseScreen):
    def build(self, box):
        header(box, "考试对比", "多场模考横向对比")
        self.count = 3
        exams = self.app().store.list_exams(reverse=True)
        if len(exams) < 2:
            empty_hint(box, "至少需要 2 场考试才能对比")
            return
        opts = [str(i) for i in range(2, min(len(exams), 6) + 1)]
        sp = Spinner(text=str(self.count), values=opts, size_hint=(None, None),
                     height=dp(36), width=dp(90), font_name=cn(), font_size=dp(13))
        sp.bind(text=lambda inst, t: self._on_count(int(t)))
        row = BoxLayout(size_hint_y=None, height=dp(40))
        row.add_widget(sp)
        box.add_widget(row)
        self.body = BoxLayout(orientation="vertical")
        box.add_widget(self.body)
        self._render()

    def _on_count(self, n):
        self.count = n
        self._render()

    def _render(self):
        self.body.clear_widgets()
        store = self.app().store
        exams = store.list_exams(reverse=True)[:self.count]
        mods = store.modules()
        fig = plt.figure(figsize=(7.0, 4.2), dpi=85)
        ax = fig.add_subplot(111)
        x = np.arange(len(mods))
        width = 0.8 / len(exams)
        palette = ["#2F6FED", "#22a06b", "#E0922B", "#e5534b", "#9b59b6"]
        for i, e in enumerate(exams):
            st = store.exam_stat(e)
            ys = [st["per"].get(m["key"], {}).get("acc", 0) * 100 for m in mods]
            ax.bar(x + i * width, ys, width, label=e.get("date", "") + " " + (e.get("name", "") or ""),
                   color=palette[i % len(palette)])
        ax.set_xticks(x + width * (len(exams) - 1) / 2)
        ax.set_xticklabels([m["name"] for m in mods], rotation=45, ha="right", fontsize=7)
        ax.set_ylabel("正确率%", fontsize=9)
        ax.set_ylim(0, 100)
        ax.legend(fontsize=7, loc="upper right")
        ax.grid(True, axis="y", linestyle=":", alpha=0.4)
        ax.set_title("各模块正确率对比", fontsize=11)
        fig.tight_layout()
        chart = KivyChart(figsize=(7.0, 4.2))
        chart.set_figure(fig)
        wrap = Card(title=f"最近 {self.count} 场对比")
        wrap.add_widget(chart)
        self.body.add_widget(wrap)
