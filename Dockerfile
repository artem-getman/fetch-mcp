# ---------- build stage ----------
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-deps -r requirements.txt

# ---------- run stage ----------
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.cache/pip /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links /wheels -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]