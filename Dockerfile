FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY cf_copilot cf_copilot
COPY data/playbook data/playbook
ENV DEMO_MODE=1
EXPOSE 8080
CMD ["uvicorn", "cf_copilot.api.fast:app", "--host", "0.0.0.0", "--port", "8080"]
