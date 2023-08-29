import os
from flask import Flask, request, jsonify
import json
import subprocess
from celery import Celery

app = Flask(__name__)

# Configure Celery
app.config["CELERY_BROKER_URL"] = os.environ.get(
    "CELERY_BROKER_URL", "redis://redis:6379/0"
)
app.config["CELERY_RESULT_BACKEND"] = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://redis:6379/0"
)

celery = Celery(app.name, broker=app.config["CELERY_BROKER_URL"])
celery.conf.update(app.config)


@app.route("/process-pdal", methods=["POST"])
def process_pdal():
    data = request.get_json()

    if not all(k in data for k in ("input_file", "output_file", "resolution")):
        return jsonify({"error": "Missing required parameters."}), 400

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
