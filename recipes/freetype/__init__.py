# 本地覆盖 p4a 内置的 freetype recipe。
#
# 两级问题都已根治：
#
# 1) savannah 502：官方 p4a 把 freetype 源码写死为 savannah.gnu.org 的发布包，
#    而 savannah 长期间歇性返回 502，导致 CI 在下载阶段直接失败。
#    -> 改从 GitHub 官方归档拉取 freetype 源码（CI runner 必能连通 GitHub）。
#       该归档（VER-2-14-1.tar.gz）内已含预生成的 ./configure，p4a 可直接编译，
#       且 p4a 会把顶层目录自动重命名为 freetype，与官方处理 savannah 包一致。
#
# 2) 子模块 dlg 缺失：freetype 2.14 的 git 归档不含 git 子模块 dlg（官方 savannah
#    发布包会把子模块一起打包，但 github git archive 不含子模块），编译时 make 的
#    copy_submodule 步骤找不到 subprojects/dlg/include/dlg/output.h 而失败。
#    -> 在 build_arch 开头，额外从 GitHub 把 dlg 子模块（钉死 freetype 2.14.1 所用
#       的 commit 395ccad2c1e0，仓库为 nyorain/dlg）拉下来放进 subprojects/dlg。
from pythonforandroid.recipes.freetype import FreetypeRecipe

import os
import shutil
import tarfile
import tempfile
import urllib.request

DLG_COMMIT = '395ccad2c1e0'
DLG_URL = 'https://github.com/nyorain/dlg/archive/{}.tar.gz'.format(DLG_COMMIT)


def _download(url, dest, tries=6):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'p4a-freetype-dlg'})
            with urllib.request.urlopen(req, timeout=180) as r, open(dest, 'wb') as f:
                shutil.copyfileobj(r, f)
            if os.path.getsize(dest) > 0:
                return
        except Exception as e:  # noqa: BLE001
            last = e
    raise RuntimeError('failed to download {}: {}'.format(url, last))


def _ensure_dlg(build_dir):
    """Ensure subprojects/dlg/include/dlg/output.h exists (freetype needs it
    at `make` time via the copy_submodule step)."""
    dlg_dir = os.path.join(build_dir, 'subprojects', 'dlg')
    marker = os.path.join(dlg_dir, 'include', 'dlg', 'output.h')
    if os.path.exists(marker):
        return
    os.makedirs(dlg_dir, exist_ok=True)

    tmp = os.path.join(build_dir, '.dlg_archive.tar.gz')
    _download(DLG_URL.format(), tmp)

    with tempfile.TemporaryDirectory() as td:
        with tarfile.open(tmp) as tf:
            tf.extractall(td)
        dirs = [e for e in os.listdir(td)
                if os.path.isdir(os.path.join(td, e)) and not e.startswith('.')]
        src = os.path.join(td, dirs[0]) if dirs else td
        for name in os.listdir(src):
            s = os.path.join(src, name)
            d = os.path.join(dlg_dir, name)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
    os.remove(tmp)


class FreetypeRecipe(FreetypeRecipe):
    url = 'https://github.com/freetype/freetype/archive/refs/tags/VER-2-14-1.tar.gz'

    def build_arch(self, arch, with_harfbuzz=False):
        # Pull the dlg git-submodule (pinned to freetype 2.14.1's commit) into
        # the source tree *before* make runs the copy_submodule step.
        _ensure_dlg(self.get_build_dir(arch.arch))
        return super().build_arch(arch, with_harfbuzz=with_harfbuzz)


# p4a 的 Recipe.get_recipe 通过 `mod.recipe` 获取 recipe 实例，本地覆盖 recipe
# 必须按官方约定在模块级暴露该实例，否则会报
# "module 'pythonforandroid.recipes.freetype' has no attribute 'recipe'"。
recipe = FreetypeRecipe()
