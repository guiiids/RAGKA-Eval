FROM python:3.11-slim-bullseye

WORKDIR /app

# Pre-copy only requirements to leverage layer caching
COPY requirements.txt .

RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends gcc && \
	pip install --no-cache-dir -r requirements.txt && \
	apt-get purge -y --auto-remove gcc && \
	rm -rf /var/lib/apt/lists/*

# Copy the rest of the app
COPY . .

EXPOSE 8000

ENTRYPOINT ["gunicorn", "main:app", "--bind", "0.0.0.0:8000"]
