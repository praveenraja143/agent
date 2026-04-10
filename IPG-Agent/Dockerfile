FROM python:3.11-slim

# Install Chromium and its dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    chromium \
    chromium-driver \
    --no-install-recommends \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set binary paths for Selenium
ENV CHROMIUM_PATH=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directory for profile
RUN mkdir -p data/chrome_profile

EXPOSE 10000
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "--workers", "1", "--threads", "4", "server:app"]
