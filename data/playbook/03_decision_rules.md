# Payment Action Decision Rules

## Purpose

This document defines the rules the system uses to select the correct communication
action for any given invoice at any point in time.

---

## Primary Decision Variables

1. **days_past_due** — number of days since the due date (negative = not yet due)
2. **cust_late_ratio** — historical proportion of late payments for this customer
3. **total_open_amount** — outstanding invoice amount in USD/CAD
4. **business_segment** — customer industry segment
5. **cust_n_transactions** — number of previous invoices with this customer

---

## Action Selection Rules

### Rule 1: New customers (cust_n_transactions < 3)
- Always use the soft template regardless of days_past_due.
- Reason: insufficient history to assess risk. Preserve the relationship.
- Exception: if days_past_due > 30, escalate to standard template.

### Rule 2: High-value invoices (total_open_amount > $50,000)
- Trigger each stage 2 days earlier than the standard timeline.
- Example: First overdue notice at +3 days instead of +5 days.
- Reason: cash flow impact justifies earlier intervention.

### Rule 3: Low-risk customers (cust_late_ratio < 0.20)
- Use friendly tone templates.
- Skip the due-today notification (Stage 3) — assumed to be administrative oversight.
- Start overdue notices at +7 days instead of +5 days.

### Rule 4: High-risk customers (cust_late_ratio > 0.60)
- Use firm tone from Stage 4 onwards.
- Do not skip any stage.
- At Stage 5 (+15 days), copy the account manager on the email.

### Rule 5: Grocery Retail segment
- Standard timeline applies.
- Note: Large retail chains (Walmart, Kroger, Costco) often have internal AP processing
  delays of 3–5 days. Factor this in before escalating.

### Rule 6: Food Distribution segment
- Standard timeline applies.
- Distributors typically operate on tighter cash cycles. Escalate on schedule.

### Rule 7: Invoice already marked as paid
- No action. Do not send any communication.
- Log payment confirmation in the system.

---

## Action Output Format

For each invoice, the system should output:

```
{
  "invoice_id": "[INVOICE_ID]",
  "customer_name": "[CUSTOMER_NAME]",
  "action": "send_email",
  "template": "stage_4_first_overdue",
  "tone": "neutral",
  "priority": "high",
  "days_past_due": 5,
  "amount": 32500.00,
  "reasoning": "Invoice 5 days overdue. Customer late ratio 45% (medium risk). Standard Stage 4 template applies."
}
```

---

## Priority Levels

| Priority | Condition |
|----------|-----------|
| Critical | days_past_due > 30 OR amount > $100,000 |
| High     | days_past_due > 10 OR amount > $50,000 |
| Medium   | days_past_due between 1 and 10 |
| Low      | days_past_due <= 0 (not yet due) |

---

## Do Not Contact Rules

- Do not send more than one email per day to the same customer.
- Do not send emails on weekends or public holidays.
- If a customer has contacted AR team in the last 48 hours, pause automated emails and flag for manual review.
- If a payment plan has been agreed, suspend automated emails and monitor against plan schedule.
