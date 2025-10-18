# Frontend Dockerfile for Vite React dev server
FROM node:20-alpine

WORKDIR /app

# Copy package manifest and lock if present
COPY ./frontend/package.json ./
# If you had a package-lock.json or pnpm-lock.yaml, copy it here too for better caching

# Install dependencies
RUN npm install

# Copy source
COPY ./frontend/index.html ./index.html
COPY ./frontend/vite.config.js ./vite.config.js
COPY ./frontend/src ./src

EXPOSE 5173

# Run Vite dev server and bind to all interfaces
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
