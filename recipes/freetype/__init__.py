# -*- coding: utf-8 -*-
"""本地覆盖 freetype recipe：绕开 download.savannah.gnu.org 长期 502。

根因链（逐个已修）：
1. p4a 内置 freetype 从 savannah 下载，镜像长期 502 → 改用 GitHub 源。
2. GitHub 归档（archive/refs/tags/VER-2-14-1.tar.gz）因 .gitattributes
   `export-ignore` 不含生成的 ./configure，也不含 git 子模块 dlg →
   改为 `git clone --recursive` 拉全量源码覆盖进 build 目录。
3. git 源码树里 builds/unix/configure 是【生成物】（被 .gitignore 忽略，
   由根目录 autogen.sh 生成）。缺它时顶层 ./configure 会执行
   `cd builds/unix; ./configure ...` 并报 `/bin/sh: ./configure: not found`
   （make: *** [builds/unix/detect.mk:91: setup] Error 127）。
   → 在 p4a 调 configure 之前先跑 `sh autogen.sh` 补齐。
   CI 已安装 autoconf/automake/libtool/libtool-bin/pkg-config/libltdl-dev，
   autogen.sh 所需工具齐全。

以上步骤全部幂等：文件已存在则直接跳过，不重复 clone / 不重复 autogen。
"""
import os
import shutil
import subprocess

from pythonforandroid.recipes.freetype import FreetypeRecipe as _Base


FT_TAG = "VER-2-14-1"
FT_URL = "https://github.com/freetype/freetype.git"


def _run(cmd, cwd=None, env=None):
    subprocess.check_call(cmd, cwd=cwd, env=env)


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

    def _ensure_unix_configure(self, build_dir):
        """builds/unix/configure 是 autogen.sh 的生成物，git 源码树里没有；缺则生成。"""
        unix_cfg = os.path.join(build_dir, "builds", "unix", "configure")
        if os.path.exists(unix_cfg):
            os.chmod(unix_cfg, 0o755)
            return
        autogen = os.path.join(build_dir, "autogen.sh")
        if not os.path.exists(autogen):
            raise RuntimeError(
                "freetype source missing both builds/unix/configure and autogen.sh: %s"
                % build_dir
            )
        env = os.environ.copy()
        # autogen.sh 用 GNUMAKE 定位 GNU make；显式指定避免个别环境探测失败。
        env.setdefault("GNUMAKE", "make")
        # 用宿主工具链生成 configure（与交叉编译环境无关），故用干净的 os.environ。
        _run(["sh", "autogen.sh"], cwd=build_dir, env=env)
        if not os.path.exists(unix_cfg):
            raise RuntimeError(
                "autogen.sh finished but builds/unix/configure still missing: %s"
                % unix_cfg
            )
        os.chmod(unix_cfg, 0o755)
        top_cfg = os.path.join(build_dir, "configure")
        if os.path.exists(top_cfg):
            os.chmod(top_cfg, 0o755)

    def build_arch(self, arch):
        build_dir = self.get_build_dir(arch)
        self._ensure_full_source(build_dir)
        self._ensure_unix_configure(build_dir)
        super().build_arch(arch)


recipe = FreetypeRecipe()
