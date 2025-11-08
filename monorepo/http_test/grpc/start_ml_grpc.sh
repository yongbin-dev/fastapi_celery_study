#!/bin/bash
# ML 서버를 gRPC 모드로 시작

cd packages/ml_server

export USE_GRPC="true"
export GRPC_PORT=50051

echo "🚀 ML 서버 시작 중..."
echo "USE_GRPC=$USE_GRPC"
echo "GRPC_PORT=$GRPC_PORT"

uv run uvicorn ml_app.main:app --port 8001
