import json
import math
import re
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP

HALF_HOUR = 1800
KEY_BASE = 10_000_000_000  # key = meter_number * KEY_BASE + epoch_seconds
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
MILLI = Decimal("0.001")

METER_RE = re.compile(r"^M\s*[-_ ]?\s*(\d{1,7})$")
QUALITY_RANK = {
    "A": 2, "ACTUAL": 2,
    "E": 1, "EST": 1, "ESTIMATED": 1, "SUB": 1, "SUBSTITUTED": 1,
}
QUALITY_NAME = {2: "actual", 1: "estimated", 0: None}

_meter_cache = {}
_time_cache = {}


def parse_meter(value):
    """M-####### -> int meter number, or None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 0 <= value < 10_000_000 else None
    if not isinstance(value, str):
        return None
    n = _meter_cache.get(value)
    if n is None:
        m = METER_RE.match(value.strip().upper())
        n = int(m.group(1)) if m else -1
        _meter_cache[value] = n
    return n if n >= 0 else None


def parse_time(value):
    """Any timestamp shape -> int UTC epoch seconds, or None."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        value = int(value)
    if isinstance(value, int):
        return value // 1000 if value > 100_000_000_000 else value  # ms -> s
    if not isinstance(value, str):
        return None
    t = _time_cache.get(value)
    if t is not None:
        return t
    s = value.strip()
    try:
        if s.isdigit():
            t = parse_time(int(s))
        elif re.fullmatch(r"\d+\.\d+", s):
            t = parse_time(float(s))
        else:
            if s[-1:] in ("Z", "z"):
                s = s[:-1] + "+00:00"
            if len(s) > 10 and s[10] in " t":
                s = s[:10] + "T" + s[11:]
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            t = int((dt - EPOCH).total_seconds())
    except (ValueError, OverflowError):
        return None
    _time_cache[value] = t
    return t


def parse_kwh(value):
    """Number / numeric string / {value, unit} -> int thousandths of a kWh, or None."""
    if value is None or isinstance(value, bool):
        return None
    scale = 1
    if isinstance(value, dict):
        if str(value.get("unit", "")).strip().lower() == "wh":
            scale = 1000
        value = value.get("value")
        if value is None or isinstance(value, bool):
            return None
    if isinstance(value, str):
        s = value.strip().replace(" ", "")
        low = s.lower()
        if low.endswith("kwh"):
            s = s[:-3]
        elif low.endswith("wh"):
            s, scale = s[:-2], 1000
        if "," in s:
            if "." in s:
                s = s.replace(",", "")  # 41,310.757
            else:
                s = s.replace(",", ".")  # 1,510 (decimal comma)
        value = s
    elif not isinstance(value, (int, float)):
        return None
    try:
        d = Decimal(str(value))
    except ArithmeticError:
        return None
    if not d.is_finite():
        return None
    if scale != 1:
        d = d / scale
    m = int(d.quantize(MILLI, rounding=ROUND_HALF_UP) * 1000)
    return m if m >= 0 else None


def fmt_kwh(m):
    return None if m is None else f"{m // 1000}.{m % 1000:03d}"


def quality_rank(value):
    if not isinstance(value, str):
        return 0
    return QUALITY_RANK.get(value.strip().upper(), 0)


def unwrap(record):
    """Return (record, is_correction, is_delete). Handles change-event envelopes."""
    if "meter_id" in record:
        return record, False, False
    payload = record.get("payload")
    if isinstance(payload, dict):
        record = payload
        if "meter_id" in record:
            return record, False, False
    after = record.get("after")
    before = record.get("before")
    op = str(record.get("op", "")).lower()
    if isinstance(after, dict) and op not in ("d", "delete"):
        if isinstance(before, dict):
            # identity from before if after omits it; values only from after
            merged = {k: before[k] for k in ("meter_id", "interval_end") if k in before}
            merged.update(after)
            return merged, True, False
        return after, True, False
    if isinstance(before, dict):
        return before, True, True
    return record, False, False


class Handler:
    def __init__(self):
        # key -> [quality_rank, usage_milli, register_milli, corrected]
        self.held = {}

    def process(self, raw):
        try:
            record = json.loads(raw)
        except (ValueError, TypeError):
            return []
        if not isinstance(record, dict):
            return []
        try:
            record, corrected, deleted = unwrap(record)
            meter = parse_meter(record.get("meter_id"))
            ts = parse_time(record.get("interval_end"))
        except Exception:
            return []
        if meter is None or ts is None or not 0 < ts < KEY_BASE:
            return []
        key = meter * KEY_BASE + ts

        if deleted:
            self.held.pop(key, None)
            return []

        try:
            usage = parse_kwh(record.get("kwh"))
            register = parse_kwh(record.get("register"))
        except Exception:
            usage = register = None
        rank = quality_rank(record.get("quality"))

        existing = self.held.get(key)
        if existing is None:
            self.held[key] = [rank, usage, register, corrected]
        elif corrected:
            # a correction overwrites the fields it carries
            if "quality" in record:
                existing[0] = rank
            if "kwh" in record:
                existing[1] = usage
            if "register" in record:
                existing[2] = register
            existing[3] = True
        elif existing[3]:
            pass  # already corrected; a late original read must not undo it
        elif rank > existing[0]:
            self.held[key] = [rank, usage, register, False]
        elif rank == existing[0]:
            # retry / late duplicate of the same quality: newest wins, but keep known values
            if usage is not None:
                existing[1] = usage
            if register is not None:
                existing[2] = register
        return []

    def finalize(self):
        held = self.held
        # pass 1: register-only meters -> usage is the register's rise over the interval
        for key, entry in held.items():
            if entry[1] is None and entry[2] is not None:
                prev = held.get(key - HALF_HOUR)
                if prev is not None and prev[2] is not None and entry[2] >= prev[2]:
                    entry[1] = entry[2] - prev[2]
        # pass 2: build rows, freeing held state as we go to keep peak memory down
        rows = []
        meter_str = {}
        time_str = {}
        while held:
            key, (rank, usage, register, _) = held.popitem()
            meter, ts = divmod(key, KEY_BASE)
            m = meter_str.get(meter)
            if m is None:
                m = meter_str[meter] = f"M-{meter:07d}"
            t = time_str.get(ts)
            if t is None:
                t = time_str[ts] = (EPOCH + timedelta(seconds=ts)).strftime("%Y-%m-%dT%H:%M:%SZ")
            rows.append({
                "meter_id": m,
                "interval_end": t,
                "usage_kwh": fmt_kwh(usage),
                "register_kwh": fmt_kwh(register),
                "quality": QUALITY_NAME[rank],
            })
        rows.reverse()
        self.held = {}
        return rows
