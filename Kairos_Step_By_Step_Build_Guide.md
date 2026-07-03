# DevPulse — Step 1 to Step N (Complete Build Sequence)

Every step below is one atomic action. Do them in order. Each step has the same shape: **Step number → Action → Why/Detail**. N = 148 (the project is complete and demo-ready at Step 148).

---

## PHASE A — Environment & Project Setup (Steps 1–12)

**Step 1: Install Docker Desktop (or Docker Engine + Docker Compose plugin) on your machine.**
Everything in this project runs in containers — this is the one non-negotiable prerequisite.

**Step 2: Install Python 3.11+ locally.**
Needed to run extractor/transform scripts outside containers during development, and for your local virtual environment.

**Step 3: Create the project root folder: `mkdir devpulse && cd devpulse`.**
This is your single repository root.

**Step 4: Initialize git: `git init`.**
Version control from day one — also lets you demonstrate commit history as part of your portfolio.

**Step 5: Create a Python virtual environment: `python -m venv venv`.**
Keeps project dependencies isolated from your system Python.

**Step 6: Activate the virtual environment.**
`source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows).

**Step 7: Create a `.gitignore` file.**
Add `venv/`, `.env`, `__pycache__/`, `*.pyc`, `data/raw/`, `.DS_Store` so secrets and generated data never get committed.

**Step 8: Create the top-level folder structure.**
`mkdir extractors transforms dags dashboards agent tests docs data` — one folder per responsibility, keeps the repo navigable.

**Step 9: Create a `requirements.txt` file.**
List core packages you already know you need: `requests`, `tenacity`, `pandas`, `pyarrow`, `python-dotenv`, `pytest`.

**Step 10: Run `pip install -r requirements.txt`.**
Confirms your environment works before you write any real logic.

**Step 11: Create an empty `README.md`.**
You'll fill this in progressively — starting it now builds the habit of documenting as you go, not at the end.

**Step 12: Make your first commit: `git add . && git commit -m "Initial project scaffold"`.**
Establishes your baseline; every future step should end in a small, focused commit.

---

## PHASE B — GitHub API Access Setup (Steps 13–20)

**Step 13: Log into GitHub and go to Settings → Developer settings → Personal access tokens → Fine-grained tokens.**
Fine-grained tokens are safer than classic tokens — scoped to specific repos and permissions.

**Step 14: Generate a new fine-grained token with read-only access to "Pull requests," "Contents," "Actions," and "Issues" for one repository you own (or a public repo you plan to track).**
Minimal permission scope — a good security practice to mention in interviews.

**Step 15: Copy the token somewhere temporarily safe (you won't see it again).**
Standard token hygiene.

**Step 16: Create a `.env` file in the project root.**
This holds all secrets — never committed to git (already excluded in Step 7).

**Step 17: Add `GITHUB_TOKEN=<your token>` to `.env`.**
First secret stored.

**Step 18: Add `GITHUB_REPO_OWNER=<your username>` and `GITHUB_REPO_NAME=<repo name>` to `.env`.**
Parameterizes which repo you're tracking so nothing is hardcoded in scripts.

**Step 19: Create a `.env.example` file with the same keys but empty/placeholder values.**
This gets committed instead of `.env` — lets anyone clone your repo and know what secrets they need to supply.

**Step 20: Test the token with a raw curl call: `curl -H "Authorization: Bearer $TOKEN" https://api.github.com/repos/<owner>/<repo>/pulls`.**
Confirms auth works before you write any Python around it — isolates API issues from code issues.

---

## PHASE C — First Extractor: Pull Requests (Steps 21–32)

**Step 21: Create `extractors/__init__.py` (empty file).**
Makes `extractors` a proper Python package.

**Step 22: Create `extractors/config.py`.**
Loads environment variables via `python-dotenv` and exposes them as constants (`GITHUB_TOKEN`, `REPO_OWNER`, `REPO_NAME`) for all extractor scripts to import.

**Step 23: Create `extractors/github_client.py`.**
A thin wrapper class around `requests` that sets the `Authorization` header and base URL once, so every extractor script doesn't repeat that boilerplate.

**Step 24: Add pagination handling to `github_client.py`.**
GitHub returns max 100 items per page — parse the `Link` response header and follow `rel="next"` until exhausted.

**Step 25: Add rate-limit handling to `github_client.py` using `tenacity`.**
Wrap the request method with a retry decorator that backs off exponentially on HTTP 403/429 responses, checking the `X-RateLimit-Reset` header.

**Step 26: Create `extractors/fetch_pull_requests.py`.**
This script will call `GET /repos/{owner}/{repo}/pulls?state=all` using the client from Step 23.

**Step 27: In `fetch_pull_requests.py`, call the endpoint and print the raw JSON of the first page only.**
Get visual confirmation of the real data shape before building anything further on top of it.

**Step 28: Extend the script to loop through all pages using the pagination logic from Step 24.**
Confirms full pagination works end-to-end on a real repo.

**Step 29: Convert the collected list of PR JSON objects into a Pandas DataFrame.**
First transformation — raw JSON to tabular form.

**Step 30: Select and rename only the fields you need (`id`, `number`, `user.login`, `created_at`, `merged_at`, `closed_at`, `state`, `additions`, `deletions`, `changed_files`).**
Trims noise early; keeps downstream schemas predictable.

**Step 31: Write the DataFrame to a local Parquet file: `data/raw/pull_requests.parquet`.**
Parquet is columnar, compressed, and the standard format for analytical pipelines — better than CSV/JSON for this purpose.

**Step 32: Run the script end-to-end and confirm the Parquet file is created and readable via `pd.read_parquet()`.**
Full extractor #1 is now functionally complete.

---

## PHASE D — Remaining Extractors (Steps 33–44)

**Step 33: Create `extractors/fetch_commits.py` calling `GET /repos/{owner}/{repo}/commits`.**
Second data entity.

**Step 34: Extract and save fields: `sha`, `commit.author.name`, `commit.author.date`, `stats.additions`, `stats.deletions`.**
Note: `stats` requires fetching each commit individually via `GET /repos/{owner}/{repo}/commits/{sha}` — the list endpoint doesn't include stats.

**Step 35: Save commits to `data/raw/commits.parquet`.**
Same pattern as Step 31.

**Step 36: Create `extractors/fetch_reviews.py`.**
Loops through every PR from Step 32's output and calls `GET /repos/{owner}/{repo}/pulls/{pr}/reviews` for each.

**Step 37: Extract fields: `id`, `pull_request_url`, `user.login`, `submitted_at`, `state`.**
The core data needed to calculate review turnaround time later.

**Step 38: Save reviews to `data/raw/reviews.parquet`.**
Third entity done.

**Step 39: Create `extractors/fetch_workflow_runs.py` calling `GET /repos/{owner}/{repo}/actions/runs`.**
This is your CI/CD data source — critical for deployment frequency and change failure rate.

**Step 40: Extract fields: `id`, `name`, `status`, `conclusion`, `run_started_at`, `updated_at`, `head_branch`.**
`conclusion` (success/failure/cancelled) is what powers the change-failure-rate metric.

**Step 41: Save workflow runs to `data/raw/workflow_runs.parquet`.**
Fourth entity done.

**Step 42: Create `extractors/fetch_issues.py` calling `GET /repos/{owner}/{repo}/issues?state=all`.**
Fifth entity — needed for a full engineering-health picture, and to demonstrate handling the GitHub API's PR/issue overlap.

**Step 43: In the issues script, filter out any item that has a `pull_request` key.**
GitHub's issues endpoint returns PRs too — this filter keeps issues and PRs cleanly separated.

**Step 44: Save issues to `data/raw/issues.parquet`.**
All five raw extractors are now complete and independently runnable.

---

## PHASE E — Landing Zone & Partitioning (Steps 45–49)

**Step 45: Change every extractor's output path to include a date partition, e.g., `data/raw/pull_requests/dt=2026-07-02/data.parquet`.**
Mimics real-world data lake partitioning — each pipeline run lands in its own folder instead of overwriting the previous one.

**Step 46: Create a small `extractors/state.py` module that reads/writes a `pipeline_state.json` file tracking the last successful extraction timestamp per entity.**
Enables incremental extraction later instead of always pulling full history.

**Step 47: Update each extractor to accept a `since` parameter and pass it to the GitHub API where supported (e.g., commits support `?since=`).**
First step toward efficient, incremental pipelines rather than brute-force full pulls every run.

**Step 48: After a successful extraction, update `pipeline_state.json` with the current run's timestamp.**
Closes the loop on incremental logic.

**Step 49: Manually run all five extractors once and confirm five partitioned folders exist under `data/raw/`.**
Landing zone is complete and verified.

---

## PHASE F — Data Quality Layer (Steps 50–56)

**Step 50: Create `transforms/quality_checks.py`.**
Central module for all validation logic.

**Step 51: Write a `check_row_count(df, min_rows=1)` function that raises an exception if a DataFrame is empty.**
Catches silent extraction failures (e.g., API returned nothing due to a bad token or wrong repo name).

**Step 52: Write a `check_required_columns(df, required_cols)` function.**
Confirms expected fields exist before downstream code assumes they do.

**Step 53: Write a `check_no_nulls(df, critical_cols)` function for fields that must never be null (e.g., `id`, `created_at`).**
Prevents corrupt records from silently entering staging tables.

**Step 54: Write a `check_timestamp_logic(df)` function that flags any row where `merged_at` is earlier than `created_at`.**
A concrete, explainable data-integrity rule — good interview example of a "business logic" validation, not just a generic null check.

**Step 55: Wire all four checks into each extractor script, run immediately after loading the Parquet file back into memory.**
Quality gate now runs as part of every extraction, not as an afterthought.

**Step 56: Write one `pytest` test per check function using small hand-built DataFrames (both passing and failing cases).**
Confirms your validation logic itself is correct — tests the tests.

---

## PHASE G — Local Warehouse: Postgres in Docker (Steps 57–64)

**Step 57: Create `docker-compose.yml` in the project root.**
Central definition of every service in the stack.

**Step 58: Add a `postgres` service to `docker-compose.yml` using the official `postgres:16` image, with environment variables for `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`.**
This will serve as both your analytical warehouse (for now) and Airflow's metadata database.

**Step 59: Add a named volume for Postgres data persistence.**
So data survives container restarts.

**Step 60: Run `docker compose up -d postgres` and confirm it starts with `docker ps`.**
First running service.

**Step 61: Connect to it using a DB client (DBeaver, TablePlus, or `psql`) to confirm connectivity.**
Sanity check before building anything on top.

**Step 62: Create a `sql/00_create_staging_tables.sql` file defining `stg_pull_requests`, `stg_commits`, `stg_reviews`, `stg_workflow_runs`, `stg_issues` with appropriate column types.**
Staging schema, matching the fields you extracted in Phase D.

**Step 63: Run this SQL file against Postgres manually to create the tables.**
Confirms your schema syntax is valid.

**Step 64: Create `transforms/load_staging.py` that reads each Parquet file and bulk-inserts it into its matching staging table using `pandas.to_sql()` (or a faster `COPY`-based method).**
First "Load" step of ELT — raw files are now queryable via SQL.

---

## PHASE H — Star Schema Warehouse Design (Steps 65–74)

**Step 65: Create `sql/01_create_dim_tables.sql` defining `dim_repo`, `dim_contributor`, `dim_date`.**
Dimension tables first, since facts will reference them.

**Step 66: Write a one-time SQL script (or Python loop) to populate `dim_date` with every date for the next 3 years (`date_key`, `date`, `week`, `month`, `quarter`, `year`, `is_weekend`).**
Standard data-warehousing pattern — a pre-built calendar dimension simplifies all future date-based joins/filters.

**Step 67: Write SQL to populate `dim_repo` from distinct repo values in staging.**
One row per tracked repository.

**Step 68: Write SQL to populate `dim_contributor` from distinct usernames across commits/PRs/reviews staging tables.**
One row per unique person.

**Step 69: Create `sql/02_create_fact_pull_requests.sql`.**
Defines the `fact_pull_requests` table structure (foreign keys to `dim_repo`, `dim_contributor`, `dim_date`, plus measures like `lead_time_hours`, `additions`, `deletions`).

**Step 70: Write the `INSERT INTO fact_pull_requests SELECT ...` transformation joining `stg_pull_requests` to the dimension tables and calculating `lead_time_hours = EXTRACT(EPOCH FROM (merged_at - created_at))/3600`.**
Core transformation logic — raw timestamps become a business metric.

**Step 71: Create and populate `fact_reviews` similarly, joining `stg_reviews` to `fact_pull_requests` and calculating `turnaround_hours` from PR creation to first review.**
Second fact table.

**Step 72: Create and populate `fact_ci_runs` from `stg_workflow_runs`, calculating `duration_seconds` and a boolean `is_failure` from the `conclusion` field.**
Third fact table — powers deployment frequency and change failure rate.

**Step 73: Add a `fact_deployments` table (can initially be the subset of `fact_ci_runs` where `workflow_name` matches your deploy workflow, e.g., `name = 'Deploy'`).**
Distinguishes "any CI run" from "an actual deployment event" — a meaningful business distinction to explain in an interview.

**Step 74: Run all fact table population scripts and spot-check row counts against the original staging tables to confirm no silent data loss in the joins.**
Validates the warehouse layer is complete and trustworthy.

---

## PHASE I — Metrics SQL Layer (Steps 75–84)

**Step 75: Create `sql/metrics/dora_deployment_frequency.sql`.**
`COUNT(*) FROM fact_deployments WHERE is_failure = false GROUP BY date_key` (or weekly bucket) — your first DORA metric.

**Step 76: Create `sql/metrics/dora_lead_time.sql`.**
`AVG(lead_time_hours) FROM fact_pull_requests WHERE is_merged = true`, bucketed by week.

**Step 77: Create `sql/metrics/dora_change_failure_rate.sql`.**
`SUM(CASE WHEN is_failure THEN 1 ELSE 0 END)::float / COUNT(*) FROM fact_deployments`, bucketed by week.

**Step 78: Create `sql/metrics/dora_mttr.sql`.**
For each failed deployment, find the timestamp of the next successful deployment on the same repo and average the gap — the trickiest of the four, using a self-join or window function (`LEAD()`).

**Step 79: Create `sql/metrics/code_churn.sql`.**
`SUM(additions + deletions) FROM fact_pull_requests GROUP BY contributor_key, week`.

**Step 80: Create `sql/metrics/bus_factor.sql`.**
Rank contributors by total commits per repo descending, cumulative-sum their share, and find the minimum number of contributors whose combined commits exceed 50% of the total.

**Step 81: Create `sql/metrics/review_turnaround.sql`.**
`AVG(turnaround_hours) FROM fact_reviews GROUP BY week`.

**Step 82: Create `sql/metrics/ci_reliability.sql`.**
`(COUNT(*) FILTER (WHERE NOT is_failure))::float / COUNT(*) FROM fact_ci_runs`, trailing 7-day and 30-day windows.

**Step 83: Wrap each metric SQL file as a Postgres VIEW (`CREATE VIEW v_dora_lead_time AS ...`) rather than a one-off query.**
Views make metrics queryable at any time without rerunning scripts — this is what Grafana and the agent will read from.

**Step 84: Manually query each view and sanity-check the numbers against a small manual calculation on 2–3 known PRs.**
Trust but verify — catch calculation bugs before they propagate into dashboards and AI reports.

---

## PHASE J — Apache Airflow Orchestration (Steps 85–98)

**Step 85: Add `airflow-init`, `airflow-webserver`, and `airflow-scheduler` services to `docker-compose.yml`, using the official `apache/airflow` image, pointing at the same Postgres service for metadata.**
Airflow needs its own metadata schema — can share the Postgres container but should use a separate database within it.

**Step 86: Create a second database inside Postgres specifically for Airflow's metadata (`airflow_meta`), separate from your warehouse database.**
Keeps orchestration metadata cleanly separated from analytical data.

**Step 87: Run `docker compose up airflow-init` to run Airflow's DB migrations and create an admin user.**
One-time setup step.

**Step 88: Run `docker compose up -d` to start all services and open the Airflow UI at `localhost:8080`.**
Confirms the orchestration layer itself works before adding your DAG.

**Step 89: Mount your local `dags/` folder into the Airflow containers via a volume in `docker-compose.yml`.**
Lets you edit DAG files locally and have Airflow pick them up automatically.

**Step 90: Create `dags/devpulse_pipeline.py` with a basic DAG skeleton (`dag_id`, `schedule_interval`, `start_date`, `catchup=False`).**
Skeleton before logic.

**Step 91: Add a `PythonOperator` task calling `fetch_pull_requests.py`'s main function.**
First real task in the DAG.

**Step 92: Add one `PythonOperator` task per remaining extractor (commits, reviews, workflow runs, issues), and set them to run in parallel (no dependency between them).**
They're independent data sources — no reason to serialize them.

**Step 93: Add a `PythonOperator` task for the data quality checks (Phase F), set to depend on ALL extraction tasks completing (`>>` after all five).**
Quality gate correctly positioned after extraction, before loading.

**Step 94: Add a `PythonOperator` task for `load_staging.py`, depending on the quality check task.**
Staging load only happens if data passed validation.

**Step 95: Add a task (`PostgresOperator` or `PythonOperator` running SQL) executing the dimension/fact table population scripts from Phase H, depending on the staging load task.**
Warehouse transformation step in the DAG.

**Step 96: Set `retries=2` and `retry_delay=timedelta(minutes=5)` as default task arguments.**
Basic resilience — transient API/network failures shouldn't fail the whole pipeline immediately.

**Step 97: Set the DAG's `schedule_interval` to `@daily` (or `0 6 * * *` for 6am daily).**
Defines your production cadence.

**Step 98: Trigger the DAG manually from the Airflow UI and watch all tasks go green in order.**
First full end-to-end orchestrated run — this is a major milestone, the entire ELT pipeline is now automated.

---

## PHASE K — Anomaly Detection (Steps 99–106)

**Step 99: Create `transforms/anomaly_detection.py`.**
Dedicated module for statistical/ML detection logic.

**Step 100: Write a `z_score_anomalies(series, threshold=2.5)` function using NumPy, returning indices/dates where the absolute z-score exceeds the threshold.**
Simplest, most explainable method — good baseline.

**Step 101: Write an `iqr_anomalies(series)` function using the 1.5×IQR rule.**
A second, non-parametric method — useful to mention you know multiple approaches and their tradeoffs (z-score assumes normality, IQR doesn't).

**Step 102: Apply `z_score_anomalies` to the weekly review turnaround metric (from Step 81) and print any flagged weeks.**
First applied test on real data.

**Step 103: Install `scikit-learn` and add it to `requirements.txt`.**
Needed for the multivariate method.

**Step 104: Write an `isolation_forest_anomalies(df, features)` function that fits an `IsolationForest` model on multiple metrics at once (e.g., review turnaround + CI failure rate + churn for the same week) and returns an anomaly score per row.**
Catches combined-signal anomalies a single metric would miss (e.g., a week that's only mildly unusual on each metric individually but unusual in combination).

**Step 105: Create an `anomalies` table in the warehouse (`metric_name`, `period`, `value`, `method`, `severity`) and a Python task that writes detected anomalies into it.**
Makes anomalies queryable/dashboardable, not just printed to console.

**Step 106: Add this anomaly detection task to the Airflow DAG, depending on the metrics views being available (after Phase I/H tasks).**
Anomaly detection now runs automatically every pipeline execution.

---

## PHASE L — Grafana Dashboards (Steps 107–116)

**Step 107: Add a `grafana` service to `docker-compose.yml` using the official `grafana/grafana` image, exposing port 3000.**
Visualization layer added to the stack.

**Step 108: Run `docker compose up -d grafana` and log into `localhost:3000` with the default admin credentials.**
Confirm the service runs before configuring anything.

**Step 109: Add your Postgres warehouse as a Data Source inside Grafana (Connections → Data Sources → PostgreSQL), pointing at the warehouse database (not the Airflow metadata one).**
Connects visualization to your actual data.

**Step 110: Create a new Dashboard called "DevPulse — Engineering Health."**
Container for all panels.

**Step 111: Add a "Stat" panel for current-week Deployment Frequency, querying the `v_dora_deployment_frequency` view.**
First scorecard-style panel.

**Step 112: Add "Stat" panels for the other three DORA metrics (Lead Time, Change Failure Rate, MTTR) the same way.**
Completes the DORA scorecard row.

**Step 113: Add a "Time Series" panel showing Lead Time trend over the last 12 weeks.**
First trend visualization.

**Step 114: Add a "Bar Chart" panel showing Code Churn by contributor for the current month.**
Demonstrates a different chart type and a contributor-level breakdown.

**Step 115: Add a "Table" panel querying the `anomalies` table, sorted by most recent, color-coded by severity.**
Surfaces the anomaly detection work visually.

**Step 116: Set the dashboard's auto-refresh interval to match your DAG schedule (e.g., every 1 hour) and save it.**
Dashboard now stays live in sync with pipeline runs.

---

## PHASE M — GenAI Weekly Digest Agent (Steps 117–130)

**Step 117: Sign up for an Anthropic or OpenAI API key and add it to `.env` as `LLM_API_KEY`.**
Credential setup for the agent.

**Step 118: Create the `agent/` package with `__init__.py`.**
Isolates agent logic from the rest of the pipeline.

**Step 119: Create `agent/tools.py` with a `query_metrics_db()` function that runs SQL against the metrics views and returns the current week + prior 4-week average as a JSON-serializable dict.**
The agent's first "tool" — real data access, not hardcoded text.

**Step 120: Add a `get_top_contributors(repo, week)` function to `tools.py`, querying `fact_pull_requests` grouped by contributor.**
Second tool — lets the agent name specific people/drivers behind a metric change, not just report the number.

**Step 121: Add a `get_anomalies(week)` function to `tools.py` querying the `anomalies` table.**
Third tool — feeds anomaly context directly into the agent's reasoning.

**Step 122: Create `agent/prompts.py` containing the system instruction string (agent's role, constraints: use only provided numbers, be concise, fixed output structure).**
Separates prompt content from orchestration logic for easy iteration.

**Step 123: Create `agent/digest_agent.py` with a `DigestAgent` class.**
Main orchestration class for the agent loop.

**Step 124: Implement `DigestAgent.gather()`, calling all three tool functions from Steps 119–121 and merging results into one context dict.**
The "Gather" stage of the ReAct-style loop.

**Step 125: Implement `DigestAgent.build_prompt(context)`, formatting the system instruction + JSON context + output-structure instruction into the final LLM request.**
Prompt assembly, kept as its own testable function.

**Step 126: Implement `DigestAgent.generate()`, sending the prompt to the LLM API and returning the raw text response.**
The actual "Generate" call.

**Step 127: Implement `DigestAgent.validate(report_text, context)`, a guardrail function that extracts any numbers mentioned in the report and checks each exists somewhere in the source context JSON, flagging (not necessarily blocking) mismatches.**
Core hallucination guardrail — this is the detail most other candidates' "AI projects" will be missing.

**Step 128: Implement a fallback: if the LLM call fails or validation fails badly, generate a simple templated (non-AI) report from the same context dict instead.**
Ensures the pipeline never silently fails to deliver a report — resilience over cleverness.

**Step 129: Write a `pytest` test for `validate()` using a hand-crafted report with one deliberately wrong number, confirming it gets flagged.**
Proves the guardrail actually works, not just exists.

**Step 130: Run the full agent manually end-to-end against your real warehouse data and read the generated report for quality/tone.**
First real, human-reviewed output — iterate on the prompt from Step 122 if the tone or structure isn't right.

---

## PHASE N — Automated Delivery (Steps 131–135)

**Step 131: Create a Slack workspace (or use an existing one) and add an Incoming Webhook app, copying the webhook URL.**
Delivery channel setup.

**Step 132: Add `SLACK_WEBHOOK_URL` to `.env`.**
Secret storage, same pattern as before.

**Step 133: Create `agent/delivery.py` with a `post_to_slack(report_text)` function using `requests.post()` against the webhook URL, formatted with basic Slack Markdown.**
Delivery mechanism.

**Step 134: Wire `DigestAgent`'s output into `post_to_slack()` in a small `agent/run_weekly_digest.py` script.**
Ties gather → generate → validate → deliver into one callable entrypoint.

**Step 135: Add this script as a new Airflow DAG (`dags/weekly_digest.py`) scheduled `@weekly`, separate from the daily ELT DAG.**
Digest cadence is intentionally different from ingestion cadence — weekly summary, daily data refresh.

---

## PHASE O — Testing & Quality Hardening (Steps 136–140)

**Step 136: Write `pytest` unit tests for each metric SQL calculation, using a small seeded test schema with known input rows and hand-calculated expected outputs.**
Confirms your SQL logic (Phase I) is correct, not just "runs without error."

**Step 137: Write an integration test that runs the full Airflow DAG against a small test repo (via `airflow dags test`) and asserts all tasks succeed.**
Confirms orchestration end-to-end, not just individual pieces.

**Step 138: Add a `.github/workflows/ci.yml` GitHub Actions file that installs dependencies and runs `pytest` on every push.**
Automated CI for your own project — a strong, easy-to-add credibility signal.

**Step 139: Add `black` and `ruff` (or `flake8`) to `requirements.txt` and run them across the codebase, fixing any issues.**
Code quality/consistency pass.

**Step 140: Add a `pre-commit` config running `black`/`ruff`/`pytest` automatically before every commit.**
Prevents quality regressions going forward, demonstrates dev-practice maturity.

---

## PHASE P — Documentation & Portfolio Packaging (Steps 141–146)

**Step 141: Write the full `README.md`: project description, the architecture diagram (from the earlier spec, adapted as an image or ASCII block), and a "Why I built this" paragraph tying it to real DevOps/data-engineering concepts.**
This is often the *only* thing a recruiter or hiring manager actually reads — make it count.

**Step 142: Add a "Quick Start" section to the README: clone, copy `.env.example` to `.env`, fill in secrets, `docker compose up -d`, trigger the DAG.**
Lets anyone (including an interviewer) actually run your project.

**Step 143: Take screenshots of the Grafana dashboard, the Airflow DAG graph view, and a sample AI-generated Slack report; add them to a `docs/screenshots/` folder and embed them in the README.**
Visual proof matters more than text for a portfolio project.

**Step 144: Record a 2–3 minute screen-recording walking through: triggering the DAG, watching it complete, viewing the dashboard update, and reading the AI digest.**
A short demo video is disproportionately persuasive — link it in your README and resume/portfolio site.

**Step 145: Write a short `docs/ARCHITECTURE.md` explaining each design decision (why star schema, why Airflow, why the guardrails on the agent) — this becomes your interview cheat sheet.**
Forces you to articulate the "why," which is what interviewers actually probe for.

**Step 146: Push the full repository to GitHub as a public repo with a clear name (`devpulse` or `devpulse-analytics`), add topics/tags (`data-engineering`, `airflow`, `dora-metrics`, `genai`), and pin it on your GitHub profile.**
Discoverability and presentation — this is the artifact a recruiter will actually click into.

---

## PHASE Q — Optional Stretch Goals (Steps 147–148, do only after 1–146 are solid)

**Step 147: Migrate the SQL transformation layer (Phase H/I) into dbt models, adding `dbt test` assertions (`not_null`, `unique`, `relationships`) and generating dbt's auto-lineage documentation site.**
Adds a highly-regarded analytics-engineering tool to your stack and gives you free, visual data lineage documentation.

**Step 148: Convert `docker-compose.yml` into Kubernetes manifests (start with `kompose convert`, then hand-tune Deployments/Services/ConfigMaps/Secrets/PVCs) and deploy on a local `k3s` or `minikube` cluster.**
Demonstrates orchestration beyond Compose — the final, most advanced stretch capability, and a natural place to stop.

---

**N = 148. At this point DevPulse is a complete, tested, documented, containerized, orchestrated, AI-augmented data platform — ready to be Project #1 on your resume.**
