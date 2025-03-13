FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads

ENV FLASK_APP=app.py
EXPOSE 6969

CMD ["gunicorn", "--bind", "0.0.0.0:6969", "--workers", "4", "app:app"]