# Base image - VULNERABLE: CVE-2022-41716 (HIGH)
# Recommended: golang:1.21.5-alpine
FROM golang:1.19.0-alpine AS builder

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
# CVE-2024-22222 (MEDIUM) - libcrypto3 3.1.0-r0 -> 3.1.4-r0
RUN apk upgrade --no-cache libcrypto3=3.1.0-r0

# TYPE 3: Explicit OS package installations (VULNERABLE - will be fixed by Renovate)
# CVE-2024-55555 (HIGH) - bash 5.2.15-r0 -> 5.2.21-r0
RUN apk --no-cache add ca-certificates bash=5.2.15-r0

WORKDIR /root/

COPY --from=builder /app/api-gateway .

EXPOSE 8080

CMD ["./api-gateway"]
