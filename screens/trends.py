# -*- coding: utf-8 -*-
"""趋势分析：总体正确率折线、用时柱状（按卷型筛选）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp

from ui import make_scroll, header, Card, empty_hint, paper_spinner, cn
from core import CN_FONT, ACCENT
from charts import KivyChart
from screens.base import BaseScreen


def _fig():
    fig = plt.figure(figsize=(7.0, 3.6), dpi=85)
    return fig


class TrendsScreen(BaseScreen):
    def build(self, box):
        header(box, "趋势分析", "正确率 / 用时随时间变化")
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
        trend = store.overall_trend(paper_types=pts)
        if not trend:
            empty_hint(self.body, "暂无考试数据")
            return

        # 折线：总体正确率
        fig = _fig()
        ax = fig.add_subplot(111)
        xs = [t[0] for t in trend]
        ys = [t[1] * 100 for t in trend]
        ax.plot(range(len(xs)), ys, marker="o", color=ACCENT, linewidth=2)
        ax.set_xticks(range(len(xs)))
        ax.set_xticklabels(xs, rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("正确率%", fontsize=9)
        ax.set_ylim(0, 100)
        ax.set_title("总体正确率走势", fontsize=11)
        ax.grid(True, linestyle=":", alpha=0.4)
        fig.tight_layout()
        c1 = KivyChart(figsize=(7.0, 3.6))
        c1.set_figure(fig)
        wrap = Card(title="正确率走势")
        wrap.add_widget(c1)
        self.body.add_widget(wrap)

        # 柱状：用时
        dur = store.duration_trend(paper_types=pts)
        if dur:
            fig2 = _fig()
            ax2 = fig2.add_subplot(111)
            dx = [d[0] for d in dur]
            dy = [d[1] for d in dur]
            ax2.bar(range(len(dx)), dy, color="#E0922B")
            ax2.set_xticks(range(len(dx)))
            ax2.set_xticklabels(dx, rotation=45, ha="right", fontsize=8)
            ax2.set_ylabel("分钟", fontsize=9)
            ax2.set_title("考试用时", fontsize=11)
            ax2.grid(True, axis="y", linestyle=":", alpha=0.4)
            fig2.tight_layout()
            c2 = KivyChart(figsize=(7.0, 3.6))
            c2.set_figure(fig2)
            wrap2 = Card(title="用时分布")
            wrap2.add_widget(c2)
            self.body.add_widget(wrap2)
