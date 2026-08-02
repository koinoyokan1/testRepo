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
RUN apk --no-cache add ca-certificates openssl=3.0.7-r0 curl=7.88.0-r0
WORKDIR /root/

COPY --from=builder /app/api-gateway .

EXPOSE 8080

CMD ["./api-gateway"]
