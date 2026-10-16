# ==============================================================================
# Multi-Stage Dockerfile para AnimeFinder Frontend (React + Vite + Nginx)
# ==============================================================================

# --- Etapa 1: Compilación de Assets con Node.js ---
FROM node:22-alpine AS builder

WORKDIR /app

# Copiar archivos de dependencias
COPY package.json package-lock.json ./

# Instalar dependencias exactas
RUN npm ci

# Copiar código fuente
COPY tsconfig.json tsconfig.node.json vite.config.ts index.html ./
COPY src/ ./src/

# Compilar bundle estático para producción
RUN npm run build

# --- Etapa 2: Servidor Web Nginx Ligero ---
FROM nginx:alpine AS runner

# Eliminar configuración por defecto de Nginx
RUN rm -rf /etc/nginx/conf.d/default.conf

# Copiar configuración personalizada con Reverse Proxy
COPY nginx.conf /etc/nginx/conf.d/animefinder.conf

# Copiar bundle compilado desde la etapa de build
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# Healthcheck interno de Nginx
HEALTHCHECK --interval=15s --timeout=5s --start-period=3s --retries=3 \
    CMD wget -q -O - http://localhost/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
