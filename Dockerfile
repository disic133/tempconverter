# TempConverter — OCI image
FROM python:3.12-slim

# Task 1a: update ALL OS packages as part of the build
RUN apt-get update && apt-get -y upgrade \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Task 1c: install all required Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# copy the application source
COPY . .

# run as a non-root user (least privilege; also works under OpenShift's restricted SCC)
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Task 1b: expose port 5000/TCP
EXPOSE 5000/tcp

# Task 1d: correct command to start the Flask application
ENV FLASK_APP=app.py
CMD ["python", "app.py"]
