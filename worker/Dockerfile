FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc git && rm -rf /var/lib/apt/lists/*

# Playwright dependencies (optional flag will control usage, but we install deps just in case)
# For now, minimal. If USE_PLAYWRIGHT is true, we might need a heavy image or install deps.
# Using a simpler approach: install playwright cli and install-deps if needed, or stick to slim if playright is optional feature flag.
# Let's start simple.

COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared code
COPY shared /app/shared

# Copy worker code
COPY worker /app/worker

ENV PYTHONPATH=/app

CMD ["python", "-m", "worker.app.main"]
