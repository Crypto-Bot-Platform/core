#!/bin/bash

echo 'Building images for exchanges...'
docker build -f exchange/public/deployment/Dockerfile.bittrex -t tsboris/cbp-bittrex-public:latest .
docker push tsboris/cbp-bittrex-public:latest

echo 'Building global market image...'
docker build -f global-market/deployment/Dockerfile -t tsboris/cbp-global-market:latest .
docker push tsboris/cbp-global-market:latest

echo 'Building elastic recorder...'
docker build -f recorder/deployment/Dockerfile.elastic -t tsboris/cbp-elastic-recorder:latest .
docker push tsboris/cbp-elastic-recorder:latest
