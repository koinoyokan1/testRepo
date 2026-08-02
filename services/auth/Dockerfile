# Base image - VULNERABLE: CVE-2022-41716 (HIGH)
# Recommended: golang:1.21.5-alpine
FROM golang:1.26.5-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o auth-service .

FROM alpine:latest
# Security: Upgrade base image OS packages to fix vulnerabilities
# Fixes: CVE-2024-77777
RUN apk upgrade --no-cache alpine-baselayout=3.4.3-r0

RUN apk --no-cache add ca-certificates git=2.38.1-r0
WORKDIR /root/

COPY --from=builder /app/auth-service .

EXPOSE 8081

CMD ["./auth-service"]
