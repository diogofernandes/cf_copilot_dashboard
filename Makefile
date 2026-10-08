.PHONY: install demo api dashboard test lint train
install:
	python -m pip install -r requirements_dev.txt
demo:
	python -m cf_copilot.demo
api:
	DEMO_MODE=1 EMAIL_PROVIDER=local_rules uvicorn cf_copilot.api.fast:app --host 127.0.0.1 --port 8080
dashboard:
	streamlit run dashboard/app.py
test:
	python -m pytest
lint:
	ruff check cf_copilot dashboard/app.py tests
train:
	python -m cf_copilot.interface.main
