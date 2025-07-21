#!/bin/bash
source .env
uv run --env-file .env main.py index.html
npx staticrypt index.html -p $STATICRYPT_PASSWORD --short
cp encrypted/index.html index.html
rm -rf encrypted
