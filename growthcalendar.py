from utils.apiUrl import fetchWeatherData, KOREAN_CITIES
import datetime
import asyncio
import random

class GrowthCalendar:
    def __init__(self):
        # 작물별 생육 단계와 권장 파종 시기 설정
        self.crops = {
            "토마토": {
                "growth_stages": {
                    "발아기": (0, 7),
                    "본잎성장기": (8, 30),
                    "개화기": (31, 60),
                    "결실기": (61, 90),
                    "수확기": (91, 120)
                },
                "recommended_period": "봄: 2-3월, 가을: 8-9월",
                "specific_day_tasks": {
                    7: "지지대를 설치하세요.",
                    14: "첫 번째 가지치기를 시작하세요.",
                    30: "병충해 예방을 위한 스프레이 작업을 하세요."
                }
            },
            "상추": {
                "growth_stages": {
                    "발아기": (0, 5),
                    "본잎성장기": (6, 20),
                    "수확기": (21, 40)
                },
                "recommended_period": "봄: 2-4월, 가을: 8-9월",
                "specific_day_tasks": {
                    5: "추가로 씨를 뿌려 수확 주기를 늘리세요.",
                    10: "첫 번째 수확을 시작할 수 있습니다.",
                    20: "비료를 추가하세요."
                }
            },
            "감자": {
                "growth_stages": {
                    "발아기": (0, 14),
                    "생육기": (15, 45),
                    "괴경비대기": (46, 90),
                    "수확기": (91, 120)
                },
                "recommended_period": "봄: 2-3월, 가을: 8월",
                "specific_day_tasks": {
                    10: "흙을 북돋아 주세요.",
                    20: "추가 비료를 공급하세요.",
                    40: "꽃이 피면 물 주기를 줄이세요."
                }
            },
            "딸기": {
                "growth_stages": {
                    "발아기": (0, 10),
                    "생육기": (11, 30),
                    "개화기": (31, 45),
                    "결실기": (46, 60),
                    "수확기": (61, 90)
                },
                "recommended_period": "봄: 3-4월, 가을: 8-9월",
                "specific_day_tasks": {
                    10: "첫 번째 잎이 나면 비료를 주세요.",
                    20: "꽃눈이 형성되면 온도 관리를 하세요.",
                    30: "꽃이 피면 인공수분을 도와주세요.",
                    45: "과실이 맺히면 지지대를 설치하세요."
                }
            },
            "당근": {
                "growth_stages": {
                    "발아기": (0, 7),
                    "생육기": (8, 30),
                    "뿌리비대기": (31, 60),
                    "수확기": (61, 90)
                },
                "recommended_period": "봄: 2-3월, 가을: 8-9월",
                "specific_day_tasks": {
                    7: "첫 번째 잎이 나면 솎아내기를 하세요.",
                    15: "토양을 부드럽게 해주세요.",
                    30: "비료를 추가하세요.",
                    45: "뿌리가 보이면 흙을 덮어주세요."
                }
            },
            "오이": {
                "growth_stages": {
                    "발아기": (0, 5),
                    "생육기": (6, 20),
                    "개화기": (21, 35),
                    "결실기": (36, 50),
                    "수확기": (51, 70)
                },
                "recommended_period": "봄: 3-4월, 가을: 8-9월",
                "specific_day_tasks": {
                    5: "첫 번째 잎이 나면 지지대를 설치하세요.",
                    15: "가지치기를 시작하세요.",
                    25: "꽃이 피면 인공수분을 도와주세요.",
                    35: "과실이 맺히면 물 주기를 늘리세요."
                }
            },
            "고추": {
                "growth_stages": {
                    "발아기": (0, 7),
                    "생육기": (8, 30),
                    "개화기": (31, 45),
                    "결실기": (46, 70),
                    "수확기": (71, 100)
                },
                "recommended_period": "봄: 2-3월, 가을: 8-9월",
                "specific_day_tasks": {
                    7: "첫 번째 잎이 나면 비료를 주세요.",
                    15: "지지대를 설치하세요.",
                    30: "가지치기를 시작하세요.",
                    45: "꽃이 피면 인공수분을 도와주세요.",
                    60: "과실이 맺히면 물 주기를 늘리세요."
                }
            }
        }

    async def get_weather_guidance(self, city="서울", target_date=None):
        weather_data = await fetchWeatherData(city)
        return self._process_weather_guidance(weather_data, target_date)

    def _process_weather_guidance(self, weather_data, target_date=None):
        guidance = []
        today = datetime.date.today()
        target_date = target_date or today
        
        # 현재 날씨에 대한 가이드
        current = weather_data['current']
        guidance.append({
            "date": today.isoformat(),
            "type": "weather",
            "temperature": current.get('avg temp'),
            "rainfall": current.get('rainFall', 0),
            "message": f"현재 날씨: {current['avg temp']}°C"
        })
        
        # 주간 날씨에 대한 가이드
        for idx, day in enumerate(weather_data['weekly']):
            date = today + datetime.timedelta(days=idx)
            guidance.append({
                "date": date.isoformat(),
                "type": "weather",
                "temperature": day.get('avg temp'),
                "rainfall": day.get('rainFall', 0),
                "message": f"날씨 예보: {day['avg temp']}°C"
            })

        return guidance

    def update_sowing_date(self, crop_name, new_date):
        """작물의 파종일을 업데이트합니다."""
        if crop_name in self.crops:
            self.crops[crop_name]["sowing_date"] = new_date

    def get_crop_guidance(self, crop_name, sowing_date, target_date):
        guidance = []
        
        if not sowing_date:
            guidance.append({
                "type": "sowing_period",
                "date": target_date.strftime("%Y-%m-%d"),
                "message": "파종일을 설정해주세요",
                "crop": crop_name
            })
            return guidance

        days_since_sowing = (target_date - sowing_date).days

        if crop_name in self.crops:
            crop_info = self.crops[crop_name]
            growth_stages = crop_info["growth_stages"]
            
            # 수확기 시작일 계산
            harvest_start = growth_stages["수확기"][0]
            harvest_start_date = sowing_date + datetime.timedelta(days=harvest_start)
            
            # 현재 날짜가 수확 시작일인 경우에만 수확기 시작 메시지 추가
            if target_date == harvest_start_date:
                guidance.append({
                    "type": "harvest",
                    "date": target_date.strftime("%Y-%m-%d"),
                    "message": f"{crop_name} 수확기 시작",
                    "crop": crop_name
                })

            # 생육 단계 메시지 추가
            for stage_name, (start_day, end_day) in growth_stages.items():
                if start_day <= days_since_sowing <= end_day:
                    guidance.append({
                        "type": "growth",
                        "date": target_date.strftime("%Y-%m-%d"),
                        "message": self._get_stage_guidance(crop_name, stage_name, days_since_sowing),
                        "crop": crop_name
                    })
                    break

            # specific_day_tasks 처리
            if "specific_day_tasks" in crop_info:
                for day, task in crop_info["specific_day_tasks"].items():
                    task_date = sowing_date + datetime.timedelta(days=int(day))
                    if target_date == task_date:
                        guidance.append({
                            "type": "task",
                            "date": target_date.strftime("%Y-%m-%d"),
                            "message": task,
                            "crop": crop_name
                        })

        return guidance

    def _get_stage_guidance(self, crop, stage, days_since_sowing):
        """생육 단계별 가이드 메시지를 반환합니다."""
        base_guidance = {
            "발아기": "충분한 수분 공급과 적정 온도 유지가 중요합니다.",
            "본잎성장기": "잡초 제거와 충분한 영양 공급이 필요합니다.",
            "개화기": "수분 작업과 적절한 온도 관리가 중요합니다.",
            "결실기": "과실의 크기와 상태를 주기적으로 확인하세요.",
            "생육기": "잎의 상태를 관찰하고 병해충 관리를 하세요.",
            "괴경비대기": "토양 수분 관리와 북주기 작업이 필요합니다.",
            "뿌리비대기": "토양 수분을 적절히 유지하고 비료를 공급하세요.",
            "수확기": "적정 수확 시기를 확인하고 준비하세요."
        }
        
        guidance = base_guidance.get(stage, "정기적인 관리가 필요합니다.")
        return f"파종 {days_since_sowing + 1}일차 ({stage}): {guidance}"
