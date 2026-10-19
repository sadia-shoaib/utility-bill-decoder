"""Plain-Python calculations for Level 2.

The model never does arithmetic. Values are computed here and passed in as FACTS;
the model only phrases answers from them.
"""
import re
from statistics import mean

MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def _index(ym: str) -> int:
    year, month = map(int, ym.split("-"))
    return year * 12 + month - 1


def _month(index: int) -> str:
    year, month = divmod(index, 12)
    return f"{year:04d}-{month + 1:02d}"


def _round(value, digits=1):
    return None if value is None else round(value, digits)


def build_usage(history: dict, current_month, current_units) -> dict:
    """Month -> units, sorted oldest first, including the current bill's month."""
    usage = {}
    for item in history.get("usage_history") or []:
        month, units = item.get("month"), item.get("units")
        if isinstance(month, str) and MONTH_RE.match(month) and isinstance(units, (int, float)):
            usage[month] = units
    if current_month and isinstance(current_units, (int, float)):
        usage[current_month] = current_units
    return dict(sorted(usage.items()))


def build_facts(level1: dict, history: dict) -> dict:
    cur_month = level1.get("bill_month")
    cur_units = level1.get("units_consumed")
    cur_bill = level1.get("current_bill")
    within = level1.get("payable_within_due_date")
    after = level1.get("payable_after_due_date")
    taxes = level1.get("total_taxes")
    charges = level1.get("charges") or []
    usage = build_usage(history, cur_month, cur_units)

    facts = {
        "current_month": cur_month,
        "current_units": cur_units,
        "current_bill_pkr": cur_bill,
        "payable_within_due_date_pkr": within,
        "payable_after_due_date_pkr": after,
        "due_date": level1.get("due_date"),
        "late_payment_increase_pkr": (after - within)
        if isinstance(after, (int, float)) and isinstance(within, (int, float)) else None,
        "fpa_charges_current_month_pkr": [c["amount"] for c in charges if c.get("type") == "fpa"],
        "surcharge_lines_current_month_pkr": [c["amount"] for c in charges if c.get("type") == "surcharge"],
        "total_taxes_pkr": taxes,
        "tax_share_percent": _round(taxes / cur_bill * 100)
        if isinstance(taxes, (int, float)) and isinstance(cur_bill, (int, float)) and cur_bill else None,
        "net_metered": history.get("net_metered"),
        "net_metering_evidence": history.get("net_metering_evidence"),
        "usage_units_by_month": usage,
        "months_in_usage_history": len(usage),
    }

    if usage:
        top_month, top_units = max(usage.items(), key=lambda kv: kv[1])
        values = list(usage.values())
        facts["highest_units_month"] = top_month
        facts["highest_units"] = top_units
        facts["months_above_200_units"] = [m for m, u in usage.items() if u > 200]
        facts["average_units_all_months"] = _round(mean(values))
        facts["last_3_months_units"] = dict(list(usage.items())[-3:])
        facts["expected_next_month_units_estimate"] = _round(mean(values[-12:]))
        recent = values[-3:]
        if len(recent) == 3:
            facts["units_trend_last_3_months"] = (
                "up" if recent[2] > recent[0] else "down" if recent[2] < recent[0] else "flat"
            )
        if isinstance(cur_units, (int, float)):
            facts["current_vs_average_units"] = _round(cur_units - mean(values))

    if cur_month:
        last_year = _month(_index(cur_month) - 12)
        facts["same_month_last_year"] = last_year
        facts["units_same_month_last_year"] = usage.get(last_year)
        if usage.get(last_year) is not None and isinstance(cur_units, (int, float)):
            facts["difference_vs_same_month_last_year_units"] = cur_units - usage[last_year]

        prev_month = _month(_index(cur_month) - 1)
        prev_units = usage.get(prev_month)
        facts["units_previous_month"] = prev_units
        if prev_units is not None and isinstance(cur_bill, (int, float)) and isinstance(cur_units, (int, float)) and cur_units:
            cost_per_unit = cur_bill / cur_units
            facts["bill_cost_per_unit_pkr"] = _round(cost_per_unit, 2)
            facts["rough_bill_at_previous_month_units_estimate_pkr"] = round(cost_per_unit * prev_units)

    summer = {m: u for m, u in usage.items() if int(m[5:]) in (6, 7, 8)}
    winter = {m: u for m, u in usage.items() if int(m[5:]) in (12, 1, 2)}
    facts["summer_months_units"] = summer
    facts["winter_months_units"] = winter
    if summer and winter:
        facts["summer_avg_units_per_month"] = _round(mean(summer.values()))
        facts["winter_avg_units_per_month"] = _round(mean(winter.values()))
        facts["summer_minus_winter_avg_units_per_month"] = _round(mean(summer.values()) - mean(winter.values()))

    billing = [b for b in history.get("billing_history") or [] if isinstance(b, dict)]
    facts["billing_history_rows"] = billing
    facts["months_with_no_payment_recorded"] = [
        b.get("month") for b in billing if not b.get("pay_date") and not b.get("paid_amount")
    ]
    billed = [b["billed_amount"] for b in billing if isinstance(b.get("billed_amount"), (int, float))]
    if billed:
        facts["average_billed_amount_history_pkr"] = _round(mean(billed), 2)
        facts["average_monthly_bill_estimate_pkr"] = _round(mean(billed), 2)

    return facts
