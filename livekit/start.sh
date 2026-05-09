#!/bin/sh
cat > /tmp/livekit.yaml <<EOF
port: 7880
log_level: info
bind_addresses:
  - "0.0.0.0"

rtc:
  tcp_port: 7881
  port_range_start: 50000
  port_range_end: 60000
  use_external_ip: true

redis:
  address: redis:6379
  password: "${REDIS_PASSWORD}"
  db: 0

turn:
  enabled: true
  domain: livekit.ether.care
  tls_port: 5349

keys:
  "${LIVEKIT_API_KEY}": "${LIVEKIT_API_SECRET}"
EOF
exec livekit-server --config /tmp/livekit.yaml