# AI Self-Healing CI/CD Pipeline

Welcome to the **Self-Healing Pipeline**, an intelligent CI/CD workflow that doesn't just report failures—it fixes them! 

Powered by GitHub Actions, Python, and the Groq LLM (Llama-3), this pipeline monitors your continuous integration and deployment stages. When a step fails, the pipeline automatically intercepts the failure logs, analyzes the root cause using AI, and securely pushes a fix back to your repository.

## Features

- **Automated Root Cause Analysis**: Intercepts stdout/stderr logs on pipeline failure and feeds them to an LLM acting as a DevOps engineer.
- **Auto-Remediation**: The AI outputs structured JSON containing the exact string replacement required to fix the issue.
- **Strict Security & Whitelisting**: The self-healer is sandboxed. It is only permitted to modify infrastructure and configuration files (e.g., equirements.txt\, \.github/workflows/ci.yml\, \k8s/deployment.yaml\). Attempts to modify application code or tests (\main.py\, \	est_main.py\) are safely blocked.
- **Graceful Escalation**: If the AI cannot safely fix the issue, hallucinates a file, or exceeds the maximum healing retry limit (\HEAL_COUNT >= 2\), it gracefully falls back by automatically opening a detailed GitHub Issue.

## Architecture

1. **\ci.yml\**: The GitHub Actions workflow that runs your tests, security scans (Trivy), and deployment (Kubernetes). 
2. **\healer/analyze.py\**: Triggered on failure. Sends the captured logs to the Groq API and requests a structured JSON fix.
3. **\healer/fix.py\**: Parses the JSON. Validates the target file against the whitelist. Edits the file locally, commits the change, and pushes it back to GitHub using the \GITHUB_TOKEN\.
4. **\healer/prompt.py\**: Contains the highly-engineered System Prompt that guides the LLM to provide exact, naive-replacement safe string changes.

## How to Test It

You can test the self-healer by intentionally breaking the pipeline:
1. **Typo in dependencies**: Edit equirements.txt\ and misspell a package.
2. **Vulnerability**: Pin a vulnerable package (e.g., equests==2.20.0\) to trigger a Trivy security failure.
3. **OOM Crash**: Lower the Kubernetes memory limit in \k8s/deployment.yaml\ to 4Mi\.
4. **Escalation Test**: Break a file not in the whitelist (like \	ests/test_main.py\) and watch the bot open an issue instead of touching your code!
