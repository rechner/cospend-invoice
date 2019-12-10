#!/bin/bash
app="cospend-invoice"
docker build -t ${app} .
docker run -d -p 5050:80 \
    --name=${app} \
    -v $PWD:/app \
    -e API_URL=https://somesite.url/apps/cospend/api/projects/project/password \
    ${app}
