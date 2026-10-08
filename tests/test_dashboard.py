"""Exercise the restored course design against the real synthetic demo."""
from pathlib import Path
import ast
import hashlib
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from cf_copilot.api.fast import app as api

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def dashboard(monkeypatch):
 import requests
 monkeypatch.setenv("DEMO_MODE","1")
 monkeypatch.setenv("EMAIL_PROVIDER","local_rules")
 with TestClient(api) as client:
  def get(url,**kwargs):
   return client.get("/"+url.split(":8080/",1)[1])
  def post(url,**kwargs):
   kwargs.pop("timeout",None)
   return client.post("/"+url.split(":8080/",1)[1],**kwargs)
  monkeypatch.setattr(requests,"get",get)
  monkeypatch.setattr(requests,"post",post)
  yield AppTest.from_file(ROOT/"dashboard"/"app.py",default_timeout=30).run()

def button(app,key):
 return next(b for b in app.button if b.key==key)

def test_original_theme_is_preserved():
 tree=ast.parse((ROOT/"dashboard/styles/theme.py").read_text())
 css=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
          and any(isinstance(t,ast.Name) and t.id=="_CSS" for t in n.targets))
 assert hashlib.sha256(css.encode()).hexdigest()=="8c452a0a786f5ec28369b5a24ed12411471b6d0ca8328dc4ccd13f2272172d8e"

def test_original_landing_and_complete_workflow(dashboard):
 assert not dashboard.exception
 assert any("Predict." in m.value and "Get Paid." in m.value for m in dashboard.markdown)
 button(dashboard,"btn_sample").click().run()
 assert not dashboard.exception
 assert len(dashboard.session_state["df"])==24
 button(dashboard,"btn_forecast").click().run()
 assert not dashboard.exception
 assert len(dashboard.session_state["weekly_forecast"])==7
 button(dashboard,"btn_predict").click().run()
 assert not dashboard.exception
 assert len(dashboard.session_state["predictions_df"])==10
 dashboard.selectbox[0].select_index(1).run()
 assert not dashboard.exception
 selected=dashboard.session_state["selected_invoice"]["doc_id"]
 button(dashboard,"btn_rag").click().run()
 assert not dashboard.exception
 assert dashboard.session_state["ai_result"]["doc_id"]==selected
 assert dashboard.session_state["ai_result"]["provider"]=="local_rules"
 dashboard.selectbox[0].select_index(2).run()
 assert dashboard.session_state["ai_result"] is None

def test_reference_change_clears_old_results(dashboard):
 button(dashboard,"btn_sample").click().run()
 button(dashboard,"btn_forecast").click().run()
 dashboard.date_input[0].set_value(pd.Timestamp("2024-10-02").date()).run()
 assert not dashboard.exception
 assert dashboard.session_state["weekly_forecast"] is None
 assert dashboard.session_state["selected_invoice"] is None

def test_failed_api_never_invents_a_forecast(dashboard,monkeypatch):
 import requests
 button(dashboard,"btn_sample").click().run()
 def failed(*args,**kwargs):raise requests.ConnectionError()
 monkeypatch.setattr(requests,"post",failed)
 button(dashboard,"btn_forecast").click().run()
 assert not dashboard.exception
 assert dashboard.session_state["weekly_forecast"] is None
 assert dashboard.error

def test_reset_clears_loaded_data(dashboard):
 button(dashboard,"btn_sample").click().run()
 next(b for b in dashboard.button if "Reset" in b.label).click().run()
 assert not dashboard.exception
 assert dashboard.session_state["df"] is None
 assert dashboard.session_state["step"]==1


def test_recruiter_case_study_is_available(dashboard):
 assert [tab.label for tab in dashboard.tabs] == ["Cash Flow Co-Pilot", "About the project"]
 text = "\n".join(item.value for item in dashboard.markdown)
 assert "Why it fits this problem" in text
 assert "Built collaboratively" in text
 assert any("synthetic demonstration results" in info.value for info in dashboard.info)
 assert any("45.2%" == metric.value for metric in dashboard.metric)
