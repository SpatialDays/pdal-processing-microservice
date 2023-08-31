import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import subprocess
from celery import Celery

app = Flask(__name__)
CORS(app)

# Configure Celery
app.config["CELERY_BROKER_URL"] = os.environ.get(
    "CELERY_BROKER_URL", "redis://redis:6379/0"
)
app.config["CELERY_RESULT_BACKEND"] = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://redis:6379/0"
)

celery = Celery(app.name, broker=app.config["CELERY_BROKER_URL"])
celery.conf.update(app.config)


@app.route("/pdal-info", methods=["POST"])
def pdal_info():
    data = request.get_json()

    if "input_file" not in data or "input_file_download_url" not in data:
        return jsonify({"error": "Missing required parameters."}), 400

    input_file_download_url = data.get("input_file_download_url")
    if input_file_download_url:
        if not os.path.exists(f"./data/{data.get('input_file')}"):
            response = requests.get(input_file_download_url)
            with open(f"./data/{data.get('input_file')}", "wb") as f:
                f.write(response.content)

    input_file = data.get("input_file")

    cmd = ["pdal", "info", f"./data/{input_file}"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()

    parsed = json.loads(stdout)
    print(json.dumps(parsed, indent=4))
    return jsonify({"message": stdout}), 200


@app.route("/rasterize-pc", methods=["POST"])
def rasterize_pc():
    data = request.get_json()

    if not all(k in data for k in ("input_file", "output_file", "resolution")):
        return jsonify({"error": "Missing required parameters."}), 400

    if data.get("input_file_download_url"):
        if not os.path.exists(f"./data/{data.get('input_file')}"):
            response = requests.get(data.get("input_file_download_url"))
            with open(f"./data/{data.get('input_file')}", "wb") as f:
                f.write(response.content)

    input_file = data["input_file"]
    output_file = data["output_file"]

    try:
        resolution = float(data["resolution"])
    except ValueError:
        return jsonify({"error": "Resolution should be a number."}), 400

    # This will now dispatch the task to Celery asynchronously
    task = run_pdal_command.delay(input_file, output_file, resolution)
    return jsonify({"message": "Task dispatched", "task_id": task.id}), 202


@app.route("/task/<task_id>", methods=["GET"])
def check_task_status(task_id):
    task = celery.AsyncResult(task_id)
    return jsonify({"task_status": task.state, "result": task.result}), 200


@celery.task(bind=True)
def run_pdal_command(self, input_file, output_file, resolution):
    pipeline_str = construct_pipeline(input_file, output_file, resolution)
    cmd = ["pdal", "pipeline", "-s"]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
    process.communicate(pipeline_str)


def construct_pipeline(input_file, output_file, resolution):
    pipeline = {
        "pipeline": [
            f"/data/{input_file}",
            {
                "type": "writers.gdal",
                "filename": f"/data/{output_file}",
                "output_type": "mean",
                "resolution": resolution,
            },
        ]
    }
    return json.dumps(pipeline)


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("APP_DEBUG", "True") == "True",
        host=os.environ.get("APP_HOST", "0.0.0.0"),
        port=int(os.environ.get("APP_PORT", 5000)),
    )
