# -------- STAGE 1: Builder --------
FROM python:3.11-alpine AS builder
WORKDIR /app

# System-Abhängigkeiten
RUN apk add --no-cache git build-base

# Arbeitsverzeichnis und pip-Installationspfad
ENV INSTALL_PATH=/install

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=${INSTALL_PATH} -r requirements.txt

# SMA EMETER Simulator clonen
RUN git clone https://github.com/RalfOGit/sma-emeter-simulator.git /app/simulator

# -------- STAGE 2: Runtime --------
FROM python:3.11-alpine AS runtime
WORKDIR /app

# Für numpy etc.
RUN apk add --no-cache libgcc libstdc++

# ENV für Pfad zu installierten Paketen
ENV PYTHONPATH=/install/lib/python3.11/site-packages
ENV PATH=/install/bin:$PATH

# Kopiere nur das Nötige
COPY --from=builder /install /install
COPY --from=builder /app/simulator /app/simulator
COPY mqtt_wrapper.py .

CMD ["python", "mqtt_wrapper.py"]
