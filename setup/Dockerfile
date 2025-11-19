FROM python:3.11-slim

WORKDIR /app

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true

# Install system dependencies for LibreOffice and PDF processing
# Fix Java certificate issue by pre-configuring debconf
RUN echo "ca-certificates-java ca-certificates-java/truststore select" | debconf-set-selections || true && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        libreoffice \
        libreoffice-writer \
        libreoffice-impress \
        poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY server/requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt


# Copy the rest of the application
COPY server/ /app

RUN mkdir -p /app/uploads/aividfromppt/tts
RUN mkdir -p /app/uploads/aividfromppt/videos
RUN touch /app/uploads/aividfromppt/videos/test.mp4
RUN chmod -R 755 /app/uploads/aividfromppt

# Expose the port
ENV FASTAPI_PORT=8201
EXPOSE $FASTAPI_PORT

# Run the application
CMD uvicorn main:app --host 0.0.0.0 --port ${FASTAPI_PORT} --loop asyncio --reload
