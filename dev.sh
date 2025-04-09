#!/bin/bash

# 1. DB 실행
if docker compose ps | grep -q "database.*Up"; then
  echo "🟢 DB가 이미 돌아가고 있어요!"
else
  echo "🔄 DB를 실행할게요..."
  docker compose up --build -d database
  echo "⏳ DB 준비 중..."
  until docker exec database pg_isready -U postgres &>/dev/null; do
    echo "⏳ 아직 준비 중... 조금만 기다려주세요"
    sleep 3
  done
  echo "✅ DB 준비 완료!"
fi

# 2. 가상환경 체크 및 생성
if [ ! -d ".venv" ]; then
  echo "🔨 가상환경이 없네요. 새로 만들게요..."
  python3 -m venv .venv
  echo "✅ .venv 생성 완료!"
fi

# 3. 가상환경 활성화
source .venv/bin/activate
echo "🔌 가상환경 활성화 완료!"

# 4. 의존성 설치
if pip freeze | grep -q "fastapi"; then
  echo "📦 의존성은 이미 설치돼 있어요!"
else
  echo "📥 requirements.txt에 따라 패키지를 설치할게요..."
  pip install -r requirements.txt
  echo "✅ 패키지 설치 완료!"
fi

# 5. 서버 실행
echo "🚀 서버를 실행합니다!"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000