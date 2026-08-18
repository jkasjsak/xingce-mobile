# -*- coding: utf-8 -*-
"""本地覆盖 freetype recipe：绕开 download.savannah.gnu.org 长期 502。

根因：p4a 内置 freetype 从 savannah 下载，该镜像长期 502 直接导致构建失败。
修正：改用 SourceForge 的【发布版】tarball（与 savannah 同源，已含预生成的
./configure 与 vendored 的 dlg 源码），CI runner 可稳定连上。

p4a 的下载机制会用 `versioned_url`（即本文件的 `url`，其中 {version} 自动替换）
下载并解包，随后在 build_arch 里执行 ./configure。发布版 tarball 自带
configure 与 dlg，无需 git clone、无需处理 export-ignore / 子模块，最稳妥。

附多镜像兜底：若主镜像不可达，自动回退 GitHub Releases / GNU / savannah。
"""
import os

from pythonforandroid.logger import info
from pythonforandroid.recipes.freetype import FreetypeRecipe as _Base


class FreetypeRecipe(_Base):
    version = '2.14.1'
    # savannah 长期 502；改用 SourceForge 发布版 tarball（含 configure + dlg）
    url = 'https://downloads.sourceforge.net/project/freetype/freetype2/{version}/freetype-{version}.tar.gz'

    # 多镜像兜底（与 url 同源的不同 host），任一可达即可完成下载
    _MIRRORS = [
        'https://downloads.sourceforge.net/project/freetype/freetype2/{v}/freetype-{v}.tar.gz',
        'https://github.com/freetype/freetype/releases/download/VER-{v_}/freetype-{v}.tar.gz',
        'https://mirror.nju.edu.cn/gnu/freetype/freetype-{v}.tar.gz',
        'https://ftp.gnu.org/gnu/freetype/freetype-{v}.tar.gz',
        'https://download.savannah.gnu.org/releases/freetype/freetype-{v}.tar.gz',
    ]

    def download_file(self, url, target, cwd=None):
        # 仅对 freetype 源码 tarball 做多镜像兜底；其余（补丁等）走默认逻辑
        if 'freetype' not in url or not url.endswith('.tar.gz'):
            return super().download_file(url, target, cwd=cwd)
        v = self.version
        v_ = v.replace('.', '-')
        last_err = None
        for tpl in self._MIRRORS:
            m = tpl.format(v=v, v_=v_)
            try:
                super().download_file(m, target, cwd=cwd)
                return
            except Exception as e:  # noqa: BLE001 - 兜底重试任一镜像
                last_err = e
                # 清理可能写入的半截文件，便于下一个镜像干净重试
                try:
                    if os.path.exists(target):
                        os.remove(target)
                except OSError:
                    pass
                info('freetype 镜像下载失败，尝试下一个: {} ({})'.format(m, e))
        if last_err is not None:
            raise last_err


recipe = FreetypeRecipe()
