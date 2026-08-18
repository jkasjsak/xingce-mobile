[app]

# (str) 应用标题
title = 行测模考分析

# (str) 包名
package.name = xingcemobile
# (str) 域名（反向，用于包名前缀）
package.domain = com.xingce

# (str) 源码目录（. 表示当前项目根）
source.dir = .
# (list) 包含的扩展名
source.include_exts = py,png,jpg,kv,json,ttf,otf,ttc,txt
# (list) 必须排除的目录：.venv 含桌面二进制（数百 MB 且不兼容安卓），务必排除！
source.exclude_dirs = .venv,tests,.git,__pycache__,wheels,build,dist
# (list) 排除模式
source.exclude_patterns = *.pyc,*.pyo,._*,*~,extract_wheels.py,_mock_run.py,sitecustomize.py

# (list) 入口：buildozer 会找 main.py 里的 XingceApp
source.main = main.py

# (list) 依赖（buildozer 经 python-for-android 自动拉取对应 Android 轮子）
# 注意：numpy/matplotlib/pillow 等【绝不能钉版本号】！p4a 会按版本号 git checkout
# 对应 tag，钉成不存在的版本（如 numpy==1.26.4）会直接 git checkout 失败、构建挂掉。
# 用第一版成功构建的写法：全部不钉版本，纯 Python 依赖（kiwisolver/cycler/fonttools/
# python-dateutil/pytz/six）由 p4a 作为 matplotlib 的传递依赖自动解析。
requirements = hostpython3==3.11.9,python3==3.11.9,kivy==2.3.1,pandas,numpy,matplotlib,pillow

# (str) 应用版本
version = 1.0.1

# (list) 权限（Android 11+ 走作用域存储；旧版读写下载目录用）
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# (int) 目标 API / 最低 API
android.api = 34
android.minapi = 24

# (str) 显式指定 NDK 版本（buildozer 自动下载，无需许可证）
android.ndk = 28c

# (str) 目标 CPU 架构（现代手机主流 arm64；如需兼容旧机可加 armeabi-v7a）
android.archs = arm64-v8a

# (str) SDK 路径：由 CI 的 android-actions/setup-android 注入（许可证已接受），避免 buildozer 自管 SDK 时的许可卡死
android.sdk_path = /usr/local/lib/android/sdk
# 自动接受 SDK 许可，避免 sdkmanager 因许可未确认而在构建早期直接失败
android.accept_sdk_license = True

# (str) 屏幕方向
orientation = portrait

# (bool) 允许备份
android.allow_backup = True
android.accept_backup_rules = True

# (list) 额外资源（中文字体已入库 fonts/msyh.ttf，CI 仍会兜底下载）
presplash.filename =
icon.filename =

[buildozer]

# (int) 日志等级
log_level = 2

# (str) 默认目标
default.target = android
