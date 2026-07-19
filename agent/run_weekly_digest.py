from agent.digest_agent import DigestAgent
from agent.delivery import post_to_slack

def main():
    agent = DigestAgent()
    report = agent.run()
    post_to_slack(report)

if __name__ == "__main__":
    main()