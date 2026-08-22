# STRATA — API + built web app on one port.
# Build: docker build -t strata .
# Run:   docker run --env-file .env -p 8080:8080 strata

FROM node:22-bookworm-slim AS web
WORKDIR /src/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 STRATA_PORT=8080
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY director_api ./director_api
COPY medicomarketing_agent ./medicomarketing_agent
COPY examples ./examples
COPY skills ./skills
COPY start_director.py ./
COPY --from=web /src/web/dist ./web/dist
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "director_api.app:app", "--host", "0.0.0.0", "--port", "8080"]
