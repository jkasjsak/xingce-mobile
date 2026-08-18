# -*- coding: utf-8 -*-
"""总览看板：概览统计、最近考试、智能洞察、薄弱模块、达标进度。"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp

from ui import make_scroll, header, Card, empty_hint, kv_button, cn
from core import pct, ACCENT
from screens.base import BaseScreen


def _row(parent, label, value, color=(0.12, 0.15, 0.2, 1)):
    box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28))
    box.add_widget(Label(
        text=label, font_name=cn(), font_size=dp(13),
        color=(0.36, 0.4, 0.45, 1), size_hint=(0.6, 1), halign="left",
    ))
    box.add_widget(Label(
        text=value, font_name=cn(), font_size=dp(13), bold=True,
        color=color, size_hint=(0.4, 1), halign="right",
    ))
    parent.add_widget(box)


class OverviewScreen(BaseScreen):
    def build(self, box):
        store = self.app().store
        pf = self.app().paper_filter
        pts = [pf] if pf else None
        header(box, "总览", "模考数据一览")

        exams = store.list_exams(reverse=True, paper_types=pts)
        # 概览卡
        card = Card(title="概览")
        if not exams:
            empty_hint(card, "还没有考试记录，点「录入」添加第一场模考。")
        else:
            latest = exams[0]
            est = store.score_estimate(latest)
            st = store.exam_stat(latest)
            _row(card, "考试场次", f"{len(store.list_exams(paper_types=pts))} 场")
            _row(card, "最新估分", f"{est['score']:.1f} 分", (0.13, 0.63, 0.42, 1))
            _row(card, "最新正确率", pct(st["overall_acc"]), (0.18, 0.43, 0.93, 1))
            trend = store.overall_trend(paper_types=pts)
            if len(trend) >= 2:
                first_acc = trend[0][1]
                last_acc = trend[-1][1]
                delta = last_acc - first_acc
                arrow = "↑" if delta > 0.005 else ("↓" if delta < -0.005 else "→")
                sc = (0.13, 0.63, 0.42, 1) if delta >= 0 else (0.9, 0.33, 0.29, 1)
                _row(card, "正确率走向",
                     f"{arrow} {first_acc*100:.1f}%→{last_acc*100:.1f}%（{abs(delta)*100:.1f}点）", sc)
            else:
                _row(card, "正确率走向", "样本不足（≥2场）", (0.45, 0.5, 0.56, 1))
            goal = store.get_overall_goal(paper_types=pts)
            _row(card, "总体目标", pct(goal), (0.88, 0.57, 0.17, 1))
        box.add_widget(card)

        # 智能洞察
        ins_card = Card(title="智能洞察")
        for line in store.insights(paper_types=pts):
            ins_card.add_widget(Label(
                text="• " + line, font_name=cn(), font_size=dp(13),
                color=(0.25, 0.29, 0.35, 1), size_hint_y=None,
                height=dp(20) * max(1, int(len(line) / 22) + 1),
                halign="left", text_size=(dp(330), None),
            ))
        box.add_widget(ins_card)

        # 薄弱模块
        wk = store.weaknesses(paper_types=pts)
        if wk:
            wk_card = Card(title="薄弱模块（优先突破）")
            for m, avg in wk[:4]:
                _row(wk_card, m["name"], pct(avg), (0.9, 0.33, 0.29, 1))
            box.add_widget(wk_card)

        # 最近考试
        if exams:
            rec_card = Card(title="最近考试")
            for e in exams[:6]:
                est = store.score_estimate(e)
                st = store.exam_stat(e)
                sub = f"{e.get('paper_type','')} · 正确率 {pct(st['overall_acc'])} · 估分 {est['score']:.1f}"
                row2 = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(46), spacing=dp(2))
                row2.add_widget(Label(
                    text=f"{e.get('date','')} {e.get('name','')}", font_name=cn(),
                    font_size=dp(14), bold=True, color=(0.12, 0.15, 0.2, 1),
                    size_hint_y=None, height=dp(22), halign="left",
                ))
                row2.add_widget(Label(
                    text=sub, font_name=cn(), font_size=dp(12),
                    color=(0.45, 0.5, 0.56, 1), size_hint_y=None, height=dp(20), halign="left",
                ))
                rec_card.add_widget(row2)
            box.add_widget(rec_card)

        box.add_widget(kv_button("＋ 录入成绩", lambda *a: self.app().open_add(None), size_hint=(1, None)))
