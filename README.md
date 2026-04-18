# PA3 — Cloud Development Base Application

A sensor dashboard web app that reads/writes to PostgreSQL and calls an Azure Function for data aggregation.

## Repository Structure

```
/app            Main Flask web application (you will write the Dockerfile here)
/functions      Azure Functions project (implement aggregation logic here)
/shared         Common utilities imported by both /app and /functions
```

## Environment Variables

| Variable       | Description                          | Example                                                         |
|----------------|--------------------------------------|-----------------------------------------------------------------|
| `DATABASE_URL` | PostgreSQL connection string         | `postgresql://pa3admin:pass@db-host:5432/pa3db`                 |
| `FUNCTION_URL` | Azure Function HTTP trigger endpoint | `https://func-XXXXX.azurewebsites.net/api/aggregate`            |
| `FUNCTION_KEY` | Azure Function API key               | `your-function-key-here`                                        |
| `PORT`         | Port to listen on (default: 8080)    | `8080`                                                          |

## Local Development

**Note:** The Dockerfile is not provided — you will write it as part of Task 1.
Build from the **repo root** so Docker can access both `/app` and `/shared`:

```bash
# Build from repo root (not from inside /app)
docker build -t pa3-app:latest -f app/Dockerfile .

# Run without database (partial UI — expected at this stage)
docker run -p 8080:8080 -e PORT=8080 pa3-app:latest

# Run with a local PostgreSQL instance
docker run -p 8080:8080 \
  -e PORT=8080 \
  -e DATABASE_URL=postgresql://pa3admin:secret@host.docker.internal:5432/pa3db \
  pa3-app:latest
```

## Shared Module

The `/shared/models.py` module contains:
- `SensorReading` — data model class for sensor data
- `format_response()` — standard JSON response envelope
- `validate_reading()` — input validation for sensor readings

Both `/app` and `/functions` import and use these utilities.

## API Endpoints

| Method | Path             | Description                                    |
|--------|------------------|------------------------------------------------|
| GET    | `/`              | Dashboard HTML page                            |
| GET    | `/health`        | Health check                                   |
| GET    | `/api/readings`  | List recent sensor readings (JSON)             |
| POST   | `/api/readings`  | Add a new sensor reading (JSON body)           |
| GET    | `/api/aggregate` | Calls the Azure Function and returns results   |

## Azure Functions

A skeleton `aggregate` function is provided in `/functions/aggregate/`. You must:

1. Implement meaningful aggregation logic inside `__init__.py`
2. Use the shared module (already imported — verify it works)
3. Accept the JSON payload sent by the web app (`{"readings": [...]}`)
4. Return aggregated statistics (e.g., averages, counts, min/max per sensor)

The web app calls your function via `POST /api/aggregate` — the `FUNCTION_URL`
must point to your deployed function endpoint:
```
https://func-<rollnum>.azurewebsites.net/api/aggregate
```

## Dockerfile Hints

When writing your Dockerfile (Task 1), keep in mind:
- The build context must be the repo root (not inside /app)
- All configuration comes from environment variables
- All configuration comes from environment variables, no hardcoded values
- See the README environment variables table for what the app expects
# cloud-development-pa3
