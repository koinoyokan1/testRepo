# Base image - VULNERABLE: CVE-2022-21824 (HIGH)
# Recommended: node:20.10.0-alpine
FROM node:16.14.0-alpine

# TYPE 3: Explicit OS package installations (VULNERABLE - will be fixed by Renovate)
# CVE-2026-55555 (HIGH) - curl 8.0.1-r0 -> 8.7.1-r0
RUN apk --no-cache add ca-certificates curl=8.0.1-r0

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --production

# Copy application files
COPY . .

# Build the application
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
