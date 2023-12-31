import logging

logging.basicConfig(level=logging.DEBUG)
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import subprocess
from celery import Celery
from blob_helper_utility import blob_mapping_utility

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
@app.route("/pdal-info/", methods=["POST"])
def pdal_info():
    data = request.get_json()

    if "input_file" not in data:
        return jsonify({"error": "Missing required parameters."}), 400

    input_file_download_url = data.get("input_file")
    # remove sas token from input_file_download_url
    if "?" in input_file_download_url:
        input_file_download_url = input_file_download_url.split("?")[0]
    blob_mapping_utility.download_blob(input_file_download_url)
    input_file = blob_mapping_utility.get_mounted_filepath_from_url(input_file_download_url)
    cmd = ["pdal", "info", input_file]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    blob_mapping_utility.cleanup_files()

    parsed = json.loads(stdout)
    print(json.dumps(parsed, indent=4))
    return jsonify({"message": stdout}), 200


@app.route("/rasterize-pc", methods=["POST"])
@app.route("/rasterize-pc/", methods=["POST"])
def rasterize_pc():
    data = request.get_json()

    if not all(k in data for k in ("input_file", "resolution")):
        return jsonify({"error": "Missing required parameters."}), 400

    input_file = data["input_file"]

    try:
        resolution = float(data["resolution"])
    except ValueError:
        return jsonify({"error": "Resolution should be a number."}), 400

    # This will now dispatch the task to Celery asynchronously
    task = run_pdal_command.delay(input_file, resolution)
    return jsonify({"message": "Task dispatched", "task_id": task.id}), 202


@app.route("/task/<task_id>", methods=["GET"])
def check_task_status(task_id):
    task = celery.AsyncResult(task_id)
    return jsonify({"task_status": task.state, "result": task.result}), 200


@celery.task(bind=True)
def run_pdal_command(self, input_file, resolution):
    if "?" in input_file:
        input_file = input_file.split("?")[0]
    blob_mapping_utility.download_blob(input_file)
    input_file = blob_mapping_utility.get_mounted_filepath_from_url(input_file)
    output_file = input_file.replace(".laz", ".tif")
    pipeline_str = construct_pipeline(input_file, output_file, resolution)
    cmd = ["pdal", "pipeline", "-s"]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
    process.communicate(pipeline_str)
    blob_mapping_utility.upload_blob(output_file)
    # cleanup here
    blob_mapping_utility.cleanup_files()


def construct_pipeline(input_file, output_file, resolution):
    pipeline = {
        "pipeline": [
            f"{input_file}",
            {
                "type": "writers.gdal",
                "filename": f"{output_file}",
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
