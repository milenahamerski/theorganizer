server {
    listen 443 ssl;
    server_name theorganizer.com www.theorganizer.com;

    ssl_certificate /etc/ssl/certs/theorganizer.crt;
    ssl_certificate_key /etc/ssl/private/theorganizer.key;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name theorganizer.com www.theorganizer.com;
    return 301 https://$host$request_uri;
}
