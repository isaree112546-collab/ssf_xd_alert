"""build_site.py — รันใน GitHub Actions: เรียก SET API -> สะสมประวัติใน data/set_ca.csv -> สร้างเว็บใน site/"""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fetch_ca import fetch, to_rows

HEADER = ["DATE", "STOCK", "xd", "ปันผล", "EXTRA DIVIDEND"]
HIST = Path("data/set_ca.csv")


def s(v: object) -> str:
    return "" if v in ("", None) else str(v)


def d(x: str) -> datetime:
    return datetime.strptime(x, "%d/%m/%Y")


def read_history() -> dict[tuple[str, str, str], list[str]]:
    out: dict[tuple[str, str, str], list[str]] = {}
    if HIST.exists():
        with HIST.open(encoding="utf-8-sig", newline="") as f:
            for r in list(csv.reader(f))[1:]:
                if len(r) >= 5 and r[0] and r[1] and r[2]:
                    out[(r[0], r[1], r[2])] = r[:5]
    return out


def read_ssf() -> list[str]:
    p = Path("ssf_list.txt")
    if not p.exists():
        return []
    text = "\n".join(line.split("#", 1)[0] for line in p.read_text(encoding="utf-8").splitlines())
    return sorted({t.upper() for t in re.split(r"[\s,;]+", text) if t})


def main() -> int:
    key = os.getenv("SET_API_KEY", "")
    if not key:
        print("ไม่พบ SET_API_KEY (ตั้งที่ Settings > Secrets and variables > Actions)", file=sys.stderr)
        return 2
    payload = fetch(key)
    hist = read_history()
    for r in to_rows(payload):  # ข้อมูลล่าสุดจาก SET ทับของเดิม ส่วนที่ SET เลิกแสดงยังคงเก็บไว้
        hist[(r[0], r[1], r[2])] = [s(x) for x in r]
    rows = sorted(hist.values(), key=lambda r: (d(r[2]), r[1], d(r[0])))

    HIST.parent.mkdir(exist_ok=True)
    with HIST.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(HEADER)
        w.writerows(rows)

    site = Path("site")
    shutil.rmtree(site, ignore_errors=True)
    site.mkdir()
    shutil.copy("template/index.html", site / "index.html")
    meta = {
        "asOf": payload.get("asOfDate"),
        "generatedAt": datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%d/%m/%Y %H:%M"),
        "ssf": read_ssf(),
        "rows": rows,
    }
    (site / "data.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    print(f"ข้อมูล SET ณ {meta['asOf']} | ประวัติ {len(rows)} แถว | หุ้น SSF {len(meta['ssf'])} ตัว")
    return 0


if __name__ == "__main__":
    sys.exit(main())
