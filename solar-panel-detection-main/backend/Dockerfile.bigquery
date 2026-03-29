FROM python:3.11-slim

WORKDIR /app

# Copy API file
COPY api_bigquery.py .

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    google-cloud-bigquery==3.14.1

# Run
CMD ["uvicorn", "api_bigquery:app", "--host", "0.0.0.0", "--port", "8080"]
