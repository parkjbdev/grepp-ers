# GREPP ERS (Exam Reservation System)

## 실행방법

### Makefile 활용

- 빠른 실행을 위해 Makefile을 제작해두었습니다.
- `make help`을 통해 사용법을 확인할 수 있습니다.
- `make dev`를 통해 개발환경을 실행할 수 있습니다.
- `make prod`를 통해 배포환경을 실행할 수 있습니다.
- 문제가 있을 경우, `make clean`을 통해 캐시를 삭제하고 다시 시도할 수 있습니다.
- 문제가 지속될 경우, docker-compose를 통해 직접 실행할 수 있습니다.

### Docker Compose 활용

#### Launch Production Build

```sh
docker compose down -v # Just to be sure...
docker compose up --build -p grepp-ers-dev -d
```

#### Launch Development Build

```shell
docker compose down -v # Just to be sure...
docker compose -f docker-compose.yml -f docker-compose.dev.yml -p grepp-ers-dev up -d --build
```

## API 문서

API 문서는 FastAPI에서 제공하는 Swagger UI를 통해 확인할 수 있습니다.

Swagger를 통해 API를 테스트할 수 있습니다.

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 기본 계정

테스트를 위한 기본 User와 Admin 계정은 아래와 같습니다.

- User
    - ID: `user`
    - Password: `password`
- Admin
    - ID: `admin`
    - Password: `password`
    - admin의 경우, 권한을 DB에서 직접 수정해야 합니다.

### 직접 실행

#### 1. Launch PostgreSQL DB

Launch your own database and set variables in .env file or...

```shell
# Use Docker
docker compose -f docker-compose.yml -p grepp-ers up -d database
```

#### 2. Install Dependencies and Launch FastAPI Server

```shell
python -m venv .venv
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt
# For development
fastapi dev

# For release
# fastapi run
```

## 요구사항

### 1. 예약 조회, 신청

- [x] 고객은 예약 신청이 가능한 시간과 인원을 알 수 있습니다.

- [x] 예약은 시험 시작 3일 전까지 신청 가능하며, 동 시간대에 최대 5만명까지 예약할 수 있습니다. 이때, 확정되지 않은 예약은 5만명의 제한에 포함되지 않습니다. 예약에는 시험 일정과 응시 인원이
포함되어야 합니다.
(예를 들어, 4월 15일 14시부터 16시까지 이미 3만 명의 예약이 확정되어 있을 경우, 예상 응시 인원이 2만명 이하인 추가 예약 신청이 가능합니다.)

- [x] 고객은 본인이 등록한 예약만 조회할 수 있습니다.

- [x] 어드민은 고객이 등록한 모든 예약을 조회할 수 있습니다.

### 2. 예약 수정 및 확정

- [x] 예약 확정: 고객의 예약 신청 후, 어드민이 이를 확인하고 확정을 통해 예약이 최종적으로 시험 운영 일정에 반영됩니다. 확정되지 않은 예약은 최대 인원 수 계산에 포함되지 않습니다.

- [x] 고객은 예약 확정 전에 본인 예약을 수정할 수 있습니다.

- [x] 어드민은 모든 고객의 예약을 확정할 수 있습니다.

- [x] 어드민은 고객 예약을 수정할 수 있습니다.

### 3. 예약 삭제

- [x] 고객은 확정 전에 본인 예약을 삭제할 수 있습니다.

- [x] 어드민은 모든 고객의 예약을 삭제할 수 있습니다.

## 기술스택

- Python 3.13.2
- FastAPI
- PostgreSQL
- asyncpg

## 주요파일

### DB (`database` 폴더)

- `database/init-scripts`은 도커가 DB를 초기화할 때 사용하는 SQL 스크립트입니다.
    - db user 및 db extension을 shell 파일을 통해 설정합니다. db user에 관한 정보는 `.env`와 `docker-compose.yml`에 들어있습니다.
    - 테이블 선언에 관한 정보가 sql 파일에 들어있습니다.

### SERVER (`app` 폴더)

- `app/dependencies/config.py` 에서 Dependency Injection 에 관한 클래스 정보를 설정합니다.
- MVC 구조를 활용하였으며, 이를 이루는 가장 주요한 기반은 `app/repositories`, `app/services`, `app/controllers`로 나누어져 있습니다.