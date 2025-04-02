import os
import requests
from dotenv import load_dotenv
from typing import List, Dict
from fastapi import HTTPException
import logging
from datetime import datetime, timedelta
import httpx

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

INFOMATION_API_KEY = os.getenv("INFOMATION_API_KEY")
BASE_URL = "https://www.rda.go.kr/young/api"

async def get_support_programs() -> List[Dict]:
    """농업 지원사업 정보를 가져오는 함수"""
    try:
        # API 엔드포인트 설정
        endpoint = f"{BASE_URL}/policyList"
        
        # API 요청 파라미터
        params = {
            "serviceKey": INFOMATION_API_KEY,
            "typeDv": "json",
            "rowCnt": 30
        }
        
        # API 요청
        response = requests.get(endpoint, params=params)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if not data:
                    return []
                
                # policy_list에서 데이터 추출
                items = data.get("policy_list", [])
                if not items:
                    return []
                
                # 지원사업 정보 정리
                support_programs = []
                for item in items:
                    # 신청기간 구성
                    appl_start = item.get("applStDt", "").replace(".", "-")
                    appl_end = item.get("applEdDt", "").replace(".", "-")
                    application_period = f"{appl_start} ~ {appl_end}" if appl_start and appl_end else ""
                    
                    program = {
                        "id": item.get("seq", ""),
                        "title": item.get("title", ""),
                        "category": item.get("typeDv", ""),
                        "target": item.get("eduTarget", ""),
                        "content": item.get("contents", ""),
                        "application_period": application_period,
                        "organization": item.get("chargeAgency", ""),
                        "department": item.get("chargeDept", ""),
                        "contact": item.get("chargeTel", ""),
                        "area": item.get("area2Nm", ""),
                        "url": item.get("infoUrl", "")
                    }
                    support_programs.append(program)
                
                return support_programs
            except Exception as e:
                logger.error(f"Error parsing response: {str(e)}")
                raise HTTPException(status_code=500, detail="응답 데이터 파싱 실패")
        else:
            raise HTTPException(status_code=response.status_code, detail="API 요청 실패")
            
    except Exception as e:
        logger.error(f"Error in get_support_programs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_support_detail(content_id: str) -> Dict:
    """특정 지원사업의 상세 정보를 가져오는 함수"""
    try:
        endpoint = f"{BASE_URL}/policyView"
        
        params = {
            "serviceKey": INFOMATION_API_KEY,
            "typeDv": "json",
            "seq": content_id
        }
        
        response = requests.get(endpoint, params=params)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if not data:
                    raise HTTPException(status_code=404, detail="지원사업 정보를 찾을 수 없습니다")
                
                item = data.get("policy_view", {})
                if not item:
                    raise HTTPException(status_code=404, detail="지원사업 정보를 찾을 수 없습니다")
                
                # 신청기간 구성
                appl_start = item.get("applStDt", "").replace(".", "-")
                appl_end = item.get("applEdDt", "").replace(".", "-")
                application_period = f"{appl_start} ~ {appl_end}" if appl_start and appl_end else ""
                
                detail = {
                    "id": item.get("seq", ""),
                    "title": item.get("title", ""),
                    "category": item.get("typeDv", ""),
                    "target": item.get("eduTarget", ""),
                    "content": item.get("contents", ""),
                    "application_period": application_period,
                    "organization": item.get("chargeAgency", ""),
                    "department": item.get("chargeDept", ""),
                    "contact": item.get("chargeTel", ""),
                    "area": item.get("area2Nm", ""),
                    "url": item.get("infoUrl", "")
                }
                
                return detail
            except Exception as e:
                logger.error(f"Error parsing response: {str(e)}")
                raise HTTPException(status_code=500, detail="응답 데이터 파싱 실패")
        else:
            raise HTTPException(status_code=response.status_code, detail="API 요청 실패")
            
    except Exception as e:
        logger.error(f"Error in get_support_detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_education_programs() -> List[Dict]:
    """교육 프로그램 정보를 가져오는 함수"""
    try:
        endpoint = f"{BASE_URL}/eduList"
        
        params = {
            "serviceKey": INFOMATION_API_KEY,
            "typeDv": "json",
            "rowCnt": 30
        }
        
        response = requests.get(endpoint, params=params)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if not data:
                    return []
                
                # edu_list에서 데이터 추출
                items = data.get("edu_list", [])
                if not items:
                    return []
                
                education_programs = []
                for item in items:
                    # 교육기간 구성
                    edu_start = item.get("eduStDt", "").replace(".", "-")
                    edu_end = item.get("eduEdDt", "").replace(".", "-")
                    period = f"{edu_start} ~ {edu_end}" if edu_start and edu_end else ""
                    
                    # 신청기간 구성
                    appl_start = item.get("applStDt", "").replace(".", "-")
                    appl_end = item.get("applEdDt", "").replace(".", "-")
                    application_period = f"{appl_start} ~ {appl_end}" if appl_start and appl_end else ""
                    
                    program = {
                        "id": item.get("seq", ""),
                        "title": item.get("title", ""),
                        "category": item.get("typeDv", ""),
                        "target": item.get("eduTarget", ""),
                        "period": period,
                        "application_period": application_period,
                        "eduMethod": item.get("eduMethod", ""),
                        "eduMethod2": item.get("eduMethod2", ""),
                        "eduMethod3": item.get("eduMethod3", ""),
                        "organization": item.get("chargeAgency", ""),
                        "department": item.get("chargeDept", ""),
                        "contact": item.get("chargeTel", ""),
                        "capacity": item.get("eduCnt", ""),
                        "eduTime": item.get("eduTime", ""),
                        "price": item.get("price", ""),
                        "content": item.get("contents", ""),
                        "url": item.get("infoUrl", "")
                    }
                    education_programs.append(program)
                
                return education_programs
            except Exception as e:
                logger.error(f"Error parsing response: {str(e)}")
                raise HTTPException(status_code=500, detail="응답 데이터 파싱 실패")
        else:
            raise HTTPException(status_code=response.status_code, detail="API 요청 실패")
            
    except Exception as e:
        logger.error(f"Error in get_education_programs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_education_detail(edu_id: str):
    """교육 프로그램 상세 정보 조회"""
    try:
        url = f"http://api.nongsaro.go.kr/service/edu/eduDetail"
        params = {
            "apiKey": INFOMATION_API_KEY,
            "eduId": edu_id,
            "format": "json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "body" not in data:
                raise ValueError("응답에 body 필드가 없습니다")
                
            edu_data = data["body"]
            if not edu_data:
                raise ValueError("교육 프로그램 정보를 찾을 수 없습니다")
                
            # 필수 필드 검증
            required_fields = ["eduNm", "eduContent", "eduTarget", "eduPeriod", "eduApplyPeriod", 
                             "eduMethod", "eduMethod2", "eduMethod3", "eduCapacity", "eduTime", 
                             "eduPrice", "eduOrg", "eduDept", "eduTel", "eduReq", "eduDoc"]
            
            for field in required_fields:
                if field not in edu_data:
                    edu_data[field] = "정보 없음"
            
            return {
                "id": edu_id,
                "title": edu_data.get("eduNm", "제목 없음"),
                "content": edu_data.get("eduContent", "내용 없음"),
                "target": edu_data.get("eduTarget", "대상 없음"),
                "period": edu_data.get("eduPeriod", "기간 미정"),
                "application_period": edu_data.get("eduApplyPeriod", "신청기간 미정"),
                "eduMethod": edu_data.get("eduMethod", ""),
                "eduMethod2": edu_data.get("eduMethod2", ""),
                "eduMethod3": edu_data.get("eduMethod3", ""),
                "capacity": edu_data.get("eduCapacity", "0"),
                "eduTime": edu_data.get("eduTime", "0"),
                "price": edu_data.get("eduPrice", "무료"),
                "organization": edu_data.get("eduOrg", "기관 미정"),
                "department": edu_data.get("eduDept", "부서 미정"),
                "contact": edu_data.get("eduTel", "연락처 미정"),
                "requirements": edu_data.get("eduReq", "자격 없음"),
                "documents": edu_data.get("eduDoc", "서류 없음")
            }
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error in get_education_detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"교육 프로그램 정보 조회 실패: {str(e)}")
    except Exception as e:
        logger.error(f"Error in get_education_detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"교육 프로그램 정보 처리 실패: {str(e)}")
