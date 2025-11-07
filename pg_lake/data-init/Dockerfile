FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir trino pandas pyarrow

COPY initialize_data.py /app/

CMD ["python", "/app/initialize_data.py"]

