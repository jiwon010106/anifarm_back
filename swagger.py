from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def custom_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="농산물 가격 예측 API",
        version="1.0.0",
        description="농산물 가격 예측 및 커뮤니티 서비스를 위한 API 문서",
        routes=app.routes,
    )

    # API 태그 정의
    openapi_schema["tags"] = [
        {
            "name": "기본",
            "description": "기본 API"
        },
        {
            "name": "이미지 분류",
            "description": "농산물 이미지 분류 API"
        },
        {
            "name": "날씨",
            "description": "날씨 및 위성 데이터 API"
        },
        {
            "name": "가격",
            "description": "농산물 가격 정보 API"
        },
        {
            "name": "챗봇",
            "description": "AI 챗봇 관련 API"
        },
        {
            "name": "인증",
            "description": "사용자 인증 관련 API"
        },
        {
            "name": "커뮤니티",
            "description": "게시판 및 댓글 관련 API"
        },
        {
            "name": "경영모의계산",
            "description": "경영모의계산 관련 API"
        },
        {
            "name": "YouTube",
            "description": " 추천 교육 영상 YouTube API"
        },
        {
            "name": "Crawler",
            "description": "소비 트렌드 농산물 뉴스 API"
        },
        {
            "name": "퀴즈",
            "description": "퀴즈 관련 API"
        }
    ]

    # 라우트에 태그 추가
    for path, route in openapi_schema["paths"].items():
        for method, operation in route.items():
            # 이미지 분류 관련 엔드포인트
            if any(img_path in path for img_path in ["/kiwi_predict", "/chamoe_predict", "/plant_predict", "/strawberry_predict", "/potato_predict", "/tomato_predict", "/apple_predict", "/grape_predict", "/corn_predict"]):
                operation["tags"] = ["이미지 분류"]
            
            # 날씨 관련 엔드포인트
            if any(weather_path in path for weather_path in ["/weather", "/api/satellite"]):
                operation["tags"] = ["날씨"]
            
            # 가격 관련 엔드포인트
            if any(price_path in path for price_path in ["/api/price", "/api/sales", "/api/top10", "/api/market", "/predictions/"]):
                operation["tags"] = ["가격"]
            
            # 챗봇 관련 엔드포인트
            if any(chat_path in path for chat_path in ["/chat", "/reset"]):
                operation["tags"] = ["챗봇"]

            if "tags" not in operation:
                operation["tags"] = ["기본"]
            
            # 인증 관련 엔드포인트
            if any(auth_path in path for auth_path in ["/auth/", "/register", "/login"]):
                operation["tags"] = ["인증"]
            
            # 커뮤니티 관련 엔드포인트
            if any(comm_path in path for comm_path in ["/api/write/", "/api/comments/", "/api/posts/"]):
                operation["tags"] = ["커뮤니티"]
            
            # 경영모의계산 관련 엔드포인트
            if any(business_path in path for business_path in ["/api/crop-data"]):
                operation["tags"] = ["경영모의계산"]

            # 퀴즈 관련 엔드포인트
            if any(quiz_path in path for quiz_path in ["/api/quiz"]):
                operation["tags"] = ["퀴즈"]
            
    app.openapi_schema = openapi_schema
    return app.openapi_schema 