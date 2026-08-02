# Base image - VULNERABLE: CVE-2022-21824 (HIGH)
# Recommended: node:20.10.0-alpine
FROM node:18.20.8-alpine

# Security: Upgrade base image OS packages to fix vulnerabilities
# Fixes: CVE-2024-44444, CVE-2024-55555
RUN apk upgrade --no-cache ca-certificates=20240705-r0 musl=1.2.5-r0

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install OS-level dependencies
RUN apk add --no-cache libssl3=3.0.8-r0 libcrypto3=3.0.8-r0

# Install dependencies
RUN npm ci --production

# Copy application files
COPY . .

# Build the application
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
