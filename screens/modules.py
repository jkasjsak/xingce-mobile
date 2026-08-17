# -*- coding: utf-8 -*-
"""模块诊断：雷达图（12 模块平均正确率）+ 各模块正确率柱状。"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp

from ui import make_scroll, header, Card, empty_hint, paper_spinner
from core import ACCENT
from charts import KivyChart
from screens.base import BaseScreen


class ModulesScreen(BaseScreen):
    def build(self, box):
        header(box, "模块诊断", "各模块平均正确率")
        self.pt = self.app().paper_filter or ""
        sp = paper_spinner(self.app().store.all_paper_types(), self.pt, self._on_filter)
        bar = BoxLayout(size_hint_y=None, height=dp(40))
        bar.add_widget(sp)
        box.add_widget(bar)
        self.body = BoxLayout(orientation="vertical", size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height"))
        box.add_widget(self.body)
        self._render()

    def _on_filter(self, pt):
        self.pt = pt or ""
        self.app().paper_filter = self.pt or None
        self._render()

    def _render(self):
        self.body.clear_widgets()
        store = self.app().store
        pts = [self.pt] if self.pt else None
        mods = store.modules()
        avgs = [(m, store.module_avg(m["key"], pts)) for m in mods]
        if not any(a for _, a in avgs):
            empty_hint(self.body, "暂无考试数据")
            return

        # 雷达图（极坐标，r 0~100）
        fig = plt.figure(figsize=(6.8, 5.4), dpi=85)
        ax = fig.add_subplot(111, polar=True)
        keys = [m["key"] for m in mods]
        vals = [store.module_avg(k, pts) * 100 for k in keys]
        angles = np.linspace(0, 2 * np.pi, len(keys), endpoint=False).tolist()
        vals_c = vals + [vals[0]]
        angles_c = angles + [angles[0]]
        ax.plot(angles_c, vals_c, color=ACCENT, linewidth=2)
        ax.fill(angles_c, vals_c, color=ACCENT, alpha=0.22)
        ax.set_xticks(angles)
        ax.set_xticklabels([m["name"] for m in mods], fontsize=8)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=7, color="#888")
        ax.set_title("12 模块平均正确率雷达", fontsize=11)
        fig.tight_layout()
        radar = KivyChart(figsize=(6.8, 5.4))
        radar.set_figure(fig)
        wrap = Card(title="正确率雷达")
        wrap.add_widget(radar)
        self.body.add_widget(wrap)

        # 柱状：各模块平均正确率（薄弱在前）
        fig2 = plt.figure(figsize=(7.0, 3.8), dpi=85)
        ax2 = fig2.add_subplot(111)
        sorted_m = sorted(avgs, key=lambda x: x[1])
        names = [m["name"] for m, _ in sorted_m]
        ys = [a * 100 for _, a in sorted_m]
        colors = ["#e5534b" if v < 60 else ("#E0922B" if v < 75 else "#22a06b") for v in ys]
        ax2.bar(range(len(names)), ys, color=colors)
        ax2.set_xticks(range(len(names)))
        ax2.set_xticklabels(names, rotation=45, ha="right", fontsize=7)
        ax2.set_ylabel("正确率%", fontsize=9)
        ax2.set_ylim(0, 100)
        ax2.grid(True, axis="y", linestyle=":", alpha=0.4)
        ax2.set_title("各模块平均正确率", fontsize=11)
        fig2.tight_layout()
        bar = KivyChart(figsize=(7.0, 3.8))
        bar.set_figure(fig2)
        wrap2 = Card(title="模块正确率对比")
        wrap2.add_widget(bar)
        self.body.add_widget(wrap2)
