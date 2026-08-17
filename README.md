# 行测模考分析 · 手机版（Android）

桌面版（customtkinter，Windows exe）的**全功能移植**：总览、录入成绩、考试计时、趋势分析、模块诊断（雷达图）、考试对比、目标追踪、数据管理、考试记录。数据层（`data_store.py`）原样复用，算分/估分逻辑零改写。

技术栈：**Kivy 2.3.1（纯 Python）+ matplotlib + pandas**，打包为 Android APK。

---

## 一、怎么拿到可安装的 APK（你不用装任何开发工具）

本环境（云端沙箱）无法直接编译 APK（buildozer 需要 Linux + Android SDK/NDK）。
最省事的方案是 **GitHub Actions 云端自动构建**：你只需把代码推到 GitHub，云端自动编译，下载即可安装。

### 步骤

1. **准备一个 GitHub 账号**（免费）。
2. 在本机打开 `XingceMobile` 文件夹的终端，执行：
   ```bash
   git init
   git add -A
   git commit -m "init xingce mobile"
   ```
3. 在 GitHub 网页**新建一个仓库**（例如 `xingce-mobile`，**不要**勾选 README/.gitignore）。
   复制它的地址，例如 `https://github.com/你的用户名/xingce-mobile.git`。
4. 回到终端，关联并推送：
   ```bash
   git remote add origin https://github.com/你的用户名/xingce-mobile.git
   git branch -M main
   git push -u origin main
   ```
5. 进入该仓库的 **Actions** 页面，会看到 `Build Android APK` 工作流自动开始运行
   （也可点 `Run workflow` 手动触发）。
6. 等待约 **20–40 分钟**（首次要下载 Android SDK/NDK 并编译 numpy/pandas/matplotlib）。
7. 运行完成后，在当次运行的 **Artifacts** 区下载 `xingce-mobile-apk`，
   里面是 `bin/行测模考分析-1.0.0-arm64-v8a-debug.apk`。
8. **手机安装**：
   - 把 APK 传到手机（微信文件传输/数据线/网盘）。
   - Android 首次装“未知来源”应用：弹窗里允许「安装未知应用」（对应来源如“文件管理”或浏览器）。
   - 点击 APK 完成安装。

> 以后改了任何代码，`git push` 一次就会自动重新出 APK。

---

## 二、本地桌面调试（可选，需 Windows + VC++ 运行库）

```bash
cd XingceMobile
.venv\Scripts\python.exe main.py
```

中文显示：Windows 自动用系统微软雅黑；安卓打包时由 CI 自动下载中文字体并打入 APK（图表中文不会变方块）。

---

## 三、目录结构

```
XingceMobile/
├── main.py            # App + 底部导航 + 屏幕管理
├── core.py            # 计时控制器 TimerController + 格式化/配色 + 字体查找
├── ui.py              # Kivy 基础组件（Card/header/Spinner/按钮）
├── charts.py          # KivyChart：matplotlib(Agg) 渲染 → 手势控件（拖动/捏合/重置/存图）
├── data_store.py      # 数据层（算分/估分/备份/计时持久化），原样复用桌面版
├── default_data.json  # 种子数据（12 细分模块等）
├── buildozer.spec     # 安卓打包配置
├── .github/workflows/build.yml  # 云端自动构建 APK
├── fonts/             # 中文字体（CI 下载，无需手动放）
└── screens/           # 9 个视图：overview/add/timer/trends/modules/compare/goals/data/exams
```

---

## 四、说明与限制

- 当前产出的是 **debug 签名 APK**：可正常安装使用，但不能直接上架应用商店（商店需 release 签名）。
- 目标架构为 `arm64-v8a`（近 8 年主流手机）；如需兼容更旧的 32 位机，在 `buildozer.spec` 把 `android.arch` 改为 `arm64-v8a,armeabi-v7a`。
- 桌面版 `行测模考分析.exe`（v1.9.6）**完全未改动**。
- 真机打包若遇编译问题（多为网络/SDK 版本），优先查看 Actions 日志，通常在 `buildozer android debug` 步骤。
