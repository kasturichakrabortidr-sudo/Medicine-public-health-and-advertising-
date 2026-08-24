# STRATA — one container: build the website, then run the Python app.
FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=web /web/dist /app/web/dist
EXPOSE 8080
CMD ["sh", "-c", "uvicorn director_api.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
