"""
01_extract_elan.py
Parse ELAN .eaf files and export clean CSVs for:
- gesture strokes (with gesture_type joined)
- language (English intervals as annotated)

Folder assumptions (your project):
D:\Multimodal_CodeSwitching_Twi_English\
  annotations\eaf\GH001.eaf ...
  data_index\   (outputs go here)

Run:
  python scripts\01_extract_elan.py
"""

from pathlib import Path
import xml.etree.ElementTree as ET
import csv

BASE_DIR = Path(__file__).resolve().parents[1]
EAF_DIR = BASE_DIR / "annotations" / "eaf"
OUT_DIR = BASE_DIR / "data_index"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---- tier names (your exact tiers) ----
TIER_GEST_STROKE = "gesture_stroke"
TIER_GEST_TYPE   = "gesture_type"   # child of gesture_stroke
TIER_LANGUAGE    = "language"       # you labeled only English

def load_time_slots(root):
    time_slots = {}
    time_order = root.find("TIME_ORDER")
    for ts in time_order.findall("TIME_SLOT"):
        ts_id = ts.attrib["TIME_SLOT_ID"]
        tv = ts.attrib.get("TIME_VALUE")
        if tv is not None:
            time_slots[ts_id] = int(tv)
    return time_slots

def get_tier(root, tier_id):
    for t in root.findall("TIER"):
        if t.attrib.get("TIER_ID") == tier_id:
            return t
    return None

def parse_alignable(tier, time_slots):
    """Return list of dicts with ann_id,start_ms,end_ms,value"""
    out = []
    for ann in tier.findall("ANNOTATION"):
        a = ann.find("ALIGNABLE_ANNOTATION")
        if a is None:
            continue
        ann_id = a.attrib["ANNOTATION_ID"]
        s = time_slots.get(a.attrib["TIME_SLOT_REF1"])
        e = time_slots.get(a.attrib["TIME_SLOT_REF2"])
        val = (a.findtext("ANNOTATION_VALUE") or "").strip()
        out.append({"ann_id": ann_id, "start_ms": s, "end_ms": e, "value": val})
    return out

def parse_ref(tier):
    """Return list of dicts with ann_id,parent_ann_id,value"""
    out = []
    for ann in tier.findall("ANNOTATION"):
        r = ann.find("REF_ANNOTATION")
        if r is None:
            continue
        ann_id = r.attrib["ANNOTATION_ID"]
        parent = r.attrib["ANNOTATION_REF"]
        val = (r.findtext("ANNOTATION_VALUE") or "").strip()
        out.append({"ann_id": ann_id, "parent_ann_id": parent, "value": val})
    return out

def main():
    eaf_files = sorted(EAF_DIR.glob("*.eaf"))
    if not eaf_files:
        raise SystemExit(f"No .eaf files found in {EAF_DIR}")

    gestures_rows = []
    english_rows = []
    audit_rows = []

    for eaf_path in eaf_files:
        file_id = eaf_path.stem

        root = ET.parse(eaf_path).getroot()
        time_slots = load_time_slots(root)

        t_stroke = get_tier(root, TIER_GEST_STROKE)
        t_gtype  = get_tier(root, TIER_GEST_TYPE)
        t_lang   = get_tier(root, TIER_LANGUAGE)

        if t_stroke is None or t_gtype is None or t_lang is None:
            audit_rows.append([file_id, "MISSING_TIER",
                               f"stroke={t_stroke is not None}, type={t_gtype is not None}, lang={t_lang is not None}"])
            continue

        strokes = parse_alignable(t_stroke, time_slots)
        gtypes  = parse_ref(t_gtype)
        lang    = parse_alignable(t_lang, time_slots)

        # map gesture_type by parent stroke ann_id
        gtype_map = {g["parent_ann_id"]: g["value"].lower() for g in gtypes}

        # gestures
        for s in strokes:
            start_ms, end_ms = s["start_ms"], s["end_ms"]
            if start_ms is None or end_ms is None or end_ms <= start_ms:
                audit_rows.append([file_id, "BAD_STROKE_TIME", s["ann_id"]])
                continue
            gestures_rows.append({
                "file": file_id,
                "stroke_id": s["ann_id"],
                "start_ms": start_ms,
                "end_ms": end_ms,
                "dur_ms": end_ms - start_ms,
                "gesture_type": gtype_map.get(s["ann_id"], "")
            })

        # language (English intervals only as you annotated)
        for l in lang:
            start_ms, end_ms = l["start_ms"], l["end_ms"]
            if start_ms is None or end_ms is None or end_ms <= start_ms:
                audit_rows.append([file_id, "BAD_LANG_TIME", l["ann_id"]])
                continue
            label = (l["value"] or "").strip()
            english_rows.append({
                "file": file_id,
                "ann_id": l["ann_id"],
                "start_ms": start_ms,
                "end_ms": end_ms,
                "dur_ms": end_ms - start_ms,
                "label": label
            })

        audit_rows.append([file_id, "OK",
                           f"gestures={len(strokes)} gesture_type={len(gtypes)} lang={len(lang)}"])

    # write outputs
    gestures_csv = OUT_DIR / "gestures.csv"
    english_csv  = OUT_DIR / "english_intervals.csv"
    audit_csv    = OUT_DIR / "elan_audit.csv"

    def write_csv(path, rows, fieldnames):
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)

    if gestures_rows:
        write_csv(gestures_csv, gestures_rows,
                  ["file","stroke_id","start_ms","end_ms","dur_ms","gesture_type"])
    if english_rows:
        write_csv(english_csv, english_rows,
                  ["file","ann_id","start_ms","end_ms","dur_ms","label"])

    with audit_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file","status","details"])
        w.writerows(audit_rows)

    print("Wrote:")
    if gestures_rows: print(" ", gestures_csv)
    if english_rows:  print(" ", english_csv)
    print(" ", audit_csv)

if __name__ == "__main__":
    main()