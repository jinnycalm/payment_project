from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routers import benefits

app = FastAPI()

# CORS 설정으로 보안 환경 구성(React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost"], # 허용 URL
    allow_credentials=True,     # 쿠키, 인증 정보 허용
    allow_methods=["*"],        # 모든 HTTP 메서드 허용 (GET, POST, PUT, DELETE 등)
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(benefits.router, prefix="/api/benefits", tags=["benefits"])