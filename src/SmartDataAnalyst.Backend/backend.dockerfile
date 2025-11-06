# backend.dockerfile
FROM python:3.12.12-slim

WORKDIR /app

# Copy dependency list and install
COPY src/SmartDataAnalyst.Backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY src/SmartDataAnalyst.Backend/ .

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]