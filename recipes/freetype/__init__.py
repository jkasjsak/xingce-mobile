# -*- coding: utf-8 -*-
"""本地覆盖 freetype recipe：绕开 download.savannah.gnu.org 长期 502。

根因：p4a 内置 freetype 从 savannah 下载，镜像长期 502 导致构建失败。
改用 GitHub 官方仓库（CI runner 必能连）。但 GitHub 归档
（archive/refs/tags/VER-2-14-1.tar.gz）因 .gitattributes `export-ignore`
不含生成的 ./configure，解包后 ./configure: not found → 构建失败。

解法（build_arch 内）：
1. 若 build 目录没有 ./configure，从 GitHub git clone 该 tag 的全量源码
   （configure 在 git 树里是已提交文件，clone 可得）覆盖进来；
2. 预置 dlg 子模块（git 归档同样不含子模块，编译时 copy_submodule 会找不到
   ./subprojects/dlg/include/dlg/output.h）→ 从 GitHub 拉 nyorain/dlg 钉死 commit。
"""
import os
import shutil
import subprocess

from pythonforandroid.recipes.freetype import FreetypeRecipe as _Base


FT_TAG = "VER-2-14-1"
FT_URL = "https://github.com/freetype/freetype.git"
DLG_COMMIT = "395ccad2c1e0"          # freetype 2.14.1 钉死的 dlg 子模块版本
DLG_URL = "https://github.com/nyorain/dlg.git"


def _run(cmd, cwd=None):
    subprocess.check_call(cmd, cwd=cwd)


def _git_clone(tag_or_branch, url, dst):
    """浅克隆到 dst（dst 必须不存在或为空），不清留 .git。"""
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    _run(["git", "clone", "--depth", "1", "--branch", tag_or_branch, url, dst])


def _overlay(src, dst):
    """把 src 目录内容（含隐藏文件，排除 .git）覆盖进 dst。"""
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
        """GitHub 归档缺 ./configure（export-ignore），用 git clone 全量源码覆盖。"""
        if os.path.exists(os.path.join(build_dir, "configure")):
            return
        tmp = os.path.join(os.path.dirname(build_dir), "_ft_git_clone")
        _git_clone(FT_TAG, FT_URL, tmp)
        try:
            _overlay(tmp, build_dir)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _ensure_dlg(self, build_dir):
        """git 归档不含子模块 dlg，编译时 copy_submodule 会找不到 output.h。从 GitHub 预置。"""
        dlg_dir = os.path.join(build_dir, "subprojects", "dlg")
        if os.path.isdir(os.path.join(dlg_dir, "include", "dlg")):
            return
        if os.path.isdir(dlg_dir):
            shutil.rmtree(dlg_dir)
        os.makedirs(dlg_dir, exist_ok=True)
        tmp = os.path.join(os.path.dirname(build_dir), "_dlg_git_clone")
        _git_clone("main", DLG_URL, tmp)
        try:
            # 取到 freetype 2.14.1 钉死的精确 commit
            _run(["git", "-C", tmp, "fetch", "--depth", "1", "origin", DLG_COMMIT])
            _run(["git", "-C", tmp, "checkout", DLG_COMMIT])
            _overlay(tmp, dlg_dir)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def build_arch(self, arch):
        build_dir = self.get_build_dir(arch)
        self._ensure_full_source(build_dir)
        self._ensure_dlg(build_dir)
        super().build_arch(arch)


recipe = FreetypeRecipe()
