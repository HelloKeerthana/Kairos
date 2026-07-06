import pandas as pd
from extractors.github_client import GitHubClient
from extractors.config import REPO_OWNER, REPO_NAME

def fetch_reviews():
    client = GitHubClient()
    prs_df = pd.read_parquet("data/raw/pull_requests.parquet")

    rows = []
    for pr_number in prs_df["number"]:
        endpoint = f"/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/reviews"
        reviews = client.get_paginated(endpoint)
        for r in reviews:
            rows.append({
                "id": r["id"],
                "pull_request_number": pr_number,
                "reviewer": r["user"]["login"] if r.get("user") else None,
                "submitted_at": r.get("submitted_at"),
                "state": r.get("state"),
            })

    if not rows:
        return pd.DataFrame(columns=["id", "pull_request_number", "reviewer", "submitted_at", "state"])

    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = fetch_reviews()
    print(df.head())
    print(f"\nTotal reviews fetched: {len(df)}")
    df.to_parquet("data/raw/reviews.parquet", index=False)
    print("Saved to data/raw/reviews.parquet")