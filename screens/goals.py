# -*- coding: utf-8 -*-
"""目标追踪：设定总体 / 分模块目标正确率，并展示当前达成进度。"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.metrics import dp

from ui import make_scroll, header, Card, kv_button, paper_spinner, cn
from core import pct, ACCENT, GREEN, ORANGE
from screens.base import BaseScreen


class GoalsScreen(BaseScreen):
    def build(self, box):
        header(box, "目标追踪", "设定目标并查看达成进度")
        self.pt = self.app().paper_filter or ""
        sp = paper_spinner(self.app().store.all_paper_types(), self.pt, self._on_filter)
        row = BoxLayout(size_hint_y=None, height=dp(40))
        row.add_widget(sp)
        box.add_widget(row)
        self.body = BoxLayout(orientation="vertical")
        box.add_widget(self.body)
        self._render()

    def _on_filter(self, pt):
        self.pt = pt or ""
        self.app().paper_filter = self.pt or None
        self._render()

    def _goal_key(self):
        return self.pt or "总计"

    def _render(self):
        self.body.clear_widgets()
        store = self.app().store
        pts = [self.pt] if self.pt else None
        gk = self._goal_key()

        # 总体目标
        overall = store.get_overall_goal(pts)
        oc = Card(title="总体目标正确率")
        self.ov_input = TextInput(
            text=f"{overall*100:.0f}", input_filter="int", size_hint=(1, None),
            height=dp(38), font_name=cn(), font_size=dp(13), multiline=False,
        )
        line = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        line.add_widget(Label(text="目标(%)", font_name=cn(), font_size=dp(13),
                              color=(0.36, 0.4, 0.45, 1), size_hint=(0.3, 1)))
        line.add_widget(self.ov_input)
        oc.add_widget(line)
        oc.add_widget(kv_button("保存总体目标", self._save_overall, size_hint=(1, None)))
        # 当前总体正确率 vs 目标
        trend = store.overall_trend(paper_types=pts)
        if trend:
            cur = trend[-1][1]
            ok = cur >= overall
            oc.add_widget(Label(
                text=f"当前最新：{pct(cur)}  /  目标 {pct(overall)}  {'✅' if ok else '⚠️未达标'}",
                font_name=cn(), font_size=dp(12), color=(0.13,0.63,0.42,1) if ok else (0.9,0.33,0.29,1),
                size_hint_y=None, height=dp(24), halign="left",
            ))
        self.body.add_widget(oc)

        # 分模块目标
        mc = Card(title="分模块目标")
        self.mod_inputs = {}
        for m in store.modules():
            cur = store.module_avg(m["key"], pts)
            goal = store.get_module_goal(m["key"], pts)
            row = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(6))
            row.add_widget(Label(text=m["name"], font_name=cn(), font_size=dp(12),
                                color=(0.2,0.24,0.3,1), size_hint=(0.32, 1), halign="left"))
            row.add_widget(Label(text=f"当前{pct(cur)}", font_name=cn(), font_size=dp(11),
                                color=(0.45,0.5,0.56,1), size_hint=(0.24, 1)))
            ti = TextInput(text=(f"{goal*100:.0f}" if goal is not None else ""),
                           hint_text="目标%", input_filter="int",
                           size_hint=(0.22, 1), font_name=cn(), font_size=dp(12), multiline=False)
            self.mod_inputs[m["key"]] = ti
            row.add_widget(ti)
            mc.add_widget(row)
        mc.add_widget(kv_button("保存分模块目标", self._save_modules, size_hint=(1, None)))
        self.body.add_widget(mc)

    def _save_overall(self):
        try:
            v = float(self.ov_input.text.strip()) / 100.0
        except Exception:
            self.app().toast("请输入数字")
            return
        self.app().store.set_overall_goal(self._goal_key(), v)
        self.app().toast("已保存总体目标")

    def _save_modules(self):
        store = self.app().store
        for key, ti in self.mod_inputs.items():
            raw = ti.text.strip()
            if not raw:
                continue
            try:
                v = float(raw) / 100.0
            except Exception:
                continue
            store.set_module_goal(self._goal_key(), key, v)
        self.app().toast("已保存分模块目标")
