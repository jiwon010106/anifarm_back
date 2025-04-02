from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import jwt
from pydantic import BaseModel, EmailStr
import os
from dotenv import load_dotenv
import pandas as pd
import uvicorn
import subprocess
import json
from enum import Enum
import logging
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import secrets
import bcrypt
from fastapi.responses import JSONResponse
import httpx
import random
import requests
from weather import get_price_data, get_satellite_data
import threading
import sys
import random
from youtube import youtube_router
from chatbot import process_query, ChatMessage, ChatRequest, ChatCandidate, ChatResponse
from Crawler.crawler_endpoint import router as crawler_router
from image_classifier import classifier, ImageClassificationResponse
from PIL import Image
import io
import aiohttp
from services.comment_service import CommentService
from services.write_service import WriteService
from pathlib import Path
from swagger import custom_openapi
from fastapi.responses import FileResponse
from fastapi import Body
from growthcalendar import GrowthCalendar
from utils.apiUrl import fetchWeatherData

from young_api import get_youth_list, get_youth_detail, get_edu_list, ContentType, SCode

from support import get_support_programs, get_support_detail, get_education_programs, get_education_detail


app = FastAPI(
    title="농산물 가격 예측 API",
    description="농산물 가격 예측 및 커뮤니티 서비스를 위한 API",
    version="1.0.0",
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.openapi = lambda: custom_openapi(app)

# Load environment variables
load_dotenv()

# 도시 매핑 정의
KOREAN_CITIES = {
    "서울": "Seoul",
    "부산": "Busan",
    "대구": "Daegu",
    "인천": "Incheon",
    "광주": "Gwangju",
    "대전": "Daejeon",
    "울산": "Ulsan",
    "제주": "Jeju"
}

class Comment(BaseModel):
    comment_id: int
    post_id: int
    user_id: str
    content: str
    created_at: datetime

class CommentCreate(BaseModel):
    post_id: int
    content: str
    user_email: str
    parent_id: Optional[int] = None

class CommentUpdate(BaseModel):
    content: str

# Backend API URL
BACKEND_URL = "http://localhost:8000"

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# 데이터베이스 설정
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
JWT_SECRET = os.getenv("JWT_SECRET")

if not all([DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT, JWT_SECRET]):
    raise ValueError("필수 환경 변수가 설정되지 않았습니다.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# JWT 설정
SECRET_KEY = JWT_SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60

# 모델 정의
class Token(BaseModel):
    access_token: str
    token_type: str

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(BaseModel):
    email: str
    password: str
    birth_date: Optional[str] = None

# 인증 관련 함수들
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401)
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401)


@app.get("/")
async def root():
    return {"message": "농산물 가격 정보 API"}

@app.get("/cities")
async def get_cities():
    """사용 가능한 도시 목록을 반환합니다."""
    return {
        "success": True,
        "data": {
            "cities": list(KOREAN_CITIES.keys()),
            "mapping": KOREAN_CITIES
        },
        "message": "도시 목록을 성공적으로 가져왔습니다"
    }

@app.get("/weather")
async def get_weather(city: str):
    try:
        if not city:
            raise ValueError("도시명이 입력되지 않았습니다")
            
        if city not in KOREAN_CITIES and city not in KOREAN_CITIES.values():
            raise ValueError("지원하지 않는 도시입니다")
            
        from utils.apiUrl import fetchWeatherData
        weather_data = await fetchWeatherData(city)
        
        return {
            "success": True,
            "data": weather_data,
            "message": "날씨 데이터를 성공적으로 가져왔습니다"
        }
    except Exception as e:
        print(f"Weather API Error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "날씨 데이터를 가져오는데 실패했습니다"
        }

# 이미지 분류 엔드포인트들
@app.post("/kiwi_predict", response_model=ImageClassificationResponse)
async def kiwi_predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        result = await classifier.classify_kiwi(image)
        return result
    except Exception as e:
        logger.error(f"키위 예측 처리 오류: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/chamoe_predict", response_model=ImageClassificationResponse)
async def chamoe_predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        result = await classifier.classify_chamoe(image)
        return result
    except Exception as e:
        logger.error(f"참외 예측 처리 오류: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/plant_predict", response_model=ImageClassificationResponse)
async def plant_predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        result = await classifier.classify_plant(image)
        return result
    except Exception as e:
        logger.error(f"식물 분류 처리 오류: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/strawberry_predict", response_model=ImageClassificationResponse)
async def strawberry_predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        result = await classifier.classify_strawberry(image)
        return result
    except Exception as e:
        logger.error(f"딸기 예측 처리 오류: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
   
@app.post("/potato_predict", response_model=ImageClassificationResponse)
async def potato_predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        result = await classifier.classify_potato(image)
        return result
    except Exception as e:
        logger.error(f"감자 예측 처리 오류: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tomato_predict", response_model=ImageClassificationResponse)
async def tomato_predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))    
        result = await classifier.classify_tomato(image)
        return result
    except Exception as e:
        logger.error(f"토마토 예측 처리 오류: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
   
@app.post("/apple_predict", response_model=ImageClassificationResponse)
async def apple_predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        result = await classifier.classify_apple(image)
        return result
    except Exception as e:
        logger.error(f"사과 예측 처리 오류: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/grape_predict", response_model=ImageClassificationResponse)
async def grape_predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        result = await classifier.classify_grape(image)
        return result
    except Exception as e:
        logger.error(f"포도 예측 처리 오류: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/corn_predict", response_model=ImageClassificationResponse)
async def corn_predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        result = await classifier.classify_corn(image)
        return result
    except Exception as e:
        logger.error(f"옥수수 예측 처리 오류: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/satellite")
async def get_satellite():
    """한반도 위성 구름 이미지 정보를 가져옵니다."""
    try:
        result = get_satellite_data()
        if result is None:
            raise HTTPException(status_code=500, detail="위성 데이터를 가져오는데 실패했습니다")
        
        # 응답 형식 수정
        return {
            "success": True,
            "data": result.get("response", {}).get("body", {}).get("items", {}).get("item", []),
            "message": "위성 이미지 데이터를 성공적으로 가져왔습니다"
        }
    except Exception as e:
        print(f"Satellite API Error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "위성 이미지 데이터를 가져오는데 실패했습니다"
        }

@app.get("/api/price")
async def get_price_info():
    try:
        result = get_price_data()
        if result is None:
            raise HTTPException(status_code=500, detail="데이터를 가져오는데 실패했습니다")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
# CSV 파일을 제공하는 엔드포인트
@app.get("/pricedata/{filename}")
async def serve_price_data(filename: str):
    file_path = os.path.join("pricedata", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}
        
@app.post("/auth/register")
async def register(user: UserCreate):
    try:
        db = SessionLocal()
        
        # 이메일 중복 확인
        check_query = text("SELECT user_id FROM auth WHERE email = :email")
        existing_user = db.execute(check_query, {"email": user.email}).scalar()
        
        if existing_user:
            return {
                "success": False,
                "message": "Email already exists"
            }
        
        # 비밀번호 해시화
        hashed_password = bcrypt.hashpw(
            user.password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # 새 사용자 추가
        query = text("""
            INSERT INTO auth (email, password, birth_date, created_at)
            VALUES (:email, :password, :birth_date, NOW())
            RETURNING user_id, email, birth_date, created_at
        """)
        
        result = db.execute(
            query,
            {
                "email": user.email,
                "password": hashed_password,
                "birth_date": user.birth_date
            }
        )
        db.commit()
        
        new_user = result.fetchone()
        
        return {
            "success": True,
            "data": {
                "user": {
                    "user_id": new_user.user_id,
                    "email": new_user.email,
                    "birth_date": new_user.birth_date.strftime('%Y-%m-%d') if new_user.birth_date else None,
                    "created_at": new_user.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": str(e)
        }
    finally:
        db.close()

# Pydantic 모델 정의
class LoginData(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CropData(BaseModel):
    crop_name: str
    revenue_per_3_3m: float
    revenue_per_hour: float
    annual_sales: float
    total_cost: float
    costs: Dict[str, float]

@app.post("/auth/login")
async def login(login_data: LoginData):
    try:
        db = SessionLocal()
        
        # 사용자 정보 조회
        query = text("""
            SELECT user_id, email, password, birth_date, created_at 
            FROM auth 
            WHERE email = :email
        """)
        result = db.execute(query, {"email": login_data.email})
        user = result.fetchone()
        
        if not user:
            return JSONResponse(
                content={
                    "success": False,
                    "message": "User not found"
                },
                status_code=404
            )
            
        # 비밀번호 확인
        if not bcrypt.checkpw(
            login_data.password.encode('utf-8'),
            user.password.encode('utf-8')
        ):
            return JSONResponse(
                content={
                    "success": False,
                    "message": "Incorrect password"
                },
                status_code=401
            )
        
        # 토큰 생성
        token_data = {
            "sub": login_data.email,
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        access_token = create_access_token(token_data)
        
        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "user": {
                        "user_id": user.user_id,
                        "email": user.email,
                        "birth_date": user.birth_date.strftime('%Y-%m-%d') if user.birth_date else None,
                        "created_at": user.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    },
                    "access_token": access_token,
                    "token_type": "bearer"
                }
            },
            status_code=200
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": str(e)
            },
            status_code=400
        )
    finally:
        db.close()


# 커뮤니티 타입 열거형 정의
class CommunityType(str, Enum):
    GARDENING = "gardening"
    MARKETPLACE = "marketplace"
    FREEBOARD = "freeboard"

# Pydantic 모델 수정
class PostCreate(BaseModel):
    title: str
    content: str
    category: str
    community_type: CommunityType

@app.post("/api/write/create")
async def create_write_post(post: PostCreate, current_user: str = Depends(get_current_user)):
    try:
        db = SessionLocal()
        write_service = WriteService(db)
        post_data = await write_service.create_post(post, current_user)
        
        return {
            "success": True,
            "data": post_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 댓글 관련 API 엔드포인트
@app.get("/api/comments/user")
async def get_my_comments(request: Request):
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            raise HTTPException(status_code=401, detail="인증 헤더가 없습니다")
            
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_email = payload.get("sub")
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

        db = SessionLocal()
        comment_service = CommentService(db)
        comments_data = await comment_service.get_user_comments(user_email)
        
        return {
            "success": True,
            "data": comments_data,
            "message": "댓글 조회 성공"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

@app.get("/api/comments/{post_id}")
async def get_comments(post_id: int):
    try:
        db = SessionLocal()
        comment_service = CommentService(db)
        comments_data = await comment_service.get_post_comments(post_id)
        
        return {
            "success": True,
            "data": comments_data,
            "message": "댓글 조회 성공"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

@app.post("/api/comments")
async def create_comment(comment: CommentCreate):
    try:
        db = SessionLocal()
        comment_service = CommentService(db)
        comment_data = await comment_service.create_comment(comment)
        
        return {
            "success": True,
            "data": comment_data,
            "message": "댓글이 성공적으로 생성되었습니다"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

@app.put("/api/comments/{comment_id}")
async def update_comment(
    comment_id: int, 
    comment_update: CommentUpdate,
    current_user: str = Depends(get_current_user)
):
    try:
        db = SessionLocal()
        comment_service = CommentService(db)
        updated_comment = await comment_service.update_comment(
            comment_id, 
            comment_update.content, 
            current_user
        )
        
        return {
            "success": True,
            "data": updated_comment,
            "message": "댓글이 성공적으로 수정되었습니다"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

@app.delete("/api/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: str = Depends(get_current_user)
):
    try:
        db = SessionLocal()
        comment_service = CommentService(db)
        await comment_service.delete_comment(comment_id, current_user)
        
        return {
            "success": True,
            "message": "댓글이 성공적으로 삭제되었습니다",
            "data": {"comment_id": comment_id}
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

@app.get("/api/test-db")
async def test_db():
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT NOW()"))
        return {"success": True, "timestamp": result.scalar()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/sales")
async def get_sales():
    try:
        query = text("""
            SELECT 
                CONCAT(year::text, LPAD(week::text, 2, '0')) as period,
                "갈치", "감", "감귤", "건고추", "건멸치", "고구마", "굴", "김", 
                "대파", "딸기", "무", "물오징어", "바나나", "방울토마토", "배", 
                "배추", "복숭아", "사과", "상추", "새우", "수박", "시금치", 
                "쌀", "양파", "오렌지", "오이", "전복", "참다래", "찹쌀", 
                "체리", "토마토", "포도"
            FROM market_data
            WHERE year BETWEEN 2021 AND 2025
            AND (year != 2025 OR week <= 13)
            ORDER BY year, week
        """)

        with engine.connect() as conn:
            result = conn.execute(query)
            rows = result.fetchall()
            
            if not rows:
                print("No data found in market_data table")
                return {}

            data = {}
            column_names = [
                "period", "갈치", "감", "감귤", "건고추", "건멸치", "고구마", 
                "굴", "김", "대파", "딸기", "무", "물오징어", "바나나", 
                "방울토마토", "배", "배추", "복숭아", "사과", "상추", "새우", 
                "수박", "시금치", "쌀", "양파", "오렌지", "오이", "전복", 
                "참다래", "찹쌀", "체리", "토마토", "포도"
            ]

            for row in rows:
                period = row[0]  # YYYYWW 형식
                period_data = {}
                
                # 각 품목의 가격 데이터 추가
                for i, value in enumerate(row[1:], 1):
                    if value is not None:  # null 값이 아닌 경우만 추가
                        period_data[column_names[i]] = float(value)
                
                data[period] = period_data

            print(f"Found data for {len(data)} periods")
            print("Sample periods:", list(data.keys())[:5])
            
            return data

    except Exception as e:
        print(f"Error in /api/sales: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/top10")
async def get_top10():
    try:
        db = SessionLocal()
        result = db.execute(text("""
            SELECT crop_name, previous_year, current_year 
            FROM sales_data
            ORDER BY current_year DESC
        """))
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result]
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/get_text")
async def get_text(request: Request):
    try:
        # 요청 본문 읽기
        body = await request.json()
        
        # Python 프로세스 실행
        process = subprocess.Popen(
            ["python", "app.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 데이터 전송 및 결과 받기
        stdout, stderr = process.communicate(input=json.dumps(body))
        
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Python Error: {stderr}")
            
        try:
            prediction = json.loads(stdout)
            return prediction
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse Python output")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/market")
async def get_market():
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT * FROM sales_data"))
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result]
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_event():
    # PostgreSQL pool 정리
    engine.dispose()

# 게시글 수정을 위한 모델
class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    community_type: Optional[CommunityType] = None

# 댓글 수정을 위한 모델
class CommentUpdate(BaseModel):
    content: str

# 게시글 수정
@app.put("/api/posts/{post_id}")
async def update_post(
    post_id: int, 
    post_update: PostUpdate, 
    current_user: str = Depends(get_current_user)
):
    try:
        db = SessionLocal()
        write_service = WriteService(db)
        updated_post = await write_service.update_post(post_id, post_update, current_user)
        
        return {
            "success": True,
            "data": updated_post,
            "message": "게시글이 성공적으로 수정되었습니다"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

# 게시글 삭제
@app.delete("/api/write/{post_id}")
async def delete_post(
    post_id: int, 
    current_user: str = Depends(get_current_user)
):
    try:
        db = SessionLocal()
        write_service = WriteService(db)
        await write_service.delete_post(post_id, current_user)
        
        return {
            "success": True,
            "message": "게시글이 성공적으로 삭제되었습니다"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

# 이메일 설정
email_conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM = os.getenv("MAIL_FROM"),
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.naver.com"),
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True
)

# 비밀번호 재설정 모델
class PasswordReset(BaseModel):
    email: EmailStr
    token: str
    new_password: str

# 비밀번호 변경 모델
class PasswordChange(BaseModel):
    current_password: str
    new_password: str

# 회원 탈퇴
@app.delete("/auth/user")
async def delete_user(current_user: str = Depends(get_current_user)):
    try:
        db = SessionLocal()
        
        # 사용자 ID 조회
        user_query = text("SELECT user_id FROM auth WHERE email = :email")
        user_result = db.execute(user_query, {"email": current_user})
        user_id = user_result.scalar()
        
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 사용자의 댓글 삭제
        db.execute(
            text("DELETE FROM comments WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        
        # 사용자의 게시글 삭제
        db.execute(
            text("DELETE FROM write WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        
        # 사용자 계정 삭제
        db.execute(
            text("DELETE FROM auth WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        
        db.commit()
        return {"success": True, "message": "User account deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# 인증 코드 저장을 위한 임시 저장소
verification_codes = {}

@app.post("/auth/verify-email")
async def send_verification_email(email: EmailStr):
    try:
        # 6자리 인증 코드 생성
        verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # 인증 코드 저장 (5분 동안 유효)
        verification_codes[email] = {
            'code': verification_code,
            'expires_at': datetime.utcnow() + timedelta(minutes=5)
        }
        
        # 이메일 발송
        message = MessageSchema(
            subject="이메일 인증",
            recipients=[email],
            body=f"""
            안녕하세요! AniFarm 회원가입을 위한 인증 코드입니다:
            
            인증 코드: {verification_code}
            
            이 코드는 3분 동안만 유효합니다.
            """,
            subtype="plain"
        )
        
        try:
            fastmail = FastMail(email_conf)
            await fastmail.send_message(message)
            return {"success": True, "message": "인증 코드가 발송되었습니다."}
        except Exception as email_error:
            print(f"이메일 발송 상세 오류: {str(email_error)}")
            print(f"오류 타입: {type(email_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"이메일 발송 중 오류가 발생했습니다: {str(email_error)}"
            )
        
    except Exception as e:
        print(f"기타 오류: {str(e)}")
        print(f"오류 타입: {type(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"처리 중 오류가 발생했습니다: {str(e)}"
        )

@app.post("/auth/verify-code")
async def verify_code(email: EmailStr, code: str):
    if email not in verification_codes:
        raise HTTPException(status_code=400, detail="인증 코드를 찾을 수 없습니다.")
        
    stored_data = verification_codes[email]
    if datetime.utcnow() > stored_data['expires_at']:
        del verification_codes[email]
        raise HTTPException(status_code=400, detail="인증 코드가 만료되었습니다.")
        
    if code != stored_data['code']:
        raise HTTPException(status_code=400, detail="잘못된 인증 코드입니다.")
        
    # 인증 성공 시 코드 삭제
    del verification_codes[email]
    return {"success": True, "message": "이메일이 성공적으로 인증되었습니다."}

@app.get("/auth/verify-email/{token}")
async def verify_email_token(token: str):
    try:
        # 토큰 검증
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        email = payload["email"]
        
        # 여기서 필요한 경우 사용자의 이메일 인증 상태를 업데이트할 수 있습니다
        # 예: Auth 테이블에 verified 필드를 추가하여 업데이트
        
        return {"message": "이메일이 성공적으로 인증되었습니다."}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=400,
            detail="인증 링크가 만료되었습니다. 다시 인증 이메일을 요청해주세요."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=400,
            detail="유효하지 않은 인증 링크입니다."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"인증 처리 중 오류가 발생했습니다: {str(e)}"
        )

# 비밀번호 재설정 요청
@app.post("/auth/reset-password-request")
async def request_password_reset(email: EmailStr):
    try:
        db = SessionLocal()
        
        # 사용자 존재 확인
        user_query = text("SELECT user_id FROM auth WHERE email = :email")
        user_result = db.execute(user_query, {"email": email})
        if not user_result.scalar():
            raise HTTPException(status_code=404, detail="User not found")
        
        # 재설정 토큰 생성
        token = secrets.token_urlsafe(32)
        
        # 토큰 저장
        query = text("""
            INSERT INTO password_resets (email, token, created_at)
            VALUES (:email, :token, NOW())
        """)
        db.execute(query, {"email": email, "token": token})
        db.commit()
        
        # 이메일 발송
        message = MessageSchema(
            subject="비밀번호 재설정",
            recipients=[email],
            body=f"""
            안녕하세요!
            아래 링크를 클릭하여 비밀번호를 재설정해주세요:
            http://localhost:3000/reset-password?token={token}
            """
        )
        
        fastmail = FastMail(email_conf)
        await fastmail.send_message(message)
        
        return {"success": True, "message": "Password reset email sent"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# 비밀번호 재설정
@app.post("/auth/reset-password")
async def reset_password(reset_data: PasswordReset):
    try:
        db = SessionLocal()
        
        # 토큰 유효성 검사
        token_query = text("""
            SELECT email FROM password_resets 
            WHERE token = :token AND created_at > NOW() - INTERVAL '2 hour'
            AND used = false
        """)
        result = db.execute(token_query, {"token": reset_data.token})
        stored_email = result.scalar()
        
        if not stored_email or stored_email != reset_data.email:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        
        # 비밀번호 해시화
        hashed_password = bcrypt.hashpw(
            reset_data.new_password.encode('utf-8'), 
            bcrypt.gensalt()
        )
        
        # 비밀번호 업데이트
        update_query = text("""
            UPDATE auth SET password = :password 
            WHERE email = :email
        """)
        db.execute(update_query, {
            "password": hashed_password.decode('utf-8'),
            "email": reset_data.email
        })
        
        # 토큰 사용 완료 표시
        db.execute(
            text("UPDATE password_resets SET used = true WHERE token = :token"),
            {"token": reset_data.token}
        )
        
        db.commit()
        return {"success": True, "message": "Password reset successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# 비밀번호 수정 모델
class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

@app.post("/auth/update-password")
async def update_password(
    password_data: PasswordUpdate,
    current_user: str = Depends(get_current_user)
):
    try:
        db = SessionLocal()
        
        # 현재 사용자의 비밀번호 확인
        query = text("SELECT password FROM auth WHERE email = :email")
        result = db.execute(query, {"email": current_user})
        stored_password = result.scalar()
        
        if not stored_password:
            return {
                "success": False,
                "message": "User not found"
            }
        
        # 현재 비밀번호 확인
        if not bcrypt.checkpw(
            password_data.current_password.encode('utf-8'),
            stored_password.encode('utf-8')
        ):
            return {
                "success": False,
                "message": "Current password is incorrect"
            }
        
        # 새 비밀번호 해시화
        new_hashed_password = bcrypt.hashpw(
            password_data.new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # 비밀번호 업데이트
        update_query = text("""
            UPDATE auth 
            SET password = :password 
            WHERE email = :email
            RETURNING user_id, email, birth_date, created_at
        """)
        
        result = db.execute(
            update_query,
            {
                "password": new_hashed_password,
                "email": current_user
            }
        )
        db.commit()
        
        updated_user = result.fetchone()
        
        return {
            "success": True,
            "data": {
                "user": {
                    "user_id": updated_user.user_id,
                    "email": updated_user.email,
                    "birth_date": updated_user.birth_date.strftime('%Y-%m-%d') if updated_user.birth_date else None,
                    "created_at": updated_user.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            },
            "message": "Password updated successfully"
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": str(e)
        }
    finally:
        db.close()

@app.get("/api/write/community/{community_type}")
async def get_community_posts(community_type: str):
    try:
        db = SessionLocal()
        write_service = WriteService(db)
        posts_data = await write_service.get_community_posts(community_type)
        
        return {
            "success": True,
            "data": posts_data
        }
    except Exception as e:
        print(f"[ERROR] 게시글 조회 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }
    finally:
        db.close()

@app.get("/api/posts/{post_id}")
async def get_post_detail(post_id: int):
    try:
        db = SessionLocal()
        write_service = WriteService(db)
        post_data = await write_service.get_post(post_id)
        
        return {
            "success": True,
            "data": post_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

@app.get("/auth/user")
async def get_user_info(current_user: str = Depends(get_current_user)):
    try:
        db = SessionLocal()
        
        # 사용자 정보 조회
        query = text("""
            SELECT 
                user_id, 
                email, 
                TO_CHAR(birth_date, 'YYYY-MM-DD') as birth_date,
                TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at
            FROM auth 
            WHERE email = :email
        """)
        result = db.execute(query, {"email": current_user})
        user = result.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        return {
            "success": True,
            "data": {
                "user_id": user.user_id,
                "email": user.email,
                "birth_date": user.birth_date,
                "created_at": user.created_at
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# 유튜브 라우터 포함 (기존 경로: /api/youtube/ 및 /api/youtube/videos)
app.include_router(youtube_router)

# 내 게시글 조회 엔드포인트
@app.get("/api/write/user")  # URL 변경
async def get_my_posts(current_user: str = Depends(get_current_user)):
    try:
        db = SessionLocal()
        write_service = WriteService(db)
        posts_data = await write_service.get_user_posts(current_user)
        
        return {
            "success": True,
            "data": posts_data,
            "message": "게시글 조회 성공"
        }
        
    except Exception as e:
        logger.error(f"게시글 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/reset")
async def reset_conversation():
    """
    대화 기록 초기화
    """
    app.state.conversation_history.clear()
    return {"message": "대화 기록이 초기화 되었습니다."}

# 챗봇 엔드포인트
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    농산물 재배법에 답해 드립니다. - 농산물 재배법 상담 챗봇
    """
    try:
        # 기존 대화 기록 가져오기
        conversation_history = app.state.conversation_history

        # 현재 사용자의 입력 메시지 가져오기
        current_message = request.contents[-1].parts[0].get("text", "") if request.contents else ""

        # AI 응답 생성
        response = await process_query(current_message, conversation_history)

        # 응답 변환 및 반환
        return ChatResponse(
            candidates=[
                ChatCandidate(
                    content=ChatMessage(
                        role="model",
                        parts=[
                            {
                                "text": response
                            }
                        ]
                    )
                )
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'오류 발생: {str(e)}')

# 대화 기록 초기화
app.state.conversation_history = []

# Crawler 라우터 포함
app.include_router(crawler_router, prefix="/api/crawler")

@app.get("/predictions/{crop}/{city}")
async def get_predictions(crop: str, city: str):
    try:
        from utils.apiUrl import fetchWeatherData
        from pricepython.price import predict_prices
        
        weather_data = await fetchWeatherData(city)
        predictions = predict_prices(crop, weather_data)
        
        if 'error' in predictions:
            raise Exception(predictions['error'])
            
        return {
            "predictions": predictions,
            "weather_data": weather_data['raw']
        }
    except Exception as e:
        print(f"Error in predictions: {str(e)}")
        return {"error": str(e)}

# --- 퀴즈 관련 Pydantic 모델 추가 ---
from pydantic import BaseModel
from typing import List

class QuizQuestion(BaseModel):
    id: int
    crop: str
    question: str
    option_1: str
    option_2: str
    option_3: str
    option_4: str
    correct_answer: str

class QuizAnswer(BaseModel):
    quiz_id: int
    selected_answer: str

class QuizSubmission(BaseModel):
    answers: List[QuizAnswer]

# --- 퀴즈 문제 조회 엔드포인트 ---
@app.get("/api/quiz/{crop}", response_model=List[QuizQuestion])
async def get_quiz_by_crop(crop: str):
    """
    지정한 작물(crop)에 해당하는 퀴즈 문제와 선택지를 반환합니다.
    정답 정보는 포함하지 않아, 클라이언트가 퀴즈를 풀 때 미리 알 수 없습니다.
    """
    db = SessionLocal()
    try:
        query = text("""
            SELECT id, crop, question, option_1, option_2, option_3, option_4, correct_answer
            FROM quiz 
            WHERE crop = :crop
        """)
        results = db.execute(query, {"crop": crop})
        rows = results.fetchall()
        quiz_data = []
        for row in rows:
            quiz_data.append({
                "id": row[0],
                "crop": row[1],
                "question": row[2],
                "option_1": row[3],
                "option_2": row[4],
                "option_3": row[5],
                "option_4": row[6],
                "correct_answer": row[7]
            })
        return quiz_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# 작물 이름 조회 엔드포인트
class CropOption(BaseModel):
    id: int
    crop: str

@app.get("/api/quiz", response_model=List[CropOption])
async def get_crop_options():
    """
    퀴즈 테이블에서 중복되지 않는 작물명을 추출하여,
    각 작물의 최초 id(또는 그룹화한 id)를 함께 반환합니다.
    """
    db = SessionLocal()
    try:
        # 그룹별 최소 id를 작물의 고유 id로 사용합니다.
        query = text("SELECT MIN(id) AS id, crop FROM quiz GROUP BY crop")
        results = db.execute(query)
        rows = results.fetchall()
        crops = [{"id": row[0], "crop": row[1]} for row in rows]
        return crops
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/data/{table_name}")
async def get_table_data(table_name: str):
    try:
        # 데이터베이스 연결
        engine = create_engine(os.getenv("DATABASE_URL"))
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 테이블 존재 여부 확인
        result = db.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')"))
        table_exists = result.scalar()
        
        if not table_exists:
            raise HTTPException(status_code=404, detail=f"테이블 '{table_name}'을(를) 찾을 수 없습니다.")
        
        # 테이블 데이터 조회
        query = text(f"SELECT * FROM {table_name}")
        result = db.execute(query)
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result]
        
        db.close()
        return {"status": "success", "data": data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crop-data")
async def get_crop_data():
    """
    모든 작물의 데이터를 조회합니다.
    """
    try:
        db = SessionLocal()
        
        # 작물 기본 정보 조회
        query = text("""
            SELECT 
                c.id,
                c.crop_name,
                c.revenue_per_3_3m,
                c.revenue_per_hour,
                c.annual_sales,
                c.total_cost,
                json_object_agg(cc.cost_type, cc.amount) as costs
            FROM crops c
            LEFT JOIN crop_costs cc ON c.id = cc.crop_id
            GROUP BY c.id, c.crop_name, c.revenue_per_3_3m, c.revenue_per_hour, c.annual_sales, c.total_cost
            ORDER BY c.crop_name
        """)
        
        result = db.execute(query)
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result]
        
        return {
            "success": True,
            "data": data,
            "message": "작물 데이터를 성공적으로 조회했습니다."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/crop-data/{crop_name}")
async def get_crop_data_by_name(crop_name: str):
    """
    특정 작물의 데이터를 조회합니다.
    """
    try:
        db = SessionLocal()
        
        # 특정 작물 데이터 조회
        query = text("""
            SELECT 
                c.id,
                c.crop_name,
                c.revenue_per_3_3m,
                c.revenue_per_hour,
                c.annual_sales,
                c.total_cost,
                json_object_agg(cc.cost_type, cc.amount) as costs
            FROM crops c
            LEFT JOIN crop_costs cc ON c.id = cc.crop_id
            WHERE c.crop_name = :crop_name
            GROUP BY c.id, c.crop_name, c.revenue_per_3_3m, c.revenue_per_hour, c.annual_sales, c.total_cost
        """)
        
        result = db.execute(query, {"crop_name": crop_name})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"'{crop_name}' 작물의 데이터를 찾을 수 없습니다."
            )
            
        data = dict(zip(result.keys(), row))
        
        return {
            "success": True,
            "data": data,
            "message": f"'{crop_name}' 작물 데이터를 성공적으로 조회했습니다."
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/api/crop-data")
async def create_or_update_crop_data(crop_data: CropData):
    """
    새로운 작물 데이터를 추가하거나 기존 데이터를 업데이트합니다.
    """
    try:
        db = SessionLocal()
        
        # 트랜잭션 시작
        db.execute(text("BEGIN"))
        
        # 작물이 이미 존재하는지 확인
        check_query = text("SELECT id FROM crops WHERE crop_name = :crop_name")
        existing_crop = db.execute(check_query, {"crop_name": crop_data.crop_name}).scalar()
        
        if existing_crop:
            # 기존 작물 정보 업데이트
            update_query = text("""
                UPDATE crops
                SET revenue_per_3_3m = :revenue_per_3_3m,
                    revenue_per_hour = :revenue_per_hour,
                    annual_sales = :annual_sales,
                    total_cost = :total_cost
                WHERE crop_name = :crop_name
                RETURNING id
            """)
            result = db.execute(update_query, {
                "crop_name": crop_data.crop_name,
                "revenue_per_3_3m": crop_data.revenue_per_3_3m,
                "revenue_per_hour": crop_data.revenue_per_hour,
                "annual_sales": crop_data.annual_sales,
                "total_cost": crop_data.total_cost
            })
            crop_id = result.scalar()
            
            # 기존 경영비 삭제
            db.execute(text("DELETE FROM crop_costs WHERE crop_id = :crop_id"), {"crop_id": crop_id})
        else:
            # 새로운 작물 추가
            insert_query = text("""
                INSERT INTO crops (
                    crop_name, revenue_per_3_3m, revenue_per_hour, 
                    annual_sales, total_cost
                )
                VALUES (
                    :crop_name, :revenue_per_3_3m, :revenue_per_hour,
                    :annual_sales, :total_cost
                )
                RETURNING id
            """)
            result = db.execute(insert_query, {
                "crop_name": crop_data.crop_name,
                "revenue_per_3_3m": crop_data.revenue_per_3_3m,
                "revenue_per_hour": crop_data.revenue_per_hour,
                "annual_sales": crop_data.annual_sales,
                "total_cost": crop_data.total_cost
            })
            crop_id = result.scalar()
        
        # 경영비 정보 추가
        for cost_type, amount in crop_data.costs.items():
            cost_query = text("""
                INSERT INTO crop_costs (crop_id, cost_type, amount)
                VALUES (:crop_id, :cost_type, :amount)
            """)
            db.execute(cost_query, {
                "crop_id": crop_id,
                "cost_type": cost_type,
                "amount": amount
            })
        
        # 트랜잭션 커밋
        db.execute(text("COMMIT"))
        
        return {
            "success": True,
            "message": f"작물 데이터가 성공적으로 {'업데이트' if existing_crop else '추가'}되었습니다.",
            "data": {
                "id": crop_id,
                **crop_data.dict()
            }
        }
        
    except Exception as e:
        db.execute(text("ROLLBACK"))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/auth/refresh")
async def refresh_token(current_user: str = Depends(get_current_user)):
    try:
        # 현재 사용자의 이메일로 새 토큰 생성
        token_data = {
            "sub": current_user,
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        new_token = create_access_token(token_data)
        
        return {
            "success": True,
            "data": {
                "newToken": new_token,
                "token_type": "bearer"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # GrowthCalendar 인스턴스 생성
growth_calendar = GrowthCalendar()

@app.get("/api/growth_calendar")
async def get_growth_calendar(city: str = "서울", crop: str = "all", sowing_date: str = None, target_date: str = None):
    try:
        # 날씨 데이터 가져오기
        weather_data = await fetchWeatherData(city)
        
        # 파종일과 대상 날짜 처리
        if sowing_date:
            sowing_date = datetime.strptime(sowing_date, "%Y-%m-%d").date()
        
        # 현재 날짜 기준으로 해당 월의 첫날과 마지막 날 계산
        if target_date:
            current_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            current_date = datetime.now().date()
            
        first_day = current_date.replace(day=1)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
        # 날씨 기반 가이드 생성
        weather_guidance = []
        
        # 현재 날짜 기준으로 날씨 가이드 추가
        today = datetime.now().date()
        current = weather_data["current"]
        weather_guidance.append({
            "type": "weather",
            "date": today.strftime("%Y-%m-%d"),
            "temperature": current.get("avg temp", 0),
            "rainfall": current.get("rainFall", 0),
            "message": f"현재 날씨: {current.get('avg temp', 0)}°C"
        })
        
        # 주간 날씨 가이드 추가 (현재 날짜부터)
        for i, day in enumerate(weather_data["weekly"]):
            future_date = today + timedelta(days=i)
            weather_guidance.append({
                "type": "weather",
                "date": future_date.strftime("%Y-%m-%d"),
                "temperature": day.get("avg temp", 0),
                "rainfall": day.get("rainFall", 0),
                "message": f"날씨 예보: {day.get('avg temp', 0)}°C"
            })
        
        # 작물 가이드 초기화
        crop_guidance = []
        
        # 파종일이 지정된 경우에만 작물 가이드 추가
        if sowing_date and crop != "all":
            # 해당 월의 모든 날짜에 대해 가이드 생성
            current = first_day
            while current <= last_day:
                daily_guidance = growth_calendar.get_crop_guidance(
                    crop_name=crop,
                    sowing_date=sowing_date,
                    target_date=current
                )
                crop_guidance.extend(daily_guidance)
                current += timedelta(days=1)
        
        # 모든 가이드 합치기
        all_guidance = weather_guidance + crop_guidance
        
        return {
            "success": True,
            "data": {
                "guidance": all_guidance,
                "weather": weather_data
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 캘린더 데이터 저장을 위한 Pydantic 모델
class CalendarData(BaseModel):
    region: str
    crop: str
    growth_date: str

@app.post("/api/growth_calendar/save")
async def save_growth_calendar(
    calendar_data: CalendarData,
    current_user: str = Depends(get_current_user)
):
    try:
        db = SessionLocal()
        
        # 현재 사용자의 user_id 조회
        user_query = text("SELECT user_id FROM auth WHERE email = :email")
        user_result = db.execute(user_query, {"email": current_user})
        user_id = user_result.scalar()
        
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 캘린더 데이터 저장
        query = text("""
            INSERT INTO growth_calendar (user_id, region, crop, growth_date)
            VALUES (:user_id, :region, :crop, :growth_date)
            RETURNING id, region, crop, growth_date, created_at
        """)
        
        result = db.execute(
            query,
            {
                "user_id": user_id,
                "region": calendar_data.region,
                "crop": calendar_data.crop,
                "growth_date": calendar_data.growth_date
            }
        )
        db.commit()
        
        saved_data = result.fetchone()
        
        return {
            "success": True,
            "data": {
                "id": saved_data.id,
                "region": saved_data.region,
                "crop": saved_data.crop,
                "growth_date": saved_data.growth_date.strftime('%Y-%m-%d'),
                "created_at": saved_data.created_at.strftime('%Y-%m-%d %H:%M:%S')
            },
            "message": "캘린더 데이터가 성공적으로 저장되었습니다."
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/growth_calendar/user")
async def get_user_calendar(current_user: str = Depends(get_current_user)):
    try:
        db = SessionLocal()
        
        # 현재 사용자의 user_id 조회
        user_query = text("SELECT user_id FROM auth WHERE email = :email")
        user_result = db.execute(user_query, {"email": current_user})
        user_id = user_result.scalar()
        
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 사용자의 캘린더 데이터 조회
        query = text("""
            SELECT id, region, crop, growth_date, created_at
            FROM growth_calendar
            WHERE user_id = :user_id
            ORDER BY growth_date DESC
        """)
        
        result = db.execute(query, {"user_id": user_id})
        calendar_data = []
        
        for row in result:
            calendar_data.append({
                "id": row.id,
                "region": row.region,
                "crop": row.crop,
                "growth_date": row.growth_date.strftime('%Y-%m-%d'),
                "created_at": row.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return {
            "success": True,
            "data": calendar_data,
            "message": "캘린더 데이터를 성공적으로 조회했습니다."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.delete("/api/growth_calendar/{calendar_id}")
async def delete_calendar_data(
    calendar_id: int,
    current_user: str = Depends(get_current_user)
):
    try:
        db = SessionLocal()
        
        # 현재 사용자의 user_id 조회
        user_query = text("SELECT user_id FROM auth WHERE email = :email")
        user_result = db.execute(user_query, {"email": current_user})
        user_id = user_result.scalar()
        
        if not user_id:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 캘린더 데이터가 현재 사용자의 것인지 확인
        check_query = text("""
            SELECT id FROM growth_calendar 
            WHERE id = :calendar_id AND user_id = :user_id
        """)
        result = db.execute(check_query, {
            "calendar_id": calendar_id,
            "user_id": user_id
        })
        
        if not result.scalar():
            raise HTTPException(
                status_code=404, 
                detail="해당 캘린더 데이터를 찾을 수 없거나 삭제 권한이 없습니다"
            )
        
        # 캘린더 데이터 삭제
        delete_query = text("""
            DELETE FROM growth_calendar 
            WHERE id = :calendar_id AND user_id = :user_id
        """)
        
        db.execute(delete_query, {
            "calendar_id": calendar_id,
            "user_id": user_id
        })
        db.commit()
        
        return {
            "success": True,
            "message": "캘린더 데이터가 성공적으로 삭제되었습니다",
            "data": {"id": calendar_id}
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# 가격 데이터 저장 API
@app.post("/api/price/save")
async def save_price_data(price_data: List[Dict]):
    """가격 데이터를 데이터베이스에 저장합니다."""
    try:
        db = SessionLocal()
        
        # 고유 제약조건 추가
        try:
            db.execute(text("""
                ALTER TABLE price_data 
                ADD CONSTRAINT price_data_item_name_date_key 
                UNIQUE (item_name, date)
            """))
            db.commit()
        except Exception as e:
            logger.info(f"고유 제약조건이 이미 존재합니다: {str(e)}")
            db.rollback()

        for item in price_data:
            # 데이터 유효성 검사
            if not all(key in item for key in ['item_name', 'price', 'date', 'category_code']):
                logger.error(f"필수 필드 누락: {item}")
                continue

            # 날짜 형식 변환
            try:
                import re
                date_str = re.sub(r'[()]', '', item['date'])
                logger.info(f"처리할 날짜 문자열: {date_str}")
                
                # '당일 MM/DD' 형식 처리
                if date_str.startswith('당일'):
                    today = datetime.now()
                    logger.info(f"현재 날짜: {today}")
                    month, day = map(int, date_str.split()[1].split('/'))
                    logger.info(f"추출된 월/일: {month}/{day}")
                    try:
                        date_obj = today.replace(month=month, day=day).date()
                        logger.info(f"당일 형식 처리 성공: {date_obj}")
                    except ValueError as ve:
                        logger.error(f"날짜 생성 실패: {str(ve)}")
                        continue
                else:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    logger.info(f"일반 형식 처리: {date_obj}")
            except Exception as e:
                logger.error(f"날짜 형식 변환 실패: {item['date']}, 오류: {str(e)}")
                continue

            # 가격 데이터 정제
            price = item['price'].replace(',', '')
            price_change = item.get('price_change', 0)
            yesterday_price = item.get('yesterday_price', 0)

            # previous_date 처리
            previous_date_str = item.get('previous_date')
            previous_date_obj = None
            
            if previous_date_str:
                try:
                    if '일전' in previous_date_str:
                        # "N일전 MM/DD" 형식 처리
                        days_ago = int(previous_date_str.split('일전')[0])
                        month, day = map(int, previous_date_str.split()[1].split('/'))
                        current_date = datetime.now().date()
                        previous_date_obj = current_date.replace(month=month, day=day) - timedelta(days=days_ago)
                    else:
                        # "YYYY-MM-DD" 형식 처리
                        previous_date_obj = datetime.strptime(previous_date_str, "%Y-%m-%d").date()
                except Exception as e:
                    logger.error(f"이전 날짜 변환 중 오류 발생: {str(e)}")
                    # previous_date 변환 실패 시 null로 처리
                    previous_date_obj = None

            # SQL 쿼리 실행
            query = text("""
                INSERT INTO price_data (
                    item_name, price, unit, date, previous_date, price_change, 
                    yesterday_price, category_code, category_name, 
                    has_dpr1, created_at
                ) VALUES (:item_name, :price, :unit, :date, :previous_date, :price_change, 
                    :yesterday_price, :category_code, :category_name, 
                    :has_dpr1, NOW())
                ON CONFLICT (item_name, date) 
                DO UPDATE SET 
                    price = EXCLUDED.price,
                    unit = EXCLUDED.unit,
                    previous_date = EXCLUDED.previous_date,
                    price_change = EXCLUDED.price_change,
                    yesterday_price = EXCLUDED.yesterday_price,
                    category_code = EXCLUDED.category_code,
                    category_name = EXCLUDED.category_name,
                    has_dpr1 = EXCLUDED.has_dpr1
            """)
            
            db.execute(query, {
                "item_name": item['item_name'],
                "price": price,
                "unit": item.get('unit', ''),
                "date": date_obj,
                "previous_date": previous_date_obj,
                "price_change": price_change,
                "yesterday_price": yesterday_price,
                "category_code": item['category_code'],
                "category_name": item.get('category_name', ''),
                "has_dpr1": item.get('has_dpr1', False)
            })
        
        db.commit()
        return {
            "success": True,
            "message": "가격 데이터가 성공적으로 저장되었습니다."
        }

    except Exception as e:
        db.rollback()
        logger.error(f"가격 데이터 저장 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"가격 데이터 저장 중 오류가 발생했습니다: {str(e)}"
        )
    finally:
        db.close()

# 가격 데이터 조회 API
@app.get("/api/price/from-db")
async def get_price_data_from_db():
    try:
        result = db.execute(text("SELECT * FROM price_data"))
        price_data = []
        for row in result:
            price_data.append({
                "item_name": row.item_name,
                "price": row.price,
                "unit": row.unit,
                "date": row.date.strftime("%Y-%m-%d"),
                "previous_date": row.previous_date.strftime("%Y-%m-%d"),
                "price_change": row.price_change,
                "yesterday_price": row.yesterday_price,
                "category_code": row.category_code,
                "category_name": row.category_name,
                "has_dpr1": row.has_dpr1
            })
        return {"data": {"item": price_data}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/youth/list")
def youth_list(
    s_code: str = SCode.YOUNG_FARMER_VIDEO.value,
    type_dv: str = ContentType.JSON.value,
    row_cnt: Optional[int] = 200  # 전체 데이터를 가져오기 위해 충분히 큰 값으로 설정
):
    return get_youth_list(
        s_code=SCode(s_code),
        type_dv=ContentType(type_dv),
        row_cnt=row_cnt  # row_cnt 파라미터 추가
    )

@app.get("/api/youth/view")
async def get_youth_view(s_code: str, seq: str):
    """
    청년농업인 상세 정보 조회 엔드포인트
    
    Args:
        s_code: 분류코드 (01: 청년농영상, 02: 청년농소개, 03: 기술우수사례, 04: 극복·실패사례)
        seq: 게시글 번호
    """
    try:
        result = get_youth_detail(s_code=s_code, seq=seq)
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/young/edu")
async def get_young_edu_list(
    search_category: str = "교육",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    row_cnt: Optional[int] = None
):
    """
    청년농 교육 정보 목록 조회 엔드포인트
    """
    try:
        result = get_edu_list(
            search_category=search_category,
            start_date=start_date,
            end_date=end_date,
            row_cnt=row_cnt
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500, 
                detail=result.get("message", "API 호출 실패")
            )
            
        return result
        
    except Exception as e:
        logger.error(f"API 호출 중 오류 발생: {str(e)}")

# 지원사업 API 엔드포인트
@app.get("/api/support/programs")
async def get_programs():
    """지원사업 목록을 반환합니다."""
    try:
        programs = await get_support_programs()
        return {
            "success": True,
            "data": programs,
            "message": "지원사업 목록을 성공적으로 가져왔습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/support/detail/{content_id}")
async def get_program_detail(content_id: str):
    """특정 지원사업의 상세 정보를 반환합니다."""
    try:
        detail = await get_support_detail(content_id)
        return {
            "success": True,
            "data": detail,
            "message": "지원사업 상세 정보를 성공적으로 가져왔습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 교육 프로그램 API 엔드포인트
@app.get("/api/education/programs")
async def get_edu_programs():
    """교육 프로그램 목록을 반환합니다."""
    try:
        programs = await get_education_programs()
        return {
            "success": True,
            "data": programs,
            "message": "교육 프로그램 목록을 성공적으로 가져왔습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/education/detail/{edu_id}")
async def get_edu_detail(edu_id: str):
    """교육 프로그램 상세 정보를 반환합니다."""
    try:
        detail = await get_education_detail(edu_id)
        return {
            "success": True,
            "data": detail,
            "message": "교육 프로그램 상세 정보를 성공적으로 가져왔습니다."
        }
    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Main Server is running on port 8000")
    
    try:
        # 메인 앱 실행
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        pass