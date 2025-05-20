from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import json
import sys

app = Flask(__name__)

@app.route("/execute", methods=["POST"])
def execute_script_with_nsjail():
    #parse json from incoming request 
    data = request.get_json()

    if not data or "script" not in data:
        return jsonify({"error": "Missing script in request"}), 400
    #get the script string from the request payload
    script = data["script"]

    unsafe_keywords = ["import os", "import subprocess", "open(", "eval(", "exec(", "__import__"]
    if any(keyword in script for keyword in unsafe_keywords):
        return jsonify({
        "error": "Blocked script for using restricted keywords",
        "details": "The script contains one or more unsafe keywords such as 'import os' or 'eval'."}), 400

    #initialize temp file path to esnure cleanup later
    tmp_path = None
    stdout = ""
    stderr = ""
    #check if running in google cloud run(fallback)
    if os.getenv("CLOUD_RUN", "0") == "1":
        try:
            #create a temperoray .py file and wrtie the submitted scrip to it 
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as tmp:
                #append code to searialize main() result as JSON
                tmp.write(script + "\n\nimport json\nprint(json.dumps(main()))")
                #SAve tem file 
                tmp_path = tmp.name
            #run the script using the regualr python interpreter
            result = subprocess.run(
                #command to run script
                ["python3", tmp_path],
                #capture standard output
                stdout=subprocess.PIPE,
                #capture standard error
                stderr=subprocess.PIPE,
                #return output as string
                text=True,
                #timeout to prevent long running scripts
                timeout=10
            )
            #get the standard output
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            lines = stdout.splitlines()
            if not lines:
                raise ValueError("No output received from script")
            #check if the last line is a valid JSON
            last_line = lines[-1]
            #parse the output as JSON
            parsed = json.loads(last_line)
            #return the result as JSON
            return jsonify({
                "note": "running direct execution fallback (nsjail not available in Cloud Run)",
                "result": parsed,
                "stdout": stdout
            }), 200

        except subprocess.TimeoutExpired:
            return jsonify({"error": "Script execution timed out in fallback"}), 400
        except Exception as e:
                return jsonify({
                    "error": "Script did not return valid JSON from main()",
                    "details": str(e),
                    "stdout": stdout,
                    "stderr": stderr
                }), 400

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    # Use nsjail for local sandboxed execution
    # nsJail is a tool that can be used to run untrusted code in a secure environment
    # It creates a new namespace and restricts the resources available to the code
    # This is useful for running untrusted code safely, as it prevents the code from accessing sensitive resources
    # or performing malicious actions
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as tmp:
            tmp.write(script + "\n\nimport json\nprint(json.dumps(main()))")
            tmp_path = tmp.name


        result = subprocess.run(
            [
                "/opt/nsjail/nsjail",
                "--quiet",
                "--mode", "o",
                "--time_limit", "5",
                "--disable_proc",
                "--disable_clone_newnet",
                "--disable_clone_newipc",
                "--chroot", "/",
                "--user", "99999",
                "--group", "99999",
                "--rlimit_as", "128",
                "--rlimit_cpu", "2",
                "--",
                "python3", tmp_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )


        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        lines = stdout.splitlines()
        if not lines:
            raise ValueError("No output received from script")
        last_line = lines[-1]
        parsed = json.loads(last_line)

        return jsonify({
            "result": parsed,
            "stdout": stdout
        }), 200

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Script execution timed out"}), 400
    except Exception as e:
        return jsonify({
            "error": "Script did not return valid JSON from main()",
            "details": str(e),
            "stdout": stdout,
            "stderr": stderr
        }), 400
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == '__main__':#
    app.run(host='0.0.0.0', port=8080)
