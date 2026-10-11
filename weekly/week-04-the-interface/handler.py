import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

TEST_MAP = {
    "2345-7": "glucose",    "GLU": "glucose",
    "2951-2": "sodium",     "NA": "sodium",
    "2823-3": "potassium",  "K": "potassium",
    "2160-0": "creatinine", "CREAT": "creatinine",
    "718-7": "hemoglobin",  "HGB": "hemoglobin",
    "6690-2": "wbc",        "WBC": "wbc",
}

UNIT_ALIASES = {
    "K/uL": "10*3/uL",
    "mEq/L": "mmol/L",
}

EASTERN = ZoneInfo("America/New_York")
CENTRAL = ZoneInfo("America/Chicago")

STATUS_RANK = {"C": 3, "F": 2, "W": 1, "P": 0}
STATUS_NAME = {"F": "final", "P": "preliminary", "C": "corrected"}


def parse_segments(message):
    segs = {}
    for segment in message.split("\r"):
        if not segment:
            continue
        fields = segment.split("|")
        segs[fields[0]] = fields
    if ("MSH" not in segs or "PID" not in segs
            or "OBR" not in segs or "OBX" not in segs):
        return None
    return segs


def is_real_result(segs):
    msh = segs["MSH"]
    if len(msh) < 11:
        return False
    if msh[8] != "ORU^R01":
        return False
    if msh[10] != "P":
        return False
    return True


def clean_accession(raw):
    return raw.strip().split("^")[0].upper()


def clean_test(raw):
    if not raw:
        return None
    code = raw.split("^")[0].strip().upper()
    return TEST_MAP.get(code)


def clean_patient_id(pid):
    if len(pid) <= 3 or not pid[3]:
        return None
    components = pid[3].split("^")
    if len(components) < 4:
        return None
    if components[3] != "HOSP":
        return None
    if not re.fullmatch(r"\d{8}", components[0]):
        return None
    return components[0]


def clean_value(raw):
    if not raw:
        return None
    raw = raw.strip()
    if raw[:1] in ("<", ">"):
        return None
    try:
        d = Decimal(raw)
        return format(d.quantize(Decimal("0.01")), "f")
    except (InvalidOperation, ArithmeticError, ValueError):
        return None


def clean_unit(raw):
    if not raw:
        return None
    raw = raw.strip()
    if raw in UNIT_ALIASES:
        return UNIT_ALIASES[raw]
    return raw.replace("^", "*")


def clean_observed_at(raw, connection):
    if not raw:
        return None
    raw = raw.strip()
    try:
        dt = datetime.strptime(raw, "%Y%m%d%H%M%S%z")
    except ValueError:
        try:
            naive = datetime.strptime(raw, "%Y%m%d%H%M%S")
        except ValueError:
            return None
        tz = (EASTERN if connection == "lis-results"
              else CENTRAL if connection == "reflab-results"
              else None)
        if tz is None:
            return None
        dt = naive.replace(tzinfo=tz)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_status_code(obx, obr):
    if len(obx) > 11 and obx[11]:
        return obx[11].strip()
    if len(obr) > 25 and obr[25]:
        return obr[25].strip()
    return ""


class Handler:
    def __init__(self):
        self.held = {}

    def process(self, raw):
        try:
            rec = json.loads(raw)
        except ValueError:
            return []

        try:
            segs = parse_segments(rec.get("message", ""))
            if segs is None:
                return []

            if not is_real_result(segs):
                return []

            obr = segs["OBR"]
            obx = segs["OBX"]

            accession = clean_accession(obr[3]) if len(obr) > 3 and obr[3] else None
            test = clean_test(obx[3] if len(obx) > 3 else None)
            if not accession or not test:
                return []

            key = (accession, test)
            existing = self.held.get(key)
            status_code = resolve_status_code(obx, obr)

            if status_code == "U":
                if existing is not None and STATUS_RANK["F"] >= existing["_rank"]:
                    existing["status"] = "final"
                    existing["_rank"] = max(existing["_rank"], STATUS_RANK["F"])
                return []

            new_rank = STATUS_RANK.get(status_code, -1)

            if existing is not None and new_rank < existing["_rank"]:
                return []

            patient_id = clean_patient_id(segs["PID"])
            value = None if status_code == "W" else clean_value(obx[5] if len(obx) > 5 else None)
            unit = clean_unit(obx[6] if len(obx) > 6 else None)
            observed_at = clean_observed_at(obr[7] if len(obr) > 7 else None,
                                             rec.get("connection"))
            status = STATUS_NAME.get(status_code)

            self.held[key] = {
                "accession": accession,
                "test": test,
                "patient_id": patient_id,
                "value": value,
                "unit": unit,
                "observed_at": observed_at,
                "status": status,
                "_rank": new_rank,
            }
            return []
        except Exception:
            return []

    def finalize(self):
        out = []
        for row in self.held.values():
            clean_row = {k: v for k, v in row.items() if k != "_rank"}
            out.append(clean_row)
        return out
