# Kairos
(Blog incoming soon...)


Kairos is a self-hosted data platform that pulls raw GitHub activity (commits, PRs, reviews, CI/CD runs), runs it through an orchestrated pipeline into a Postgres warehouse, computes DORA metrics and a few custom engineering health signals, flags anomalies, puts it all on a live Grafana dashboard, and has an AI agent that writes a weekly digest and posts it to Slack on its own.

I built this to actually understand the full data engineering stack end to end, real GitHub API data, real orchestration, real bugs to debug along the way (there were a lot of those, more on that below).

## what it actually does

- pulls PRs, commits, reviews, and CI runs from GitHub on a schedule
- runs data quality checks before anything touches the warehouse
- loads everything into a proper star schema (fact/dim tables) in Postgres
- computes DORA metrics: lead time, deployment frequency, change failure rate
- flags anomalies using both z-score and IQR (z-score alone misses outliers on small datasets — IQR catches what z-score misses, learned that one the hard way)
- dashboards all of it in Grafana
- an agent gathers the week's metrics, writes a report, checks its own numbers against the source data before sending it, and falls back to a plain templated report if the AI call fails for any reason
- posts the digest to Slack automatically, on its own weekly schedule, separate from the daily pipeline

## how it's built

everything runs in Docker. Airflow handles orchestration (two DAGs — one daily for the ETL, one weekly for the digest). Postgres is the warehouse. Grafana reads straight from it. the agent uses Gemini's API. tests run through pytest, and there's a GitHub Actions workflow that runs them on every push.

**stack:** Python, SQL, Apache Airflow, PostgreSQL, Grafana, Docker Compose, Gemini API, pytest

**architecture**

```
                     ┌─────────────────────────┐
                     │   GitHub REST API        │
                     │   (source system)         │
                     └────────────┬─────────────┘
                                  │ (1) EXTRACT
                                  ▼
                ┌─────────────────────────────────┐
                │  Python Extractor Scripts         │
                │  - fetch_commits.py                │
                │  - fetch_pull_requests.py           │
                │  - fetch_reviews.py                 │
                │  - fetch_workflow_runs.py (CI/CD)   │
                └────────────┬─────────────────────┘
                             │ raw JSON → Parquet
                             ▼
                ┌─────────────────────────────────┐
                │  Landing Zone                      │
                │  /data/raw/*.parquet (local)        │
                └────────────┬─────────────────────┘
                             │ (2) ORCHESTRATED by Airflow DAG
                             ▼
                ┌─────────────────────────────────┐
                │  Data Quality Checks               │
                │  - required field / null checks      │
                │  - row-count sanity checks           │
                │  - timestamp ordering checks         │
                └────────────┬─────────────────────┘
                             │ (3) LOAD (raw → staging)
                             ▼
                ┌─────────────────────────────────┐
                │  Staging Tables (Postgres)          │
                │  stg_pull_requests, stg_commits,     │
                │  stg_reviews, stg_workflow_runs      │
                └────────────┬─────────────────────┘
                             │ (4) TRANSFORM
                             ▼
                ┌─────────────────────────────────┐
                │  Warehouse — Star Schema            │
                │  fact_pull_requests                 │
                │  fact_deployments                   │
                │  dim_repo / dim_contributor          │
                └───────┬─────────────────┬───────┘
                        │                 │
          (5a)          ▼                 ▼          (5b)
    ┌───────────────────────┐   ┌─────────────────────────┐
    │  Metrics Layer           │   │  Anomaly Detection Layer  │
    │  - DORA metric SQL views  │   │  - Z-score (small samples) │
    │    lead time, deploy freq,│   │  - IQR (catches what        │
    │    change failure rate    │   │    z-score misses)           │
    └───────────┬────────────┘   └────────────┬─────────────┘
                │                              │
                ▼                              ▼
    ┌────────────────────┐         ┌────────────────────────┐
    │  Grafana Dashboards   │         │  Weekly Digest Agent      │
    │  (live off warehouse)  │         │  gather → generate →       │
    └────────────────────┘         │  validate → fallback       │
                                    └────────────┬────────────┘
                                                 │ (6) DELIVER
                                                 ▼
                                    ┌────────────────────────┐
                                    │  Slack (Incoming Webhook) │
                                    └────────────────────────┘

Everything above except GitHub itself runs as a Docker container,
orchestrated via docker-compose.yml, with Airflow as scheduler.
```

## the pipeline, start to finish

**1. Airflow runs the daily pipeline**

extract → validate → load → build warehouse → populate → compute metrics, all as one DAG with real dependencies and retries.

<img width="1600" height="820" alt="airflow dag graph view" src="https://github.com/user-attachments/assets/e4a40746-5995-48c6-9ad6-fe6fcd792c84" />
<img width="1600" height="822" alt="airflow gantt view" src="https://github.com/user-attachments/assets/a356b7fa-4b82-4539-8c94-fe741dd59398" />
<img width="1600" height="810" alt="airflow audit log" src="https://github.com/user-attachments/assets/ede3ba3b-6c46-4a6a-945d-df58b12aaaa2" />

**2. everything's containerized**

one `docker compose up` and the whole stack comes alive — Postgres, Airflow, Grafana, all of it.

<img width="962" height="155" alt="docker compose up" src="https://github.com/user-attachments/assets/bb97d3c2-a40b-4b51-82be-1ec2888571cf" />
<img width="1526" height="47" alt="docker container row" src="https://github.com/user-attachments/assets/e20e5e0e-6b35-4185-9433-3b3cc67de68f" />
<img width="1600" height="132" alt="docker compose ps output" src="https://github.com/user-attachments/assets/79e448ea-d30f-48e9-bbcb-94e87e7b7fa8" />
<img width="707" height="1132" alt="docker desktop container list" src="https://github.com/user-attachments/assets/32e75570-c53c-4e4c-8372-86f1579c4217" />

**3. the dashboard**

DORA metrics, commit activity by contributor, and flagged anomalies, all live off the warehouse.

<img width="926" height="292" alt="grafana lead time panel" src="https://github.com/user-attachments/assets/4019bb3c-6bb9-49cd-9755-5239300ad02b" />
<img width="937" height="295" alt="grafana deployment frequency panel" src="https://github.com/user-attachments/assets/3cc5239b-c6a8-4432-beec-0f811e945991" />
<img width="937" height="290" alt="grafana change failure rate panel" src="https://github.com/user-attachments/assets/89be77f7-4c42-46be-a45f-b2f21d801ea7" />
<img width="938" height="293" alt="grafana commits by contributor panel" src="https://github.com/user-attachments/assets/c844380b-4607-424b-8fd6-0da871acb3cf" />

**4. anomaly detection catching something real**

this one's a CI run that took 2700 seconds against an expected range of roughly -277 to 651 — z-score missed it (small sample size problem), IQR caught it.

<img width="1600" height="140" alt="grafana anomalies table" src="https://github.com/user-attachments/assets/0fa8b580-7f9d-461d-b589-5b6148058d02" />

**5. the AI digest, landing in Slack on its own**

this is generated by the agent reading the actual warehouse data, not made up — every number in it traces back to a real query.

<img width="1600" height="783" alt="slack ai digest message" src="https://github.com/user-attachments/assets/92c52f87-8e88-4f68-97ef-95e1e63f2875" />

## a sample report

here's an actual report the agent generated off real pipeline data, included in the repo so you don't need your own API key to see what it produces: [`docs/sample-digest-report.md`](docs/sample-digest-report.md)

## running it yourself

```bash
git clone https://github.com/HelloKeerthana/Kairos.git
cd Kairos
cp .env.example .env   # fill in your GitHub token, Gemini key, Slack webhook
docker compose up -d
```

airflow: http://localhost:8080 (admin/admin)
grafana: http://localhost:3000 (admin/admin)

trigger `kairos_etl_pipeline` first, then `kairos_weekly_digest`.

test repo this pulls data from: https://github.com/HelloKeerthana/test-repo

## what's not finished yet

- MTTR is stubbed — needs a failed deployment to measure recovery time from, and my test CI has been mostly green
- review turnaround time has no data — my test PRs didn't have a second reviewer
- currently pointed at a small test repo, but works against any repo, just swap the `.env` values

## what i'd do differently with more time

- swap polling for GitHub webhooks so ingestion is real-time instead of scheduled
- partition the warehouse tables by date once there's enough volume to matter
- try Isolation Forest for catching anomalies across multiple metrics at once, instead of one metric at a time like z-score/IQR do now
- migrate the SQL transform layer to dbt for the testing and lineage docs that come for free with it
