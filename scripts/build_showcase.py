"""Build the credential-free static showcase from real synthetic API responses."""
import os
import sys
import json
import re
from html import escape
from pathlib import Path
from io import BytesIO
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DEMO_MODE"] = "1"
os.environ["EMAIL_PROVIDER"] = "local_rules"
import pandas as pd
from fastapi.testclient import TestClient
from cf_copilot.api.fast import app
from dashboard.styles.theme import _CSS
from dashboard.components import landing, about

OUT = ROOT / "docs/site"
OUT.mkdir(parents=True, exist_ok=True)
with TestClient(app) as client:
    csv = client.get("/demo/invoices").content
    def request(path):
        response = client.post(path, files={"file": ("invoices.csv", csv, "text/csv")},
                               data={"reference_date": "2024-10-01"})
        response.raise_for_status()
        return response.json()
    rankings = request("/prioritise_invoices")
    drafts = {}
    for row in rankings:
        keys = ("doc_id","cust_number","name_customer","total_open_amount","due_in_date",
                "days_past_due","cust_late_ratio","cust_n_transactions","risk_category")
        payload = {key: row[key] for key in keys if key in row}
        payload["doc_id"] = str(payload["doc_id"])
        payload["cust_number"] = str(payload["cust_number"])
        payload["due_in_date"] = payload["due_in_date"][:10]
        response = client.post("/rag_script", json=payload)
        response.raise_for_status()
        drafts[str(row["doc_id"])] = response.json()
    data = {"reference_date":"2024-10-01",
            "invoices": json.loads(pd.read_csv(BytesIO(csv),dtype={"doc_id":str,"cust_number":str}).to_json(orient="records")),
            "forecast":request("/predict_cashflow"),"rankings":rankings,
            "predictions":request("/predict")["predictions"],"drafts":drafts,
            "metrics":json.loads((ROOT/"docs/demo_metrics.json").read_text())}
(OUT/"demo-data.json").write_text(json.dumps(data, indent=2).replace("; ", ", "))
(OUT/"sample-invoices.csv").write_bytes(csv)

def md(text):
    def inline(value):
        return re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", escape(value))
    parts=[]
    for block in str(text).strip().split("\n\n"):
        lines=block.splitlines()
        if all(re.match(r"^\d+\. ", line) for line in lines):
            parts.append("<ol>"+"".join("<li>"+inline(re.sub(r"^\d+\. ","",line))+"</li>" for line in lines)+"</ol>")
        elif all(line.startswith("- ") for line in lines):
            parts.append("<ul>"+"".join("<li>"+inline(line[2:])+"</li>" for line in lines)+"</ul>")
        else:parts.append("<p>"+inline(block)+"</p>")
    return "".join(parts)

class Capture:
    def __init__(self):self.html=[]
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def markdown(self,text,unsafe_allow_html=False):
        self.html.append(text if unsafe_allow_html else md(text))
    def write(self,text):self.html.append(md(text))
    def title(self,text):self.html.append("<h1>"+escape(text)+"</h1>")
    def subheader(self,text):self.html.append("<h2>"+escape(text)+"</h2>")
    def caption(self,text):self.html.append("<p class='note'>"+escape(text)+"</p>")
    def info(self,text):self.html.append("<div class='notice'>"+escape(text)+"</div>")
    def columns(self,count):return [self for _ in range(count)]
    def metric(self,label,value):self.html.append("<div class='metric'><span>"+escape(label)+"</span><strong>"+escape(str(value))+"</strong></div>")
    def link_button(self,label,url):self.html.append("<a class='btn-secondary' href='"+escape(url)+"' target='_blank' rel='noopener'>"+escape(label)+"</a>")

cap=Capture();landing.st=cap
landing.render_nav();nav="".join(cap.html);cap.html=[]
landing.render_hero();hero="".join(cap.html);cap.html=[]
hero=hero.replace("Upload your receivables and our AI predicts payment risks, forecasts", "Explore sample receivables, payment risks, and forecasts")
hero=hero.replace("Start Predicting Free","Try the Sample Demo")
hero=re.sub(r'<div class="hero-sub">.*?</div>', '<div class="hero-sub">Explore sample receivables, forecast cash flow and prepare collection drafts — all in one platform.</div>', hero, flags=re.S)
landing.render_how_it_works();features="".join(cap.html[:2])+"<div class=\"feature-grid\" id=\"features\">"+"".join(cap.html[2:])+"</div>";cap.html=[]
features=features.replace("Upload Your Data","Load Sample Invoices").replace("Upload your CSV","Load the sample CSV")
features=features.replace("RAG-powered insights explain each risk score, then draft a personalised collection email tuned to the risk level.",
                          "Explore invoice risk and a personalised sample collection draft prepared with local policy rules.")
about.st=cap;about.render_about();explanation="".join(cap.html)
explanation=explanation.replace("The default demonstration uses deterministic local collection rules.",
                               "This GitHub Pages showcase uses recorded Random Forest results for the supplied synthetic invoices. No Python server runs in your browser. The sample drafts were prepared with deterministic local collection rules.")
(OUT/"landing.html").write_text(nav+hero+features)
(OUT/"about.html").write_text(explanation.replace("; ", ", "))
(OUT/"original-theme.css").write_text(_CSS.replace("<style>","").replace("</style>",""))
print("Static showcase generated:",len(data["invoices"]),"invoices,",len(drafts),"drafts")
print("Ranking keys:",list(rankings[0]))
print("Draft keys:",list(next(iter(drafts.values()))))
