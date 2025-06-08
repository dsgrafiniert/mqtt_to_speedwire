# --------- STAGE 2: Python Runtime ---------
FROM python:3.11-slim

# Installiere system libraries (für netifaces etc., falls nötig)
RUN apt-get update && apt-get install -y gcc libffi-dev libssl-dev python3-dev build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kopiere Python-Dateien und requirements
COPY *.py /app/.

COPY requirements.txt /app/requirements.txt

# Installiere Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "mqtt_wrapper.py"]
