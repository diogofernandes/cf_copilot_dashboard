"""Single-service public demo entry point for Streamlit Community Cloud."""
import os
import runpy
import threading
import time
from pathlib import Path
import requests
import streamlit as st
import uvicorn

os.environ["DEMO_MODE"] = "1"
os.environ["EMAIL_PROVIDER"] = "local_rules"
os.environ["API_URL"] = "http://127.0.0.1:8765"

@st.cache_resource(show_spinner=False)
def start_demo_api():
    from cf_copilot.api.fast import app
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8765, log_level="warning"))
    thread = threading.Thread(target=server.run, name="portfolio-demo-api", daemon=True)
    thread.start()
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if not thread.is_alive():
            raise RuntimeError("The demonstration API could not start.")
        try:
            response = requests.get("http://127.0.0.1:8765/health", timeout=1)
            if response.ok and response.json().get("model_ready"):
                return server
        except (requests.RequestException, ValueError):
            pass
        time.sleep(0.2)
    server.should_exit = True
    raise RuntimeError("The demonstration model did not become ready within 90 seconds.")

start_demo_api()
runpy.run_path(str(Path(__file__).parent / "dashboard/app.py"), run_name="__main__")
