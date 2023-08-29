# PDAL Processing Server

A Flask server integrated with Celery for rasterizing `.laz` files (other pipelines can be used in future)

## Setup and Running

1. Build and run using Docker Compose:

```bash
docker-compose up --build
```

2. Send a `.laz` file to turn into a TIFF: 
```bash
curl -X POST -H "Content-Type: application/json" \
-d '{"input_file":"<input_filename>", "output_file":"<output_filename>", "resolution":<resolution_value>}' \
http://localhost:5000/process-pdal
```
   

3. Check the status of the task:

```bash 
curl http://localhost:5000/task/<task_id>
```
