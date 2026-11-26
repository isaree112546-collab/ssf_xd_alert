"""fetch_ca.py — เรียก SET corporate-action API แล้วบันทึกเป็น CSV (เฉพาะ XD เงินปันผลสด)

ใช้:
  python fetch_ca.py --api-key "YOUR_KEY"                 # ใส่ key เป็นพารามิเตอร์
  SET_API_KEY="YOUR_KEY" python fetch_ca.py               # หรือผ่าน environment variable (ปลอดภัยกว่า)
  python fetch_ca.py --ssf MINT,BCH,TQM --out xd.csv      # กรองเฉพาะหุ้นที่มี SSF

หมายเหตุ: ตามเอกสาร SET ส่ง key ทาง HTTP header ชื่อ `api-key` (ไม่ใช่ query parameter)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import date, datetime
from typing import Any, Optional

import requests

URL = "https://marketplace.set.or.th/api/public/reference-data/corporate-action"
PROFILE_URL = "https://marketplace.set.or.th/api/public/reference-data/security-profile"  # query: reportDate=YYYY-MM-DD


def fetch(api_key: str, url: str = URL, params: Optional[dict[str, str]] = None,
          retries: int = 4, timeout: int = 30) -> Any:
    last = ""
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers={"api-key": api_key, "Accept": "application/json"},
                             timeout=timeout)
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}: {r.text[:200]}"
            if r.status_code in (401, 403, 404):  # key ผิด/ไม่มีสิทธิ์: ลองซ้ำไม่ช่วย
                break
        except requests.RequestException as exc:
            last = str(exc)
        time.sleep(1.5 * 2 ** i)
    raise RuntimeError(f"เรียก API ไม่สำเร็จ: {last}")


def shrink(node: Any, n: int = 3) -> Any:
    """ตัดทุก list ให้เหลือ n รายการแรก ไว้ดูโครงสร้าง response"""
    if isinstance(node, list):
        return [shrink(x, n) for x in node[:n]]
    if isinstance(node, dict):
        return {k: shrink(v, n) for k, v in node.items()}
    return node


def pdate(v: Any) -> Optional[date]:
    s = str(v or "").strip()[:10]
    for f in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            d = datetime.strptime(s, f).date()
            return d.replace(year=d.year - 543) if d.year > 2400 else d
        except ValueError:
            pass
    return None


def to_rows(payload: dict[str, Any], ssf: Optional[set[str]] = None) -> list[list[Any]]:
    """caType CD: signDate = วัน XD, offeringPrice = ปันผล/หุ้น, announceDate = วันแจ้งข่าว
    API ไม่มีฟิลด์ปันผลพิเศษ: ถ้าหุ้นเดียวกันมี CD หลายแถวในวัน XD/วันประกาศเดียวกัน
    แถวแรก = ปันผล, ที่เหลือรวมเป็น EXTRA (เป็นการเดา ตรวจกับข่าวจริง)"""
    groups: dict[tuple[date, str, date], list[float]] = {}
    for rec in payload.get("corporateActions") or []:
        if str(rec.get("caType", "")).upper() != "CD":
            continue
        stock = str(rec.get("securitySymbol") or "").strip().upper()
        xd, ann, amt = pdate(rec.get("signDate")), pdate(rec.get("announceDate")), rec.get("offeringPrice")
        if not stock or not xd or amt is None or (ssf and stock not in ssf):
            continue
        groups.setdefault((ann or date.today(), stock, xd), []).append(float(amt))
    rows = []
    for (ann, stock, xd), a in sorted(groups.items(), key=lambda kv: (kv[0][2], kv[0][1])):
        rows.append([ann.strftime("%d/%m/%Y"), stock, xd.strftime("%d/%m/%Y"),
                     a[0], round(sum(a[1:]), 6) if len(a) > 1 else ""])
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--api-key", default=os.getenv("SET_API_KEY", ""))
    ap.add_argument("--ssf", default="", help="รายชื่อหุ้นที่มี SSF คั่นด้วย comma (ว่าง = ทุกตัว)")
    ap.add_argument("--out", default="set_ca.csv")
    ap.add_argument("--profile-sample", action="store_true",
                    help="เรียก security-profile แล้วบันทึกตัวอย่าง response (ย่อแล้ว) เป็น profile_sample.json")
    ap.add_argument("--report-date", default=date.today().isoformat(), help="YYYY-MM-DD (ใช้กับ --profile-sample)")
    a = ap.parse_args()
    if not a.api_key:
        print("ต้องระบุ API key (--api-key หรือตัวแปร SET_API_KEY)", file=sys.stderr)
        return 2
    if a.profile_sample:
        data = fetch(a.api_key, PROFILE_URL, {"reportDate": a.report_date})
        with open("profile_sample.json", "w", encoding="utf-8") as f:
            json.dump(shrink(data), f, ensure_ascii=False, indent=2)
        print(f"บันทึกตัวอย่างแล้ว -> profile_sample.json (reportDate={a.report_date})")
        return 0
    ssf = {s.strip().upper() for s in a.ssf.split(",") if s.strip()} or None
    payload = fetch(a.api_key)
    rows = to_rows(payload, ssf)
    with open(a.out, "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig ให้ Excel เปิดภาษาไทยได้
        w = csv.writer(f)
        w.writerow(["DATE", "STOCK", "xd", "ปันผล", "EXTRA DIVIDEND"])
        w.writerows(rows)
    print(f"ข้อมูล ณ {payload.get('asOfDate')} — บันทึก {len(rows)} แถว -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
