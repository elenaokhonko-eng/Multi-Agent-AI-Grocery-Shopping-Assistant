# ------------------------------------------------------------
# Dockerfile – Ubuntu‑based, Python 3.11, minimal image
# ------------------------------------------------------------
FROM python:3.11-slim

# 1. System‑level deps that some Python packages need
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
        && rm -rf /var/lib/apt/lists/*

# 2. Create a non‑root user (optional but good practice)
ARG USERNAME=appuser
ARG UID=1000
ARG GID=1000
RUN groupadd --gid $GID $USERNAME \
    && useradd --uid $UID --gid $GID -m $USERNAME

# 3. Set work directory
WORKDIR /app

# 4. Copy only the source code (ignore .venv, .git, __pycache__, etc.)
# Ensure the log directory exists and is writable by the non‑root user (or root)
RUN mkdir -p /app/data && chmod -R 777 /app/data

# Ensure the log directory exists and is writable by the non‑root user
RUN mkdir -p /app/data && chown $UID:$GID /app/data
RUN touch /app/data/scraper.log && chown $UID:$GID /app/data/scraper.log

# 5. Install Python dependencies.
#    If you have a requirements.txt file, you can replace the inline list.
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 6. Switch to the non‑root user
USER $USERNAME

# 7. Default command – runs the test that validates the Singapore pipeline.
#    Adjust if you want to start the API server instead.
CMD ["python", "Web_scraper/test_singapore_pipeline.py"]
