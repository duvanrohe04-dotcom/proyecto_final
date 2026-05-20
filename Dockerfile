FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=run.py

EXPOSE 81

CMD ["gunicorn", "--bind", "0.0.0.0:81", "--workers", "2", "run:app"]