# --------- STAGE 1: Build sma-emeter-simulator binary ---------
FROM debian:bullseye-slim AS builder

RUN apt-get update && apt-get install -y \
    git cmake g++ build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# Klone das Repository
RUN git clone --recurse-submodules https://github.com/RalfOGit/sma-emeter-simulator.git .
RUN git clone https://github.com/RalfOGit/libspeedwire.git libspeedwire
# Baue die Binary
RUN cmake -B build && cmake --build build
RUN ls
RUN ls build
# --------- STAGE 2: Python Runtime ---------
FROM python:3.11-slim

# Installiere system libraries (für netifaces etc., falls nötig)
RUN apt-get update && apt-get install -y gcc libffi-dev libssl-dev python3-dev build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kopiere Python-Dateien und requirements
COPY mqtt_wrapper.py /app/mqtt_wrapper.py
COPY requirements.txt /app/requirements.txt

# Kopiere die kompilierte Binary aus dem Builder
COPY --from=builder /src/build/sma-emeter-simulator /app/send_emeter_data

# Installiere Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Stelle sicher, dass die Binary ausführbar ist
RUN chmod +x /app/send_emeter_data

CMD ["python", "mqtt_wrapper.py"]
