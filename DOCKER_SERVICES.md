# Docker Compose Services for Arroyopy

This docker-compose setup provides a complete observability stack for development.

## Services

### 1. Kvrocks (Redis-compatible storage)
- **Port**: 6379
- **Purpose**: Redis-compatible key-value store for testing
- **Access**: `redis-cli -h localhost -p 6379`

### 2. Jaeger (Distributed Tracing)
- **UI Port**: 16686
- **OTLP gRPC Port**: 4317
- **OTLP HTTP Port**: 4318
- **Purpose**: Collect and visualize distributed traces
- **Access**: http://localhost:16686

### 3. Prometheus (Metrics Collection)
- **Port**: 9090
- **Purpose**: Scrape and store metrics from Arroyopy applications
- **Access**: http://localhost:9090
- **Configuration**: `prometheus.yml`

### 4. Grafana (Metrics Visualization)
- **Port**: 3000
- **Purpose**: Create dashboards to visualize Prometheus metrics
- **Access**: http://localhost:3000
- **Default Credentials**: admin/admin

## Quick Start

### Start all services:
```bash
docker-compose up -d
```

### Start specific services:
```bash
# Just Jaeger for tracing
docker-compose up -d jaeger

# Full observability stack
docker-compose up -d jaeger prometheus grafana

# Just Redis
docker-compose up -d kvrocks
```

### View logs:
```bash
docker-compose logs -f [service_name]
```

### Stop services:
```bash
docker-compose down
```

### Stop and remove volumes:
```bash
docker-compose down -v
```

## Configuration

### Prometheus
Edit `prometheus.yml` to configure scrape targets. By default, it scrapes:
- Arroyopy app on `host.docker.internal:8000`
- Prometheus itself on `localhost:9090`

**Linux Note**: Replace `host.docker.internal` with your Docker bridge IP (usually `172.17.0.1`). Find it with:
```bash
ip addr show docker0 | grep inet
```

### Grafana
Datasources are automatically configured via `grafana-datasources.yml`.

To create dashboards:
1. Go to http://localhost:3000
2. Login (admin/admin)
3. Create → Dashboard
4. Add panels with PromQL queries:
   - `arroyopy_messages_per_second`
   - `arroyopy_avg_processing_seconds`
   - `rate(arroyopy_messages_received_total[5m])`

**Quick Start Dashboard:**
Import the pre-configured dashboard:
1. Go to Dashboards → Import
2. Upload `grafana-dashboard.json`
3. Select the Prometheus datasource
4. Click Import

This dashboard includes:
- Messages per second by listener type
- Average processing time by operator type
- Total messages received
- Processing time percentiles (p50, p95, p99)

## Using with Arroyopy

### 1. Start your Arroyopy application with telemetry:
```python
from arroyopy import init_telemetry
from prometheus_client import start_http_server

# Initialize OpenTelemetry
init_telemetry(service_name="my-app")

# Start metrics server
start_http_server(8000)
```

### 2. View traces in Jaeger:
- Open http://localhost:16686
- Select service "my-app"
- Click "Find Traces"

### 3. View metrics in Prometheus:
- Open http://localhost:9090
- Go to Graph
- Enter query: `arroyopy_avg_processing_seconds`

### 4. Create dashboards in Grafana:
- Open http://localhost:3000
- Create new dashboard
- Add Prometheus queries for visualization

## Data Persistence

Metrics and dashboard data are persisted in Docker volumes:
- `prometheus-data`: Prometheus time-series database
- `grafana-data`: Grafana dashboards and settings

## Ports Summary

| Service    | Port  | Purpose           |
|------------|-------|-------------------|
| Kvrocks    | 6379  | Redis API         |
| Jaeger UI  | 16686 | Web Interface     |
| Jaeger OTLP| 4317  | Trace Collection  |
| Prometheus | 9090  | Metrics & UI      |
| Grafana    | 3000  | Dashboards & UI   |

All ports are bound to `127.0.0.1` for security on development machines.
