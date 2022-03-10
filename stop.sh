#!/bin/bash

kubectl delete deployment cbp-binanceus-public
kubectl delete deployment cbp-bittrex-public
kubectl delete deployment cbp-ftx-public

kubectl delete deployment global-market
kubectl delete deployment elastic-recorder
kubectl delete deployment timescale-recorder

