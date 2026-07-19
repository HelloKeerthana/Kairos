import pandas as pd
from extractors.github_client import GitHubClient
from extractors.config import REPO_OWNER, REPO_NAME


def fetch_workflow_runs():
    client = GitHubClient()
    endpoint = f"/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs"
    response = client._request(
        f"https://api.github.com{endpoint}", params={"per_page": 100}
    ).json()
    raw_runs = response.get("workflow_runs", [])

    print("RAW RESPONSE LENGTH:", len(raw_runs))

    if not raw_runs:
        return pd.DataFrame(
            columns=[
                "id",
                "name",
                "status",
                "conclusion",
                "run_started_at",
                "updated_at",
                "head_branch",
            ]
        )

    rows = [
        {
            "id": r["id"],
            "name": r["name"],
            "status": r["status"],
            "conclusion": r["conclusion"],
            "run_started_at": r["run_started_at"],
            "updated_at": r["updated_at"],
            "head_branch": r["head_branch"],
        }
        for r in raw_runs
    ]

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = fetch_workflow_runs()
    print(df.head())
    print(f"\nTotal workflow runs fetched: {len(df)}")
    df.to_parquet("data/raw/workflow_runs.parquet", index=False)
    print("Saved to data/raw/workflow_runs.parquet")
