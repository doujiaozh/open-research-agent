FROM python:3.11-slim

LABEL description="Open Research Agent - web deployable AI research agent"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ ./agent/
COPY cli/ ./cli/
COPY web/ ./web/

ENV BACKEND=intern
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

CMD ["python", "web/server.py"]