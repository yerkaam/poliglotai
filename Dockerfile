# Single image for cloud deploys (Render, Railway, Fly.io): Angular build + Django API.
# Local development and self-hosting use docker-compose.yml instead.

FROM node:20-alpine AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ .
RUN npx ng build --configuration production

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SPA_DIR=/app/spa PORT=8000
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=web /web/dist/frontend/browser /app/spa
RUN DJANGO_DEBUG=0 DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py createcachetable && (python manage.py create_demo_accounts --from-env || true) && (python manage.py ensure_admin || true) && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT} --workers ${WEB_CONCURRENCY:-3} --timeout 90"]
