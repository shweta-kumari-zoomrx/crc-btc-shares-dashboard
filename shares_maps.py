"""shares_maps.py — Survey metadata for CRC/BTC Shares Dashboard.
QID-based response key maps extracted from AP Portal survey 492204, 2026-06-24.
All current/future maps: {stratum: {lot: {drug_name: response_key}}}
"""

# ── Region ────────────────────────────────────────────────────────────────────
REGION_MAP = {
    "West":  ["Nordrhein-Westfalen", "Saarland", "Rheinland-Pfalz", "Hessen"],
    "South": ["Bayern", "Baden-Württemberg"],
    "East":  ["Berlin", "Thüringen", "Sachsen", "Brandenburg",
               "Sachsen-Anhalt", "Mecklenburg-Vorpommern"],
    "North": ["Hamburg", "Schleswig-Holstein", "Niedersachsen", "Bremen"],
}

def map_region(v):
    if not v: return "Unknown"
    s = str(v)
    for region, states in REGION_MAP.items():
        if any(st in s for st in states):
            return region
    return "Other"

# ── CRC current shares — Q3_15Z (QID 6094694) ─────────────────────────────────
# 2D matrix. Response key: f"6094694_{ihc}_{lot}_{Bcode}"
# Drugs shown per LoT confirmed from AP portal survey editor 2026-06-24.

_CRC_CURR_1L = {
    "Bevacizumab + fluoropyrimidine-based chemotherapy": "B2",
    "Cetuximab + FOLFOX / FOLFIRI":                     "B4",
    "Nivolumab + ipilimumab":                            "B7",
    "NTRK inhibitors":                                   "B8",
    "Panitumumab + FOLFOX/FOLFIRI":                      "B11",
    "Pembrolizumab":                                     "B12",
    "Ramucirumab + FOLFIRI":                             "B13",
    "Chemotherapy":                                      "B16",
    "Clinical trial":                                    "B17",
}
_CRC_CURR_2L = {
    "Aflibercept + FOLFIRI":                             "B1",
    "Bevacizumab + fluoropyrimidine-based chemotherapy": "B2",
    "Cetuximab ± FOLFIRI":                               "B3",
    "Encorafenib + cetuximab":                           "B5",
    "Nivolumab + ipilimumab":                            "B7",
    "NTRK inhibitors":                                   "B8",
    "Panitumumab + FOLFIRI":                             "B10",
    "Regorafenib":                                       "B14",
    "Chemotherapy":                                      "B16",
    "Clinical trial":                                    "B17",
}
_CRC_CURR_3L = {
    "Aflibercept + FOLFIRI":                             "B1",
    "Bevacizumab + fluoropyrimidine-based chemotherapy": "B2",
    "Cetuximab ± FOLFIRI":                               "B3",
    "Encorafenib + cetuximab":                           "B5",
    "Fruquintinib":                                      "B6",
    "Nivolumab + ipilimumab":                            "B7",
    "NTRK inhibitors":                                   "B8",
    "Panitumumab":                                       "B9",
    "Regorafenib":                                       "B14",
    "Trifluridine-tipiracil ± bevacizumab":              "B15",
    "Chemotherapy":                                      "B16",
    "Clinical trial":                                    "B17",
}
_CRC_CURR_LOTS = {"1L": _CRC_CURR_1L, "2L": _CRC_CURR_2L, "3L": _CRC_CURR_3L}

def _crc_curr(ihc):
    return {
        lot: {d: f"6094694_{ihc}_{lot}_{b}" for d, b in drugs.items()}
        for lot, drugs in _CRC_CURR_LOTS.items()
    }

CRC_CURR = {ihc: _crc_curr(ihc) for ihc in ("IHC3", "IHC2", "IHCUK")}

# ── CRC future shares — Q6_20/25/30Z per stratum (9 questions) ───────────────
# Response key: f"{qid}_{code}"
_CRC_FUT_QIDS = {
    "IHC3":  {"1L": 6094754, "2L": 6094756, "3L": 6094758},
    "IHC2":  {"1L": 6094723, "2L": 6094726, "3L": 6094727},
    "IHCUK": {"1L": 6094755, "2L": 6094757, "3L": 6094759},
}
_CRC_FUT_1L = {
    "Bevacizumab + fluoropyrimidine-based chemotherapy": "A1",
    "Cetuximab + FOLFOX / FOLFIRI":                     "A2",
    "Nivolumab + ipilimumab":                            "A3",
    "NTRK inhibitors":                                   "A4",
    "Panitumumab + FOLFOX/FOLFIRI":                      "A5",
    "Pembrolizumab":                                     "A6",
    "Chemotherapy":                                      "A7",
    "ENHERTU":                                           "PX",
    "PRODUCT Y + trastuzumab":                           "PY",
}
_CRC_FUT_2L = {
    "Aflibercept + FOLFIRI":                             "A1",
    "Bevacizumab + fluoropyrimidine-based chemotherapy": "A2",
    "Cetuximab ± FOLFIRI":                               "A3",
    "Encorafenib + cetuximab":                           "A4",
    "Nivolumab + ipilimumab":                            "A5",
    "NTRK inhibitors":                                   "A6",
    "Panitumumab + FOLFIRI":                             "A7",
    "Pembrolizumab":                                     "A8",
    "Ramucirumab + FOLFIRI":                             "A9",
    "Chemotherapy":                                      "A10",
    "ENHERTU":                                           "PX",
    "PRODUCT Y + trastuzumab":                           "PY",
}
_CRC_FUT_3L = {
    "Aflibercept + FOLFIRI":                             "A1",
    "Bevacizumab + fluoropyrimidine-based chemotherapy": "A2",
    "Cetuximab ± FOLFIRI":                               "A3",
    "Encorafenib + cetuximab":                           "A4",
    "Fruquintinib":                                      "A5",
    "Nivolumab + ipilimumab":                            "A6",
    "NTRK inhibitors":                                   "A7",
    "Panitumumab":                                       "A8",
    "Pembrolizumab":                                     "A9",
    "Ramucirumab + FOLFIRI":                             "A10",
    "Regorafenib":                                       "A11",
    "Trifluridine-tipiracil ± bevacizumab":              "A12",
    "Chemotherapy":                                      "A13",
    "ENHERTU":                                           "PX",
    "PRODUCT Y + trastuzumab":                           "PY",
}
_CRC_FUT_LOTS = {"1L": _CRC_FUT_1L, "2L": _CRC_FUT_2L, "3L": _CRC_FUT_3L}

def _crc_fut(ihc):
    qids = _CRC_FUT_QIDS[ihc]
    return {
        lot: {d: f"{qids[lot]}_{c}" for d, c in drugs.items()}
        for lot, drugs in _CRC_FUT_LOTS.items()
    }

CRC_FUT = {ihc: _crc_fut(ihc) for ihc in ("IHC3", "IHC2", "IHCUK")}

# ── CRC weight question — Q3_10Z (QID 6094691) ────────────────────────────────
# 2D matrix: rows=LoT (1L/2L/3L), cols=IHC (IHC3/IHC2/IHCUK). Values in #.
# Response key: f"6094691_{lot}_{ihc}"
def crc_weight_key(lot, ihc):
    return f"6094691_{lot}_{ihc}"

# ── BTC current shares — Q13_05Z_1L/2L/3L (QIDs 6094722/724/725) ────────────
# IHC3+ only. Response key: f"{qid}_{code}"
BTC_CURR = {
    "IHC3": {
        "1L": {
            "Cisplatin + gemcitabine":                   "6094722_A1",
            "Durvalumab + cisplatin + gemcitabine":      "6094722_A2",
            "Pembrolizumab + cisplatin + gemcitabine":   "6094722_A3",
            "Clinical trial":                            "6094722_A4",
        },
        "2L": {
            "Futibatinib":                               "6094724_A1",
            "Ivosidenib":                                "6094724_A2",
            "NTRK inhibitors":                           "6094724_A3",
            "Pembrolizumab":                             "6094724_A4",
            "Pemigatinib":                               "6094724_A5",
            "Zanidatamab":                               "6094724_A6",
            "Chemotherapy":                              "6094724_A7",
            "Clinical trial":                            "6094724_A8",
        },
        "3L": {
            "Futibatinib":                               "6094725_A1",
            "NTRK inhibitors":                           "6094725_A2",
            "Pembrolizumab":                             "6094725_A3",
            "Pemigatinib":                               "6094725_A4",
            "Zanidatamab":                               "6094725_A5",
            "Clinical trial":                            "6094725_A6",
        },
    }
}
# Other response keys for BTC current
BTC_CURR_OTHER = {"1L": "6094722_Other", "2L": "6094724_Other", "3L": "6094725_Other"}

# ── BTC future shares — Q16_05/10/15Z (QIDs 6094731/732/733) ─────────────────
# Product A = ENHERTU. IHC3+ only.
BTC_FUT = {
    "IHC3": {
        "1L": {
            "Cisplatin + gemcitabine":                   "6094731_A1",
            "Durvalumab + cisplatin + gemcitabine":      "6094731_A2",
            "Pembrolizumab + cisplatin + gemcitabine":   "6094731_A3",
            "ENHERTU":                                   "6094731_PA",
        },
        "2L": {
            "Futibatinib":                               "6094732_A1",
            "Ivosidenib":                                "6094732_A2",
            "NTRK inhibitors":                           "6094732_A3",
            "Pembrolizumab":                             "6094732_A4",
            "Pemigatinib":                               "6094732_A5",
            "Zanidatamab":                               "6094732_A6",
            "Chemotherapy":                              "6094732_A7",
            "ENHERTU":                                   "6094732_PA",
        },
        "3L": {
            "Futibatinib":                               "6094733_A1",
            "NTRK inhibitors":                           "6094733_A2",
            "Pembrolizumab":                             "6094733_A3",
            "Pemigatinib":                               "6094733_A4",
            "Zanidatamab":                               "6094733_A5",
            "ENHERTU":                                   "6094733_PA",
        },
    }
}

# ── BTC weight question — Q13_00Z (QID 6094719) ───────────────────────────────
# "What % of your IHC3+ BTC patients are in 1L/2L/3L?" Values in %.
# Multiply by eligible BTC volume (6094650_A2 + 6094650_A3) to get patient count.
BTC_LOT_PCT_KEY  = "6094719"          # sub-keys: 6094719_1L, 6094719_2L, 6094719_3L
BTC_ELIGIBLE_KEY = ("6094650_A2", "6094650_A3")   # unresectable + metastatic BTC

# ── Series lists (display order for dashboard) ────────────────────────────────
CRC_ALL_SERIES = [
    "ENHERTU",
    "PRODUCT Y + trastuzumab",
    "Pembrolizumab",
    "Nivolumab + ipilimumab",
    "Encorafenib + cetuximab",
    "Panitumumab + FOLFOX/FOLFIRI",
    "Panitumumab + FOLFIRI",
    "Panitumumab",
    "Cetuximab + FOLFOX / FOLFIRI",
    "Cetuximab ± FOLFIRI",
    "Ramucirumab + FOLFIRI",
    "Aflibercept + FOLFIRI",
    "Bevacizumab + fluoropyrimidine-based chemotherapy",
    "Regorafenib",
    "Fruquintinib",
    "Trifluridine-tipiracil ± bevacizumab",
    "NTRK inhibitors",
    "Chemotherapy",
    "Clinical trial",
    "Other",
]

BTC_ALL_SERIES = [
    "ENHERTU",
    "Durvalumab + cisplatin + gemcitabine",
    "Pembrolizumab + cisplatin + gemcitabine",
    "Cisplatin + gemcitabine",
    "Zanidatamab",
    "Pemigatinib",
    "Futibatinib",
    "Ivosidenib",
    "Pembrolizumab",
    "NTRK inhibitors",
    "Chemotherapy",
    "Clinical trial",
    "Other",
]
