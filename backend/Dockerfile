# Use slim Python base
FROM python:3.10-slim

# Ensure we have up-to-date OS packages (patch CVEs)
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
       build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set our working dir
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy FastAPI application code
COPY app ./app

# Expose the port Uvicorn will run on
EXPOSE 8000

# Launch the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
