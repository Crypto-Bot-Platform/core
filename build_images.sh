#!/bin/bash

echo 'Building images for exchanges...'
docker build -f exchange/public/deployment/Dockerfile.bittrex -t tsboris/cbp-bittrex-public:latest .
docker push tsboris/cbp-bittrex-public:latest
docker build -f exchange/public/deployment/Dockerfile.binanceus -t tsboris/cbp-binanceus-public:latest .
docker push tsboris/cbp-binanceus-public:latest
docker build -f exchange/public/deployment/Dockerfile.ftx -t tsboris/cbp-ftx-public:latest .
docker push tsboris/cbp-ftx-public:latest

echo 'Building global market image...'
docker build -f global-market/deployment/Dockerfile -t tsboris/cbp-global-market:latest .
docker push tsboris/cbp-global-market:latest

echo 'Building elastic recorder...'
docker build -f recorder/deployment/Dockerfile.elastic -t tsboris/cbp-elastic-recorder:latest .
docker push tsboris/cbp-elastic-recorder:latest

echo 'Building timescale recorder...'
docker build -f recorder/deployment/Dockerfile.timescale -t tsboris/cbp-timescale-recorder:latest .
docker push tsboris/cbp-timescale-recorder:latest
