# SonarQube Integration Guide

## Overview

SonarQube is integrated into the NouvelAir CI/CD pipeline for static code analysis and code quality monitoring.

## Prerequisites

### GitHub Secrets (required)

Configure these secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

| Secret | Description | Example |
|--------|-------------|---------|
| `SONAR_TOKEN` | SonarQube authentication token | `sqa_xxxxxxxx...` |
| `SONAR_HOST_URL` | SonarQube server URL | `https://sonarcloud.io` |
| `SONAR_PROJECT_KEY` | Project key (optional) | `nouvelair-project` |

## Local Analysis

### Install SonarQube Scanner

```bash
# Download and install sonar-scanner
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
unzip sonar-scanner-cli-5.0.1.3006-linux.zip
export PATH=$PATH:/path/to/sonar-scanner-5.0.1.3006-linux/bin
```

### Run Analysis Locally

```bash
# Run tests with coverage
pytest tests/ --cov --cov-report=xml

# Run SonarQube analysis
sonar-scanner \
  -Dsonar.projectKey=nouvelair-project \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=YOUR_TOKEN
```

## Configuration File

The `.sonar-project.properties` file configures the analysis:

```properties
# Project identification
sonar.projectKey=nouvelair-project
sonar.projectName=NouvelAir - Application de Reservation
sonar.projectVersion=1.0

# Source configuration
sonar.sources=bookings,destinations,flights,nouvelair
sonar.exclusions=**/__pycache__/**,**/migrations/**,**/venv/**,**/manage.py

# Test coverage
sonar.python.coverage.reportPaths=coverage.xml
```

## Quality Gates

The pipeline enforces these quality rules:

| Metric | Threshold |
|--------|-----------|
| Coverage | ≥ 80% |
| Code Smells | ≤ 10 per 1000 lines |
| Critical Issues | 0 |
| Major Issues | ≤ 5 per 1000 lines |

## Integration Points

1. **GitHub Actions**: Runs on push to `main`, `sprint1`, or `sprint2` branches
2. **Coverage Report**: Automatically picks up `coverage.xml` from pytest
3. **Security Analysis**: Integrates with Bandit security reports