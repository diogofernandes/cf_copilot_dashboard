"""Real API integration. Failures remain errors; never fabricate predictions."""
import pandas as pd
import requests
from dashboard.constants import API_URL

def _get(path):
 r=requests.get(API_URL.rstrip("/")+path,timeout=15);r.raise_for_status()
 return r

def service_info():
 try:return _get("/health").json()
 except (requests.RequestException,ValueError):return {"model_ready":False,"error":"API not reachable."}

def sample_invoices():
 try:return _get("/demo/invoices").content,None
 except requests.RequestException:return None,"Could not load the sample. Start the demo API and try again."

def _post(path,file_bytes=None,reference_date=None,invoice=None):
 try:
  if invoice is not None:r=requests.post(API_URL.rstrip("/")+path,json=invoice,timeout=60)
  else:
   data={"reference_date":str(reference_date)} if reference_date else {}
   r=requests.post(API_URL.rstrip("/")+path,files={"file":("invoices.csv",file_bytes,"text/csv")},data=data,timeout=60)
  if r.status_code>=400:
   try:detail=r.json().get("detail","Request failed.")
   except ValueError:detail=r.text[:200]
   return None,f"API {r.status_code}: {detail}"
  return r.json(),None
 except requests.Timeout:return None,"Request timed out. Try again."
 except requests.RequestException:return None,"API not reachable. Start the backend and try again."
 except ValueError:return None,"Unexpected API response."

def call_predict_cashflow(file_bytes,reference_date=None):
 result,error=_post("/predict_cashflow",file_bytes,reference_date)
 return (pd.DataFrame(result) if result is not None else None),error

def call_predict(file_bytes,reference_date=None):
 result,error=_post("/predict",file_bytes,reference_date)
 return (pd.DataFrame(result["predictions"]) if result is not None else None),error

def call_prioritise_invoices(file_bytes,current_date=None):
 result,error=_post("/prioritise_invoices",file_bytes,current_date)
 return (pd.DataFrame(result) if result is not None else None),error

def call_rag_script(invoice):
 keys=("doc_id","cust_number","name_customer","total_open_amount","due_in_date","days_past_due",
       "cust_late_ratio","cust_n_transactions","risk_category")
 payload={key:invoice[key] for key in keys if key in invoice}
 payload["doc_id"]=str(payload["doc_id"]);payload["cust_number"]=str(payload["cust_number"])
 payload["due_in_date"]=str(pd.Timestamp(payload["due_in_date"]).date())
 return _post("/rag_script",invoice=payload)
