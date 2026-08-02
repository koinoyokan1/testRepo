# E2E Test - Fresh Vulnerability Set (2026-08-02)

## Overview

This is a **completely fresh end-to-end test** with new mock vulnerabilities across all six supported types. All packages, images, and CVEs are different from previous tests to ensure comprehensive coverage.

## Test Commit

**Commit**: `1581b3a`  
**Date**: 2026-08-02  
**Branch**: `main`  
**Status**: ✅ Pushed to trigger GitHub Actions workflow

---

## New Vulnerability Set

### TYPE 1: Go Module Dependencies

| Package | Current | Fixed | CVE | Severity |
|---------|---------|-------|-----|----------|
| github.com/sirupsen/logrus | 1.8.1 | 1.9.3 | CVE-2026-11111 | HIGH |
| github.com/gorilla/mux | 1.8.0 | 1.8.1 | CVE-2026-22222 | MEDIUM |
| github.com/insecure/crypto-utils | 0.3.2 | *(unfixable)* | CVE-2026-UNFIXED-001 | CRITICAL |

**Source Files Updated**:
- `go.mod` - Updated require statements
- `go.sum` - Regenerated with `go mod tidy`
- `cmd/test_imports.go` - Ensures dependencies survive tidy

---

### TYPE 2: npm Package Dependencies

| Package | Current | Fixed | CVE | Severity | Location |
|---------|---------|-------|-----|----------|----------|
| axios | 0.21.1 | 1.6.7 | CVE-2026-33333 | CRITICAL | services/web-frontend |
| lodash | 4.17.20 | 4.17.21 | CVE-2026-44444 | HIGH | services/web-frontend |
| insecure-hash | 1.0.5 | *(unfixable)* | CVE-2026-UNFIXED-002 | HIGH | services/admin-dashboard |

**Source Files Updated**:
- `services/web-frontend/package.json` - Added axios and lodash vulnerabilities
- `services/admin-dashboard/package.json` - Added insecure-hash (unfixable)

---

### TYPE 3: OS Explicit Package Installations (Alpine)

| Package | Current | Fixed | CVE | Severity | Dockerfile |
|---------|---------|-------|-----|----------|------------|
| curl | 8.0.1-r0 | 8.7.1-r0 | CVE-2026-55555 | HIGH | services/web-frontend |
| git | 2.38.1-r0 | 2.43.0-r0 | CVE-2026-66666 | CRITICAL | services/auth |

**Source Files Updated**:
- `services/web-frontend/Dockerfile` - Added `apk add curl=8.0.1-r0`
- `services/auth/Dockerfile` - Added `apk add git=2.38.1-r0`

---

### TYPE 4: OS Base Image Package Upgrades (Alpine)

| Package | Current | Fixed | CVE | Severity | Dockerfile |
|---------|---------|-------|-----|----------|------------|
| openssl | 3.1.0-r4 | 3.1.5-r0 | CVE-2026-77777 | CRITICAL | services/api-gateway |
| musl | 1.2.3-r4 | 1.2.4-r2 | CVE-2026-88888 | HIGH | services/auth |

**Source Files Updated**:
- `services/api-gateway/Dockerfile` - Added `apk upgrade openssl=3.1.0-r4`
- `services/auth/Dockerfile` - Added `apk upgrade musl=1.2.3-r4`

---

### TYPE 5: Custom Container Images

| Image | Current | Fixed | CVE | Severity |
|-------|---------|-------|-----|----------|
| ghcr.io/company/api-gateway | v2.3.1 | v2.4.0 | CVE-2026-API-001 | CRITICAL |
| ghcr.io/company/user-service | v1.8.0 | v1.9.0 | CVE-2026-USER-001 | HIGH |

**Source Files Updated**:
- `docker-compose.yml` - Updated custom image versions and CVE comments

---

### TYPE 6: Prebuilt Container Base Images

| Image | Current | Fixed | CVE | Severity |
|-------|---------|-------|-----|----------|
| postgres | 13.2 | 16.2 | CVE-2026-PG-001 | CRITICAL |
| nginx | 1.21.0 | 1.25.4 | CVE-2026-NGINX-001 | HIGH |

**Source Files Updated**:
- `docker-compose.yml` - Updated prebuilt image references
- `image_map.json` - Contains postgres:13.2 and nginx:1.21.0

---

## Expected Renovate PRs

The workflow should generate **12 PRs** (2 per type):

### Go Module PRs (2)
1. ✅ **logrus**: Update github.com/sirupsen/logrus to v1.9.3 (CVE-2026-11111, HIGH)
   - Reviewers: alice, bob, charlie, david (core-services)
2. ✅ **mux**: Update github.com/gorilla/mux to v1.8.1 (CVE-2026-22222, MEDIUM)
   - Reviewers: alice, bob, charlie, david (core-services)

### npm Package PRs (2)
3. ✅ **axios**: Update axios to v1.6.7 (CVE-2026-33333, CRITICAL)
   - Reviewers: xavier, yvonne (web-frontend)
4. ✅ **lodash**: Update lodash to v4.17.21 (CVE-2026-44444, HIGH)
   - Reviewers: xavier, yvonne (web-frontend)

### OS Explicit Package PRs (2)
5. ✅ **curl**: Update curl in Dockerfile to 8.7.1-r0 (CVE-2026-55555, HIGH)
   - Reviewers: xavier, yvonne (web-frontend)
6. ✅ **git**: Update git in Dockerfile to 2.43.0-r0 (CVE-2026-66666, CRITICAL)
   - Reviewers: david (auth)

### OS Base Image Package PRs (2)
7. ✅ **openssl**: Upgrade openssl to 3.1.5-r0 (CVE-2026-77777, CRITICAL)
   - Reviewers: alice, bob (api-gateway)
8. ✅ **musl**: Upgrade musl to 1.2.4-r2 (CVE-2026-88888, HIGH)
   - Reviewers: david (auth)

### Custom Image PRs (2)
9. ✅ **api-gateway**: Rebuild and update to v2.4.0 (CVE-2026-API-001, CRITICAL)
   - Reviewers: alice, bob (api-gateway)
10. ✅ **user-service**: Rebuild and update to v1.9.0 (CVE-2026-USER-001, HIGH)
    - Reviewers: frank (user-service)

### Prebuilt Image PRs (2)
11. ✅ **postgres**: Update postgres to 16.2 (CVE-2026-PG-001, CRITICAL)
    - Reviewers: paul, quinn (base-images)
12. ✅ **nginx**: Update nginx to 1.25.4 (CVE-2026-NGINX-001, HIGH)
    - Reviewers: alice, bob (proxy)

---

## Unfixable Vulnerabilities

Two GitHub Issues should be created for unfixable vulnerabilities:

1. **github.com/insecure/crypto-utils** (CVE-2026-UNFIXED-001, CRITICAL)
   - Go package with no fix available
   - Recommendation: Migrate to crypto/rand from stdlib

2. **insecure-hash** (CVE-2026-UNFIXED-002, HIGH)
   - npm package with no fix available
   - Recommendation: Use crypto.createHash from Node.js

---

## Verification Steps

1. ✅ **Commit created**: `1581b3a`
2. ✅ **Pushed to main**: Workflow should trigger automatically
3. ⏳ **GitHub Actions**: Check workflow logs at https://github.com/koinoyokan1/testRepo/actions
4. ⏳ **Renovate PRs**: 12 PRs should be created with correct reviewers
5. ⏳ **GitHub Issues**: 2 issues should be created for unfixable vulns

---

## Key Differences from Previous Tests

- **All new packages**: No overlap with previous CVE-2024-* vulnerabilities
- **Different Dockerfiles affected**: Spread across web-frontend, auth, api-gateway
- **Different npm packages**: axios and lodash instead of validator and qs
- **Different Go packages**: logrus and mux instead of uuid and yaml
- **Different prebuilt images**: postgres and nginx instead of rabbitmq and elasticsearch
- **Fresh CVE IDs**: All using CVE-2026-* to distinguish from prior tests

---

## Success Criteria

✅ All 12 PRs created with correct reviewers assigned  
✅ 2 GitHub issues created for unfixable vulnerabilities  
✅ No PRs defaulting to techleads/architects  
✅ Component-specific reviewers for all packages  
✅ Correct version constraints in all PRs  
✅ No duplicate PRs or missing vulnerability types
