FROM ubuntu:22.04

# Update packages
RUN apt-get update && apt-get install -y \
    bash \
    nano \
    vim \
    curl \
    wget \
    git \
    build-essential \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash minios

# Set working directory
WORKDIR /home/minios

# Default command
CMD ["/bin/bash"]
