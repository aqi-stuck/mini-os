FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /logs && chmod 777 /logs

RUN cat > /usr/local/bin/logger.sh << 'EOF'

LOG_FILE="/logs/system.log"

echo "[Logger Service] Started at $(date)" >> $LOG_FILE
echo "[Logger Service] Listening for logs at $(hostname)" >> $LOG_FILE

{
echo "=== System Information ==="
echo "Hostname: $(hostname)"
echo "Time: $(date)"
echo "Uptime: $(uptime)"
echo ""
} >> $LOG_FILE

while true; do
sleep 60
echo "[$(date +'%Y-%m-%d %H:%M:%S')] Logger heartbeat" >> $LOG_FILE
done
EOF

RUN chmod +x /usr/local/bin/logger.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD test -d /logs || exit 1

CMD ["/usr/local/bin/logger.sh"]
