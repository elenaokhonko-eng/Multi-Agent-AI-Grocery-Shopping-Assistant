# ------------------------------------------------------------
# Dockerfile – Ubuntu-based, Python 3.11, FastAPI Backend
# ------------------------------------------------------------
FROM python:3.11-slim

# 1. System-level dependencies for PostgreSQL & compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
        && rm -rf /var/lib/apt/lists/*

# 2. Set work directory
WORKDIR /app

# 3. Copy dependencies and install
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Copy source code
COPY packages /app/packages
COPY apps /app/apps
COPY tests /app/tests
COPY docs /app/docs

# 5. Install local editable packages
RUN pip install --no-cache-dir -e .

# 6. Create non-root user
ARG USERNAME=appuser
ARG UID=1000
ARG GID=1000
RUN groupadd --gid $GID $USERNAME \
    && useradd --uid $UID --gid $GID -m $USERNAME \
    && mkdir -p /app/data && chown -R $UID:$GID /app

USER $USERNAME

# 7. Expose FastAPI port
EXPOSE 8000

# 8. Start FastAPI backend
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
