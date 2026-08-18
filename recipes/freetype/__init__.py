# 本地覆盖 p4a 内置的 freetype recipe。
#
# 问题：官方 p4a 把 freetype 源码写死为 savannah.gnu.org 的发布包，
# 而 savannah 长期间歇性返回 502，导致 CI 在下载阶段直接失败（重跑也失败）。
#
# 修复：改从 GitHub 官方归档拉取 freetype 源码。CI runner 必然能连通 GitHub。
# 该归档（VER-2-14-1.tar.gz）内已含预生成的 ./configure，p4a 的 build_arch
# 可直接执行 ./configure，无需 autogen。
# 解包时 p4a 会把顶层目录 freetype-VER-2-14-1 自动重命名为 freetype，
# 与内置 recipe 处理 savannah 包（freetype-2.14.1）的方式完全一致，无需额外处理。
from pythonforandroid.recipes.freetype import FreetypeRecipe


class FreetypeRecipe(FreetypeRecipe):
    url = 'https://github.com/freetype/freetype/archive/refs/tags/VER-2-14-1.tar.gz'
