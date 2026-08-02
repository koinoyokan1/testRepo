# Base image - VULNERABLE: CVE-2022-41716 (HIGH)
# Recommended: golang:1.21.5-alpine
FROM golang:1.19.0-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o auth-service .

FROM alpine:latest

# TYPE 4: Base image OS package upgrades (VULNERABLE - will be fixed by Renovate)
# CVE-2026-88888 (HIGH) - musl 1.2.3-r4 -> 1.2.4-r2
RUN apk upgrade --no-cache musl=1.2.3-r4

# TYPE 3: Explicit OS package installations (VULNERABLE - will be fixed by Renovate)
# CVE-2026-66666 (CRITICAL) - git 2.38.1-r0 -> 2.43.0-r0
RUN apk --no-cache add ca-certificates git=2.38.1-r0

WORKDIR /root/

COPY --from=builder /app/auth-service .

EXPOSE 8081

CMD ["./auth-service"]
