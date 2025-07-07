FROM nginx:latest

# Add a simple CORS-enabled config
RUN echo 'server {\n\
    listen 80;\n\
    location / {\n\
        root /usr/share/nginx/html;\n\
        index index.html index.htm;\n\
        add_header Access-Control-Allow-Origin "*" always;\n\
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS, PUT, DELETE" always;\n\
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept" always;\n\
        if ($request_method = OPTIONS) {\n\
            add_header Access-Control-Allow-Origin "*";\n\
            add_header Access-Control-Allow-Methods "GET, POST, OPTIONS, PUT, DELETE";\n\
            add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept";\n\
            add_header Content-Length 0;\n\
            add_header Content-Type "text/plain charset=UTF-8";\n\
            return 204;\n\
        }\n\
    }\n\
}' > /etc/nginx/conf.d/default.conf

COPY vector/out/ /usr/share/nginx/html