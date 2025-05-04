from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import json

app = Flask(__name__)

@app.route("/execute", methods=["POST"])
def execute_script_with_nsjail():
    data = request.get_json()

    if not data or "script" not in data:
        return jsonify({"error": "Missing script in request"}), 400

    script = data["script"]

    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as tmp:
            # Add line to ensure the result is printed as JSON
            tmp.write(script + "\n\nimport json\nprint(json.dumps(main()))")
            tmp_path = tmp.name

        # Run the script using nsjail
        result = subprocess.run(
            [
                "/opt/nsjail/nsjail",
                "--quiet",
                "--mode", "o",  # standalone mode
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

        # Try to parse stdout as JSON
        try:
            parsed = json.loads(stdout)
        except Exception as e:
            print(" nsjail failed to run — likely due to Cloud Run limitations. Falling back to direct execution.")
            return jsonify({
                "error": "Script did not return valid JSON from main()",
                "stdout": stdout,
                "stderr": stderr
            }), 400

        return jsonify({
            "result": parsed,
            "stdout": stdout
        }), 200

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Script execution timed out"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

    
# route will handle script execution
# @app.route("/execute", methods = ["POST"])
# def execute_script_wihtout_nsjail():
#     # parsing the JSON body from the post request
#     data = request.get_json()
#     #input validation
#     if not data or 'script' not in data:
#         return jsonify({'error':"Missing Script in request"}),400
    
#     script = data['script']
    
#     #redirecting stdout to capture any rpint() output
#     old_stdout = sys.stdout
#     redirected_output = sys.stdout = io.StringIO()

#     try:
#         with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as tmp:
#             # Add line to ensure the result is printed as JSON
#             tmp.write(script + "\n\nimport json\nprint(json.dumps(main()))")
#             tmp_path = tmp.name
#         local_variables = {}
#         # execute the users script safely in a limited name space
#         exec(script, {}, local_variables)
#         #checking if scripts define a main
#         if 'main' not in local_variables:
#             raise Exception("No 'main' function found")
        
#         #call the users main() func
#         result = local_variables['main']()

#         #make sure the return val can be serialized into json

#         json.dumps(result)

#         # capture any output from print() statements
#         stdout = redirected_output.getvalue()

#         # return both the result and printed output

#         return jsonify({'result': result, 'stdout': stdout})
#     except Exception as e:
#         return jsonify({"error":str(e)}),400
#     finally:
#         sys.stdout = old_stdout

