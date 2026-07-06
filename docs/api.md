# CodeGuardian AI — API Reference

> All endpoints live under `/api/v1`. The Next.js frontend proxies them
> via `/api/backend/*` for development.

## Auth

| Method | Path                | Body                                | Returns |
|--------|---------------------|-------------------------------------|---------|
| POST   | `/auth/register`    | `{email,username,password,...}`     | User    |
| POST   | `/auth/login`       | `{username_or_email,password}`      | Tokens  |
| POST   | `/auth/refresh`     | `?refresh_token=...`                | Tokens  |
| GET    | `/auth/me`          | —                                   | User    |

## Projects

| Method | Path                       | Body / Query                        |
|--------|----------------------------|-------------------------------------|
| GET    | `/projects`                | `?search=&skip=&limit=`             |
| POST   | `/projects`                | `{name, source_type, source_ref}`   |
| GET    | `/projects/{id}`           | —                                   |
| GET    | `/projects/{id}/stats`     | —                                   |
| DELETE | `/projects/{id}`           | —                                   |

## Uploads

| Method | Path                | Form                                  |
|--------|---------------------|---------------------------------------|
| POST   | `/uploads/file`     | `file`, `project_name?`               |
| POST   | `/uploads/zip`      | `file`, `project_name?`               |

## Analyses

| Method | Path                                  | Body                       |
|--------|---------------------------------------|----------------------------|
| POST   | `/analyses`                           | `{project_id, config?}`    |
| GET    | `/analyses?project_id=...`            | —                          |
| GET    | `/analyses/{id}`                      | —                          |
| GET    | `/analyses/{id}/status`               | —                          |
| DELETE | `/analyses/{id}`                      | —                          |

## Agents

| Method | Path                                          | Notes                        |
|--------|-----------------------------------------------|------------------------------|
| GET    | `/agents`                                     | Agent metadata               |
| GET    | `/agents/runs/{analysis_id}`                  | Per-agent run status         |
| GET    | `/agents/findings/{analysis_id}?agent=&sev=`  | Filtered findings            |
| POST   | `/agents/runs/{analysis_id}/{agent_name}`     | Re-run a single agent        |

## Chat

| Method | Path                                       | Body / Query            |
|--------|--------------------------------------------|-------------------------|
| POST   | `/chat/sessions`                           | `{analysis_id?, title}` |
| GET    | `/chat/sessions`                           | —                       |
| GET    | `/chat/sessions/{id}`                      | —                       |
| POST   | `/chat/sessions/{id}/messages`             | `{content}`             |
| DELETE | `/chat/sessions/{id}`                      | —                       |

## Reports

| Method | Path                                  | Format            |
|--------|---------------------------------------|-------------------|
| GET    | `/reports/{id}/markdown`              | `text/markdown`   |
| GET    | `/reports/{id}/html`                  | `text/html`       |
| GET    | `/reports/{id}/pdf`                   | `application/pdf` |
| GET    | `/reports/{id}/patch`                 | `text/x-diff`     |
| GET    | `/reports/{id}/bundle`                | `application/zip` |

## Dashboard

| Method | Path                  | Notes                |
|--------|-----------------------|----------------------|
| GET    | `/dashboard/summary`  | Aggregated KPIs.     |
