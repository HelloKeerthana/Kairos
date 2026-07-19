import os
import requests
from dotenv import load_dotenv

load_dotenv()

def post_to_slack(report_text: str):
    """Send the digest report to Slack via Incoming Webhook."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("[WARNING] No SLACK_WEBHOOK_URL set — skipping delivery, printing instead:")
        print(report_text)
        return False

    payload = {
        "text": report_text,
    }

    response = requests.post(webhook_url, json=payload)

    if response.status_code == 200:
        print("Report posted to Slack successfully.")
        return True
    else:
        print(f"[ERROR] Slack delivery failed: {response.status_code} {response.text}")
        return False