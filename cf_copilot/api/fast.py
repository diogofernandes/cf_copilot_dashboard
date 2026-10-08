"""Validated invoice API with explicit synthetic demonstration mode."""

import logging
import os
from contextlib import asynccontextmanager
from io import BytesIO
import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from cf_copilot.params import CURRENT_DATE, CHROMA_PATH, GEMINI_API_KEY
from cf_copilot.ml_logic.registry import load_model, predict
from cf_copilot.ml_logic.data import load_historical_data
from cf_copilot.cashflow_prediction.registry import predict_cashflow
from cf_copilot.collection_ranking.invoices_ranker import get_priority_invoices
from cf_copilot.rag.script_generator import generate_script, load_vector_store

logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


@asynccontextmanager
async def lifespan(app):
    app.state.demo = os.environ.get("DEMO_MODE", "1") == "1"
    app.state.vector_store = None
    app.state.startup_error = None
    if app.state.demo:
        from cf_copilot.demo import prepare_demo, DEMO_DATE

        app.state.pipeline, app.state.historical_data, app.state.metadata = prepare_demo()
        app.state.reference_date = DEMO_DATE
    else:
        app.state.reference_date = CURRENT_DATE
        app.state.metadata = {}
        try:
            app.state.pipeline = load_model()
            app.state.historical_data = load_historical_data()
        except Exception:
            logger.exception("Model/history initialization failed")
            app.state.pipeline = None
            app.state.historical_data = None
            app.state.startup_error = "Model or history unavailable."
    if os.environ.get("EMAIL_PROVIDER", "local_rules") == "gemini_rag":
        if not GEMINI_API_KEY or not CHROMA_PATH.exists():
            app.state.startup_error = "Gemini key or vector store unavailable."
        else:
            try:
                app.state.vector_store = load_vector_store(CHROMA_PATH)
            except Exception:
                logger.exception("Vector store initialization failed")
                app.state.startup_error = "Vector store unavailable."
    yield


app = FastAPI(title="CF Copilot", version="1.0.0", lifespan=lifespan)


@app.get("/")
def root():
    return {"message": "CF Copilot API", "docs": "/docs"}


@app.get("/health")
def health():
    ready = getattr(app.state, "pipeline", None) is not None
    return {
        "status": "ready" if ready else "unavailable",
        "model_ready": ready,
        "demo_mode": getattr(app.state, "demo", False),
        "reference_date": str(getattr(app.state, "reference_date", CURRENT_DATE).date()),
        "email_provider": "gemini_rag"
        if getattr(app.state, "vector_store", None) is not None
        else "local_rules",
        "startup_error": getattr(app.state, "startup_error", None),
    }


@app.get("/demo/invoices")
def demo_invoices():
    if not getattr(app.state, "demo", False):
        raise HTTPException(404, "Demo mode is disabled.")
    from cf_copilot.demo import synthetic_upload
    from fastapi.responses import Response

    return Response(
        synthetic_upload().to_csv(index=False),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="sample_invoices.csv"'},
    )


@app.get("/model-info")
def model_info():
    return {
        "demo_mode": getattr(app.state, "demo", False),
        "metadata": getattr(app.state, "metadata", {}),
        "buckets": {str(w): f"{7 * (w - 1) + 1}–{7 * w} days" if w < 7 else "43+ days" for w in range(1, 8)},
        "currency": "USD",
        "risk_definition": "Probability of payment after 28 days; not probability of default.",
    }


async def read_csv(file):
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Upload exceeds 5 MB.")
    try:
        return pd.read_csv(BytesIO(content), dtype={"doc_id": "string", "cust_number": "string"})
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError, ValueError):
        raise HTTPException(422, "Upload a valid UTF-8 CSV.")


def context(reference_date):
    if getattr(app.state, "pipeline", None) is None:
        raise HTTPException(503, "Model unavailable. Prepare the demo or train a model.")
    try:
        date = pd.Timestamp(reference_date).normalize() if reference_date else app.state.reference_date
        if pd.isna(date) or date.tz is not None:
            raise ValueError()
    except (ValueError, TypeError):
        raise HTTPException(422, "Reference date must be YYYY-MM-DD without a timezone.")
    return date, app.state.historical_data


def record_json(df):
    import json

    return json.loads(df.to_json(orient="records", date_format="iso"))


@app.post("/predict")
async def post_predict(file: UploadFile = File(...), reference_date: str | None = Form(None)):
    date, history = context(reference_date)
    df = await read_csv(file)
    try:
        result = predict(app.state.pipeline, df, date, history)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    predictions = [
        {
            "doc_id": str(row.doc_id),
            "predicted_bucket": int(result["week_bucket"][i]),
            "bucket_probabilities": {
                f"week_{w + 1}": float(p) for w, p in enumerate(result["probabilities"][i])
            },
        }
        for i, row in enumerate(result["invoices"].itertuples())
    ]
    return {"predictions": predictions, "reference_date": str(date.date()), "demo_mode": app.state.demo}


@app.post("/predict_cashflow")
async def post_cashflow(file: UploadFile = File(...), reference_date: str | None = Form(None)):
    date, history = context(reference_date)
    try:
        return record_json(predict_cashflow(await read_csv(file), app.state.pipeline, date, history))
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@app.post("/prioritise_invoices")
async def post_prioritise(file: UploadFile = File(...), reference_date: str | None = Form(None)):
    date, history = context(reference_date)
    try:
        return record_json(get_priority_invoices(await read_csv(file), app.state.pipeline, date, history))
    except ValueError as exc:
        raise HTTPException(422, str(exc))


class InvoiceDraft(BaseModel):
    doc_id: str
    cust_number: str
    name_customer: str
    total_open_amount: float = Field(ge=0, allow_inf_nan=False)
    due_in_date: str
    days_past_due: int
    cust_late_ratio: float = Field(default=0, ge=0, le=1)
    cust_n_transactions: int = Field(default=0, ge=0)
    risk_category: str = "Unknown"


@app.post("/rag_script")
def post_rag_script(invoice: InvoiceDraft):
    if os.environ.get("EMAIL_PROVIDER", "local_rules") == "gemini_rag" and app.state.vector_store is None:
        raise HTTPException(503, "Gemini RAG unavailable. Check credentials and build the vector store.")
    try:
        return generate_script(
            invoice.model_dump(), app.state.vector_store, reference_date=str(app.state.reference_date.date())
        )
    except Exception:
        logger.exception("Draft generation failed")
        raise HTTPException(502, "Draft generation failed. Review this invoice manually.")
