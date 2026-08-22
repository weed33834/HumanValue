"""版本一致性校验: VERSION 为唯一权威,四处引用必须同步。

校验点:
1. frontend/package.json 的 version 字段
2. 三语 README 的版本徽章 (badge/version-X.Y.Z-blue.svg)
3. CHANGELOG.md 顶部条目 (## [vX.Y.Z])

任一不一致以非零码退出,供 CI 门禁使用。
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def main() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail(f"VERSION 文件不是合法语义化版本: {version!r}")

    pkg = json.loads((ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    if pkg.get("version") != version:
        fail(f"frontend/package.json version={pkg.get('version')!r} != VERSION={version!r}")

    for name in ("README.md", "README.zh-CN.md", "README.ja-JP.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        m = re.search(r"badge/version-([\d.]+)-blue", text)
        if not m:
            fail(f"{name} 未找到版本徽章")
        elif m.group(1) != version:
            fail(f"{name} 徽章版本 {m.group(1)!r} != VERSION={version!r}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"^## \[v([\d.]+)\]", changelog, re.MULTILINE)
    if not m:
        fail("CHANGELOG.md 未找到任何版本条目")
    elif m.group(1) != version:
        fail(f"CHANGELOG 顶部条目 v{m.group(1)} != VERSION={version}")

    print(f"OK: 版本一致性通过 ({version})")


if __name__ == "__main__":
    main()
