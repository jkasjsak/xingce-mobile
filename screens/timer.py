# -*- coding: utf-8 -*-
"""考试计时：开始 / 暂停 / 继续 / 重置 / 结束并录入。状态持久化到数据文件。"""
from datetime import datetime

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp

from ui import make_scroll, header, Card, kv_button, cn
from core import fmt_elapsed, fmt_dur, ACCENT
from screens.base import BaseScreen


class TimerScreen(BaseScreen):
    def on_enter(self):
        if not self._built:
            sv, box = make_scroll()
            self.box = box
            self.add_widget(sv)
            self.build(box)
            self._built = True
        self._start_clock()

    def on_leave(self):
        self._stop_clock()

    def _start_clock(self):
        self._stop_clock()
        self._evt = Clock.schedule_interval(lambda dt: self._tick(), 1)

    def _stop_clock(self):
        if getattr(self, "_evt", None):
            self._evt.cancel()
            self._evt = None

    def build(self, box):
        header(box, "考试计时", "记录本场模考已用时")
        t = self.app().timer

        big = Card(title="")
        self.elapsed_label = Label(
            text=fmt_elapsed(t.elapsed()), font_name=cn(), font_size=dp(46), bold=True,
            color=(0.12, 0.15, 0.2, 1), size_hint_y=None, height=dp(70), halign="center",
        )
        big.add_widget(self.elapsed_label)
        self.status_label = Label(
            text=self._status_text(), font_name=cn(), font_size=dp(14),
            color=(0.45, 0.5, 0.56, 1), size_hint_y=None, height=dp(26), halign="center",
        )
        big.add_widget(self.status_label)
        box.add_widget(big)

        self.btn_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        box.add_widget(self.btn_row)
        self._refresh_buttons()

        box.add_widget(kv_button(
            "结束并记录用时 → 录入成绩", self._finish,
            bg=(0.13, 0.63, 0.42, 1), size_hint=(1, None),
        ))

    def _status_text(self):
        t = self.app().timer
        s = t.state
        if s["end"]:
            return "已结束"
        if s["paused"]:
            return "已暂停"
        if s["running"]:
            return "计时中…"
        return "未开始"

    def _refresh_buttons(self):
        self.btn_row.clear_widgets()
        t = self.app().timer
        s = t.state
        if not s["start"] or s["end"]:
            self.btn_row.add_widget(kv_button("▶ 开始", self._start, bg=ACCENT))
        elif s["paused"]:
            self.btn_row.add_widget(kv_button("▶ 继续", self._resume, bg=(0.13, 0.63, 0.42, 1)))
            self.btn_row.add_widget(kv_button("⏹ 重置", self._reset, bg=(0.6, 0.64, 0.7, 1)))
        else:
            self.btn_row.add_widget(kv_button("⏸ 暂停", self._pause, bg=(0.88, 0.57, 0.17, 1)))
            self.btn_row.add_widget(kv_button("⏹ 重置", self._reset, bg=(0.6, 0.64, 0.7, 1)))

    def _tick(self):
        try:
            self.elapsed_label.text = fmt_elapsed(self.app().timer.elapsed())
        except Exception:
            pass

    def _start(self):
        try:
            self.app().timer.start()
            self._after_action()
        except Exception:
            import traceback; traceback.print_exc()

    def _pause(self):
        try:
            self.app().timer.pause()
            self._after_action()
        except Exception:
            import traceback; traceback.print_exc()

    def _resume(self):
        try:
            self.app().timer.resume()
            self._after_action()
        except Exception:
            import traceback; traceback.print_exc()

    def _reset(self):
        try:
            self.app().timer.reset()
            self.status_label.text = self._status_text()
            self.elapsed_label.text = fmt_elapsed(0)
            self._refresh_buttons()
        except Exception:
            import traceback; traceback.print_exc()

    def _after_action(self):
        try:
            self.status_label.text = self._status_text()
            self.elapsed_label.text = fmt_elapsed(self.app().timer.elapsed())
            self._refresh_buttons()
        except Exception:
            import traceback; traceback.print_exc()

    def _finish(self):
        try:
            t = self.app().timer
            sec = t.elapsed()
            dur_min = round(sec / 60.0, 1)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st = t.state.get("start")
            self.app().pending_timer = {
                "duration_min": dur_min,
                "start_time": st.strftime("%Y-%m-%d %H:%M:%S") if isinstance(st, datetime) else None,
                "end_time": now,
            }
            t.reset()
            self._after_action()
            self.app().open_add(None)
        except Exception:
            import traceback; traceback.print_exc()
