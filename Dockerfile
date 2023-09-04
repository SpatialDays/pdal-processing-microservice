FROM pdal/pdal:sha-d0bb6358

WORKDIR /app
COPY requirements.txt /app
RUN python3 -m pip3 install -r requirements.txt
COPY . /app



EXPOSE 5000
CMD ["python3", "app.py"]
