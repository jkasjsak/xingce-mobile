# -*- coding: utf-8 -*-
"""录入成绩：12 模块答题卡（每模块题量按卷型自动取，填错题数），支持编辑。"""
from datetime import date

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.metrics import dp

from ui import make_scroll, header, Card, kv_button, cn, paper_spinner
from core import pct, ACCENT
from screens.base import BaseScreen
from data_store import PAPER_TYPES


class AddScreen(BaseScreen):
    def on_enter(self):
        eid = self.app().edit_eid
        if self._built and getattr(self, "_built_eid", None) == eid:
            return
        self._built_eid = eid
        # 内联重建（避免调用 BaseScreen.rebuild 触发 on_enter 递归）
        self.clear_widgets()
        self._built = False
        sv, box = make_scroll()
        self.box = box
        self.add_widget(sv)
        self.build(box)
        self._built = True

    def build(self, box):
        store = self.app().store
        eid = self.app().edit_eid
        editing = eid is not None
        exam = store.get_exam(eid) if editing else None

        header(box, "录入成绩" if not editing else "编辑成绩", "填写每模块错题数")

        # 基本信息
        info = Card(title="基本信息")
        self.date_input = TextInput(
            text=(exam.get("date") if exam else date.today().isoformat()),
            size_hint=(1, None), height=dp(38), font_name=cn(), font_size=dp(13),
            multiline=False,
        )
        self.name_input = TextInput(
            text=(exam.get("name", "") if exam else ""),
            hint_text="考试名称（可选）", size_hint=(1, None), height=dp(38),
            font_name=cn(), font_size=dp(13), multiline=False,
        )
        default_pt = (exam.get("paper_type") if exam else "江苏A类")
        self.pt = default_pt
        sp = paper_spinner(PAPER_TYPES, default_pt, self._on_paper)
        info.add_widget(_labelled("日期", self.date_input))
        info.add_widget(_labelled("名称", self.name_input))
        info.add_widget(_labelled("卷型", sp))
        box.add_widget(info)

        # 模块答题卡
        card = Card(title="答题卡（填错题数）")
        self.wrong_inputs = {}
        self.total_labels = {}
        modules = store.modules()
        existing = exam.get("modules", {}) if exam else {}
        for m in modules:
            key = m["key"]
            total = store.paper_total(key, self.pt)
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(6))
            name_lb = Label(
                text=m["name"], font_name=cn(), font_size=dp(13),
                color=(0.2, 0.24, 0.3, 1), size_hint=(0.42, 1), halign="left",
            )
            tlabel = Label(
                text=f"共{total}题", font_name=cn(), font_size=dp(12),
                color=(0.45, 0.5, 0.56, 1), size_hint=(0.2, 1), halign="center",
            )
            self.total_labels[key] = tlabel
            wi = TextInput(
                text=str(existing.get(key, {}).get("wrong", "") if isinstance(existing.get(key), dict) else ""),
                hint_text="错题", input_filter="int", input_type="number",
                size_hint=(0.22, 1),
                font_name=cn(), font_size=dp(13), multiline=False,
            )
            self.wrong_inputs[key] = wi
            acc_lb = Label(text="", font_name=cn(), font_size=dp(12),
                          color=(0.18, 0.43, 0.93, 1), size_hint=(0.16, 1), halign="right")
            wi.bind(text=lambda inst, val, k=key, tl=tlabel, al=acc_lb: self._update_acc(k, tl, al))
            row.add_widget(name_lb)
            row.add_widget(tlabel)
            row.add_widget(wi)
            row.add_widget(acc_lb)
            card.add_widget(row)
        box.add_widget(card)

        # 操作
        actions = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        save_bg = (0.18, 0.43, 0.93, 1)
        actions.add_widget(kv_button("💾 保存", lambda *a: self._save(), bg=save_bg))
        actions.add_widget(kv_button("清空", lambda *a: self._reset(exam), bg=(0.6, 0.64, 0.7, 1)))
        box.add_widget(actions)

    def _on_paper(self, pt):
        self.pt = pt
        store = self.app().store
        for key, tl in self.total_labels.items():
            tl.text = f"共{store.paper_total(key, pt)}题"

    def _update_acc(self, key, tlabel, acc_lb):
        try:
            total = int(tlabel.text.replace("共", "").replace("题", ""))
        except Exception:
            total = 0
        raw = self.wrong_inputs[key].text.strip()
        if not raw:
            acc_lb.text = ""
            return
        wrong = min(max(0, int(raw)), total) if total > 0 else 0
        if total > 0:
            acc = (total - wrong) / total
            acc_lb.text = pct(acc)
        else:
            acc_lb.text = "—"

    def _reset(self, exam):
        self.rebuild()

    def _save(self):
        store = self.app().store
        eid = self.app().edit_eid
        pt = self.pt
        modules = {}
        for m in store.modules():
            key = m["key"]
            total = store.paper_total(key, pt)
            raw = self.wrong_inputs[key].text.strip()
            if total <= 0:
                modules[key] = {"total": 0, "wrong": 0}
                continue
            try:
                wrong = int(raw) if raw else 0
            except Exception:
                wrong = 0
            wrong = min(max(0, wrong), total)
            modules[key] = {"total": total, "wrong": wrong}

        date_str = self.date_input.text.strip() or date.today().isoformat()
        name = self.name_input.text.strip()

        pending = getattr(self.app(), "pending_timer", None) or {}
        if eid:
            store.update_exam(eid, date=date_str, name=name, paper_type=pt, modules=modules,
                              duration_min=pending.get("duration_min"),
                              start_time=pending.get("start_time"),
                              end_time=pending.get("end_time"))
            msg = "已更新成绩"
        else:
            store.add_exam(date_str, name, modules, paper_type=pt,
                           duration_min=pending.get("duration_min"),
                           start_time=pending.get("start_time"),
                           end_time=pending.get("end_time"))
            msg = "已保存成绩"

        self.app().pending_timer = None
        self.app().edit_eid = None
        self.app().refresh_all()
        self.app().toast(msg)
        self.app().go("overview")


def _labelled(label, widget):
    box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(38), spacing=dp(8))
    box.add_widget(Label(
        text=label, font_name=cn(), font_size=dp(13),
        color=(0.36, 0.4, 0.45, 1), size_hint=(0.22, 1), halign="left",
    ))
    box.add_widget(widget)
    return box
