FROM python:3.11-slim

WORKDIR /app

# System deps for vedic-astrology
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-venv gcc libc-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Copy all files
COPY . .

# Setup vedic-astrology environment
RUN cd /app/skills/vedic-astrology && python3 scripts/setup_env.py

# Install runtime deps for server
RUN /app/skills/vedic-astrology/venv/bin/pip install timezonefinder

EXPOSE 8000

ENV PYTHONPATH=/app/skills/vedic-astrology/scripts

CMD ["/app/skills/vedic-astrology/venv/bin/python", "server.py"]
