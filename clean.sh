#!/bin/bash

# 1. 컨테이너 종료
if docker compose ps | grep -q "Up"; then
  echo "🧹 실행 중인 컨테이너를 종료합니다..."
  docker compose down -v
  echo "✅ 종료 완료!"
else
  echo "ℹ️ 실행 중인 컨테이너가 없어요"
fi

# 2. 임시 파일 정리
echo "🧹 pycache 및 임시 파일 정리 중..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
echo "✨ 정리 완료! 깔끔해졌어요"

# 3. 가상환경 삭제
if [ -d ".venv" ]; then
  echo "🧹 가상환경을 삭제합니다..."
  rm -rf .venv
  echo "✅ 가상환경 삭제 완료!"
else
  echo "ℹ️ 가상환경이 없어요"
fi