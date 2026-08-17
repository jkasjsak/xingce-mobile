# -*- coding: utf-8 -*-
"""考试记录：列表 / 详情 / 编辑 / 删除。"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.modalview import ModalView
from kivy.metrics import dp

from ui import make_scroll, header, Card, empty_hint, kv_button, cn
from core import pct
from screens.base import BaseScreen


class ExamsScreen(BaseScreen):
    def build(self, box):
        header(box, "考试记录", "全部模考场次")
        store = self.app().store
        exams = store.list_exams(reverse=True)
        if not exams:
            empty_hint(box, "还没有考试记录")
            return
        for e in exams:
            st = store.exam_stat(e)
            est = store.score_estimate(e)
            row = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(56), spacing=dp(2),
                            padding=(dp(4), dp(2)))
            row.add_widget(Label(
                text=f"{e.get('date','')}  {e.get('name','')}", font_name=cn(), font_size=dp(14),
                bold=True, color=(0.12,0.15,0.2,1), size_hint_y=None, height=dp(24), halign="left",
            ))
            row.add_widget(Label(
                text=f"{e.get('paper_type','')} · 正确率 {pct(st['overall_acc'])} · 估分 {est['score']:.1f}{(' · 用时'+str(e.get('duration_min'))+'分') if e.get('duration_min') else ''}",
                font_name=cn(), font_size=dp(12), color=(0.45,0.5,0.56,1),
                size_hint_y=None, height=dp(20), halign="left",
            ))
            row.bind(on_touch_down=lambda inst, ev, ex=e: self._open_detail(ex) if inst.collide_point(*ev.pos) and ev.button == "left" else None)
            box.add_widget(row)

    def _open_detail(self, exam):
        store = self.app().store
        st = store.exam_stat(exam)
        est = store.score_estimate(exam)
        mv = ModalView(size_hint=(0.92, 0.82))
        sv, body = make_scroll()
        body.add_widget(Label(text=f"{exam.get('date','')} {exam.get('name','')}", font_name=cn(),
                              font_size=dp(18), bold=True, color=(0.12,0.15,0.2,1),
                              size_hint_y=None, height=dp(30), halign="left"))
        info = Card(title="概览")
        info.add_widget(_kv("卷型", exam.get("paper_type", "")))
        info.add_widget(_kv("总体正确率", pct(st["overall_acc"])))
        info.add_widget(_kv("预估成绩", f"{est['score']:.1f} 分"))
        if exam.get("duration_min"):
            info.add_widget(_kv("用时", f"{exam['duration_min']} 分钟"))
        body.add_widget(info)

        mc = Card(title="各模块正确率")
        for m in store.modules():
            p = st["per"].get(m["key"])
            if p and p["total"] > 0:
                mc.add_widget(_kv(m["name"], f"{pct(p['acc'])}（{p['correct']}/{p['total']}）"))
        body.add_widget(mc)

        actions = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        actions.add_widget(kv_button("编辑", lambda *a: self._edit(exam, mv), bg=(0.18,0.43,0.93,1)))
        actions.add_widget(kv_button("删除", lambda *a: self._delete(exam, mv), bg=(0.9,0.33,0.29,1)))
        actions.add_widget(kv_button("关闭", lambda *a: mv.dismiss(), bg=(0.6,0.64,0.7,1)))
        body.add_widget(actions)
        mv.add_widget(sv)
        mv.open()

    def _edit(self, exam, mv):
        mv.dismiss()
        self.app().open_add(exam["id"])

    def _delete(self, exam, mv):
        mv.dismiss()
        self.app().store.delete_exam(exam["id"])
        self.app().refresh_all()
        self.app().toast("已删除")


def _kv(k, v):
    box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26))
    box.add_widget(Label(text=k, font_name=cn(), font_size=dp(13),
                         color=(0.36,0.4,0.45,1), size_hint=(0.4,1), halign="left"))
    box.add_widget(Label(text=v, font_name=cn(), font_size=dp(13),
                         color=(0.18,0.43,0.93,1), size_hint=(0.6,1), halign="right"))
    return box
