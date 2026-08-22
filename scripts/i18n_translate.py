#!/usr/bin/env python3
"""前端 i18n 批量翻译脚本 — 把视图模板中的中文提取为 i18n key 并替换。

用法:
    python scripts/i18n_translate.py                 # 扫描并翻译(安全模式)
    python scripts/i18n_translate.py --dry-run       # 仅报告不修改

策略(安全模式, 只处理不会破坏 Vue 语法的情形):
1. 文本节点: `>纯中文<` → `>{{ $t('v.xxx') }}<`   (仅当该行无 {{ }} / :绑定 / 属性)
2. 简单属性: label="中文" / title="中文" / placeholder="中文" / empty-text="中文"
   → :label="$t('v.xxx')" 等  (仅纯中文值, 无 {{ }})
3. 生成的 key 追加到 en/zh/ja 三个 locale (namespace = 视图相对路径, 形如 v.admin.AdminDashboard)
4. zh 直接用原中文, ja 用近似翻译, en 用英文(由人工/LLM 后续完善)

跳过: mobile 视图、已手工处理的视图(见 SKIP)。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEWS = ROOT / "frontend" / "src" / "views"
LOCALES = ROOT / "frontend" / "src" / "i18n" / "locales"
DRY = "--dry-run" in sys.argv

# 已手工处理的视图 (跳过)
SKIP = {
    "manager/ManagerDashboard",
    "manager/TalentValueDashboard",
    "admin/ChatView",
}

CN = re.compile(r"[\u4e00-\u9fa5]")
TEXT_NODE = re.compile(r">([^<>{}]+)<")
ATTR = re.compile(r"\b(label|title|placeholder|empty-text|description)=([\"'])([^\"']*[\u4e00-\u9fa5][^\"']*)\2")

# 简单英文/日文词典 (用于 en/ja, 尽量覆盖高频词; 未命中用 zh 兜底)
EN_GLOSS = {
    "提交": "Submit", "确认": "Confirm", "取消": "Cancel", "保存": "Save", "删除": "Delete",
    "新建": "New", "创建": "Create", "编辑": "Edit", "刷新": "Refresh", "返回": "Back",
    "搜索": "Search", "查看": "View", "详情": "Details", "操作": "Actions", "状态": "Status",
    "名称": "Name", "类型": "Type", "创建时间": "Created At", "更新时间": "Updated At",
    "暂无": "No data", "加载中": "Loading", "成功": "Success", "失败": "Failed",
    "员工": "Employee", "部门": "Department", "角色": "Role", "绩效": "Performance",
    "管理员": "Admin", "启用": "Enable", "禁用": "Disable", "关闭": "Close", "确定": "OK",
    "全部": "All", "更多": "More", "下一步": "Next", "上一步": "Previous",
}
JA_GLOSS = {
    "提交": "送信", "确认": "確認", "取消": "キャンセル", "保存": "保存", "删除": "削除",
    "新建": "新規", "创建": "作成", "编辑": "編集", "刷新": "更新", "返回": "戻る",
    "搜索": "検索", "查看": "表示", "详情": "詳細", "操作": "操作", "状态": "状態",
    "名称": "名前", "类型": "種別", "创建时间": "作成日時", "更新时间": "更新日時",
    "暂无": "データなし", "加载中": "読込中", "成功": "成功", "失败": "失敗",
    "员工": "社員", "部门": "部門", "角色": "役割", "绩效": "実績",
    "管理员": "管理者", "启用": "有効", "禁用": "無効", "关闭": "閉じる", "确定": "OK",
    "全部": "すべて", "更多": "もっと", "下一步": "次へ", "上一步": "前へ",
}


def en_fallback(zh: str) -> str:
    if zh in EN_GLOSS:
        return EN_GLOSS[zh]
    # 去掉常见后缀词再试
    return EN_GLOSS.get(zh.rstrip("：:·、"), zh)


def ja_fallback(zh: str) -> str:
    return JA_GLOSS.get(zh, zh)


def key_from(rel: str, idx: int) -> str:
    # v.admin.AdminDashboard.3
    ns = "v." + rel.replace("/", ".").replace("-", "_")
    return f"{ns}.{idx}"


def main() -> int:
    changed_files = 0
    added_keys = 0
    for vue in sorted(VIEWS.rglob("*.vue")):
        rel = str(vue.relative_to(VIEWS)).replace("\\", "/").replace(".vue", "")
        if rel in SKIP or rel.startswith("mobile/"):
            continue
        src = vue.read_text(encoding="utf-8")
        m = re.search(r"<template>(.*?)</template>", src, re.S)
        if not m:
            continue
        tpl = m.group(1)

        # 收集中文串
        texts = []
        for x in TEXT_NODE.findall(tpl):
            t = x.strip()
            if t and CN.search(t) and "{{" not in t and ":" not in t and "=" not in t:
                texts.append(t)
        attrs = [a[2].strip() for a in ATTR.findall(tpl) if "{{" not in a[2]]
        if not texts and not attrs:
            continue

        # 生成 key 替换
        ns = "v." + rel.replace("/", ".").replace("-", "_")
        mapping = {}

        def take(item):
            idx = len(mapping)
            k = f"{ns}.{idx}"
            mapping[k] = item
            return k

        new_tpl = tpl
        # 属性替换 (先处理, 避免文本节点误替换属性值)
        for name, quote, val in ATTR.findall(tpl):
            if "{{" in val:
                continue
            k = take(val.strip())
            new_tpl = new_tpl.replace(
                f'{name}={quote}{val}{quote}',
                f':{name}="$t(\'{k}\')"',
                1,
            )
        # 文本节点替换
        for x in sorted(set(texts), key=len, reverse=True):
            if "{{" in x or ":" in x:
                continue
            k = take(x)
            new_tpl = new_tpl.replace(f">{x}<", f">{{ $t('{k}') }}<", 1)

        if not mapping:
            continue

        new_src = src[: m.start(1)] + new_tpl + src[m.end(1):]
        if DRY:
            print(f"[dry] {rel}: {len(mapping)} keys")
            continue

        # 追加 locale
        for lang, fallback in (("en", en_fallback), ("zh", lambda x: x), ("ja", ja_fallback)):
            lf = LOCALES / f"{lang}.js"
            content = lf.read_text(encoding="utf-8")
            block = "\n  " + ns + ": {\n" + "\n".join(
                f"    {i}: {__import__('json').dumps(fallback(v), ensure_ascii=False)}," for i, v in mapping.items()
            ) + "\n  },\n"
            content = content.rstrip()
            if content.endswith("}"):
                content = content[:-1].rstrip() + "\n" + block.rstrip() + "\n}"
            lf.write_text(content, encoding="utf-8")

        vue.write_text(new_src, encoding="utf-8")
        changed_files += 1
        added_keys += len(mapping)
        print(f"[ok] {rel}: {len(mapping)} keys")

    print(f"\n== 完成: {changed_files} 个文件, {added_keys} 个 key ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
