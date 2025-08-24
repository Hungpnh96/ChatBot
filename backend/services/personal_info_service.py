# services/personal_info_service.py
import logging
import requests
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from config.settings import settings

logger = logging.getLogger(__name__)

class PersonalInfoService:
    """Service gọi API để lấy thông tin cá nhân của user"""
    
    def __init__(self):
        self.cache = {}  # Cache thông tin user
        self.cache_ttl = 1800  # 30 minutes
        
    def _detect_personal_question(self, user_query: str) -> bool:
        """Phân tích xem có phải câu hỏi về thông tin cá nhân không"""
        
        personal_keywords = [
            # Thông tin cơ bản
            "tôi", "mình", "em", "anh", "chị", "tên tôi", "tên mình",
            "tuổi tôi", "tuổi mình", "sinh nhật", "ngày sinh",
            
            # Thông tin liên hệ
            "số điện thoại", "email", "địa chỉ", "nhà", "ở đâu",
            "phone", "mail", "address",
            
            # Thông tin công việc
            "công việc", "làm việc", "công ty", "chức vụ", "job", "work",
            "lương", "salary", "thu nhập", "income",
            
            # Thông tin gia đình
            "gia đình", "vợ", "chồng", "con", "bố", "mẹ", "anh em",
            "family", "wife", "husband", "children", "parents",
            
            # Sở thích
            "thích", "sở thích", "hobby", "yêu thích", "quan tâm",
            
            # Lịch trình
            "lịch", "cuộc hẹn", "meeting", "schedule", "calendar",
            "hôm nay làm gì", "tuần này", "tháng này",
            
            # Tài chính cá nhân
            "tài khoản", "tiền", "account", "balance", "tiết kiệm"
        ]
        
        query_lower = user_query.lower()
        
        # Kiểm tra keywords
        for keyword in personal_keywords:
            if keyword in query_lower:
                logger.info(f"Detected personal info question: '{keyword}' in query")
                return True
        
        # Patterns cho câu hỏi cá nhân
        personal_patterns = [
            "thông tin của tôi",
            "thông tin cá nhân",
            "profile của tôi",
            "my profile",
            "my information",
            "về tôi",
            "about me"
        ]
        
        for pattern in personal_patterns:
            if pattern in query_lower:
                logger.info(f"Detected personal pattern: '{pattern}' in query")
                return True
                
        return False
    
    def _get_cache_key(self, user_id: str, info_type: str) -> str:
        """Tạo cache key"""
        return f"{user_id}_{info_type}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Kiểm tra cache còn valid không"""
        if cache_key not in self.cache:
            return False
            
        cached_time = self.cache[cache_key].get('timestamp', 0)
        return (datetime.now().timestamp() - cached_time) < self.cache_ttl
    
    async def get_user_basic_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin cơ bản của user"""
        try:
            cache_key = self._get_cache_key(user_id, "basic")
            
            # Kiểm tra cache
            if self._is_cache_valid(cache_key):
                logger.info(f"Using cached basic info for user: {user_id}")
                return self.cache[cache_key]['data']
            
            # Gọi API external
            if not settings.personal_api_base_url:
                logger.warning("Personal API not configured")
                return None
            
            url = f"{settings.personal_api_base_url}/users/{user_id}/basic"
            headers = {
                'Authorization': f'Bearer {settings.personal_api_token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Fetching basic info for user: {user_id}")
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache kết quả
            self.cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now().timestamp()
            }
            
            logger.info(f"✅ Got basic info for user: {user_id}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to get basic info for user {user_id}: {e}")
            return None
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Lấy profile đầy đủ của user"""
        try:
            cache_key = self._get_cache_key(user_id, "profile")
            
            if self._is_cache_valid(cache_key):
                logger.info(f"Using cached profile for user: {user_id}")
                return self.cache[cache_key]['data']
            
            if not settings.personal_api_base_url:
                return None
            
            url = f"{settings.personal_api_base_url}/users/{user_id}/profile"
            headers = {
                'Authorization': f'Bearer {settings.personal_api_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            self.cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now().timestamp()
            }
            
            logger.info(f"✅ Got profile for user: {user_id}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to get profile for user {user_id}: {e}")
            return None
    
    async def get_user_schedule(self, user_id: str, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Lấy lịch trình của user"""
        try:
            cache_key = self._get_cache_key(user_id, f"schedule_{date or 'today'}")
            
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]['data']
            
            if not settings.personal_api_base_url:
                return None
            
            url = f"{settings.personal_api_base_url}/users/{user_id}/schedule"
            if date:
                url += f"?date={date}"
            
            headers = {
                'Authorization': f'Bearer {settings.personal_api_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache với TTL ngắn hơn cho schedule (5 phút)
            self.cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now().timestamp() - (self.cache_ttl - 300)  # 5 min TTL
            }
            
            logger.info(f"✅ Got schedule for user: {user_id}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to get schedule for user {user_id}: {e}")
            return None
    
    def _determine_info_type(self, user_query: str) -> str:
        """Xác định loại thông tin cần lấy dựa vào câu hỏi"""
        
        query_lower = user_query.lower()
        
        # Schedule/Calendar
        if any(word in query_lower for word in ["lịch", "cuộc hẹn", "meeting", "schedule", "hôm nay làm gì"]):
            return "schedule"
        
        # Work info
        if any(word in query_lower for word in ["công việc", "công ty", "chức vụ", "job", "work", "lương"]):
            return "work"
        
        # Contact info
        if any(word in query_lower for word in ["số điện thoại", "email", "địa chỉ", "phone", "address"]):
            return "contact"
        
        # Family info
        if any(word in query_lower for word in ["gia đình", "vợ", "chồng", "con", "family"]):
            return "family"
        
        # Basic info (default)
        return "basic"
    
    def _format_personal_info(self, info_data: Dict[str, Any], info_type: str, user_query: str) -> str:
        """Format thông tin cá nhân để AI sử dụng"""
        
        if not info_data:
            return ""
        
        try:
            formatted_parts = []
            
            if info_type == "schedule":
                if "events" in info_data:
                    formatted_parts.append("Lịch trình của bạn:")
                    for event in info_data["events"][:5]:  # Top 5 events
                        time = event.get("time", "")
                        title = event.get("title", "")
                        location = event.get("location", "")
                        
                        event_str = f"- {time}: {title}"
                        if location:
                            event_str += f" tại {location}"
                        formatted_parts.append(event_str)
            
            elif info_type == "basic":
                if "name" in info_data:
                    formatted_parts.append(f"Tên: {info_data['name']}")
                if "age" in info_data:
                    formatted_parts.append(f"Tuổi: {info_data['age']}")
                if "birthday" in info_data:
                    formatted_parts.append(f"Sinh nhật: {info_data['birthday']}")
            
            elif info_type == "contact":
                if "phone" in info_data:
                    formatted_parts.append(f"Số điện thoại: {info_data['phone']}")
                if "email" in info_data:
                    formatted_parts.append(f"Email: {info_data['email']}")
                if "address" in info_data:
                    formatted_parts.append(f"Địa chỉ: {info_data['address']}")
            
            elif info_type == "work":
                if "company" in info_data:
                    formatted_parts.append(f"Công ty: {info_data['company']}")
                if "position" in info_data:
                    formatted_parts.append(f"Chức vụ: {info_data['position']}")
                if "department" in info_data:
                    formatted_parts.append(f"Phòng ban: {info_data['department']}")
            
            elif info_type == "family":
                if "spouse" in info_data:
                    formatted_parts.append(f"Vợ/Chồng: {info_data['spouse']}")
                if "children" in info_data:
                    children_list = ", ".join(info_data['children'])
                    formatted_parts.append(f"Con: {children_list}")
            
            if formatted_parts:
                result = "\n".join(formatted_parts)
                result += f"\n\n(Thông tin cá nhân cập nhật lúc {datetime.now().strftime('%H:%M %d/%m/%Y')})"
                return result
            
            return ""
            
        except Exception as e:
            logger.error(f"Error formatting personal info: {e}")
            return ""
    
    async def get_personal_info_for_query(self, user_query: str, user_id: str = "default") -> Optional[str]:
        """
        Main method: Lấy thông tin cá nhân dựa vào câu hỏi
        Trả về None nếu không phải câu hỏi cá nhân, hoặc string chứa thông tin
        """
        try:
            # Kiểm tra có phải câu hỏi cá nhân không
            if not self._detect_personal_question(user_query):
                logger.info(f"Not a personal question: {user_query}")
                return None
            
            logger.info(f"Processing personal info request: {user_query}")
            
            # Xác định loại thông tin cần lấy
            info_type = self._determine_info_type(user_query)
            logger.info(f"Determined info type: {info_type}")
            
            # Lấy thông tin tương ứng
            info_data = None
            
            if info_type == "schedule":
                info_data = await self.get_user_schedule(user_id)
            elif info_type in ["basic", "contact", "work", "family"]:
                # Lấy profile đầy đủ và extract thông tin cần thiết
                profile_data = await self.get_user_profile(user_id)
                if profile_data:
                    info_data = profile_data.get(info_type, profile_data)
            
            if info_data:
                formatted_info = self._format_personal_info(info_data, info_type, user_query)
                if formatted_info:
                    logger.info(f"✅ Found personal info: {len(formatted_info)} characters")
                    return formatted_info
            
            logger.warning(f"No personal info found for: {user_query}")
            return None
            
        except Exception as e:
            logger.error(f"Get personal info failed: {e}")
            return None
    
    def clear_user_cache(self, user_id: str):
        """Xóa cache của user (khi thông tin thay đổi)"""
        keys_to_remove = [key for key in self.cache.keys() if key.startswith(user_id)]
        for key in keys_to_remove:
            del self.cache[key]
        logger.info(f"Cleared cache for user: {user_id}")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Lấy thống kê service"""
        return {
            "cache_size": len(self.cache),
            "cache_ttl_seconds": self.cache_ttl,
            "api_configured": bool(settings.personal_api_base_url),
            "api_token_configured": bool(settings.personal_api_token)
        }

# Global instance
personal_info_service = PersonalInfoService()