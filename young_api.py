import requests
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any
from enum import Enum
import json
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# .env 파일 로드
load_dotenv()

class ContentType(Enum):
    JSON = "json"
    XML = "xml"

class SCode(Enum):
    YOUNG_FARMER_VIDEO = "01"  # 청년농영상
    YOUNG_FARMER_INTRO = "02"  # 청년농소개
    TECH_SUCCESS = "03"        # 기술우수사례
    OVERCOME_FAILURE = "04"    # 극복·실패사례

# 환경변수에서 API 키 가져오기
YOUNG_API_KEY = os.getenv("YOUNG_API_KEY")

def get_youth_list(
    s_code: SCode = SCode.YOUNG_FARMER_VIDEO,
    search_keyword: Optional[str] = None,
    cp: Optional[int] = None,
    row_cnt: Optional[int] = 200,  # 기본값을 충분히 큰 수로 설정
    type_dv: ContentType = ContentType.JSON
) -> Dict[str, Any]:
    """
    청년사례 목록 조회
    
    Args:
        s_code (SCode): 청년사례 게시판 분류코드
        search_keyword (str, optional): 제목 및 내용 검색 키워드
        cp (int, optional): 페이지 번호
        row_cnt (int, optional): 페이지당 보여줄 row 수
        type_dv (ContentType): 리턴타입 (json, xml)
    """
    try:
        url = "https://www.rda.go.kr/young/api/youthList"
        
        params = {
            'serviceKey': YOUNG_API_KEY,
            'sCode': s_code.value,
            'typeDv': type_dv.value,
            'rowCnt': str(row_cnt)  # 항상 row_cnt 파라미터 포함
        }

        if search_keyword:
            params['search_keyword'] = search_keyword
        if cp:
            params['cp'] = str(cp)

        logger.info("청년사례 목록 조회 요청")
        logger.debug(f"Request URL: {url}")
        logger.debug(f"Parameters: {params}")

        response = requests.get(
            url,
            params=params,
            verify=False
        )

        logger.debug(f"Response Status: {response.status_code}")
        logger.debug(f"Response Content: {response.text}")

        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json(),
                "message": "청년사례 목록을 성공적으로 가져왔습니다."
            }
        else:
            return {
                "success": False,
                "error": f"API returned status code {response.status_code}",
                "message": f"API 호출 실패: {response.text}"
            }

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

def get_youth_detail(s_code: str, seq: str, type_dv: str = "json") -> Dict[str, Any]:
    """
    청년사례 상세정보 조회
    
    Args:
        s_code (str): 청년사례 게시판 분류코드
        seq (str): 게시글 번호
        type_dv (str): 리턴타입 (json, xml)
    """
    try:
        # URL에 파라미터를 직접 포함
        url = f"https://www.rda.go.kr/young/api/youthView?serviceKey={YOUNG_API_KEY}&sCode={s_code}&seq={seq}&typeDv={type_dv}"
        
        logger.info("청년사례 상세정보 조회 요청")
        logger.debug(f"Request URL: {url}")

        # requests 설정
        session = requests.Session()
        session.verify = False
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }

        response = session.get(url, headers=headers)
        
        # 응답 로깅 추가
        logger.debug(f"Response Status: {response.status_code}")
        logger.debug(f"Response Headers: {dict(response.headers)}")
        logger.debug(f"Response Content: {response.text}")

        if response.status_code == 200:
            try:
                data = response.json()
                
                # 응답 구조 확인을 위한 로깅
                logger.debug(f"Parsed JSON data: {data}")
                
                # 응답 데이터가 있는 경우
                if data:
                    result = {
                        "result": {
                            "bbsSeq": data.get("bbsSeq"),
                            "bbsId": data.get("bbsId"),
                            "title": data.get("title"),
                            "contents": data.get("contents"),
                            "bbsInfo03": data.get("bbsInfo03"),
                            "bbsInfo04": data.get("bbsInfo04"),
                            "bbsInfo07": data.get("bbsInfo07"),
                            "bbsInfo08": data.get("bbsInfo08"),
                            "viewFiles": [],
                            "area1Nm": data.get("area1Nm"),
                            "area2Nm": data.get("area2Nm")
                        }
                    }

                    # 이미지 파일 정보 처리
                    if "viewFiles" in data and data["viewFiles"]:
                        files = []
                        for file_info in data["viewFiles"]:
                            file_url = file_info.get("fileUrl", "")
                            if file_url and not file_url.startswith('http'):
                                file_url = f"https://www.rda.go.kr{file_url}"
                            files.append({
                                "fileUrl": file_url,
                                "fileName": file_info.get("fileName", ""),
                                "fileSize": file_info.get("fileSize", "")
                            })
                        result["result"]["viewFiles"] = files

                    return {
                        "success": True,
                        "data": result,
                        "message": "청년사례 상세정보를 성공적으로 가져왔습니다."
                    }
                else:
                    return {
                        "success": False,
                        "error": "데이터가 비어있습니다",
                        "raw_response": response.text
                    }
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 오류: {str(e)}")
                return {
                    "success": False,
                    "error": f"JSON 파싱 오류: {str(e)}",
                    "raw_response": response.text
                }
        else:
            return {
                "success": False,
                "error": f"API returned status code {response.status_code}",
                "message": f"API 호출 실패: {response.text}"
            }

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "raw_response": response.text if 'response' in locals() else None
        }

def get_edu_list(
    search_category: str = "교육",
    type_dv: str = "json",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    row_cnt: Optional[int] = None
) -> Dict[str, Any]:
    """
    청년농 교육 정보 목록 조회
    
    Args:
        search_category (str): 카테고리 (기본값: "교육")
        type_dv (str): 응답 형식 (기본값: "json")
        start_date (str): 신청 시작일 (YYYY-MM-DD)
        end_date (str): 신청 마감일 (YYYY-MM-DD)
        row_cnt (Optional[int]): 가져올 row 수 (기본값: None - 모든 데이터 조회)
    """
    try:
        if not YOUNG_API_KEY:
            raise ValueError("YOUNG_API_KEY가 설정되지 않았습니다.")

        params = {
            'serviceKey': YOUNG_API_KEY,
            'search_category': search_category,
            'typeDv': type_dv,
            'sd': start_date or datetime.now().strftime("%Y-%m-%d"),
            'ed': end_date or datetime.now().strftime("%Y-%m-%d")
        }

        if row_cnt:
            params['rowCnt'] = str(row_cnt)

        url = "https://www.rda.go.kr/young/api/eduList"
        
        logger.info("청년농 교육 정보 목록 조회 요청")
        logger.debug(f"Request URL: {url}")
        logger.debug(f"Parameters: {params}")

        response = requests.get(
            url,
            params=params,
            verify=True,
            timeout=30
        )

        logger.debug(f"Response Status: {response.status_code}")
        logger.debug(f"Response Headers: {dict(response.headers)}")
        logger.debug(f"Response Content: {response.text[:500]}")

        response.raise_for_status()

        return {
            "success": True,
            "data": response.json(),
            "message": "청년농 교육 정보를 성공적으로 가져왔습니다."
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"API 요청 중 오류가 발생했습니다: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"예상치 못한 오류가 발생했습니다: {str(e)}"
        }
