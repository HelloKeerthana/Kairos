# Kairos

Kairos is a self-hosted data platform that pulls raw GitHub activity (commits, PRs, reviews, CI/CD runs), runs it through an orchestrated pipeline into a Postgres warehouse, computes DORA metrics and a few custom engineering health signals, flags anomalies, puts it all on a live Grafana dashboard, and has an AI agent that writes a weekly digest and posts it to Slack on its own.

I built this to actually understand the full data engineering stack end to end , real GitHub API data, real orchestration, real bugs to debug along the way (there were a lot of those, more on that below).

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

**arch**

                         ┌─────────────────────────┐
                         │   GitHub REST/GraphQL    │
                         │   API (source system)    │
                         └────────────┬─────────────┘
                                      │ (1) EXTRACT
                                      ▼
                    ┌─────────────────────────────────┐
                    │  Python Extractor Scripts        │
                    │  - fetch_commits.py               │
                    │  - fetch_pull_requests.py          │
                    │  - fetch_reviews.py                │
                    │  - fetch_issues.py                 │
                    │  - fetch_workflow_runs.py (CI/CD)  │
                    └────────────┬─────────────────────┘
                                 │ raw JSON
                                 ▼
                    ┌─────────────────────────────────┐
                    │  Landing Zone (raw storage)       │
                    │  Local: /data/raw/*.parquet       │
                    │  Cloud: S3 / GCS bucket            │
                    └────────────┬─────────────────────┘
                                 │ (2) ORCHESTRATED by Airflow DAG
                                 ▼
                    ┌─────────────────────────────────┐
                    │  Data Quality Checks              │
                    │  - schema validation                │
                    │  - null/row-count checks            │
                    │  - freshness checks                 │
                    └────────────┬─────────────────────┘
                                 │ (3) LOAD (raw → staging)
                                 ▼
                    ┌─────────────────────────────────┐
                    │  Staging Tables (warehouse)       │
                    │  stg_commits, stg_pull_requests,   │
                    │  stg_reviews, stg_workflow_runs    │
                    └────────────┬─────────────────────┘
                                 │ (4) TRANSFORM (SQL / PySpark / dbt)
                                 ▼
                    ┌─────────────────────────────────┐
                    │  Warehouse — Star Schema           │
                    │  fact_pull_requests                │
                    │  fact_deployments                  │
                    │  fact_reviews                      │
                    │  dim_repo / dim_contributor / dim_date │
                    └───────┬─────────────────┬───────┘
                            │                 │
              (5a)          ▼                 ▼          (5b)
        ┌───────────────────────┐   ┌─────────────────────────┐
        │  Metrics Layer          │   │  Anomaly Detection Layer  │
        │  - DORA metrics SQL     │   │  - Isolation Forest         │
        │  - churn / bus factor   │   │  - Z-score on review time    │
        │  - review turnaround    │   │  - Build failure spike flag  │
        └───────────┬────────────┘   └────────────┬─────────────┘
                    │                              │
                    ▼                              ▼
        ┌────────────────────┐         ┌────────────────────────┐
        │  Grafana Dashboards  │         │  Weekly Digest Agent     │
        │  (real-time viz)      │         │  (LLM reasoning + report) │
        └────────────────────┘         └────────────┬────────────┘
                                                     │ (6) DELIVER
                                                     ▼
                                        ┌────────────────────────┐
                                        │  Slack / Email Report     │
                                        └────────────────────────┘

All services above (except GitHub itself) run as Docker containers,
orchestrated via docker-compose.yml, with Airflow as the scheduler/conductor.


## the pipeline, start to finish

**1. Airflow runs the daily pipeline**
extract → validate → load → build warehouse → populate → compute metrics, all as one DAG with real dependencies and retries.

`[image: airflow-dag-graph.png]`
<img width="1600" height="820" alt="d1db8259-ebc5-4c5e-8a44-6dd9356a0ff6" src="https://github.com/user-attachments/assets/e4a40746-5995-48c6-9ad6-fe6fcd792c84" />
<img width="1600" height="822" alt="2d3ca22c-ead8-417a-8f6d-dd118673e73b" src="https://github.com/user-attachments/assets/a356b7fa-4b82-4539-8c94-fe741dd59398" />
<img width="1600" height="810" alt="8a73ed55-cbd3-4c69-8ab9-77ad386594d4" src="https://github.com/user-attachments/assets/ede3ba3b-6c46-4a6a-945d-df58b12aaaa2" />


**2. everything's containerized**
one `docker compose up` and the whole stack comes alive — Postgres, Airflow, Grafana, all of it.

<img width="1526" height="47" alt="1062e30c-4f7c-4495-94c6-042531c25470" src="https://github.com/user-attachments/assets/e20e5e0e-6b35-4185-9433-3b3cc67de68f" />


`[image: docker-compose-ps.png]`
<img width="1600" height="132" alt="749b9715-47ce-4ded-a1dd-23aff3b66790" src="https://github.com/user-attachments/assets/79e448ea-d30f-48e9-bbcb-94e87e7b7fa8" />


`[image: docker-desktop-containers.png]`
<img width="707" height="1132" alt="29c560a2-a876-40e4-87b9-c63b60f23c66" src="https://github.com/user-attachments/assets/32e75570-c53c-4e4c-8372-86f1579c4217" />


**3. the dashboard**
DORA metrics, commit activity by contributor, and flagged anomalies, all live off the warehouse.

`[image: grafana-lead-time.png]`
<img width="926" height="292" alt="020c3d51-1775-4e30-a674-5cc879136c85" src="https://github.com/user-attachments/assets/4019bb3c-6bb9-49cd-9755-5239300ad02b" />

`[image: grafana-deployment-frequency.png]`
<img width="937" height="295" alt="56e1aa37-24f1-4d74-8ddf-c3a11e84ee9e" src="https://github.com/user-attachments/assets/3cc5239b-c6a8-4432-beec-0f811e945991" />

`[image: grafana-change-failure-rate.png]`
<img width="937" height="290" alt="b840278b-fd9c-4505-bfaf-63a322236b9b" src="https://github.com/user-attachments/assets/89be77f7-4c42-46be-a45f-b2f21d801ea7" />

`[image: grafana-commits-by-contributor.png]`
<img width="938" height="293" alt="ae883674-ae9f-424d-bfd9-e5f59c0e3606" src="https://github.com/user-attachments/assets/c844380b-4607-424b-8fd6-0da871acb3cf" />


**4. anomaly detection catching something real**
this one's a CI run that took 2700 seconds against an expected range of roughly -277 to 651 — z-score missed it (small sample size problem), IQR caught it.

`[image: grafana-anomalies-table.png]`
<img width="1600" height="140" alt="5f888689-a041-4be3-bdf7-cf6cb757163d" src="https://github.com/user-attachments/assets/0fa8b580-7f9d-461d-b589-5b6148058d02" />


**5. the AI digest, landing in Slack on its own**
this is generated by the agent reading the actual warehouse data, not made up — every number in it traces back to a real query.

`[image: slack-ai-digest.png]`
<img width="1600" height="783" alt="d8bbd519-32e3-42a9-927e-f76f3f029a31" src="https://github.com/user-attachments/assets/92c52f87-8e88-4f68-97ef-95e1e63f2875" />


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

## what's not finished yet

- MTTR is stubbed — needs a failed deployment to measure recovery time from, and my test CI has been mostly green
- review turnaround time has no data — my test PRs didn't have a second reviewer
- currently pointed at a small test repo, but works against any repo, just swap the `.env` values

  
  the repo --> https://github.com/HelloKeerthana/test-repo

## what i'd do differently with more time

- swap polling for GitHub webhooks so ingestion is real-time instead of scheduled
- partition the warehouse tables by date once there's enough volume to matter
- try Isolation Forest for catching anomalies across multiple metrics at once instead of one at a time
- migrate the SQL transform layer to dbt for the testing and lineage docs that come for free with it
