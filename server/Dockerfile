FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY config/ ./config/

RUN mkdir -p /app/data

EXPOSE 5000

ENV FLASK_APP=app.main
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app.main:app"]