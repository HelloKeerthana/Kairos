import pandas as pd
from extractors.github_client import GitHubClient
from extractors.config import REPO_OWNER, REPO_NAME
from extractors.data_quality import validate_commits


def fetch_commits():
    client = GitHubClient()
    endpoint = f"/repos/{REPO_OWNER}/{REPO_NAME}/commits"
    raw_commits = client.get_paginated(endpoint, params={"per_page": 100})

    print("RAW RESPONSE LENGTH:", len(raw_commits))

    if not raw_commits:
        return pd.DataFrame(columns=["sha", "author_name", "date", "additions", "deletions"])

    rows = []
    for c in raw_commits:
        sha = c["sha"]
        detail = client._request(f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits/{sha}").json()
        rows.append({
            "sha": sha,
            "author_name": c["commit"]["author"]["name"],
            "date": c["commit"]["author"]["date"],
            "additions": detail.get("stats", {}).get("additions"),
            "deletions": detail.get("stats", {}).get("deletions"),
        })

    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = fetch_commits()
    validate_commits(df)
    print(df.head())
    print(f"\nTotal commits fetched: {len(df)}")
    df.to_parquet("data/raw/commits.parquet", index=False)
    print("Saved to data/raw/commits.parquet")