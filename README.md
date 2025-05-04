# Stacksync Secure Script Executor

This API service allows execution of arbitrary Python scripts in a secure, sandboxed environment.  
It's designed for use cases like **Stacksync**, where customers define custom logic for transforming or filtering data during real-time syncs between CRMs and databases.

The service uses **Flask** for the API and **nsjail** to securely execute untrusted code locally.  
In production (Cloud Run), it defaults to a lighter sandbox due to container restrictions.

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

👉 https://stacksync-runner-klbdcp445q-uc.a.run.app

Note: Visiting the base URL will return 404 Not Found.
Use a POST request to the /execute endpoint as shown below.

## 🚀 API Usage

### POST /execute

**Request Body:**
```json
{
  "script": "def main():\n  print('hello')\n  return {\"msg\": \"done\"}"
}

```

**Response Body:**
```json
{
  "result": {"msg": "done"},
  "stdout": "hello\n"
}


```
### Script

curl -X POST https://stacksync-runner-klbdcp445q-uc.a.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def main():\n  print(\"Hello from cloud!\")\n  return {\"msg\": \"success\"}"}'

---

#### . 🔐 **Security Note** (why `nsjail` is only local)


Locally, the service uses nsjail to sandbox untrusted code using Linux namespaces.

On Cloud Run, nsjail fails to launch due to restricted system calls (e.g., CLONE_NEWUSER, CLONE_NEWPID), so the script does not execute.

The application gracefully logs this and avoids unsafe execution.

Input validation ensures:

A main() function is present

The result is JSON-serializable


### Submission Info
GitHub Repo: [[Stacksync executor](https://github.com/andresam321/stacksync-script-executor)]

Cloud Run URL: https://stacksync-runner-klbdcp445q-uc.a.run.app

Estimated time to complete: ~3–4 hours (including Docker, testing, and deployment)