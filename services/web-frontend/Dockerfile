# Base image - VULNERABLE: CVE-2022-21824 (HIGH)
# Recommended: node:20.10.0-alpine
FROM node:16.14.0-alpine

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
