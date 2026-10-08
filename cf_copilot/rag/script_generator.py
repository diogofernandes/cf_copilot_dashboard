"""Explicit local draft policy, with optional Gemini retrieval. Never sends email."""


def load_vector_store(path):
    from cf_copilot.rag.gemini_generator import load_vector_store as load

    return load(path)


def build_vector_store(playbook_path, chroma_path):
    from cf_copilot.rag.gemini_generator import build_vector_store as build

    return build(playbook_path, chroma_path)


def generate_script(invoice, vector_store=None, k=4, reference_date=None):
    if vector_store is not None:
        from cf_copilot.rag.gemini_generator import generate_script as generate

        result = generate(invoice, vector_store, k, reference_date)
        result["provider"] = "gemini_rag"
        if result.get("action") == "send_email":
            result["action"] = "draft_email"
        return result
    days = int(invoice["days_past_due"])
    tone = "friendly" if days <= 7 else "neutral" if days <= 30 else "firm"
    body = (
        f"Dear {invoice['name_customer']},\n\nRegarding invoice {invoice['doc_id']} for "
        + "$"
        + f"{invoice['total_open_amount']:,.2f}, due on {invoice['due_in_date']}.\n\n"
    )
    body += (
        "Please let us know if you need a copy of the invoice or payment details."
        if days <= 0
        else "Please confirm the expected payment date or let us know of any billing issue."
    )
    body += "\n\nKind regards,\nAccounts Receivable Team"
    return {
        "action": "draft_email",
        "stage": "upcoming_reminder" if days <= 0 else "overdue_follow_up",
        "tone": tone,
        "priority": "high" if days > 30 else "medium" if days > 0 else "low",
        "subject": f"Payment follow-up — {invoice['doc_id']}",
        "email_body": body,
        "reasoning": f"Local demonstration policy: {max(days, 0)} days overdue. Human review required.",
        "playbook_reference": "demo_policy.md",
        "provider": "local_rules",
        "doc_id": invoice["doc_id"],
        "retrieved_sections": ["demo_policy.md"],
    }


if __name__ == "__main__":
    from cf_copilot.params import PLAYBOOK_PATH, CHROMA_PATH

    build_vector_store(PLAYBOOK_PATH, CHROMA_PATH)
