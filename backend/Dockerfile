FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create data directory for SQLite fallback
RUN mkdir -p data

EXPOSE 8001

# Render 등 PaaS는 $PORT로 바인딩 포트를 주입한다. 없으면 로컬 기본값 8001.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}
