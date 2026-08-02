# Base image - VULNERABLE: CVE-2022-41716 (HIGH)
# Recommended: golang:1.21.5-alpine
FROM golang:1.19.13-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o api-gateway .

# Final stage
FROM alpine:latest

# TYPE 4: Base image OS package upgrades (VULNERABLE - will be fixed by Renovate)
# CVE-2026-77777 (CRITICAL) - openssl 3.1.0-r4 -> 3.1.5-r0
RUN apk upgrade --no-cache openssl=3.1.0-r4

WORKDIR /root/

COPY --from=builder /app/api-gateway .

EXPOSE 8080

CMD ["./api-gateway"]
