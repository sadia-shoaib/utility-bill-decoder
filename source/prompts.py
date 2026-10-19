LEVEL1_PROMPT = """
You are extracting data from a Pakistani electricity bill (K-Electric, LESCO or IESCO).
Return ONLY a JSON object with exactly these keys:

{
  "provider": "KE | LESCO | IESCO",
  "tariff": "string or null",
  "sanctioned_load_kw": number or null,
  "bill_month": "YYYY-MM or null",
  "reading_date": "YYYY-MM-DD or null",
  "issue_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "previous_reading": number or null,
  "current_reading": number or null,
  "units_consumed": number or null,
  "charges": [{"type": "energy|fixed|fpa|quarterly_adjustment|surcharge|meter_rent|subsidy|other", "amount": number}],
  "total_charges": number or null,
  "taxes": [{"type": "gst|electricity_duty|income_tax|municipal_tax|other_tax", "amount": number}],
  "total_taxes": number or null,
  "current_bill": number or null,
  "arrears": number or null,
  "payable_within_due_date": number or null,
  "payable_after_due_date": number or null
}

Rules:
- Extract values exactly as printed. Do not recalculate, round or correct amounts.
- Amounts are plain numbers in PKR: remove "Rs.", commas and labels. "19,964" becomes 19964.
- Credits and subsidies are negative. "38209CR" becomes -38209.
- Dates: "22nd Sep 2026" becomes "2026-09-22"; "MAR 2026" becomes "2026-03".
- Skip charge lines printed as 0 or blank. Keep separate entries for repeated types.
- Classify tax lines by their section (Taxes and Duties / Government), not by name.
- If several late-payment amounts are shown, use the highest for payable_after_due_date.
- Use null for anything not printed, blank, covered by a grey box, or unreadable. Do not guess.
- Never include names, addresses, CNIC, account, reference, consumer or meter numbers.
- Output raw JSON only. No markdown, no commentary.
"""

HISTORY_PROMPT = """
Read this Pakistani electricity bill image and return ONLY a JSON object with these keys:

{
  "net_metered": true | false | null,
  "net_metering_evidence": "short phrase describing what you saw, or null",
  "usage_history": [{"month": "YYYY-MM", "units": number}],
  "billing_history": [{"month": "YYYY-MM", "billed_amount": number or null, "pay_date": "YYYY-MM-DD or null", "paid_amount": number or null}]
}

Rules:
- usage_history: one entry per bar in the usage history chart, oldest first. Read the units value shown for each bar. Work out each year from the year labels on the chart.
- billing_history: one entry per row of the billing and payment history table, in the order printed. Convert "MM/YY" to "YYYY-MM" (03/26 becomes 2026-03).
- net_metered: true only if the bill shows net metering, solar export or net-metered wording. false if the bill is a normal consumption bill with no such sign. null if unclear.
- Use null for any value that is not printed or is unreadable. Do not guess.
- Never include names, addresses, CNIC, account, reference, consumer or meter numbers.
- Output raw JSON only. No markdown, no commentary.
"""

ANSWER_PROMPT = """
You answer customer questions about one Pakistani electricity bill. You receive BILL DATA (extracted from the bill), FACTS (values already calculated in code) and QUESTIONS.

Rules:
- Use only BILL DATA and FACTS. Do not use outside tariff or rate information.
- Use the numbers in FACTS exactly. Do not do your own arithmetic.
- If a needed value is null or missing, say plainly that the bill does not show it. Do not guess.
- If a value is an estimate or projection (its FACTS name contains "estimate"), say it is an estimate and briefly explain how it was calculated.
- If a question can be read more than one way, state the reading you used.
- Answer in English, in 1 to 3 short sentences, with the key numbers and units (PKR or units).
- Never include personal identifiers.
- Return ONLY a JSON object whose keys are the question IDs (for example "Q1") and whose values are the answer strings.
"""
