# GREPP ERS (Exam Reservation System)

## 실행방법

### Docker Compose 활용 (Recommended)
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
