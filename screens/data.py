# -*- coding: utf-8 -*-
"""数据管理：导入 / 导出、自定义模块与卷型、备份恢复。"""
import os
import datetime

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.metrics import dp

from ui import make_scroll, header, Card, kv_button, cn
from core import ACCENT, C, VERSION
from screens.base import BaseScreen
from data_store import PAPER_TYPES

MODULE_COLORS = ["#EF6F6C", "#E5945C", "#C084CB", "#5AA9E6", "#4FC0A8",
                 "#F2C14E", "#9b59b6", "#3E8FCF", "#e5534b", "#22a06b"]


class DataScreen(BaseScreen):
    def build(self, box):
        header(box, "数据管理", "导入导出 · 自定义 · 备份")
        store = self.app().store

        # 导入导出
        io_card = Card(title="数据文件")
        io_card.add_widget(kv_button("⬆ 导出 JSON", self._export, bg=(0.18, 0.43, 0.93, 1), size_hint=(1, None)))
        io_card.add_widget(kv_button("⬇ 导入 JSON", self._import, bg=(0.13, 0.63, 0.42, 1), size_hint=(1, None)))
        box.add_widget(io_card)

        # 自定义模块
        mod_card = Card(title="自定义模块")
        self.mod_box = BoxLayout(orientation="vertical", size_hint_y=None)
        self.mod_box.bind(minimum_height=self.mod_box.setter("height"))
        mod_card.add_widget(self.mod_box)
        self._render_modules()
        add_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        self.new_mod_name = TextInput(hint_text="模块名", size_hint=(0.6, 1), font_name=cn(), font_size=dp(12), multiline=False)
        self.new_mod_total = TextInput(hint_text="题量", input_filter="int", size_hint=(0.25, 1), font_name=cn(), font_size=dp(12), multiline=False)
        add_row.add_widget(self.new_mod_name)
        add_row.add_widget(self.new_mod_total)
        add_row.add_widget(kv_button("＋", self._add_module, bg=(0.18, 0.43, 0.93, 1), size_hint=(0.15, 1), height=dp(40), font_size=dp(16)))
        mod_card.add_widget(add_row)
        box.add_widget(mod_card)

        # 自定义卷型
        paper_card = Card(title="自定义卷型")
        self.paper_box = BoxLayout(orientation="vertical", size_hint_y=None)
        self.paper_box.bind(minimum_height=self.paper_box.setter("height"))
        paper_card.add_widget(self.paper_box)
        self._render_papers()
        add_p = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        self.new_paper_name = TextInput(hint_text="卷型名", size_hint=(0.8, 1), font_name=cn(), font_size=dp(12), multiline=False)
        add_p.add_widget(self.new_paper_name)
        add_p.add_widget(kv_button("＋", self._add_paper, bg=(0.18, 0.43, 0.93, 1), size_hint=(0.2, 1), height=dp(40), font_size=dp(16)))
        paper_card.add_widget(add_p)
        box.add_widget(paper_card)

        # 备份
        bak_card = Card(title="备份与恢复")
        self.bak_box = BoxLayout(orientation="vertical", size_hint_y=None)
        self.bak_box.bind(minimum_height=self.bak_box.setter("height"))
        bak_card.add_widget(self.bak_box)
        self._render_backups()
        box.add_widget(bak_card)

        # 版本号（#14：需在界面可见）
        box.add_widget(Label(
            text=f"行测模考分析 · 手机版 v{VERSION}",
            font_name=cn(), font_size=dp(11), color=C("muted"),
            size_hint_y=None, height=dp(26), halign="center",
        ))

    # ---- 导入导出 ----
    def _export(self):
        from kivy.utils import platform as kplatform
        if kplatform == "android":
            d = "/sdcard/Download"
        else:
            d = os.path.expanduser("~/Downloads")
        os.makedirs(d, exist_ok=True)
        fn = os.path.join(d, f"行测数据_{datetime.datetime.now():%Y%m%d_%H%M%S}.json")
        try:
            self.app().store.export_json(fn)
            self.app().toast(f"已导出：{fn}")
        except Exception as ex:
            self.app().toast(f"导出失败：{ex}")

    def _import(self):
        fc = FileChooserListView(filters=["*.json"], path=os.path.expanduser("~"))
        def on_sel(inst, sel, *a):
            if sel:
                try:
                    ok = self.app().store.import_json(sel[0])
                    if ok:
                        self.app().refresh_all()
                        self.app().toast("导入成功")
                    else:
                        self.app().toast("文件格式不正确")
                except Exception as ex:
                    self.app().toast(f"导入失败：{ex}")
            popup.dismiss()
        fc.bind(on_selection=on_sel)
        popup = Popup(title="选择 JSON 文件", content=fc, size_hint=(0.95, 0.85))
        popup.open()

    # ---- 模块 ----
    def _render_modules(self):
        self.mod_box.clear_widgets()
        for m in self.app().store.modules():
            if m.get("builtin", True) is False or m.get("custom"):
                tag = "自定义"
            else:
                tag = "内置"
            row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
            row.add_widget(Label(text=f"{m['name']}（{tag} 共{m.get('total',0)}题）",
                                font_name=cn(), font_size=dp(12), color=(0.2,0.24,0.3,1),
                                size_hint=(0.7, 1), halign="left"))
            row.add_widget(kv_button("删除", lambda *a, k=m["key"]: self._del_module(k),
                                    bg=(0.9,0.33,0.29,1), size_hint=(0.3, 1), height=dp(34), font_size=dp(12)))
            self.mod_box.add_widget(row)

    def _add_module(self):
        name = self.new_mod_name.text.strip()
        try:
            total = int(self.new_mod_total.text.strip() or "0")
        except Exception:
            total = 0
        if not name:
            self.app().toast("请输入模块名")
            return
        color = MODULE_COLORS[len(self.app().store.modules()) % len(MODULE_COLORS)]
        self.app().store.add_module(name, total, color=color, points=1.0)
        # 标记为自定义
        self.new_mod_name.text = ""
        self.new_mod_total.text = ""
        self._render_modules()
        self.app().refresh_all()

    def _del_module(self, key):
        self.app().store.remove_module(key)
        self._render_modules()
        self.app().refresh_all()

    # ---- 卷型 ----
    def _render_papers(self):
        self.paper_box.clear_widgets()
        store = self.app().store
        for p in store.all_paper_types():
            if p in PAPER_TYPES:
                tag = "内置"
            else:
                tag = "自定义"
            row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
            row.add_widget(Label(text=f"{p}（{tag}）", font_name=cn(), font_size=dp(12),
                                color=(0.2,0.24,0.3,1), size_hint=(0.7,1), halign="left"))
            if p not in PAPER_TYPES:
                row.add_widget(kv_button("删除", lambda *a, n=p: self._del_paper(n),
                                         bg=(0.9,0.33,0.29,1), size_hint=(0.3,1), height=dp(34), font_size=dp(12)))
            self.paper_box.add_widget(row)

    def _add_paper(self):
        name = self.new_paper_name.text.strip()
        if not name:
            self.app().toast("请输入卷型名")
            return
        self.app().store.add_custom_paper(name)
        self.new_paper_name.text = ""
        self._render_papers()
        self.app().refresh_all()

    def _del_paper(self, name):
        self.app().store.remove_custom_paper(name)
        self._render_papers()
        self.app().refresh_all()

    # ---- 备份 ----
    def _render_backups(self):
        self.bak_box.clear_widgets()
        baks = self.app().store.list_backups()
        if not baks:
            self.bak_box.add_widget(Label(text="暂无备份（每次保存自动轮转备份）",
                                          font_name=cn(), font_size=dp(12),
                                          color=(0.45,0.5,0.56,1), size_hint_y=None, height=dp(28), halign="left"))
            return
        for b in baks[:8]:
            row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
            row.add_widget(Label(text=os.path.basename(b), font_name=cn(), font_size=dp(11),
                                 color=(0.2,0.24,0.3,1), size_hint=(0.7,1), halign="left"))
            row.add_widget(kv_button("恢复", lambda *a, p=b: self._restore(p),
                                     bg=(0.13,0.63,0.42,1), size_hint=(0.3,1), height=dp(34), font_size=dp(12)))
            self.bak_box.add_widget(row)

    def _restore(self, path):
        try:
            self.app().store.restore_backup(path)
            self.app().refresh_all()
            self._render_backups()
            self.app().toast("已恢复备份")
        except Exception as ex:
            self.app().toast(f"恢复失败：{ex}")
