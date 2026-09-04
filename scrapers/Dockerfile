# SkillSync Scraper Service Dockerfile
# Builds a container with Python + Chromium + ChromeDriver for Selenium scrapers

# Use full Python image (not slim) because we need system packages for Chromium
FROM python:3.11

# Set working directory
WORKDIR /app

# Install Chromium and ChromeDriver for Selenium
# These are needed by the 3 Selenium-based scrapers (Rozee, Internee, Devpost)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome path for Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the scraper source code
COPY scrapers/ ./scrapers/

# Create a non-root user for security
RUN useradd --create-home appuser
USER appuser

# Run the scraper service
# -m flag runs the module as a script
CMD ["python", "-m", "scrapers.main"]
