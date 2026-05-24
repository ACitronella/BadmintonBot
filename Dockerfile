FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY main.py .
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
