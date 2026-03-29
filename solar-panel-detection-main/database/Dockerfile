FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    psycopg2-binary \
    google-cloud-storage

# Copy scripts
COPY import_streaming.py .

# Run import
CMD ["python", "import_streaming.py"]
