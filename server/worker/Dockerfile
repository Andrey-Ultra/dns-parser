FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    xvfb \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libasound2 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m camoufox fetch

COPY . .
CMD ["python", "-u", "worker.py"]