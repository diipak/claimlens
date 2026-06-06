# Stage 1: Build React Frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /frontend

# Copy dependency files
COPY frontend/package*.json ./
COPY frontend/.npmrc ./

# Install packages with peer deps flag
RUN npm ci --legacy-peer-deps

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Runner
FROM python:3.11-slim
WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend

# Copy built frontend assets from Stage 1
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Expose port (Cloud Run sets PORT env var)
EXPOSE 8080

# Run uvicorn server
CMD exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}
