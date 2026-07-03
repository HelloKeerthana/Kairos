# kairos — Engineering Analytics & DORA Metrics Platform
### Complete Project Specification & Build Guide

---

## 1. What This Project Is (Elevator Pitch)

kairos is a self-hosted data platform that pulls raw activity data from GitHub (commits, pull requests, reviews, issues, CI/CD runs), moves it through a proper ETL pipeline into a data warehouse, computes industry-standard engineering metrics (DORA metrics + custom risk indicators), visualizes them on live dashboards, detects anomalies automatically, and uses an LLM-based agent to generate a plain-English weekly report — posted automatically to Slack or email.

In one sentence for a resume/interview: **"I built an end-to-end data engineering platform that turns raw GitHub activity into automated, AI-summarized engineering health reports."**

It is deliberately designed so that almost every sentence in a typical Data Analyst / Data Engineering JD (SQL, Python, ETL, orchestration, cloud warehouses, dashboards, anomaly detection, automation, GenAI, containerization) maps to a real, working piece of this system.

---

## 2. Core Concepts & Definitions (so you can talk about it fluently)

| Term | Definition | Where it shows up in kairos |
|---|---|---|
| **ETL / ELT** | Extract-Transform-Load (transform before loading) vs Extract-Load-Transform (transform inside warehouse) | You'll do ELT: land raw JSON, transform inside the warehouse using SQL/dbt-style models |
| **Orchestration** | Scheduling and managing dependencies between data tasks | Apache Airflow DAGs |
| **DAG** | Directed Acyclic Graph — a workflow of tasks with dependencies but no loops | Your Airflow pipeline definition |
| **Data Warehouse** | A structured, query-optimized store for analytical (OLAP) workloads, as opposed to transactional (OLTP) databases | Snowflake / BigQuery / Postgres |
| **Star Schema** | A warehouse design with a central fact table (events/measurements) surrounded by dimension tables (descriptive attributes) | `fact_pull_requests`, `dim_repo`, `dim_contributor` |
| **DORA Metrics** | Four key metrics (from Google's DevOps Research and Assessment team) that measure software delivery performance | Core output of the platform |
| **Idempotency** | Running the same pipeline twice produces the same result (no duplicate data) | Built into every Airflow task |
| **Data Quality / Validation** | Automated checks that data meets expectations (no nulls where unexpected, row counts within range, schema matches) | A dedicated DAG stage |
| **Anomaly Detection** | Statistically identifying data points that deviate significantly from the norm | Z-score / IQR / Isolation Forest on metrics like review time |
| **Agent (in GenAI sense)** | An LLM-powered component that can reason over data, decide what to do, optionally call tools/functions, and produce an output autonomously | The "Weekly Digest Agent" |
| **Containerization** | Packaging an app + its dependencies into a portable unit (image) that runs identically anywhere | Docker Compose for every service |
| **Partitioning** | Splitting a large table physically (e.g., by date) so queries only scan relevant partitions — saves cost/time | Warehouse tables partitioned by `event_date` |
| **Rate Limiting** | API restriction on how many requests you can make in a time window | GitHub REST API: 5,000 req/hr authenticated |
| **Webhook vs Polling** | Push-based (GitHub notifies you) vs pull-based (you ask on a schedule) data ingestion | You'll build polling first, webhook as a stretch goal |

---

## 3. Full Tech Stack (with reasoning for each choice)

### Languages
- **Python 3.11+** — extraction scripts, transformation logic, anomaly detection, agent orchestration
- **SQL** — all warehouse transformations, metric calculations, ad-hoc analysis
- **YAML** — Docker Compose, Airflow DAG configs, CI/CD workflow files
- **Bash** — small glue scripts, container entrypoints

### Data Ingestion
- **GitHub REST API v3** + **GitHub GraphQL API v4** — primary data source
- **PyGithub** or raw `requests`/`httpx` — Python HTTP client
- **Tenacity** — retry logic with exponential backoff (handles rate limits gracefully)

### Orchestration
- **Apache Airflow** (via Docker, `apache/airflow` image) — DAG scheduling, retries, task dependencies, logging, backfills

### Storage / Warehouse (pick ONE primary; mention others as "also compatible with")
- **Option A (recommended for resume weight): Snowflake** (free trial, 30-day/$400 credit) — most in-demand in JDs like this one
- **Option B: Google BigQuery** (free tier: 1TB queries/month) — also explicitly named in the JD
- **Option C (fully free, always available): PostgreSQL** in Docker — use this for local dev/demo, mention Snowflake/BigQuery as the "production target" with a working connector

### Processing / Transformation
- **Pandas** — small-to-medium in-memory transforms
- **PySpark** (local mode, via Docker) — for the "distributed processing" story; even running Spark locally on a laptop-sized dataset is legitimate and demonstrates the skill
- **dbt (data build tool)** *(strong optional addition)* — SQL-based transformation layer with testing, documentation, and lineage built in; extremely well-regarded in analytics engineering roles

### Data Quality
- **Great Expectations** or a lightweight custom Python validation module — row count checks, null checks, schema checks, freshness checks

### Anomaly Detection / Analytics
- **scikit-learn** — Isolation Forest, z-score/IQR statistical methods
- **NumPy / SciPy** — statistical calculations

### Visualization
- **Grafana** (Docker) — live dashboards, connects directly to Postgres/warehouse
- **Plotly / Matplotlib** *(optional)* — for embedded charts inside the AI-generated report

### GenAI / Agent Layer
- **Anthropic Claude API** or **OpenAI API** — LLM for report generation and reasoning
- **Simple custom agent loop** (no heavy framework needed — but you can use **LangChain** or **LlamaIndex** if you want that on your resume too) — fetches metrics → reasons over them → drafts report → (optionally) calls a "post to Slack" tool

### Automation / Notification
- **Slack Incoming Webhooks** or **SMTP (smtplib)** — automated report delivery
- **GitHub Actions** *(meta, but great story)* — CI to test your own pipeline code on every push

### Containerization & Deployment
- **Docker** + **Docker Compose** — every service (Airflow, Postgres, Grafana, your Python app) as isolated containers
- **Kubernetes (k3s or minikube)** *(stretch goal)* — deploy the same stack as a single-node cluster to demonstrate orchestration beyond Compose

### Version Control / Dev Practices
- **Git + GitHub** — obviously; also literally your data source
- **pytest** — unit tests for transformation logic and metric calculations
- **pre-commit hooks** (black, ruff/flake8) — code quality automation

---

## 4. System Architecture (Full Diagram)

```
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
```

---

## 5. Data Sources & APIs (exact endpoints you'll use)

### GitHub REST API v3 (base: `https://api.github.com`)
| Endpoint | Purpose |
|---|---|
| `GET /repos/{owner}/{repo}/commits` | Commit history, author, timestamp, stats |
| `GET /repos/{owner}/{repo}/pulls?state=all` | All PRs with metadata |
| `GET /repos/{owner}/{repo}/pulls/{pr}/reviews` | Review events, reviewer, timestamp, state |
| `GET /repos/{owner}/{repo}/pulls/{pr}/commits` | Commits within a PR |
| `GET /repos/{owner}/{repo}/issues?state=all` | Issues (note: PRs appear here too — filter them out) |
| `GET /repos/{owner}/{repo}/actions/runs` | CI/CD workflow runs — status, conclusion, duration |
| `GET /repos/{owner}/{repo}/actions/runs/{id}/jobs` | Per-job detail within a workflow run |
| `GET /repos/{owner}/{repo}/stats/contributors` | Aggregated contributor stats |
| `GET /repos/{owner}/{repo}/deployments` | Deployment events (if repo uses GitHub Deployments API) |

### GitHub GraphQL API v4 (base: `https://api.github.com/graphql`)
Use this for anything requiring nested data in one call (much more rate-limit-efficient than REST for complex joins) — e.g., PR + reviews + commits + linked issues in a single query.

### Auth
- Personal Access Token (fine-grained), stored as an environment variable / Docker secret — **never hardcoded**
- Rate limit: 5,000 requests/hour authenticated (60/hour unauthenticated) — your extractor must respect the `X-RateLimit-Remaining` header and back off accordingly

### Optional stretch data sources
- **Slack API** (to post) — `chat.postMessage` via Incoming Webhook URL
- **PyPI/npm download stats API** — if you extend to open-source community health
- **Anthropic/OpenAI API** — `messages`/`chat.completions` endpoint for the digest agent

---

## 6. Data Model (Warehouse Schema Design)

### Staging layer (1:1 with raw API responses, lightly typed)
- `stg_commits(sha, repo, author, authored_date, additions, deletions, message)`
- `stg_pull_requests(pr_id, repo, author, created_at, merged_at, closed_at, state, additions, deletions, changed_files)`
- `stg_reviews(review_id, pr_id, reviewer, submitted_at, state)`
- `stg_workflow_runs(run_id, repo, workflow_name, status, conclusion, started_at, completed_at)`
- `stg_issues(issue_id, repo, author, created_at, closed_at, labels)`

### Warehouse layer — Star Schema

**Dimension tables**
- `dim_repo(repo_key, repo_name, language, created_at)`
- `dim_contributor(contributor_key, username, first_seen_date)`
- `dim_date(date_key, date, week, month, quarter, year, is_weekend)`

**Fact tables**
- `fact_pull_requests(pr_key, repo_key, author_key, created_date_key, merged_date_key, lead_time_hours, review_count, additions, deletions, is_merged)`
- `fact_deployments(deployment_key, repo_key, date_key, status, duration_minutes, is_failure)`
- `fact_reviews(review_key, pr_key, reviewer_key, review_date_key, turnaround_hours)`
- `fact_ci_runs(run_key, repo_key, date_key, duration_seconds, conclusion)`

This is a genuine **Kimball-style star schema** — naming it as such in an interview signals real data-modeling literacy.

---

## 7. Pipeline Stages — Step by Step Detail

### Stage 1 — Extract
- Python scripts, one per entity (commits, PRs, reviews, workflow runs, issues)
- Each script:
  1. Reads last successful extraction timestamp (stored in a small `pipeline_state` table)
  2. Calls the GitHub API with pagination (`per_page=100`, follow `Link` headers)
  3. Applies `tenacity` retry with exponential backoff on `403`/`429` (rate limit) responses
  4. Writes raw JSON → converts to Parquet → saves to landing zone with a partition folder like `/data/raw/pull_requests/dt=2026-07-02/`

### Stage 2 — Data Quality Gate
- Before promoting raw data to staging, run checks:
  - Row count > 0 (fail loudly if an extraction silently returned nothing)
  - Required fields not null (`pr_id`, `repo`, `created_at`)
  - Timestamp sanity (`created_at <= merged_at` when merged)
  - Schema match against an expected Pydantic model
- Failed checks → Airflow task fails → alert (email/Slack) → pipeline halts before bad data pollutes the warehouse

### Stage 3 — Load (raw → staging)
- Bulk load Parquet files into staging tables using `COPY INTO` (Snowflake) / `bq load` (BigQuery) / `COPY` (Postgres)
- Idempotent: staging tables are truncated-and-reloaded per partition, or use `MERGE`/upsert on primary key to avoid duplicates on reruns

### Stage 4 — Transform (staging → warehouse)
- SQL models (optionally managed with dbt) that:
  - Deduplicate
  - Join staging tables into fact/dimension tables
  - Calculate derived fields (`lead_time_hours = merged_at - created_at`)
- If using PySpark: same logic, but demonstrating a distributed engine — read Parquet from landing zone, transform with DataFrame API, write back to warehouse via JDBC/connector

### Stage 5 — Metrics Computation
SQL views/tables computing:

**DORA Metrics**
- **Deployment Frequency** = count(deployments) / time period
- **Lead Time for Changes** = avg(merged_at − first_commit_at) per PR
- **Change Failure Rate** = failed_deployments / total_deployments
- **Mean Time to Recovery (MTTR)** = avg(time between a failed deployment and the next successful one)

**Custom Engineering Health Metrics**
- **Code Churn** = lines added + removed per contributor per week
- **Bus Factor** = number of contributors responsible for 50%+ of commits in a repo (risk indicator — low number = risky)
- **Review Turnaround Time** = avg(first_review_submitted_at − pr_created_at)
- **CI Reliability** = successful_runs / total_runs over trailing 7/30 days

### Stage 6 — Anomaly Detection
- Pull the metrics time series (e.g., daily review turnaround) into a Python task
- Apply:
  - **Z-score method**: flag points beyond 2.5–3 standard deviations from a rolling mean
  - **IQR method**: flag points outside Q1 − 1.5×IQR / Q3 + 1.5×IQR
  - **Isolation Forest** (scikit-learn): unsupervised outlier detection across multiple metrics simultaneously (e.g., combining churn + review time + CI failure rate to catch multivariate anomalies a single-metric method would miss)
- Output: an `anomalies` table with `metric_name, date, value, expected_range, severity`

### Stage 7 — Dashboarding
- Grafana connected directly to the warehouse/Postgres
- Panels:
  - DORA metrics scorecards (big number panels with trend arrows)
  - Time series: deployment frequency, lead time, CI reliability over time
  - Bar chart: PR count / churn by contributor
  - Table: flagged anomalies with severity color-coding
  - Repo comparison view (if tracking multiple repos)

### Stage 8 — GenAI Weekly Digest Agent
This is the "agent" component — architecture detailed in Section 8 below.

### Stage 9 — Delivery
- Airflow task calls Slack Incoming Webhook (or SMTP) with the agent's generated report, formatted in Markdown/Slack Block Kit
- Optionally attaches a rendered chart image (Matplotlib) of the week's key metric

---

## 8. The GenAI Agent — Full Design

### Why this is a genuine "agent" and not just an API call
An "agent" implies: it has a **goal**, access to **tools/data**, and makes **decisions** about what to include/emphasize — not just "summarize this text."

### Agent workflow (ReAct-style loop, kept simple and transparent)
```
1. TRIGGER: Airflow calls agent_task.py every Monday 8am
2. GATHER: Agent's first tool call → query_metrics_db()
      - fetches this week's DORA metrics + anomalies table
3. REASON: Agent compares this week vs trailing 4-week average
      - decides which metrics moved significantly (uses the anomaly table + simple delta thresholds)
4. TOOL CALL (optional 2nd tool): get_top_contributors() 
      - so the agent can name specific drivers, not just say "PRs increased"
5. GENERATE: LLM call with a structured prompt (metrics + anomalies + deltas as JSON context)
      → produces a Markdown report: headline summary, 3-5 bullet insights,
        1 recommended action item
6. VALIDATE: simple guardrail — check the output isn't empty / doesn't hallucinate
   numbers not present in the input JSON (basic regex/number cross-check)
7. DELIVER: post_to_slack(report) tool call
```

### Prompt design (structure, not literal reproducible text)
- **System instruction**: defines the agent's role ("You are an engineering analytics assistant. Only use numbers provided in the JSON below. Be concise and specific.")
- **Context block**: this week's metrics JSON + anomaly flags + last week's numbers for comparison
- **Output instruction**: ask for a fixed structure (Headline / Key Changes / Risks / Recommendation) so downstream formatting is predictable

### Guardrails (important to mention in interviews — shows maturity)
- Agent only sees pre-computed numbers, never raw free text data → limits hallucination surface
- Output is validated against the source JSON before sending (all numbers mentioned must exist in input)
- Retry/fallback: if the LLM call fails, send a plain templated (non-AI) report instead — pipeline never silently fails

### Framework choice
- **Simplest**: a ~150-line Python class with a manual loop calling the Claude/OpenAI API + your own two tool functions — this is honestly the *better* portfolio choice because it proves you understand agents at the mechanism level, not just "I imported LangChain"
- **If you want the LangChain/LlamaIndex keyword on your resume too**: wrap the same logic using LangChain's tool-calling agent executor — but keep the custom version as your primary talking point

---

## 9. Containerization & Deployment

### docker-compose.yml services
```yaml
services:
  postgres:        # warehouse (local dev) + Airflow metadata DB
  airflow-webserver:
  airflow-scheduler:
  airflow-init:      # one-off DB migration/user creation
  grafana:
  kairos
-extractor:  # your Python extraction/transform app
```

### Key details to actually implement
- Named volumes for Postgres data + Airflow logs (persistence across restarts)
- `.env` file for secrets (GitHub token, Slack webhook, LLM API key) — never committed; `.env.example` committed instead
- Healthchecks on Postgres/Airflow so dependent services wait properly
- A single `make up` / `make down` command (simple Makefile) for one-command demo — great for interviews ("let me spin up the whole platform")

### Kubernetes stretch goal
- Convert Compose services to k8s Deployments + Services using `kompose convert` as a starting point, then hand-tune
- Deploy on `k3s` or `minikube` locally
- Demonstrates: Deployments, Services, ConfigMaps (for non-secret config), Secrets (for tokens), PersistentVolumeClaims
- Not required for MVP — flag as "designed for, demo-able on request" if time-constrained

---

## 10. Data Governance & Security Touches (small effort, high JD relevance)

- Secrets management via environment variables / Docker secrets — never in code or version control
- PII consideration: GitHub usernames are the only "personal" data — document a simple retention/anonymization policy (e.g., hash usernames in the anomaly-report layer) as a design decision you can *talk about* even if not fully implemented
- Access logging: Airflow's built-in task logs double as an audit trail of every pipeline run
- Data lineage: if using dbt, its auto-generated lineage graph is a free, visual "data governance" artifact you can screenshot for your portfolio

---

## 11. Testing Strategy

- **Unit tests** (`pytest`): metric calculation functions (e.g., feed known PR timestamps, assert lead time calculation is correct)
- **Data tests**: dbt's built-in `not_null`, `unique`, `relationships` tests on warehouse models (or Great Expectations equivalents)
- **Pipeline smoke test**: a GitHub Actions workflow that spins up the Docker Compose stack and runs one full DAG execution against a small test repo on every push — this is a great "I built CI for my own data pipeline" story

---

## 12. Feature List (organized by priority)

### MVP (build first — this alone is a strong, complete project)
1. GitHub extractor for commits + PRs + reviews (one repo)
2. Landing zone + staging tables in Postgres
3. Airflow DAG orchestrating extract → validate → load → transform
4. SQL models computing 4 DORA metrics + review turnaround
5. Grafana dashboard with 4–6 panels
6. Dockerized entire stack, one-command startup
7. Basic README with architecture diagram + setup instructions

### V2 (adds the "unique/AI" differentiation)
8. CI/CD workflow run ingestion (deployment frequency + change failure rate become real, not approximated)
9. Anomaly detection layer (z-score minimum, Isolation Forest if time allows)
10. Bus factor / code churn / contributor concentration metrics
11. GenAI Weekly Digest Agent with the tool-calling loop
12. Slack delivery automation

### V3 (stretch — do only if V1+V2 are solid)
13. Multi-repo support + repo comparison dashboard
14. dbt migration of the transform layer (adds testing + lineage + docs)
15. Kubernetes deployment
16. Webhook-based real-time ingestion instead of polling
17. Cost/query optimization case study: partition warehouse tables by date, benchmark query time/cost before vs after, document it — directly answers the JD's "optimize Athena/BigQuery/Snowflake queries" bullet with real numbers

---

## 13. Step-by-Step Build Roadmap (suggested pacing)

**Week 1 — Foundations**
- Set up repo, Docker Compose skeleton (Postgres + Airflow only), get Airflow UI running
- Write and test the GitHub extractor for pull requests (just this one entity end-to-end)
- Land raw data as Parquet locally

**Week 2 — Pipeline core**
- Add commits, reviews, workflow runs extractors
- Build the data quality gate (simple Python checks first)
- Build staging table load logic
- Wire it all into one Airflow DAG with proper task dependencies and retries

**Week 3 — Warehouse & metrics**
- Design and implement the star schema (fact/dim tables)
- Write SQL transformation models (staging → warehouse)
- Write SQL for the 4 DORA metrics + review turnaround + code churn

**Week 4 — Visualization + anomaly detection**
- Stand up Grafana, connect to Postgres, build the dashboard panels
- Implement z-score/IQR anomaly detection on 2–3 key metrics
- (If time) add Isolation Forest multivariate detection

**Week 5 — GenAI agent + delivery**
- Build the agent class: gather → reason → generate → validate → deliver
- Wire Slack webhook delivery
- Add the guardrail/fallback logic

**Week 6 — Polish for portfolio**
- Write a strong README (architecture diagram, setup steps, screenshots/GIF of the dashboard and a sample AI-generated report)
- Add tests (pytest + at least a few dbt/Great Expectations checks)
- Record a 2–3 minute Loom-style demo video walking through the pipeline running end-to-end
- (Stretch) GitHub Actions CI, Kubernetes deployment, second repo support

---

## 14. Skills You Can Legitimately Claim After Building This

SQL (window functions, CTEs, joins, aggregation) · Python (OOP, API integration, retry logic, testing) · ETL/ELT pipeline design · Apache Airflow (DAGs, scheduling, retries, sensors) · Data modeling (star schema, fact/dimension design) · PySpark basics · Data warehousing (Snowflake/BigQuery/Postgres) · Data quality/validation engineering · Statistical anomaly detection · Applied machine learning (Isolation Forest) · Data visualization (Grafana) · GenAI/LLM API integration · Agentic workflow design with guardrails · Docker & Docker Compose · (stretch) Kubernetes · CI/CD (GitHub Actions) · Git/GitHub API mastery · Slack API integration

---

## 15. Resume Bullets (ready to drop into your Projects section)

> **kairos — Engineering Analytics & DORA Metrics Platform** | Python, SQL, Apache Airflow, PySpark, Snowflake/PostgreSQL, Docker, Grafana, LLM API
> - Designed and built an end-to-end ELT pipeline ingesting GitHub REST/GraphQL API data (commits, PRs, reviews, CI/CD runs) through Airflow-orchestrated DAGs into a star-schema data warehouse, computing all four DORA metrics across tracked repositories
> - Implemented statistical and ML-based anomaly detection (Z-score, Isolation Forest) on review turnaround, CI reliability, and code churn to automatically flag engineering-process risks
> - Built an LLM-powered agent that gathers pipeline metrics, reasons over week-over-week deltas, and generates guardrailed, auto-delivered engineering health reports via Slack
> - Containerized the full stack (Airflow, Postgres, Grafana) with Docker Compose for one-command reproducible deployment; designed a data quality gate enforcing schema, null, and freshness checks before warehouse loads

---

## 16. Interview Talking Points (be ready to answer these)

- "Walk me through what happens when the DAG runs" → narrate Sections 4 and 7 in order
- "Why a star schema instead of just flat tables?" → query performance, avoids repeated joins, standard for BI/analytics workloads
- "How do you avoid duplicate data on reruns?" → idempotent partition overwrite / MERGE upsert on primary key
- "How does the AI agent avoid making things up?" → Section 8's guardrails (numbers-only context, output validation, fallback)
- "What would you do differently at scale?" → move from polling to GitHub webhooks, move Spark from local to a real cluster, partition warehouse tables by date/repo, add a proper feature store if ML expands
- "What was the hardest part?" → be honest — likely GitHub API pagination/rate limits, or getting Airflow task dependencies correct, or agent output reliability

---

## 17. Quick-Start Checklist (do this first, today)

1. `mkdir kairos && cd kairos && git init`
2. Create `docker-compose.yml` with just Postgres + Airflow (get this running before writing any extractor code)
3. Create a GitHub fine-grained PAT with read-only repo access, store in `.env`
4. Write `extractors/fetch_pull_requests.py` — get ONE repo's PR data printing to console
5. Once that works, write it to a local Parquet file
6. Only then wire it into an Airflow DAG

Build vertically (one full slice: extract → load → one metric → one dashboard panel) before going wide (all entities). A working thin pipeline beats a half-built wide one, both for learning and for demo-ability.
