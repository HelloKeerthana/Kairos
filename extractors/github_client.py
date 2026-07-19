import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_result

from extractors.config import GITHUB_TOKEN

BASE_URL = "https://api.github.com"


class GitHubClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        retry=retry_if_result(lambda r: r.status_code in (403, 429)),
    )
    def _request(self, url, params=None):
        return requests.get(url, headers=self.headers, params=params)

    def get_paginated(self, endpoint, params=None):
        """Fetch all pages from a GitHub endpoint, following Link headers."""
        url = f"{BASE_URL}{endpoint}"
        params = params or {"per_page": 100}
        results = []

        while url:
            response = self._request(url, params=params)
            response.raise_for_status()
            results.extend(response.json())

            # After the first request, params are baked into the 'next' URL already
            params = None
            url = None
            if "next" in response.links:
                url = response.links["next"]["url"]

        return results
