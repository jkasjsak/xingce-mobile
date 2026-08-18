# -*- coding: utf-8 -*-
"""本地覆盖 freetype recipe：绕开 download.savannah.gnu.org 长期 502。

根因：p4a 内置 freetype 从 savannah 下载，镜像长期 502 导致构建失败。
改用 GitHub 官方仓库（CI runner 必能连）。但 GitHub 归档
（archive/refs/tags/VER-2-14-1.tar.gz）因 .gitattributes `export-ignore`
不含生成的 ./configure，且不含 git 子模块 dlg，直接用来编译会失败。

解法（build_arch 内）：
- p4a 照常下载并解包 GitHub 归档；
- 但若 build 目录缺少 ./configure 或 subprojects/dlg/include/dlg/output.h，
  则 git clone 该 tag 的【全量源码】（--recursive 拉齐 dlg 子模块），
  整体覆盖进 build 目录，使 ./configure 与 dlg 一次到位。
"""
import os
import shutil
import subprocess

from pythonforandroid.recipes.freetype import FreetypeRecipe as _Base


FT_TAG = "VER-2-14-1"
FT_URL = "https://github.com/freetype/freetype.git"


def _run(cmd, cwd=None):
    subprocess.check_call(cmd, cwd=cwd)


def _overlay(src, dst):
    """把 src 目录内容（排除 .git）覆盖进 dst。"""
    for name in os.listdir(src):
        if name == ".git":
            continue
        s = os.path.join(src, name)
        d = os.path.join(dst, name)
        if os.path.isdir(s):
            if os.path.isdir(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)


class FreetypeRecipe(_Base):
    # 仍指向 GitHub 归档（p4a 会下载并解包；随后 build_arch 用 clone 全量覆盖）
    url = "https://github.com/freetype/freetype/archive/refs/tags/%s.tar.gz" % FT_TAG

    def _ensure_full_source(self, build_dir):
        """归档缺 ./configure（export-ignore）和 dlg 子模块；用 git clone 全量覆盖。"""
        cfg = os.path.join(build_dir, "configure")
        dlg = os.path.join(build_dir, "subprojects", "dlg", "include", "dlg", "output.h")
        if os.path.exists(cfg) and os.path.exists(dlg):
            return
        tmp = os.path.join(os.path.dirname(build_dir), "_ft_fullsrc")
        if os.path.isdir(tmp):
            shutil.rmtree(tmp)
        # --recursive 一并拉取 dlg 子模块（nyorain/dlg），CI 可连 GitHub
        _run(["git", "clone", "--recursive", "--depth", "1",
              "--branch", FT_TAG, FT_URL, tmp])
        try:
            _overlay(tmp, build_dir)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def build_arch(self, arch):
        build_dir = self.get_build_dir(arch)
        self._ensure_full_source(build_dir)
        super().build_arch(arch)


recipe = FreetypeRecipe()
