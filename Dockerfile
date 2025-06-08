# -------- STAGE 1: Builder --------
FROM python:3.11-alpine AS builder
WORKDIR /app

RUN apk add --no-cache git build-base

ENV INSTALL_PATH=/install

COPY requirements.txt .

# Erstelle /install manuell zur Sicherheit (wichtig für BuildKit!)
RUN mkdir -p ${INSTALL_PATH}
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --prefix=${INSTALL_PATH} -r requirements.txt

RUN git clone https://github.com/RalfOGit/sma-emeter-simulator.git /app/simulator

# -------- STAGE 2: Runtime --------
FROM python:3.11-alpine AS runtime
WORKDIR /app

RUN apk add --no-cache libgcc libstdc++

ENV PYTHONPATH=/install/lib/python3.11/site-packages
ENV PATH=/install/bin:$PATH

COPY --from=builder /install /install
COPY --from=builder /app/simulator /app/simulator
COPY mqtt_wrapper.py .

CMD ["python", "mqtt_wrapper.py"]
