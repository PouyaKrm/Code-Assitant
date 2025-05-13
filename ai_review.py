import os
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("GITHUB_REF").split("/")[-1]

# Get PR files diff
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3.diff"
}
pr_url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}"
response = requests.get(pr_url, headers=headers)

if response.status_code != 200:
    print("Failed to fetch PR diff")
    print(response.text)
    exit(1)

diff = response.text

# === Send to OpenAI ===
prompt = f"""You are an experienced software engineer. Please review the following pull request diff for potential improvements, bugs, or code quality issues. Be concise and helpful.

Pull Request Diff:
{diff}
"""

openai_payload = {
    "model": "gpt-4",
    "messages": [
        {"role": "system", "content": "You are a senior code reviewer."},
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.3,
}

openai_response = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    },
    json=openai_payload
)

if openai_response.status_code != 200:
    print("Failed to call OpenAI API")
    print(openai_response.text)
    exit(1)

ai_review = openai_response.json()['choices'][0]['message']['content']
print("AI Review:", ai_review)

# === Post Review as a Comment ===
comment_payload = {
    "body": ai_review
}

comments_url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"
comment_response = requests.post(
    comments_url,
    headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    },
    json=comment_payload
)

if comment_response.status_code == 201:
    print("Comment posted successfully.")
else:
    print("Failed to post comment.")
    print(comment_response.text)
