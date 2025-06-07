# -------- STAGE 1: Builder --------
FROM python:3.11-alpine AS builder
WORKDIR /app

# Abhängigkeiten für Build & git
RUN apk add --no-cache git build-base

# Requirements einfügen und installieren
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# SMA EMETER Simulator clonen
RUN git clone https://github.com/RalfOGit/sma-emeter-simulator.git /app/simulator

# -------- STAGE 2: Runtime --------
FROM python:3.11-alpine AS runtime
WORKDIR /app

# Laufzeitabhängigkeiten (z. B. für numpy)
RUN apk add --no-cache libgcc libstdc++

# Übernehme nur die nötigen Dateien vom Builder
COPY --from=builder /root/.local /root/.local
ENV PATH="/root/.local/bin:$PATH"

COPY --from=builder /app/simulator /app/simulator
COPY mqtt_wrapper.py .

CMD ["python", "mqtt_wrapper.py"]
