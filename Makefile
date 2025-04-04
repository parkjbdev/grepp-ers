# AI를 활용하여 제작되었습니다.

.PHONY: dev install clean db test setup venv activate deactivate

# 기본 명령 (그냥 'make' 실행 시)
.DEFAULT_GOAL := help

# 개발 서버 실행
dev: db activate install
	# 개발 서버를 시작합니다
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 데이터베이스 실행
db:
	# DB 상태 확인
	@if docker compose ps | grep -q "database.*Up"; then \
		echo "🟢 DB가 이미 돌아가고 있네요!"; \
	else \
		echo "🔄 DB를 시작할게요..."; \
		docker compose up --build -d database; \
		echo "⏳ DB가 완전히 준비될 때까지 잠시만 기다려주세요..."; \
		until docker exec database pg_isready -U postgres &>/dev/null; do \
			echo "⏳ DB가 아직 준비 중이에요... 조금만 더 기다려주세요"; \
			sleep 3; \
		done; \
		echo "✅ DB 준비 완료! 이제 사용할 수 있어요"; \
	fi

# 가상환경 생성
venv:
	@if [ -d ".venv" ]; then \
		echo "ℹ️ 가상환경이 이미 있네요. 새로 만들지 않을게요"; \
	else \
		echo "🔨 새 가상환경을 만들고 있어요..."; \
		python -m venv .venv; \
		echo "✨ 가상환경 생성 완료!"; \
	fi

# 가상환경 활성화
activate: venv
	@if [ -n "$$VIRTUAL_ENV" ]; then \
		echo "🟢 가상환경이 이미 활성화되어 있어요"; \
	else \
		. .venv/bin/activate || (echo "⚠️ 가상환경 활성화 중 문제가 발생했어요"; exit 1); \
		echo "🔌 가상환경 활성화 완료!"; \
	fi

# 가상환경 비활성화
deactivate:
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "ℹ️ 가상환경이 이미 꺼져있거나 활성화된 적이 없어요"; \
	else \
		deactivate; \
		echo "🔌 가상환경 비활성화 완료!"; \
	fi

# 의존성 설치
install: activate
	@if [ -n "$$VIRTUAL_ENV" ] && pip freeze | grep -q "fastapi"; then \
		echo "📦 필요한 패키지들이 이미 설치되어 있네요"; \
	else \
		echo "📥 필요한 패키지들을 설치하고 있어요..."; \
		pip install -r requirements.txt; \
		echo "✅ 패키지 설치 완료!"; \
	fi

# 개발 환경 전체 초기 설정
setup: install
	@echo "🎉 모든 개발 환경 설정이 완료되었어요! 이제 코딩을 시작해보세요"

# 테스트 실행
test: db activate
	@echo "🧪 테스트를 실행할게요..."
	pytest
	@echo "✅ 테스트 완료!"

# 모든 컨테이너 종료 및 임시 파일 정리
clean:
	@if docker compose ps | grep -q "Up"; then \
		echo "🧹 실행 중인 컨테이너들을 정리하고 있어요..."; \
		docker compose down -v; \
		echo "✅ 모든 컨테이너가 종료되었어요"; \
	else \
		echo "ℹ️ 실행 중인 컨테이너가 없네요"; \
	fi

	@echo "🧹 캐시와 임시 파일들을 정리하고 있어요..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "✨ 모든 정리가 끝났어요. 깔끔하네요!"

# 프로덕션 모드로 전체 스택 실행
prod:
	@if docker compose ps | grep -q "Up"; then \
		echo "🔄 일부 컨테이너가 이미 실행 중이네요. 깔끔하게 재시작할게요"; \
		docker compose down; \
	fi
	@echo "🚀 프로덕션 스택을 시작하고 있어요..."
	docker compose up --build -d
	@echo "✅ 프로덕션 환경이 준비되었어요!"

# 도움말
help:
	@echo "🛠️  사용할 수 있는 명령어들이에요:"
	@echo ""
	@echo "  🔧 개발 환경 설정"
	@echo "  ----------------"
	@echo "  make setup        - 한번에 모든 개발 환경을 세팅해요"
	@echo "  make venv         - 파이썬 가상환경만 만들어요"
	@echo "  make activate     - 가상환경을 켜요 (없으면 만들어요)"
	@echo "  make install      - 필요한 패키지들을 설치해요"
	@echo ""
	@echo "  🚀 개발 & 테스트"
	@echo "  ----------------"
	@echo "  make dev          - 개발 서버를 실행해요 (DB와 가상환경도 함께 준비해요)"
	@echo "  make db           - 데이터베이스만 실행해요"
	@echo "  make test         - 테스트를 돌려봐요"
	@echo ""
	@echo "  🧹 정리 & 기타"
	@echo "  ----------------"
	@echo "  make deactivate   - 가상환경을 끄고 싶을 때 사용해요"
	@echo "  make clean        - 컨테이너와 임시 파일들을 모두 정리해요"
	@echo "  make prod         - 프로덕션 모드로 모든 서비스를 실행해요"
	@echo ""
	@echo "😎 주로 쓰는 명령어는 'make dev'에요!"