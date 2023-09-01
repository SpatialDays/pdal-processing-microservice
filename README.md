# PDAL Processing Server

A Flask server integrated with Celery for rasterizing `.laz` files (other pipelines can be used in future)

## Setup and Running

1. Build and run using Docker Compose:
[app.py](app.py)
```bash
docker-compose up --build
```

2. Send a `.laz` file to turn into a TIFF: 
```bash
curl -X POST -H "Content-Type: application/json" \
-d '{"input_file":"<input_filename>", "output_file":"<output_filename>", "resolution":<resolution_value>}' \
http://localhost:5000/process-pdal
```
   
[app.py](app.py)
3. Check the status of the task:

```bash 
curl http://localhost:5000/task/<task_id>
```

## Downloading and uploading files
In order to facilitate the download and upload of the files, the blob_helper_mapping_utility is used.
See more details at: https://pypi.org/project/blob-mounting-helper-utility/ 


## Environment variables
| Variable | Description | Default              |
|----------|-------------|----------------------|
|APP_HOST| Host of the server |
|APP_PORT| Port of the server | 5000                 |
|APP_DEBUG| Debug mode | True                 |
| CELERY_BROKER_URL | URL of the broker | redis://redis:6379/0 |
| CELERY_RESULT_BACKEND | URL of the backend | redis://redis:6379/0 |
| AZURE_STORAGE_ACCOUNT_KEY| Azure storage account key | None                 |
| BLOB_MOUNTING_CONFIGURATIONS_JSON_PATH| Path to the JSON file containing the blob mounting configurations | None                 |