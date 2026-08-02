# Base image - VULNERABLE: CVE-2022-41716 (HIGH)
# Recommended: golang:1.21.5-alpine
FROM golang:1.19.13-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o auth-service .

FROM alpine:latest

# TYPE 3: Explicit OS package installations (VULNERABLE - will be fixed by Renovate)
# CVE-2024-44444 (MEDIUM) - ncurses-terminfo-base 6.3-r0 -> 6.4-r0
RUN apk --no-cache add ca-certificates ncurses-terminfo-base=6.3-r0

WORKDIR /root/

COPY --from=builder /app/auth-service .

EXPOSE 8081

CMD ["./auth-service"]
