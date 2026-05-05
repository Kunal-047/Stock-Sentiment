FROM python:3.11-slim

WORKDIR /app

# System deps for XGBoost + SHAP
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY main.py features.py model.py ./

# Model + DB are mounted at runtime (Railway volumes / local bind-mount).
# They are NOT baked into the image — keep the image lean and model-agnostic.
# Set via environment variables:
#   DB_PATH=market_data.db
#   MODEL_PATH=champion_model.pkl

EXPOSE 8000

CMD ["/bin/sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
