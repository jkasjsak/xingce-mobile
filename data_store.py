"""行测试卷分析 - 数据层（与界面解耦，可独立测试）"""
import json
import os
import sys
import uuid
from datetime import datetime, date


# 默认模块：12 个细分项；默认题量/分值取「江苏A类」卷（仅作兜底，实际按 paper_config 计算）。
# 同一大类下的子项用相近色系，便于在图表中识别归属。
DEFAULT_MODULES = [
    {"key": "zzll",    "name": "政治理论",         "total": 0,  "points": 0.70, "color": "#EF6F6C"},
    {"key": "cspd",    "name": "常识判断",         "total": 15, "points": 0.60, "color": "#E5945C"},
    {"key": "yy_frag", "name": "言语·片段阅读",     "total": 15, "points": 0.70, "color": "#C084CB"},
    {"key": "yy_logic","name": "言语·选词填空",     "total": 10, "points": 0.50, "color": "#B070C0"},
    {"key": "yy_art",  "name": "言语·文章阅读",     "total": 5,  "points": 0.70, "color": "#D49BE0"},
    {"key": "sl_num",  "name": "数量·数字推理",     "total": 5,  "points": 0.50, "color": "#5AA9E6"},
    {"key": "sl_math", "name": "数量·数学运算",     "total": 10, "points": 0.90, "color": "#3E8FCF"},
    {"key": "pd_graph","name": "判断·图形推理",     "total": 15, "points": 0.80, "color": "#4FC0A8"},
    {"key": "pd_ana",  "name": "判断·类比推理",     "total": 10, "points": 0.50, "color": "#3DA98F"},
    {"key": "pd_def",  "name": "判断·定义判断",     "total": 15, "points": 0.80, "color": "#5FCFB6"},
    {"key": "pd_logic","name": "判断·逻辑判断",     "total": 10, "points": 0.80, "color": "#2E9C84"},
    {"key": "zlfx",    "name": "资料分析",         "total": 20, "points": 0.90, "color": "#F2C14E"},
]

PAPER_TYPES = ["江苏A类", "江苏B类", "江苏C类", "国考副省级", "国考地市级", "国考行政执法"]

# 内置卷型配置版本：官方估分更新时 +1，加载时自动按官方表刷新内置卷型配置（自定义卷型不受影响）。
CONFIG_VERSION = 3

# 旧版卷型名 → 新版（用于历史数据迁移）
LEGACY_PAPER_MAP = {"A类": "江苏A类", "B类": "江苏B类", "C类": "江苏C类"}

# 六套行测卷 · 严格 100 分配平表（2025-2026 机构通用参考估分，合计精确 100）
# 题量完全对齐官方。国考无文章阅读/数字推理，故 yy_art/sl_num=0；其余模块按官方题量填。
# 国考言语理解=片段阅读+选词填空，判断推理=图推+类比+定义+逻辑；下列小计已按此拆分。
PAPER_TYPE_TOTALS = {
    # 江苏 A/B 类：135 题
    "江苏A类":   {"zzll":10,"cspd":10,"yy_frag":15,"yy_logic":10,"yy_art":5,"sl_num":5,"sl_math":15,"pd_graph":10,"pd_ana":10,"pd_def":10,"pd_logic":15,"zlfx":20},
    "江苏B类":   {"zzll":10,"cspd":10,"yy_frag":15,"yy_logic":10,"yy_art":5,"sl_num":5,"sl_math":15,"pd_graph":10,"pd_ana":10,"pd_def":10,"pd_logic":15,"zlfx":20},
    # 江苏 C 类：130 题（数学运算仅 10）
    "江苏C类":   {"zzll":10,"cspd":10,"yy_frag":15,"yy_logic":10,"yy_art":5,"sl_num":5,"sl_math":10,"pd_graph":10,"pd_ana":10,"pd_def":10,"pd_logic":15,"zlfx":20},
    # 国考副省级：135 题（言语=片段15+选词15；数量=数学运算15；判断=图10+类比10+定义10+逻辑5）
    "国考副省级": {"zzll":20,"cspd":15,"yy_frag":15,"yy_logic":15,"yy_art":0,"sl_num":0,"sl_math":15,"pd_graph":10,"pd_ana":10,"pd_def":10,"pd_logic":5, "zlfx":20},
    # 国考地市级 / 行政执法：130 题（数量=数学运算10）
    "国考地市级": {"zzll":20,"cspd":15,"yy_frag":15,"yy_logic":15,"yy_art":0,"sl_num":0,"sl_math":10,"pd_graph":10,"pd_ana":10,"pd_def":10,"pd_logic":5, "zlfx":20},
    "国考行政执法":{"zzll":20,"cspd":15,"yy_frag":15,"yy_logic":15,"yy_art":0,"sl_num":0,"sl_math":10,"pd_graph":10,"pd_ana":10,"pd_def":10,"pd_logic":5, "zlfx":20},
}

# 各细分项参考总分（题量×单价=小计，六套合计均精确 100）。
# 江苏A/B：政治7+常识6+选词5+片段10.5+文章3.5+数推3.5+运算13.5+类比5+图推8+逻辑12+定义8+资料18=100
# 江苏C：  政治8+常识7+选词6+片段10.5+文章4+数推3.5+运算9+类比6+图推8+逻辑12+定义8+资料18=100
# 国考副省：政治10+常识7.5+言语22.5(片11.25+选11.25)+数量12+判断28(图8+类8+定8+逻4)+资料20=100
# 国考地市：政治10.5+常识7.5+言语24+数量10+判断28+资料20=100
# 国考执法：政治10+常识7.5+言语24+数量10.5+判断28+资料20=100
PAPER_TYPE_POINTS = {
    "江苏A类":   {"zzll":7.0, "cspd":6.0,"yy_frag":10.5,"yy_logic":5.0,"yy_art":3.5,"sl_num":3.5,"sl_math":13.5,"pd_graph":8.0,"pd_ana":5.0,"pd_def":8.0,"pd_logic":12.0,"zlfx":18.0},
    "江苏B类":   {"zzll":7.0, "cspd":6.0,"yy_frag":10.5,"yy_logic":5.0,"yy_art":3.5,"sl_num":3.5,"sl_math":13.5,"pd_graph":8.0,"pd_ana":5.0,"pd_def":8.0,"pd_logic":12.0,"zlfx":18.0},
    "江苏C类":   {"zzll":8.0, "cspd":7.0,"yy_frag":10.5,"yy_logic":6.0,"yy_art":4.0,"sl_num":3.5,"sl_math":9.0, "pd_graph":8.0,"pd_ana":6.0,"pd_def":8.0,"pd_logic":12.0,"zlfx":18.0},
    "国考副省级": {"zzll":10.0,"cspd":7.5,"yy_frag":11.25,"yy_logic":11.25,"yy_art":0.0,"sl_num":0.0,"sl_math":12.0,"pd_graph":8.0,"pd_ana":8.0,"pd_def":8.0,"pd_logic":4.0,"zlfx":20.0},
    "国考地市级": {"zzll":10.5,"cspd":7.5,"yy_frag":12.0,"yy_logic":12.0,"yy_art":0.0,"sl_num":0.0,"sl_math":10.0,"pd_graph":8.0,"pd_ana":8.0,"pd_def":8.0,"pd_logic":4.0,"zlfx":20.0},
    "国考行政执法":{"zzll":10.0,"cspd":7.5,"yy_frag":12.0,"yy_logic":12.0,"yy_art":0.0,"sl_num":0.0,"sl_math":10.5,"pd_graph":8.0,"pd_ana":8.0,"pd_def":8.0,"pd_logic":4.0,"zlfx":20.0},
}

GOAL_DEFAULT_OVERALL = 0.75
GOAL_DEFAULT_MODULE = 0.80


def _default_paper_config(modules):
    """为给定模块列表生成默认 paper_config（每卷型的题量 + 每小题分值）。"""
    cfg = {}
    for pt in PAPER_TYPES:
        d = {}
        for m in modules:
            k = m["key"]
            tot = PAPER_TYPE_TOTALS.get(pt, PAPER_TYPE_TOTALS["江苏A类"]).get(k, 0)
            pts = PAPER_TYPE_POINTS.get(pt, PAPER_TYPE_POINTS["江苏A类"]).get(k, 0)
            perq = round(pts / tot, 4) if tot > 0 else 0
            d[k] = {"total": tot, "perq": perq}
        cfg[pt] = d
    # 自定义卷型在被添加时再生成（默认套用江苏A类）
    return cfg


def default_module_total(key, paper_type):
    """返回某模块在指定（内置）卷型下的题量；自定义卷型请用 DataStore.paper_total。"""
    return PAPER_TYPE_TOTALS.get(paper_type, PAPER_TYPE_TOTALS["江苏A类"]).get(key, 0)


def module_points(key, paper_type):
    """返回某模块在指定卷型下的「模块总分」参考值（表内原值）。"""
    return PAPER_TYPE_POINTS.get(paper_type, PAPER_TYPE_POINTS["江苏A类"]).get(key, 0)


def get_base_dir():
    """数据文件存放目录：优先放在 exe/脚本同目录，不可写时回退到用户目录。"""
    if getattr(sys, "frozen", False):
        cand = os.path.dirname(sys.executable)
    else:
        cand = os.path.dirname(os.path.abspath(__file__))
    try:
        test = os.path.join(cand, ".write_test")
        with open(test, "w") as f:
            f.write("1")
        os.remove(test)
        return cand
    except Exception:
        home = os.path.expanduser("~/Documents/XingceAnalyzer")
        os.makedirs(home, exist_ok=True)
        return home


def _seed_path():
    """内置种子数据（default_data.json）所在目录：打包后位于 _MEIPASS，开发期位于脚本目录。"""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "default_data.json")


def build_seed():
    """生成默认种子数据（含 12 细分项、空考试、空自定义卷型、paper_config）。"""
    mods = [dict(m) for m in DEFAULT_MODULES]
    return {
        "modules": mods,
        "exams": [],
        "goal": {},
        "custom_papers": [],
        "paper_config": _default_paper_config(mods),
    }


class DataStore:
    def __init__(self, path=None):
        self.path = path or os.path.join(get_base_dir(), "data.json")
        self.data = {"modules": [], "exams": [], "goal": {}, "custom_papers": [], "paper_config": {}}
        self._stat_cache = {}  # 估分/正确率缓存：exam_id -> stat 结果
        self.load()

    # ---------- 持久化 ----------
    def load(self):
        loaded = None
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
            except Exception:
                loaded = None
        # 不存在则尝试从内置种子拷贝（保证分享出去的 exe 自带默认结构）
        if not isinstance(loaded, dict):
            seed = None
            sp = _seed_path()
            if os.path.exists(sp):
                try:
                    with open(sp, "r", encoding="utf-8") as f:
                        seed = json.load(f)
                except Exception:
                    seed = None
            loaded = seed if isinstance(seed, dict) else {}
        self.data = loaded
        # 字段兜底
        self.data.setdefault("modules", [])
        self.data.setdefault("exams", [])
        self.data.setdefault("goal", {})
        self.data.setdefault("custom_papers", [])
        self.data.setdefault("paper_config", {})
        self._ensure_fields()
        # 结构迁移：若已存模块与当前 12 细分项结构不一致，则备份旧数据并重置
        cur_keys = {m["key"] for m in DEFAULT_MODULES}
        stored_keys = {m.get("key") for m in self.data.get("modules", []) if isinstance(m, dict)}
        # 仅在「模块集合与当前完全不重叠」时（即旧版 6 大类结构）才备份重置；
        # 新增自定义模块会导致 key 数量变多，属于正常情况，绝不能重置以免清空用户数据。
        if stored_keys and not (stored_keys & cur_keys):
            self._backup_and_reset()
        if not self.data["modules"]:
            self.data["modules"] = [dict(m) for m in DEFAULT_MODULES]
        # 为每个模块补充 color / points（兼容旧数据）
        for m in self.data["modules"]:
            m.setdefault("color", "#5AA9E6")
            if "points" not in m or m.get("points") is None:
                m["points"] = 1.0
        # 旧版卷型名迁移
        for e in self.data.get("exams", []):
            pt = e.get("paper_type")
            if pt in LEGACY_PAPER_MAP:
                e["paper_type"] = LEGACY_PAPER_MAP[pt]
        self._init_paper_config()
        # 版本化刷新内置卷型配置：官方估分更新时，加载即按官方表刷新内置卷型（自定义卷型不受影响）。
        # 估分本身按比值计算，刷新内置 perq 不会改变任何已记录考试的估算分数，可放心刷新。
        if self.data.get("config_version", 0) < CONFIG_VERSION:
            self._refresh_builtin_paper_config()
            self.data["config_version"] = CONFIG_VERSION
        self.save()

    def _ensure_fields(self):
        """为每个考试补充计时相关字段，保证旧数据兼容。"""
        for e in self.data.get("exams", []):
            e.setdefault("start_time", None)
            e.setdefault("end_time", None)
            e.setdefault("duration_min", None)
        for cp in self.data.get("custom_papers", []):
            cp.setdefault("totals", {})

    def _init_paper_config(self):
        """确保每个卷型都在 paper_config 中有完整的（题量, 每小题分值）配置。"""
        cfg = self.data.setdefault("paper_config", {})
        mods = self.data["modules"]
        # 内置卷型：按官方表初始化
        for pt in PAPER_TYPES:
            d = cfg.setdefault(pt, {})
            for m in mods:
                k = m["key"]
                tot = PAPER_TYPE_TOTALS.get(pt, PAPER_TYPE_TOTALS["江苏A类"]).get(k, 0)
                pts = PAPER_TYPE_POINTS.get(pt, PAPER_TYPE_POINTS["江苏A类"]).get(k, 0)
                perq = round(pts / tot, 4) if tot > 0 else 0
                d.setdefault(k, {"total": tot, "perq": perq})
        # 自定义卷型：默认空白（0/0），由用户自行配置；不清空已有配置
        known = set(PAPER_TYPES) | {c["name"] for c in self.custom_papers()}
        for cp in self.custom_papers():
            name = cp["name"]
            d = cfg.setdefault(name, {})
            for m in mods:
                k = m["key"]
                d.setdefault(k, {"total": 0, "perq": 0.0})
        # 清理已删除卷型的配置
        for pt in list(cfg.keys()):
            if pt not in known:
                del cfg[pt]
        # 确保新加模块也出现在所有配置里
        for pt, d in cfg.items():
            for m in mods:
                k = m["key"]
                if pt in PAPER_TYPES:
                    tot = PAPER_TYPE_TOTALS.get(pt, {}).get(k, 0)
                    pts = PAPER_TYPE_POINTS.get(pt, {}).get(k, 0)
                    d.setdefault(k, {"total": tot, "perq": (round(pts / tot, 4) if tot > 0 else 0)})
                else:
                    d.setdefault(k, {"total": 0, "perq": 0.0})

    def _refresh_builtin_paper_config(self):
        """按官方表覆盖刷新所有内置卷型的（题量, 每小题分值）配置；自定义卷型保持不变。"""
        mods = self.data["modules"]
        cfg = self.data.setdefault("paper_config", {})
        for pt in PAPER_TYPES:
            d = cfg.setdefault(pt, {})
            for m in mods:
                k = m["key"]
                tot = PAPER_TYPE_TOTALS.get(pt, {}).get(k, 0)
                pts = PAPER_TYPE_POINTS.get(pt, {}).get(k, 0)
                d[k] = {"total": tot, "perq": round(pts / tot, 4) if tot > 0 else 0}

    def _backup_and_reset(self):
        """把旧数据备份为 data.json.bak*，再重置为当前标准的 12 细分项结构。"""
        try:
            if os.path.exists(self.path) and os.path.getsize(self.path) > 0:
                import shutil as _sh
                bak = self.path + ".bak"
                i = 1
                while os.path.exists(bak):
                    bak = f"{self.path}.bak{i}"
                    i += 1
                _sh.copy2(self.path, bak)
        except Exception:
            pass
        self.data = build_seed()

    def _rotate_backups(self):
        """保存前滚动备份：当前文件 → .bak1，旧的 .bak{i-1} → .bak{i}（最多保留 5 份）。
        仅在 save() 检测到内容变化时调用，避免无谓刷盘。"""
        try:
            if not os.path.exists(self.path) or os.path.getsize(self.path) == 0:
                return
            import shutil as _sh
            base = self.path
            for i in range(5, 1, -1):          # bak4->bak5, bak3->bak4, ... bak1->bak2
                src = f"{base}.bak{i-1}"
                dst = f"{base}.bak{i}"
                if os.path.exists(src):
                    try:
                        _sh.move(src, dst)
                    except Exception:
                        pass
            try:
                _sh.copy2(base, f"{base}.bak1")
            except Exception:
                pass
        except Exception:
            pass

    def list_backups(self):
        """返回按时间倒序的备份文件路径列表（.bak1 最新）。"""
        out = []
        for i in range(1, 6):
            p = f"{self.path}.bak{i}"
            if os.path.exists(p):
                out.append(p)
        return out

    def restore_backup(self, bak_path):
        """从指定备份文件恢复数据（原子写），成功返回 True。"""
        if not os.path.exists(bak_path):
            return False
        try:
            with open(bak_path, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            return False
        if not isinstance(d, dict) or "exams" not in d or "modules" not in d:
            return False
        self._rotate_backups()  # 先把当前（可能坏掉的）数据留一份备份，避免覆盖后无法回退
        self.data = d
        self.data.setdefault("custom_papers", [])
        self.data.setdefault("paper_config", {})
        self.data.setdefault("goal", {})
        self._ensure_fields()
        self._init_paper_config()
        self.save()
        return True

    def save(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        dirn = os.path.dirname(self.path) or "."
        data_str = json.dumps(self.data, ensure_ascii=False, indent=2)
        # 内容未变化则不刷盘、不备份（load() 也会调 save，避免每次启动都生成备份）
        try:
            old = None
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    old = f.read()
            if old == data_str:
                if not os.path.exists(self.path):   # 极端情况：文件被删，确保重建
                    with open(self.path, "w", encoding="utf-8") as f:
                        f.write(data_str)
                self._invalidate()
                return
        except Exception:
            pass
        # 内容有变化：先滚动备份，再原子写（先写临时文件再 os.replace，崩溃也不损坏 data.json）
        self._rotate_backups()
        tmp = os.path.join(dirn, f".data.{os.getpid()}.tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(data_str)
            os.replace(tmp, self.path)
        except Exception:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        self._invalidate()

    def _invalidate(self):
        """清空统计缓存（任何写操作后应调用）。"""
        self._stat_cache = {}

    # ---------- 考试计时（全局状态持久化） ----------
    def get_timer(self):
        """返回考试计时全局状态（datetime 字段已反序列化为 datetime 对象）；无则返回 None。"""
        t = self.data.get("timer_state")
        if not isinstance(t, dict):
            return None
        out = dict(t)
        # 磁盘上是 ISO 字符串，恢复为 datetime 供界面使用
        for k in ("start", "end", "seg_start"):
            v = out.get(k)
            if isinstance(v, str):
                try:
                    out[k] = datetime.fromisoformat(v)
                except Exception:
                    out[k] = None
        return out

    def set_timer(self, state):
        """持久化考试计时全局状态（跨重启保留）。datetime 字段序列化为 ISO 字符串，避免 json.dump 报错。"""
        ser = {}
        for k, v in state.items():
            ser[k] = v.isoformat() if isinstance(v, datetime) else v
        self.data["timer_state"] = ser
        self.save()

    # ---------- 模块 ----------
    def modules(self):
        return self.data["modules"]

    def module(self, key):
        for m in self.data["modules"]:
            if m["key"] == key:
                return m
        return None

    def add_module(self, name, total, color="#5AA9E6", points=1.0):
        key = "m_" + uuid.uuid4().hex[:6]
        self.data["modules"].append({
            "key": key, "name": name, "total": int(total),
            "points": float(points), "color": color,
        })
        # 同步到所有卷型配置
        base = self.data["paper_config"].get("江苏A类", {})
        for pt, d in self.data["paper_config"].items():
            d[key] = dict(base.get(key, {"total": int(total), "perq": float(points)}))
        self.save()
        return key

    def update_module(self, key, **kw):
        m = self.module(key)
        if not m:
            return False
        for k, v in kw.items():
            if k in ("name", "total", "color"):
                m[k] = v
            elif k == "points":
                try:
                    m["points"] = float(v)
                except (TypeError, ValueError):
                    m["points"] = 0.0
        self.save()
        return True

    def remove_module(self, key):
        self.data["modules"] = [m for m in self.data["modules"] if m["key"] != key]
        # 清理目标与卷型配置
        goal = self.data.get("goal", {})
        for sub in (goal.get("overall", {}), goal.get("modules", {})):
            for v in (list(sub.values()) if isinstance(sub, dict) else []):
                if isinstance(v, dict):
                    v.pop(key, None)
        for d in self.data.get("paper_config", {}).values():
            d.pop(key, None)
        self.save()

    # ---------- 卷型配置（题量 + 每小题分值，按卷型分别配置） ----------
    def custom_papers(self):
        return self.data.setdefault("custom_papers", [])

    def all_paper_types(self):
        """内置卷型 + 用户自定义卷型。"""
        return PAPER_TYPES + [c["name"] for c in self.custom_papers() if c.get("name")]

    def paper_total(self, key, paper_type):
        """返回某模块在指定卷型下的题量。"""
        d = self.data.get("paper_config", {}).get(paper_type, {})
        return int(d.get(key, {}).get("total", 0) or 0)

    def paper_perq(self, key, paper_type):
        """返回某模块在指定卷型下的「每小题分值」。"""
        d = self.data.get("paper_config", {}).get(paper_type, {})
        return float(d.get(key, {}).get("perq", 0) or 0)

    def set_paper_module(self, key, paper_type, total, perq):
        d = self.data.setdefault("paper_config", {}).setdefault(paper_type, {})
        d[key] = {"total": int(total), "perq": float(perq)}
        self.save()

    def paper_points_total(self, paper_type):
        """该卷型配置下，Σ(题量 × 每小题分值) = 卷面总分。"""
        d = self.data.get("paper_config", {}).get(paper_type, {})
        return round(sum(v.get("total", 0) * v.get("perq", 0) for v in d.values()), 2)

    def normalize_paper(self, paper_type):
        """把该卷型每小题分值等比缩放，使卷面总分恰好为 100。"""
        d = self.data.get("paper_config", {}).get(paper_type, {})
        tot = sum(v.get("total", 0) * v.get("perq", 0) for v in d.values())
        if tot <= 0:
            return
        for v in d.values():
            v["perq"] = round(v["perq"] / tot * 100, 4)
        self.save()

    def reset_paper_official(self, paper_type):
        """把该卷型恢复为官方题量 / 分值（仅内置卷型可用）。"""
        if paper_type not in PAPER_TYPE_TOTALS:
            return False
        d = self.data.setdefault("paper_config", {}).setdefault(paper_type, {})
        for m in self.data["modules"]:
            k = m["key"]
            tot = PAPER_TYPE_TOTALS[paper_type].get(k, 0)
            pts = PAPER_TYPE_POINTS[paper_type].get(k, 0)
            d[k] = {"total": tot, "perq": round(pts / tot, 4) if tot > 0 else 0}
        self.save()
        return True

    def add_custom_paper(self, name, totals=None):
        name = (name or "").strip()
        if not name or name in self.all_paper_types():
            return False
        # 自定义卷型默认「空白起步」：题量与每小题分值全为 0，
        # 由用户自己在「数据管理 → 试卷配置」里逐模块填写题型与分值。
        if totals is None:
            totals = {m["key"]: 0 for m in self.modules()}
        self.custom_papers().append({"name": name, "totals": totals})
        d = self.data.setdefault("paper_config", {}).setdefault(name, {})
        for m in self.modules():
            d.setdefault(m["key"], {"total": 0, "perq": 0.0})
        self.save()
        return True

    def remove_custom_paper(self, name):
        before = len(self.custom_papers())
        self.data["custom_papers"] = [c for c in self.custom_papers() if c.get("name") != name]
        # 同步清理配置与目标
        self.data.get("paper_config", {}).pop(name, None)
        goal = self.data.get("goal", {})
        goal.get("overall", {}).pop(name, None)
        goal.get("modules", {}).pop(name, None)
        if len(self.custom_papers()) != before:
            self.save()
            return True
        return False

    # ---------- 考试记录 ----------
    def add_exam(self, date_str, name, modules, note="", paper_type="江苏A类",
                 start_time=None, end_time=None, duration_min=None):
        """modules: {key: {"total":int,"wrong":int}}"""
        eid = uuid.uuid4().hex[:10]
        exam = {
            "id": eid,
            "date": date_str,
            "name": name or "",
            "note": note or "",
            "paper_type": paper_type,
            "modules": modules,
            "start_time": start_time,
            "end_time": end_time,
            "duration_min": duration_min,
        }
        self.data["exams"].append(exam)
        self._stat_cache.clear()  # 数据变化：失效统计缓存（避免编辑后显示陈旧正确率/估分）
        self.save()
        return eid

    def update_exam(self, eid, **kw):
        ex = self.get_exam(eid)
        if not ex:
            return False
        for k, v in kw.items():
            ex[k] = v
        self._stat_cache.clear()  # 数据变化：失效统计缓存
        self.save()
        return True

    def delete_exam(self, eid):
        self.data["exams"] = [e for e in self.data["exams"] if e["id"] != eid]
        self._stat_cache.clear()  # 数据变化：失效统计缓存（避免删除后显示陈旧正确率/估分）
        self.save()

    def get_exam(self, eid):
        for e in self.data["exams"]:
            if e["id"] == eid:
                return e
        return None

    def list_exams(self, reverse=False, paper_types=None):
        """按日期排序（日期相同按 id 稳定排序）。paper_types 为可迭代集合时仅保留命中卷型。"""
        exs = self.data["exams"]
        if paper_types:
            pts = set(paper_types)
            exs = [e for e in exs if e.get("paper_type") in pts]
        exs = sorted(exs, key=lambda e: (e.get("date", ""), e.get("id", "")))
        return list(reversed(exs)) if reverse else exs

    # ---------- 统计 ----------
    @staticmethod
    def _parse_mod(v):
        """兼容 {total,wrong} 字典 与 [total,wrong] 列表两种历史格式。"""
        if isinstance(v, (list, tuple)) and len(v) >= 2:
            return int(v[0] or 0), int(v[1] or 0)
        if isinstance(v, dict):
            return int(v.get("total", 0) or 0), int(v.get("wrong", 0) or 0)
        return 0, 0

    @staticmethod
    def exam_stat(exam):
        """计算单次考试各模块正确率与总体正确率。"""
        per = {}
        tot_q = 0
        tot_c = 0
        for k, v in exam.get("modules", {}).items():
            total, wrong = DataStore._parse_mod(v)
            wrong = min(wrong, total)
            correct = total - wrong
            per[k] = {
                "total": total,
                "wrong": wrong,
                "correct": correct,
                "acc": (correct / total) if total > 0 else 0.0,
            }
            tot_q += total
            tot_c += correct
        overall = (tot_c / tot_q) if tot_q > 0 else 0.0
        return {"per": per, "overall_acc": overall, "total_q": tot_q, "total_c": tot_c}

    def _stat(self, exam):
        """带缓存的 exam_stat（按 exam id 缓存，避免跨模块/跨视图重复计算）。"""
        eid = exam.get("id")
        if eid is not None and eid in self._stat_cache:
            return self._stat_cache[eid]
        res = DataStore.exam_stat(exam)
        if eid is not None:
            self._stat_cache[eid] = res
        return res

    def score_estimate(self, exam):
        """按「该卷型」每小题参考分值估算百分制成绩（各卷型分别配置）。

        估分 = Σ(正确数 × 每小题分值) / Σ(已答模块题量 × 每小题分值) × 100，
        即把已作答部分换算成百分制，全对即为 100。
        每小题分值取该场考试所属卷型的 paper_config；缺失时回退模块全局 points。
        返回 {score, per_points, max_points}，max_points 为已答模块的参考分值合计。
        """
        st = self._stat(exam)
        paper = exam.get("paper_type", "江苏A类")
        earned = 0.0
        answered_pts = 0.0
        per_pts = {}
        for k, s in st["per"].items():
            if s["total"] > 0:
                perq = self.paper_perq(k, paper)
                if perq is None or perq == 0:
                    m = self.module(k)
                    perq = (m.get("points") if (m and m.get("points")) else 1.0)
                mod_max = s["total"] * perq
                earned += s["correct"] * perq
                answered_pts += mod_max
                per_pts[k] = round(s["correct"] * perq, 2)
        score = round(earned / answered_pts * 100, 1) if answered_pts > 0 else 0.0
        return {"score": score, "per_points": per_pts, "max_points": round(answered_pts, 1)}

    def module_stats(self, key, paper_types=None):
        """跨考试统计某模块：平均/最佳/最差/首次/最近/趋势。"""
        rows = []
        for e in self.list_exams(paper_types=paper_types):
            st = self._stat(e)
            if key in st["per"]:
                rows.append((e.get("date", ""), st["per"][key]["acc"]))
        if not rows:
            return None
        accs = [a for _, a in rows]
        return {
            "dates": [d for d, _ in rows],
            "accs": accs,
            "avg": sum(accs) / len(accs),
            "best": max(accs),
            "worst": min(accs),
            "first": accs[0],
            "latest": accs[-1],
            "count": len(accs),
            "trend": accs[-1] - accs[0],
        }

    def module_avg(self, key, paper_types=None):
        s = self.module_stats(key, paper_types=paper_types)
        return s["avg"] if s else 0.0

    def overall_trend(self, paper_types=None):
        """返回按时间排序的 [(date, overall_acc, name)] 列表。"""
        out = []
        for e in self.list_exams(paper_types=paper_types):
            st = self._stat(e)
            out.append((e.get("date", ""), st["overall_acc"], e.get("name", "")))
        return out

    def duration_trend(self, paper_types=None):
        """返回 [(date, duration_min, name)]，仅含记录了用时的考试。"""
        out = []
        for e in self.list_exams(paper_types=paper_types):
            d = e.get("duration_min")
            if d:
                out.append((e.get("date", ""), float(d), e.get("name", "")))
        return out

    def overall_slope(self, n=None, paper_types=None):
        """最近 n 次总体正确率的线性斜率（每场次），正数代表上升。"""
        series = [a for _, a, _ in self.overall_trend(paper_types=paper_types)]
        if n:
            series = series[-n:]
        if len(series) < 2:
            return 0.0
        x = list(range(len(series)))
        n_ = len(series)
        mx = sum(x) / n_
        my = sum(series) / n_
        num = sum((x[i] - mx) * (series[i] - my) for i in range(n_))
        den = sum((x[i] - mx) ** 2 for i in range(n_))
        return (num / den) if den else 0.0

    def weaknesses(self, paper_types=None):
        """按平均正确率升序返回模块（薄弱在前）。"""
        rows = []
        for m in self.modules():
            s = self.module_stats(m["key"], paper_types=paper_types)
            if s:
                rows.append((m, s["avg"]))
        rows.sort(key=lambda x: x[1])
        return rows

    def paper_type_averages(self):
        """各卷型的总体正确率平均值（用于分卷型横向对比）。"""
        out = {}
        for pt in self.all_paper_types():
            trend = self.overall_trend(paper_types=[pt])
            if trend:
                out[pt] = sum(a for _, a, _ in trend) / len(trend)
        return out

    def insights(self, paper_types=None):
        """生成自然语言洞察。"""
        out = []
        trend = self.overall_trend(paper_types=paper_types)
        if not trend:
            return ["还没有考试记录，去「录入」添加第一场模考吧。"]
        latest_exam = self.list_exams(reverse=True, paper_types=paper_types)[0]
        est = self.score_estimate(latest_exam)
        out.append(
            f"最新一场（{latest_exam.get('date','')}）按参考分值估算约 {est['score']:.1f} 分"
            f"（百分制，参考分值合计约 {est['max_points']:.0f} 分）。"
        )
        slope = self.overall_slope(paper_types=paper_types)
        first_acc = trend[0][1]
        last_acc = trend[-1][1]
        if len(trend) >= 2:
            delta = last_acc - first_acc
            arrow = "上升" if delta > 0.005 else ("下降" if delta < -0.005 else "基本持平")
            out.append(
                f"整体正确率从首考 {first_acc*100:.1f}% 到最近 {last_acc*100:.1f}%，"
                f"共 {len(trend)} 场，{arrow} {abs(delta)*100:.1f} 个百分点。"
            )
        if len(trend) >= 3:
            s3 = self.overall_slope(3, paper_types=paper_types)
            if s3 > 0.01:
                out.append("近 3 场呈上升势头，保持节奏。")
            elif s3 < -0.01:
                out.append("⚠ 近 3 场出现下滑，建议复盘近期错题。")
        wk = self.weaknesses(paper_types=paper_types)
        if wk:
            m, avg = wk[0]
            out.append(f"最薄弱模块：{m['name']}，平均正确率仅 {avg*100:.1f}%，建议优先突破。")
            if len(wk) > 1:
                m2, avg2 = wk[1]
                out.append(f"次薄弱：{m2['name']}（{avg2*100:.1f}%）。")
        best_improve = None
        for m in self.modules():
            s = self.module_stats(m["key"], paper_types=paper_types)
            if s and s["count"] >= 2:
                if best_improve is None or s["trend"] > best_improve[1]:
                    best_improve = (m["name"], s["trend"])
        if best_improve and best_improve[1] > 0.02:
            out.append(f"进步最大：{best_improve[0]}，正确率提升 {best_improve[1]*100:.1f} 个百分点。")
        dur = self.duration_trend(paper_types=paper_types)
        if dur:
            avg_dur = sum(d for _, d, _ in dur) / len(dur)
            out.append(f"已记录用时 {len(dur)} 场，平均耗时 {avg_dur:.0f} 分钟。")
        return out

    # ---------- 目标（总计 + 分卷型两级） ----------
    def _goal(self):
        g = self.data.setdefault("goal", {})
        g.setdefault("overall", {})
        g.setdefault("modules", {})
        g["overall"].setdefault("总计", GOAL_DEFAULT_OVERALL)
        g["modules"].setdefault("总计", {})
        return g

    def get_overall_goal(self, paper_types=None):
        """返回当前筛选对应的总体目标；未单独设置则回退到「总计」。"""
        g = self._goal()
        ov = g["overall"]
        if paper_types and len(paper_types) == 1:
            pt = paper_types[0]
            if pt in ov and ov[pt] is not None:
                return ov[pt]
        return ov.get("总计", GOAL_DEFAULT_OVERALL)

    def get_module_goal(self, key, paper_types=None):
        """返回当前筛选对应的单模块目标；未设置返回 None。"""
        g = self._goal()
        mod = g["modules"]
        if paper_types and len(paper_types) == 1:
            pt = paper_types[0]
            if pt in mod and key in mod[pt] and mod[pt][key] is not None:
                return mod[pt][key]
        return mod.get("总计", {}).get(key, None)

    def set_overall_goal(self, paper_type, val):
        g = self._goal()
        g["overall"][paper_type] = float(val)
        self.save()

    def set_module_goal(self, paper_type, key, val):
        g = self._goal()
        g["modules"].setdefault(paper_type, {})[key] = float(val)
        self.save()

    def get_goal(self):
        """兼容旧接口：返回原始目标字典。"""
        return self._goal()

    # ---------- 导入导出 ----------
    def export_json(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def export_csv(self, path):
        """导出全部考试为 CSV（含总分/估分/用时/逐模块正确率）。"""
        import csv
        exams = self.list_exams(paper_types=None)
        mods = self.modules()
        header = ["日期", "名称", "卷型", "总体正确率", "总题量", "答对", "预估成绩", "开始时间", "结束时间", "用时(分钟)"]
        for m in mods:
            header.append(f"{m['name']}正确率")
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            for e in exams:
                st = self.exam_stat(e)
                est = self.score_estimate(e)
                row = [
                    e.get("date", ""), e.get("name", ""), e.get("paper_type", ""),
                    f"{st['overall_acc']*100:.1f}%", st["total_q"], st["total_c"],
                    f"{est['score']:.1f}", e.get("start_time") or "", e.get("end_time") or "",
                    e.get("duration_min") or "",
                ]
                for m in mods:
                    p = st["per"].get(m["key"])
                    row.append(f"{p['acc']*100:.1f}%" if (p and p["total"] > 0) else "")
                w.writerow(row)

    def import_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        if "exams" in d and "modules" in d:
            self.data = d
            self.data.setdefault("custom_papers", [])
            self.data.setdefault("paper_config", {})
            self.data.setdefault("goal", {})
            self._ensure_fields()
            self._init_paper_config()
            self.save()
            return True
        return False
