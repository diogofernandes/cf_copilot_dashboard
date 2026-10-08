# Payment Communications — FAQ and Edge Cases

---

## Frequently Asked Questions

**Q: What should we do if a customer says they never received the invoice?**
A: Resend the invoice immediately with a new email. Reset the due date clock by 3 business days
to allow time for processing. Log the interaction in the AR system. Do not count this as a late
payment in the customer's history.

**Q: A customer says the invoice amount is incorrect. What do we do?**
A: Place the invoice on hold immediately. Do not send any further payment reminders until the
dispute is resolved. Escalate to the billing team within 24 hours. Resume the communication
timeline only after the corrected invoice is issued, starting from the new due date.

**Q: A customer requests an extension. How should we respond?**
A: Extensions of up to 15 days may be granted for customers with a late_ratio below 40% and
a good payment history. Extensions beyond 15 days require manager approval. Always confirm
the new agreed date in writing and update the system with the new expected payment date.
Resume the communication timeline from the new date.

**Q: What if a customer makes a partial payment?**
A: Acknowledge the partial payment immediately with a thank-you email. Update the
total_open_amount to reflect the remaining balance. Continue the communication timeline
based on the remaining amount and the original due date.

**Q: The customer is a very large account (e.g. Walmart, Kroger). Should we treat them differently?**
A: Large retail chains often have internal AP departments with processing cycles of 30–45 days.
For accounts with total annual spend above $1M, consult the account manager before sending
any overdue notices. The account manager may have context about expected payment schedules
that are not reflected in the system.

**Q: What if the invoice currency is CAD instead of USD?**
A: Apply the same timeline and rules. Always state the amount in the original invoice currency.
Do not convert amounts in communications.

**Q: A customer has multiple overdue invoices. Do we send one email per invoice?**
A: No. Consolidate all overdue invoices for the same customer into a single communication.
List each invoice individually in the email body. Use the oldest overdue invoice to determine
the communication stage.

---

## Edge Cases

### Customer with invoices in multiple business segments
Apply the rules for the segment with the higher total_open_amount.

### Invoice due on a weekend
Treat the following Monday as the effective due date for all timeline calculations.

### Customer account flagged as disputed
Suspend all automated communications. Route to the AR manager for manual handling.
Do not resume automated emails until the dispute flag is removed.

### Customer has a cust_risk_score above 0.8
Flag for immediate manual review regardless of days_past_due.
Do not send automated emails — contact by phone instead.

### Invoice amount below $500
Low-value invoices below $500 follow the standard timeline but skip Stage 6 and Stage 7.
These are resolved at Stage 5 or written off after 60 days.
