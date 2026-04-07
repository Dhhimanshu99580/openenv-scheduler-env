FROM python:3.10-slim

WORKDIR /app

COPY . .

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV API_BASE_URL=""
ENV MODEL_NAME=""
ENV GROQ_API_KEY=""

CMD ["python", "inference.py"]