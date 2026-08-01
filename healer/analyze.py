import os
import json
import requests
import sys
from prompt import SYSTEM_PROMPT

def analyze_log(log_text):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze this CI pipeline log and provide the JSON fix:\n\n{log_text}"}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if not response.ok:
        print(f"Error calling Groq API: {response.text}", file=sys.stderr)
        response.raise_for_status()
    
    response_json = response.json()
    content = response_json["choices"][0]["message"]["content"]
    
    return json.loads(content)

if __name__ == "__main__":
    log_file = sys.argv[1] if len(sys.argv) > 1 else "ci_log.txt"
    try:
        with open(log_file, "r") as f:
            log_text = f.read()
    except FileNotFoundError:
        print(f"Log file {log_file} not found.", file=sys.stderr)
        sys.exit(1)
        
    result = analyze_log(log_text)
    # Output the result as JSON to stdout
    print(json.dumps(result, indent=2))
