FROM ubuntu:latest

# Install utilities and PDAL
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    pdal \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app
ADD . /app

RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 5000
CMD ["python", "app.py"]
