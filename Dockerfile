FROM python:3.10-slim

WORKDIR /app

COPY . .

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV API_BASE_URL=""
ENV MODEL_NAME=""
ENV HF_TOKEN=""

EXPOSE 7860

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]