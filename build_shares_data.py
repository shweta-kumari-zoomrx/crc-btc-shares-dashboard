"""build_shares_data.py — CRC/BTC EU Shares Dashboard data builder.

Reads: portal-fetch-toolkit/studies/492204/respondent_data.json
Outputs: public/shares_agg.json  (aggregate only — NO microdata)

Run from this folder:  python build_shares_data.py
"""
import json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)  # BTC EU Claude Code/

DATA_JSON = os.environ.get(
    "SHARES_DATA",
    os.path.join(PROJECT_ROOT, "portal-fetch-toolkit", "studies", "492204", "respondent_data.json"),
)

sys.path.insert(0, HERE)
import shares_maps as sm

LOTS = ["1L", "2L", "3L"]
CRC_STRATA = ["IHC3", "IHC2", "IHCUK"]
CRC_OVERALL_KEYS = ["Overall_all3", "Overall_ihc_pos", "Overall_median_replace"]


# ── Value helpers ──────────────────────────────────────────────────────────────

def to_float(v):
    if v is None or v == "---" or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _median(lst):
    s = sorted(lst)
    n = len(s)
    if n == 0:
        return 0.0
    m = n // 2
    return float(s[m] if n % 2 else (s[m - 1] + s[m]) / 2)


# ── Outlier fence (midpoint of IQR and Mean+2SD fences) ───────────────────────

def outlier_fence(nums):
    q1 = statistics.quantiles(nums, n=4)[0]
    q3 = statistics.quantiles(nums, n=4)[2]
    iqr_fence = q3 + 1.5 * (q3 - q1)
    sd2_fence = statistics.mean(nums) + 2 * statistics.stdev(nums)
    return (iqr_fence + sd2_fence) / 2


def local_ol_set(pool, qid):
    """Return set of rids whose response to qid exceeds the outlier fence."""
    vals = []
    for rid, r in pool.items():
        v = to_float(r["responses"].get(qid))
        if v is not None:
            vals.append((rid, v))
    nums = [v for _, v in vals if v > 0]
    if len(nums) < 2:
        return set()
    fence = outlier_fence(nums)
    return {rid for rid, v in vals if v > fence}


# ── Segment label helpers ──────────────────────────────────────────────────────

def practice_label(v):
    if not v:
        return "Other"
    s = str(v)
    if any(k in s for k in ("University", "Academic", "Teaching")):
        return "University / Academic"
    if any(k in s for k in ("Cancer", "Special")):
        return "Cancer / Specialized"
    if "Office" in s:
        return "Office-based"
    if any(k in s for k in ("Community", "General", "Non-teach")):
        return "Community / General"
    if "Private" in s:
        return "Private clinic"
    return "Other"


def specialty_label(v):
    if not v:
        return "Other"
    c = str(v).strip()
    if c == "MED_ONC":
        return "Medical Oncologist"
    if c == "GAS_ONC":
        return "Gastroenterological Oncologist"
    return "Other"


# ── Core share computation ─────────────────────────────────────────────────────

def get_shares(rws, drug_map, other_key, weight_fn):
    """
    Compute weighted and unweighted shares for a single (ind, IHC, lot, tf) cell.

    rws        : dict  rid -> record  (pre-filtered for this cell's sample)
    drug_map   : {drug_name: response_key}
    other_key  : response_key for the Other bucket (or None)
    weight_fn  : callable(responses_dict) -> float weight

    Returns (weighted, unweighted, n, tw) where:
      weighted / unweighted are {drug: fraction (0-1)}
      n  = number of respondents who answered
      tw = sum of weights for answered respondents
    """
    drugs = list(drug_map.keys())
    all_series = drugs + (["Other"] if other_key else [])

    weights = []
    share_rows = []

    for rid, rec in rws.items():
        resp = rec["responses"]
        row = {}
        answered = False

        for drug in drugs:
            v = to_float(resp.get(drug_map[drug]))
            if v is not None:
                row[drug] = v / 100.0
                answered = True
            else:
                row[drug] = 0.0

        if other_key:
            v = to_float(resp.get(other_key))
            if v is not None:
                row["Other"] = v / 100.0
                answered = True
            else:
                row["Other"] = 0.0

        if not answered:
            continue

        w = weight_fn(resp)
        weights.append(w if (w and w > 0) else 0.0)
        share_rows.append(row)

    n = len(share_rows)
    if n == 0:
        return {s: 0.0 for s in all_series}, {s: 0.0 for s in all_series}, 0, 0.0

    tw = sum(weights) or 1.0
    wt = {s: sum(weights[i] * share_rows[i].get(s, 0.0) for i in range(n)) / tw
          for s in all_series}
    uw = {s: sum(share_rows[i].get(s, 0.0) for i in range(n)) / n
          for s in all_series}
    return wt, uw, n, sum(weights)


# ── CRC weight helper ──────────────────────────────────────────────────────────

def crc_w(resp, lot, ihc):
    v = to_float(resp.get(sm.crc_weight_key(lot, ihc)))
    return v if (v and v > 0) else 0.0


# ── CRC cells ─────────────────────────────────────────────────────────────────

def crc_current_cell(rws, ihc, lot):
    drug_map = sm.CRC_CURR[ihc][lot]
    other_key = f"6094694_{ihc}_{lot}_Other"
    # Current sample: only respondents with weight > 0 in this cell
    filtered = {rid: r for rid, r in rws.items()
                if crc_w(r["responses"], lot, ihc) > 0}
    weight_fn = lambda resp: crc_w(resp, lot, ihc)
    return get_shares(filtered, drug_map, other_key, weight_fn)


def crc_future_cell(rws, ihc, lot):
    drug_map = sm.CRC_FUT[ihc][lot]
    qid = sm._CRC_FUT_QIDS[ihc][lot]
    other_key = f"{qid}_Other"
    weight_fn = lambda resp: crc_w(resp, lot, ihc)
    return get_shares(rws, drug_map, other_key, weight_fn)


# ── CRC Overall ───────────────────────────────────────────────────────────────

def crc_overall(rws, lot, tf, method):
    """
    Combine CRC strata into Overall using one of three methods:
      all3           : IHC3 + IHC2 + IHCUK, blend by patient volume (sum of weights)
      ihc_pos        : IHC3 + IHC2 only, blend by patient volume
      median_replace : all 3 strata; replace zero weights with stratum median first,
                       then blend by total (median-replaced) volume — matches Gyn method
    Returns (weighted, unweighted, n, tw)
    """
    cell_fn = crc_current_cell if tf == "current" else crc_future_cell

    if method == "ihc_pos":
        strata = ["IHC3", "IHC2"]
    else:
        strata = CRC_STRATA

    if method in ("all3", "ihc_pos"):
        cells = {ihc: cell_fn(rws, ihc, lot) for ihc in strata}
        total_tw = sum(cells[ihc][3] for ihc in strata) or 1.0
        all_s = sm.CRC_ALL_SERIES
        wt = {s: sum(cells[ihc][0].get(s, 0.0) * cells[ihc][3]
                     for ihc in strata) / total_tw
              for s in all_s}
        active_strata = [ihc for ihc in strata if cells[ihc][2] > 0]
        denom = len(active_strata) or 1
        uw = {s: sum(cells[ihc][1].get(s, 0.0) for ihc in active_strata) / denom
              for s in all_s}
        n = max((cells[ihc][2] for ihc in strata), default=0)
        return wt, uw, n, total_tw

    # median_replace: per-stratum median weight replacement, then blend
    def stratum_weights(ihc):
        return [crc_w(r["responses"], lot, ihc) for r in rws.values()]

    # Compute median-replaced total weight per stratum for proportional blending
    strata_tw_mr = {}
    for ihc in CRC_STRATA:
        ws = stratum_weights(ihc)
        pos = [w for w in ws if w > 0]
        med = _median(pos) if pos else 0.0
        strata_tw_mr[ihc] = sum(med if w == 0 else w for w in ws)

    total_tw = sum(strata_tw_mr.values()) or 1.0

    def mr_weight_fn(ihc):
        ws = stratum_weights(ihc)
        pos = [w for w in ws if w > 0]
        med = _median(pos) if pos else 0.0
        # Map from rid to median-replaced weight
        rid_list = list(rws.keys())
        w_map = {rid_list[i]: (med if ws[i] == 0 else ws[i]) for i in range(len(rid_list))}
        return lambda resp, _rid=None: 0.0  # placeholder — we rebuild below

    # Recompute cells with median-replaced weights
    all_s = sm.CRC_ALL_SERIES

    def mr_cell(ihc):
        drug_map = sm.CRC_CURR[ihc][lot] if tf == "current" else sm.CRC_FUT[ihc][lot]
        if tf == "current":
            other_key = f"6094694_{ihc}_{lot}_Other"
            inner = {rid: r for rid, r in rws.items()
                     if crc_w(r["responses"], lot, ihc) > 0}
        else:
            qid = sm._CRC_FUT_QIDS[ihc][lot]
            other_key = f"{qid}_Other"
            inner = rws

        ws = stratum_weights(ihc)
        pos = [w for w in ws if w > 0]
        med = _median(pos) if pos else 0.0
        rid_list = list(rws.keys())
        w_map = {rid_list[i]: (med if ws[i] == 0 else ws[i]) for i in range(len(rid_list))}

        def weight_fn(resp, _w_map=w_map, _inner=inner):
            # identify respondent by matching resp object (same dict ref)
            for rid, r in _inner.items():
                if r["responses"] is resp:
                    return _w_map.get(rid, 0.0)
            return 0.0

        # Build custom version: iterate inner directly
        drugs = list(drug_map.keys())
        ks = drugs + (["Other"] if other_key else [])
        weights_list, share_rows = [], []
        for rid, rec in inner.items():
            r = rec["responses"]
            row = {}
            answered = False
            for drug in drugs:
                v = to_float(r.get(drug_map[drug]))
                if v is not None:
                    row[drug] = v / 100.0
                    answered = True
                else:
                    row[drug] = 0.0
            if other_key:
                v = to_float(r.get(other_key))
                row["Other"] = v / 100.0 if v is not None else 0.0
                if v is not None:
                    answered = True
            if not answered:
                continue
            weights_list.append(w_map.get(rid, 0.0))
            share_rows.append(row)

        n = len(share_rows)
        if n == 0:
            return {s: 0.0 for s in ks}, {s: 0.0 for s in ks}, 0, 0.0
        tw = sum(weights_list) or 1.0
        wt_d = {s: sum(weights_list[i] * share_rows[i].get(s, 0.0)
                       for i in range(n)) / tw for s in ks}
        uw_d = {s: sum(share_rows[i].get(s, 0.0) for i in range(n)) / n for s in ks}
        return wt_d, uw_d, n, sum(weights_list)

    cells_mr = {ihc: mr_cell(ihc) for ihc in CRC_STRATA}
    wt = {s: sum(cells_mr[ihc][0].get(s, 0.0) * strata_tw_mr[ihc]
                 for ihc in CRC_STRATA) / total_tw
          for s in all_s}
    active_strata = [ihc for ihc in CRC_STRATA if cells_mr[ihc][2] > 0]
    denom = len(active_strata) or 1
    uw = {s: sum(cells_mr[ihc][1].get(s, 0.0) for ihc in active_strata) / denom
          for s in all_s}
    n = max((cells_mr[ihc][2] for ihc in CRC_STRATA), default=0)
    return wt, uw, n, total_tw


# ── BTC cells ─────────────────────────────────────────────────────────────────

def btc_weight(resp, lot):
    eligible = ((to_float(resp.get("6094650_A2")) or 0.0) +
                (to_float(resp.get("6094650_A3")) or 0.0))
    pct = to_float(resp.get(f"{sm.BTC_LOT_PCT_KEY}_{lot}")) or 0.0
    return eligible * (pct / 100.0)


def btc_current_cell(rws, lot):
    drug_map = sm.BTC_CURR["IHC3"][lot]
    other_key = sm.BTC_CURR_OTHER[lot]
    filtered = {rid: r for rid, r in rws.items()
                if btc_weight(r["responses"], lot) > 0}
    weight_fn = lambda resp: btc_weight(resp, lot)
    return get_shares(filtered, drug_map, other_key, weight_fn)


def btc_future_cell(rws, lot):
    drug_map = sm.BTC_FUT["IHC3"][lot]
    qids = {"1L": 6094731, "2L": 6094732, "3L": 6094733}
    other_key = f"{qids[lot]}_Other"
    weight_fn = lambda resp: btc_weight(resp, lot)
    return get_shares(rws, drug_map, other_key, weight_fn)


# ── Per-selection block ────────────────────────────────────────────────────────

def compute_block(rws):
    """Full share block for a selection of respondents."""

    def pack(wt, uw, n, tw):
        return {
            "n": n,
            "tw": round(tw, 4),
            "weighted": {k: round(v * 100, 4) for k, v in wt.items()},
            "unweighted": {k: round(v * 100, 4) for k, v in uw.items()},
        }

    block = {"CRC": {}, "BTC": {}}

    for tf in ("current", "future"):
        block["CRC"][tf] = {}
        block["BTC"][tf] = {}

        # CRC per-stratum
        for ihc in CRC_STRATA:
            block["CRC"][tf][ihc] = {}
            for lot in LOTS:
                fn = crc_current_cell if tf == "current" else crc_future_cell
                block["CRC"][tf][ihc][lot] = pack(*fn(rws, ihc, lot))

        # CRC Overall (3 methods)
        for method, key in zip(
            ("all3", "ihc_pos", "median_replace"),
            CRC_OVERALL_KEYS,
        ):
            block["CRC"][tf][key] = {}
            for lot in LOTS:
                block["CRC"][tf][key][lot] = pack(*crc_overall(rws, lot, tf, method))

        # BTC IHC3 (only stratum); Overall = IHC3
        block["BTC"][tf]["IHC3"] = {}
        block["BTC"][tf]["Overall"] = {}
        for lot in LOTS:
            fn = btc_current_cell if tf == "current" else btc_future_cell
            d = pack(*fn(rws, lot))
            block["BTC"][tf]["IHC3"][lot] = d
            block["BTC"][tf]["Overall"][lot] = d  # alias

    return block


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    with open(DATA_JSON, encoding="utf-8") as f:
        raw = json.load(f)
    respondents = raw["respondents"]

    # Remove GLOBAL_OL
    pool = {rid: r for rid, r in respondents.items()
            if r["admin"].get("outlier_type") != "GLOBAL_OL"}
    n_global_ol = len(respondents) - len(pool)

    # Local OL: union of CRC and BTC patient volume fences
    local_ol = local_ol_set(pool, "6094646") | local_ol_set(pool, "6094649")
    print(f"Global OL removed: {n_global_ol}")
    print(f"Local OL (patient volume fence): {len(local_ol)}")

    # Build enriched records
    records = {}
    for rid, r in pool.items():
        resp = r["responses"]
        records[rid] = {
            "responses": resp,
            "OL": rid in local_ol,
            "Practice Setting": practice_label(resp.get("6094642")),
            "Specialty": specialty_label(resp.get("6094760")),
            "Region": sm.map_region(resp.get("6094652")),
        }

    active = {rid: r for rid, r in records.items() if not r["OL"]}
    print(f"Total respondents: {len(records)}  Active: {len(active)}")

    # Selections: All + each individual segment value (multi-select browser-blending
    # uses tw to combine selections the user picks simultaneously)
    seg_cols = ["Practice Setting", "Specialty", "Region"]
    selections = [("All", "All respondents")]
    for col in seg_cols:
        for val in sorted({r[col] for r in active.values()}):
            selections.append((f"{col}={val}", f"{col}: {val}"))

    agg = {"meta": {}, "data": {}}
    sel_meta = []

    for key, label in selections:
        if key == "All":
            rws = active
        else:
            col, val = key.split("=", 1)
            rws = {rid: r for rid, r in active.items() if r[col] == val}
        sel_meta.append({"key": key, "label": label, "nActive": len(rws)})
        agg["data"][key] = compute_block(rws)
        print(f"  computed: {key}  (n={len(rws)})")

    agg["meta"] = {
        "indications": {"CRC": "Colorectal Cancer", "BTC": "Biliary Tract Cancer"},
        "crcStrata": CRC_STRATA,
        "crcStrataLabels": {
            "IHC3": "IHC3+",
            "IHC2": "IHC2+",
            "IHCUK": "IHC Unknown",
        },
        "crcOverallMethods": {
            "Overall_all3": "Overall (IHC3+ + IHC2+ + Unknown)",
            "Overall_ihc_pos": "Overall (IHC3+ + IHC2+ only)",
            "Overall_median_replace": "Overall (Median replace + IHC proportion)",
        },
        "btcStrata": ["IHC3", "Overall"],
        "btcStrataLabels": {"IHC3": "IHC3+", "Overall": "Overall (IHC3+)"},
        "lots": LOTS,
        "timeframes": {
            "current": "Current (Q3.15 / Q13.05)",
            "future": "Future (Q6.20–30 / Q16.05–15)",
        },
        "series": {"CRC": sm.CRC_ALL_SERIES, "BTC": sm.BTC_ALL_SERIES},
        "segments": seg_cols,
        "segmentBlendNote": "Multi-select: browser blends tw-weighted shares across selections",
        "selections": sel_meta,
        "nTotal": len(records),
        "nActive": len(active),
        "nGlobalOL": n_global_ol,
        "nLocalOL": len(local_ol),
    }

    pub = os.path.join(HERE, "public")
    os.makedirs(pub, exist_ok=True)
    out_path = os.path.join(pub, "shares_agg.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(agg, f, separators=(",", ":"))

    kb = os.path.getsize(out_path) // 1024
    print(f"\nDone — aggregate only, no microdata.")
    print(f"  -> {out_path}  ({kb} KB)")
    print(f"  {len(selections)} selections × 2 timeframes × CRC+BTC")


if __name__ == "__main__":
    main()
