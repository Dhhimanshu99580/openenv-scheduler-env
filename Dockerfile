FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir \
    pydantic \
    openai \
    pyyaml

ENV API_BASE_URL=""
ENV MODEL_NAME=""
ENV HF_TOKEN=""

CMD ["python", "inference.py"]