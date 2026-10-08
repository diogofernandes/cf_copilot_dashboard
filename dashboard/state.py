"""Session state and invalidation; preserve invoice identity across the four steps."""
import hashlib
from io import BytesIO
import pandas as pd
import streamlit as st
from cf_copilot.ml_logic.schema import normalize_invoices

DEFAULT_STATE = {"df":None,"uploaded_bytes":None,"weekly_forecast":None,"predictions_df":None,
 "selected_invoice":None,"ai_result":None,"step":1,"input_fingerprint":None,
 "sample_bytes":None,"reference_date":None,"uploader_epoch":0,"selected_id":None,"upload_error":None,"sample_pending":False,"active_source":None,"last_upload":None}

def init_state():
 for key,value in DEFAULT_STATE.items():
  if key not in st.session_state:st.session_state[key]=value

def clear_results():
 for key in ("weekly_forecast","predictions_df","selected_invoice","ai_result","selected_id"):
  st.session_state[key]=None
 st.session_state.step=2 if st.session_state.get("df") is not None else 1

def reset_state():
 epoch=st.session_state.get("uploader_epoch",0)+1
 reference=st.session_state.get("reference_date")
 for key,value in DEFAULT_STATE.items():st.session_state[key]=value
 st.session_state.uploader_epoch=epoch
 st.session_state.reference_date=reference

def adopt_input(content,reference_date):
 fingerprint=hashlib.sha256(content+str(reference_date).encode()).hexdigest()
 if st.session_state.input_fingerprint==fingerprint:return
 clear_results()
 st.session_state.df=None;st.session_state.uploaded_bytes=None;st.session_state.step=1
 st.session_state.input_fingerprint=fingerprint;st.session_state.upload_error=None
 try:
  if len(content)>5*1024*1024:raise ValueError("Maximum file size is 5 MB.")
  df=pd.read_csv(BytesIO(content),dtype={"doc_id":"string","cust_number":"string"})
  df=normalize_invoices(df,inference=True)
  date=pd.Timestamp(reference_date)
  if (df["invoice_sent"]>date).any():raise ValueError("Invoice issue dates must be on or before the reference date.")
  if (df["invoice_paid"].notna()&(df["invoice_paid"]<=date)).any():
   raise ValueError("Upload outstanding invoices only; this file contains paid invoices.")
  st.session_state.df=df
  st.session_state.uploaded_bytes=df.to_csv(index=False).encode()
  st.session_state.step=2
 except (ValueError,UnicodeDecodeError,pd.errors.ParserError,pd.errors.EmptyDataError) as exc:
  st.session_state.upload_error=str(exc)

def select_invoice(invoice):
 identity=None if invoice is None else str(invoice["doc_id"])
 if identity!=st.session_state.selected_id:
  st.session_state.ai_result=None
 st.session_state.selected_id=identity
 st.session_state.selected_invoice=invoice
