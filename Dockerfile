FROM ubuntu:jammy-20230816

# Install utilities and PDAL
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    pdal \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
COPY . /app
CMD ["python3", "app.py"]
