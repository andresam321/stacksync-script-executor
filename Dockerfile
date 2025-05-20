FROM python:3.11-slim

# Install required packages
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    clang \
    pkg-config \
    libprotobuf-dev \
    protobuf-compiler \
    libnl-route-3-dev \
    libcap-dev \
    libseccomp-dev \
    libprotobuf-c-dev \
    protobuf-c-compiler \
    ca-certificates \
    curl \
    flex \
    bison \
    gnupg \
    && rm -rf /var/lib/apt/lists/*


# Install nsjail
RUN git clone https://github.com/google/nsjail.git /opt/nsjail && \
    cd /opt/nsjail && \
    make

# Set working directory
WORKDIR /app

# Set Cloud Run flag
ENV CLOUD_RUN=1

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Expose Flask port
EXPOSE 8080

CMD ["python", "app.py"]
