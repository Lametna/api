FROM python:3.13-slim as python-base

# Configure Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# Prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

FROM python-base as builder-base
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy project requirement files here to ensure they will be cached
WORKDIR $PYSETUP_PATH
COPY pyproject.toml poetry.lock* ./

# Install runtime deps
RUN poetry install --only main --no-root

FROM python-base as development
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy poetry and venv into image
COPY --from=builder-base $POETRY_HOME $POETRY_HOME
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

WORKDIR $PYSETUP_PATH
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root

WORKDIR /app
COPY . .

# Set entrypoint or cmd
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
