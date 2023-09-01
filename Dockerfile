FROM pdal/pdal:sha-d0bb6358

WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
COPY . /app



EXPOSE 5000
CMD ["python", "app.py"]
