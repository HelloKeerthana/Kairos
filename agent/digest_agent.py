import os
import re
from dotenv import load_dotenv
from google import genai

from agent.tools import query_metrics_db, get_top_contributors
from agent.prompts import SYSTEM_PROMPT, build_user_prompt

load_dotenv()

class DigestAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.context = None
        self.report = None

    def gather(self):
        """Step 1: pull real data via tool calls."""
        metrics = query_metrics_db()
        contributors = get_top_contributors()
        self.context = {**metrics, "top_contributors": contributors}
        return self.context

    def generate(self):
        """Step 2: call the LLM with the gathered context."""
        user_prompt = build_user_prompt(self.context)

        response = self.client.models.generate_content(
            model="gemini-2.5-pro",
            contents=user_prompt,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "max_output_tokens": 800,
            },
        )

        self.report = response.text
        return self.report

    def validate(self):
        """Step 3: guardrail — every number in the report should trace back to context."""
        if not self.report or len(self.report.strip()) == 0:
            return False, "Empty report generated."

        numbers_in_report = set(re.findall(r"\d+\.?\d*", self.report))
        context_str = str(self.context)
        numbers_in_context = set(re.findall(r"\d+\.?\d*", context_str))

        unverified = numbers_in_report - numbers_in_context
        suspicious = [n for n in unverified if len(n) > 1 and n not in numbers_in_context]

        if suspicious:
            return False, f"Unverified numbers in report: {suspicious}"

        return True, "OK"

    def fallback_report(self):
        """Step 4: if LLM fails or validation fails, produce a plain templated report."""
        lt = self.context.get("lead_time", [])
        df = self.context.get("deployment_frequency", [])
        cfr = self.context.get("change_failure_rate", [])
        anomalies = self.context.get("anomalies", [])

        lines = ["## Weekly Digest (Fallback — Templated)", ""]
        lines.append(f"- Lead time records: {len(lt)}")
        lines.append(f"- Deployment frequency records: {len(df)}")
        lines.append(f"- Change failure rate records: {len(cfr)}")
        lines.append(f"- Anomalies flagged: {len(anomalies)}")
        if anomalies:
            lines.append("\n### Anomalies")
            for a in anomalies:
                lines.append(f"- {a['metric_name']} on {a['date']}: value={a['value']} (expected {a['expected_min']}-{a['expected_max']}, severity={a['severity']})")

        return "\n".join(lines)

    def run(self):
        """Full pipeline: gather -> generate -> validate -> fallback if needed."""
        self.gather()

        try:
            self.generate()
            is_valid, reason = self.validate()
            if not is_valid:
                print(f"[WARNING] Validation failed: {reason}. Using fallback report.")
                self.report = self.fallback_report()
        except Exception as e:
            print(f"[ERROR] LLM call failed: {e}. Using fallback report.")
            self.report = self.fallback_report()

        return self.report


if __name__ == "__main__":
    agent = DigestAgent()
    report = agent.run()
    print("\n" + "="*60)
    print(report)
    print("="*60)