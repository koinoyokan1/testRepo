# Base image - VULNERABLE: CVE-2022-21824 (HIGH)
# Recommended: node:20.10.0-alpine
FROM node:16.14.0-alpine

# TYPE 4: Base image OS package upgrades (VULNERABLE - will be fixed by Renovate)
# CVE-2024-33333 (HIGH) - zlib 1.2.12-r3 -> 1.3.1-r0
RUN apk upgrade --no-cache zlib=1.2.12-r3

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
