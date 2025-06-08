# -------- STAGE 1: Builder --------
FROM python:3.11-slim AS builder
WORKDIR /app

# System dependencies for pip builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential curl && \
    rm -rf /var/lib/apt/lists/*

ENV INSTALL_PATH=/install
COPY requirements.txt .
RUN mkdir -p ${INSTALL_PATH}
RUN pip install --no-cache-dir --prefix=${INSTALL_PATH} -r requirements.txt

RUN git clone https://github.com/RalfOGit/sma-emeter-simulator.git /app/simulator

# -------- STAGE 2: Runtime --------
FROM python:3.11-slim AS runtime
WORKDIR /app

# Runtime deps (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libstdc++6 && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/install/lib/python3.11/site-packages
ENV PATH=/install/bin:$PATH

COPY --from=builder /install /install
COPY --from=builder /app/simulator /app/simulator
COPY mqtt_wrapper.py .

CMD ["python", "mqtt_wrapper.py"]
