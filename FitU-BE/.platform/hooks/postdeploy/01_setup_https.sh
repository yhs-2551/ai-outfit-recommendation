#!/bin/bash
set -e

DOMAIN="fitu-backend.duckdns.org"
EMAIL="yhsdeveloper8746@gmail.com"

echo "====== HTTPS 설정 스크립트 시작 ======"

 if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
  echo ">>> Let's Encrypt 인증서 새로 발급 시도..."
  certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect
else
  echo ">>> Let's Encrypt 인증서 갱신 시도..."
  certbot renew --quiet
fi

echo ">>> Cron 작업 설정..."
echo "0 3 * * 1 root certbot renew --quiet" > /etc/cron.d/certbot-renew
echo "====== 스크립트 성공적으로 완료 ======"