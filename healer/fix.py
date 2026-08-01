import os
import sys
import json
import datetime
import subprocess
import requests

ALLOWED_FILES = ["k8s/deployment.yaml", "requirements.txt", "jest.config.js", ".github/workflows/ci.yml"]

def escalate_issue(root_cause, log_snippet):
    github_token = os.environ.get("GITHUBB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")
    
    if not github_token or not repo:
        print("Missing GITHUBB_TOKEN or GITHUB_REPO, cannot escalate via GitHub Issue.")
        return
        
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    body = {
        "title": "[Self-Healer] Could not auto-fix pipeline",
        "body": f"**Root Cause**: {root_cause}\n\n**Log Snippet**:\n```\n{log_snippet}\n```"
    }
    
    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 201:
        print(f"Successfully created GitHub issue: {response.json().get('html_url')}")
    else:
        print(f"Failed to create GitHub issue: {response.text}")

def log_attempt(attempt_data):
    log_file = "healer/heal_log.json"
    logs = []
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                pass
                
    logs.append(attempt_data)
    
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)

def main():
    if len(sys.argv) < 2:
        print("Usage: python fix.py <analysis.json> [ci_log.txt]")
        sys.exit(1)
        
    analysis_file = sys.argv[1]
    log_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    with open(analysis_file, "r") as f:
        try:
            analysis = json.load(f)
        except json.JSONDecodeError:
            print("Failed to decode analysis JSON.")
            sys.exit(1)

    try:
        heal_count = int(os.environ.get("HEAL_COUNT", "0"))
    except ValueError:
        heal_count = 0
        
    log_snippet = ""
    if log_file and os.path.exists(log_file):
        with open(log_file, "r") as f:
            lines = f.readlines()
            log_snippet = "".join(lines[-50:])
    
    attempt_record = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "attempt": heal_count + 1,
        "root_cause": analysis.get("root_cause", "Unknown"),
        "file_edited": analysis.get("file", ""),
        "success": False
    }

    if heal_count >= 2 or analysis.get("escalate", False):
        print("Escalating issue (either escalate=True or HEAL_COUNT >= 2).")
        escalate_issue(analysis.get("root_cause", "Unknown"), log_snippet)
        log_attempt(attempt_record)
        sys.exit(0)

    target_file = analysis.get("file")
    find_str = analysis.get("find")
    replace_str = analysis.get("replace")
    
    if not target_file or target_file not in ALLOWED_FILES:
        print(f"File {target_file} is not in the whitelist or missing. Escalating.")
        escalate_issue(f"Tried to edit unauthorized file: {target_file}. " + analysis.get("root_cause", ""), log_snippet)
        log_attempt(attempt_record)
        sys.exit(0)
        
    if not os.path.exists(target_file):
        print(f"File {target_file} does not exist. Escalating.")
        escalate_issue(f"File not found: {target_file}. " + analysis.get("root_cause", ""), log_snippet)
        log_attempt(attempt_record)
        sys.exit(0)
        
    with open(target_file, "r") as f:
        content = f.read()
        
    if find_str not in content:
        print(f"Find string not found in {target_file}. Escalating.")
        escalate_issue(f"Could not find exact string to replace in {target_file}. " + analysis.get("root_cause", ""), log_snippet)
        log_attempt(attempt_record)
        sys.exit(0)
        
    new_content = content.replace(find_str, replace_str)
    
    with open(target_file, "w") as f:
        f.write(new_content)
        
    attempt_record["success"] = True
    log_attempt(attempt_record)
    
    try:
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
        subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
        subprocess.run(["git", "add", target_file], check=True)
        commit_msg = f"[self-healer] auto-fix: {analysis.get('root_cause', 'issue')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Successfully committed and pushed the fix.")
    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e}")
        escalate_issue("Git push failed during auto-fix", log_snippet)

if __name__ == "__main__":
    main()
