-- Lead Time for Changes: avg time from PR created to merged, in hours
CREATE OR REPLACE VIEW warehouse.v_dora_lead_time AS
SELECT
    r.repo_name,
    DATE_TRUNC('week', pr.created_at) AS week,
    AVG(pr.lead_time_hours) AS avg_lead_time_hours,
    COUNT(*) FILTER (WHERE pr.is_merged) AS merged_pr_count
FROM warehouse.fact_pull_requests pr
JOIN warehouse.dim_repo r ON pr.repo_key = r.repo_key
WHERE pr.is_merged = TRUE
GROUP BY r.repo_name, DATE_TRUNC('week', pr.created_at);

-- Review Turnaround Time (will be empty until you have real reviewer data)
CREATE OR REPLACE VIEW warehouse.v_review_turnaround AS
SELECT
    r.repo_name,
    pr.pr_number,
    pr.created_at,
    pr.merged_at
FROM warehouse.fact_pull_requests pr
JOIN warehouse.dim_repo r ON pr.repo_key = r.repo_key
WHERE FALSE;  -- placeholder until fact_reviews exists

-- Deployment Frequency: count of deployments per week
CREATE OR REPLACE VIEW warehouse.v_dora_deployment_frequency AS
SELECT
    r.repo_name,
    DATE_TRUNC('week', d.run_started_at) AS week,
    COUNT(*) AS deployment_count
FROM warehouse.fact_deployments d
JOIN warehouse.dim_repo r ON d.repo_key = r.repo_key
GROUP BY r.repo_name, DATE_TRUNC('week', d.run_started_at);

-- Change Failure Rate: % of deployments that failed
CREATE OR REPLACE VIEW warehouse.v_dora_change_failure_rate AS
SELECT
    r.repo_name,
    DATE_TRUNC('week', d.run_started_at) AS week,
    COUNT(*) FILTER (WHERE d.is_failure) AS failed_count,
    COUNT(*) AS total_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE d.is_failure) / COUNT(*), 2) AS failure_rate_pct
FROM warehouse.fact_deployments d
JOIN warehouse.dim_repo r ON d.repo_key = r.repo_key
GROUP BY r.repo_name, DATE_TRUNC('week', d.run_started_at);