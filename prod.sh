#!/bin/bash

# 1. 기존 컨테이너 종료
if docker compose ps | grep -q "Up"; then
  echo "🔄 실행 중인 컨테이너가 있어요. 재시작할게요!"
  docker compose down
fi

# 2. 전체 서비스 실행
echo "🚀 프로덕션 스택을 시작합니다..."
docker compose up --build -d
echo "✅ 모든 서비스가 실행 중이에요!"