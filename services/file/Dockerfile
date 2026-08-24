FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /data && chmod 777 /data

RUN cat > /usr/local/bin/filemanager.sh << 'EOF'

echo "[File Service] Started"
echo "[File Service] Data directory mounted at /data"

while true; do
sleep 3600
done
EOF

RUN chmod +x /usr/local/bin/filemanager.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD test -d /data || exit 1

CMD ["/usr/local/bin/filemanager.sh"]
