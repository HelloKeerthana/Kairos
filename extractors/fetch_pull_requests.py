import pandas as pd
from extractors.github_client import GitHubClient
from extractors.config import REPO_OWNER, REPO_NAME

def fetch_pull_requests():
    client = GitHubClient()
    endpoint = f"/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
    raw_prs = client.get_paginated(endpoint, params={"state": "all", "per_page": 100})

    print("RAW RESPONSE LENGTH:", len(raw_prs))

    if not raw_prs:
        print("No pull requests found for this repo.")
        return pd.DataFrame(columns=[
            "id", "number", "author", "created_at", "merged_at",
            "closed_at", "state", "additions", "deletions", "changed_files"
        ])

    df = pd.DataFrame(raw_prs)

    # Keep only fields available on the list endpoint
    df = df[[
        "id", "number", "user", "created_at", "merged_at",
        "closed_at", "state"
    ]].copy()
    df["author"] = df["user"].apply(lambda u: u["login"] if isinstance(u, dict) else None)
    df.drop(columns=["user"], inplace=True)

    # additions/deletions/changed_files require a per-PR detail call
    # small repo, so this is cheap — fine for now
    detail_endpoint = f"/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
    stats = []
    for pr_number in df["number"]:
        detail = client._request(f"https://api.github.com{detail_endpoint}/{pr_number}").json()
        stats.append({
            "number": pr_number,
            "additions": detail.get("additions"),
            "deletions": detail.get("deletions"),
            "changed_files": detail.get("changed_files"),
        })

    stats_df = pd.DataFrame(stats)
    df = df.merge(stats_df, on="number", how="left")

    return df

if __name__ == "__main__":
    df = fetch_pull_requests()
    print(df.head())
    print(f"\nTotal PRs fetched: {len(df)}")

    df.to_parquet("data/raw/pull_requests.parquet", index=False)
    print("Saved to data/raw/pull_requests.parquet")