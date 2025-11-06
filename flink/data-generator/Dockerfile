FROM python:3.11-slim

WORKDIR /app

# Copy the data generator script
COPY generator.py /app/
COPY requirements.txt /app/

# Install dependencies (if any)
RUN pip install --no-cache-dir -r requirements.txt

# Expose socket port
EXPOSE 9999

# Run the generator
CMD ["python", "generator.py"]
