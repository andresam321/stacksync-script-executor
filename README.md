# Stacksync Secure Script Executor

This API service enables secure execution of user-submitted Python scripts in a sandboxed environment.

It was built for use cases like Stacksync, where customers define custom logic for transforming or filtering data during real-time syncs between CRMs and databases.

🧠 Built with Flask

🔒 Uses nsjail for local sandboxing

☁️ Provides a secure Cloud Run fallback with input validation


---

## 🔧 Local Setup

### 1. Build the Docker image:

```bash
docker build -t stacksync-runner .
``` 
### 2. Run the container:
```bash
docker run -p 8080:8080 stacksync-runner . 
``` 

###  Cloud Deployment (Google Cloud Run)
The API is deployed publicly here:

👉 https://stacksync-runner-348397166528.us-central1.run.app

Note: Visiting the base URL will return 404 Not Found.
Use a POST request to the /execute endpoint as shown below.

## 🚀 API Usage

## Tested with postman


### POST /execute
#
**Request Body:**
```json
{
  "script": "def main():\n  return {\"msg\": \"Hello World\"}"
}
```

**Response Body:**
```json
{
    "note": "running direct execution fallback (nsjail not available in Cloud Run)",
    "result": {
        "msg": "Hello World"
    },
    "stdout": "{\"msg\": \"Hello World\"}"
}
```
###  POST /execute 
#
**Request Body:**
```json
{
  "script": "def main():\n  total = sum([5, 10, 15])\n  return {\"sum\": total}"
}

```
**Response Body:**
```json
{
    "note": "running direct execution fallback (nsjail not available in Cloud Run)",
    "result": {
        "sum": 30
    },
    "stdout": "{\"sum\": 30}"
}
```
### Bad Script ,  POST /execute 
#
**Request Body:**
```json
{
  "script": "def main():\n  import os\n  os.system('rm -rf /')\n  return {\"msg\": \"nope\"}"
}

```
**Response Body:**
```json
{
    "details": "The script contains one or more unsafe keywords such as 'import os' or 'eval'.",
    "error": "Blocked script for using restricted keywords"
}
```
## Script Submission Guidelines
```
To submit a script, make sure:

You define a main() function

main() returns a JSON-serializable object

Do not call main() or print the result yourself — the system appends a call to main() and handles output parsing.
```
### Script

curl -X POST https://stacksync-runner-348397166528.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def main():\n  return {\"msg\": \"Hello World\"}"}'


---

#### . 🔐 **Security Note** (why `nsjail` is only local)


Local mode: Uses nsjail to sandbox scripts in a secure namespace with memory and CPU limits.

Cloud Run fallback: Due to restricted system calls (e.g. CLONE_NEWUSER, chroot), nsjail is unavailable in Cloud Run.

As a fallback, scripts are executed with Python directly — with restricted keywords blocked (import os, subprocess, etc.) to prevent dangerous operations.

⚠️ This fallback is for testing/demo purposes only. In production, execution should be moved to a hardened environment (e.g., GCE with nsjail, or gVisor-based isolation).

### Submission Info
GitHub Repo: [[Stacksync executor](https://github.com/andresam321/stacksync-script-executor)]

Cloud Run Endpoint: https://stacksync-runner-348397166528.us-central1.run.app/execute

Time to Complete: ~5 hours (initial sandboxing, Docker/Cloud Run integration, fallback logic, testing, and documentation)
