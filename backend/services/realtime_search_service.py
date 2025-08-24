# services/realtime_search_service.py - FIXED VERSION với better search

import logging
import requests
import asyncio
import re
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
import hashlib
from bs4 import BeautifulSoup
import urllib.parse
from config.settings import settings

logger = logging.getLogger(__name__)

class RealtimeSearchService:
    """FIXED Realtime Search Service với improved search accuracy"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 1800  # Giảm xuống 30 phút để cập nhật thường xuyên hơn
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
    def _should_search(self, user_query: str) -> bool:
        """Phân tích xem câu hỏi có cần search thông tin mới không"""
        
        # ENHANCED keywords cho thông tin thời gian thực
        realtime_keywords = [
            # Thời gian - QUAN TRỌNG
            "hiện tại", "bây giờ", "hôm nay", "năm nay", "tháng này", "2024", "2025",
            "mới nhất", "gần đây", "vừa", "latest", "current", "now", "today",
            "đương nhiệm", "incumbent", "present",
            
            # Chính trị - lãnh đạo - QUAN TRỌNG  
            "chủ tịch nước", "thủ tướng", "tổng thống", "thủ tướng chính phủ",
            "president", "prime minister", "ceo", "giám đốc", "lãnh đạo",
            "đảng trưởng", "tổng bí thư",
            
            # Kinh tế - tài chính
            "giá", "tỷ giá", "chứng khoán", "vàng", "bitcoin", "usd", "vnđ",
            "price", "stock", "exchange rate", "market", "thị trường",
            
            # Thời tiết
            "thời tiết", "nhiệt độ", "mưa", "nắng", "weather", "temperature",
            "dự báo thời tiết", "forecast",
            
            # Tin tức - sự kiện
            "tin tức", "sự kiện", "news", "breaking", "báo", "thông tin mới",
            "xảy ra", "diễn ra", "vừa xảy ra", "cập nhật",
            
            # Thể thao
            "bóng đá", "world cup", "kết quả", "trận đấu", "tỷ số", "euro",
            "championship", "football", "soccer",
            
            # Công nghệ
            "iphone mới", "samsung", "update", "phiên bản mới", "ra mắt",
            "launch", "release", "tech news"
        ]
        
        query_lower = user_query.lower()
        
        # Kiểm tra keywords
        for keyword in realtime_keywords:
            if keyword in query_lower:
                logger.info(f"🔍 Detected realtime search need: '{keyword}' in query")
                return True
                
        # Patterns cho câu hỏi cần info mới
        realtime_patterns = [
            "ai là", "who is", "bao nhiêu", "how much",
            "khi nào", "when", "có gì mới", "what's new",
            "diễn biến", "tình hình", "cập nhật"
        ]
        
        for pattern in realtime_patterns:
            if pattern in query_lower:
                logger.info(f"🔍 Detected realtime pattern: '{pattern}' in query")
                return True
                
        return False
    
    def _get_cache_key(self, query: str, source: str = "") -> str:
        """Tạo cache key từ query"""
        return hashlib.md5(f"{source}_{query}".lower().encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Kiểm tra cache còn valid không"""
        if cache_key not in self.cache:
            return False
            
        cached_time = self.cache[cache_key].get('timestamp', 0)
        is_valid = (datetime.now().timestamp() - cached_time) < self.cache_ttl
        
        if not is_valid:
            logger.info(f"🗑️ Cache expired for key: {cache_key[:8]}")
        
        return is_valid
    
    async def search_wikipedia_vietnam(self, query: str) -> List[Dict[str, Any]]:
        """IMPROVED Wikipedia search với focus on current info"""
        try:
            cache_key = self._get_cache_key(query, "wikipedia_vn")
            if self._is_cache_valid(cache_key):
                logger.info(f"📦 Using cached Wikipedia VN results for: {query}")
                return self.cache[cache_key]['results']
            
            # Wikipedia Vietnamese API với multiple search strategies
            search_url = "https://vi.wikipedia.org/w/api.php"
            
            # Strategy 1: Direct search với current context
            search_params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': f"{query} 2024 2025 hiện tại",  # Thêm context mới
                'srlimit': 5,
                'srprop': 'snippet|timestamp'
            }
            
            logger.info(f"🔍 Wikipedia VN search for: {query}")
            
            response = requests.get(search_url, params=search_params, timeout=10)
            response.raise_for_status()
            
            search_data = response.json()
            results = []
            
            for item in search_data.get('query', {}).get('search', []):
                title = item.get('title', '')
                snippet = item.get('snippet', '')
                
                # Clean HTML tags from snippet
                snippet = re.sub(r'<[^>]+>', '', snippet)
                
                # Get detailed page content for first result
                if len(results) == 0:
                    try:
                        page_content = await self._get_wikipedia_page_content(title)
                        if page_content:
                            snippet = page_content
                    except Exception as e:
                        logger.warning(f"Could not get detailed content for {title}: {e}")
                
                page_url = f"https://vi.wikipedia.org/wiki/{urllib.parse.quote(title)}"
                
                results.append({
                    'title': title,
                    'snippet': snippet,
                    'link': page_url,
                    'source': 'Wikipedia (Vi)',
                    'published': 'Recent'
                })
            
            # Cache với TTL ngắn hơn cho thông tin chính trị
            cache_ttl = 900 if any(word in query.lower() for word in ["chủ tịch", "thủ tướng", "president"]) else self.cache_ttl
            
            self.cache[cache_key] = {
                'results': results,
                'timestamp': datetime.now().timestamp() - (self.cache_ttl - cache_ttl)
            }
            
            logger.info(f"✅ Found {len(results)} Wikipedia VN results for: {query}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Wikipedia VN search failed: {e}")
            return []
    
    async def _get_wikipedia_page_content(self, title: str) -> str:
        """Lấy nội dung chi tiết từ Wikipedia page"""
        try:
            content_url = "https://vi.wikipedia.org/w/api.php"
            content_params = {
                'action': 'query',
                'format': 'json',
                'titles': title,
                'prop': 'extracts',
                'exintro': True,
                'explaintext': True,
                'exsectionformat': 'plain'
            }
            
            response = requests.get(content_url, params=content_params, timeout=8)
            response.raise_for_status()
            
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            
            for page_id, page_data in pages.items():
                if page_id != '-1':  # Page exists
                    extract = page_data.get('extract', '')
                    if extract:
                        # Lấy 500 ký tự đầu và tìm thông tin quan trọng
                        extract = extract[:500]
                        
                        # Tìm thông tin về năm hiện tại
                        if '2024' in extract or '2025' in extract:
                            return extract
                        
                        return extract[:300] + "..."
            
            return ""
            
        except Exception as e:
            logger.warning(f"Error getting Wikipedia page content: {e}")
            return ""
    
    async def search_google(self, query: str, num_results: int = 3) -> List[Dict[str, Any]]:
        """IMPROVED Google search with better targeting"""
        try:
            cache_key = self._get_cache_key(query, "google_improved")
            if self._is_cache_valid(cache_key):
                logger.info(f"📦 Using cached Google results for: {query}")
                return self.cache[cache_key]['results']
            
            # IMPROVED Google search với multiple strategies
            search_queries = [
                f"{query} 2024 2025 site:vi.wikipedia.org",
                f"{query} hiện tại site:vnexpress.net",
                f"{query} mới nhất site:tuoitre.vn",
                f"{query} site:dantri.com.vn"
            ]
            
            all_results = []
            
            for search_query in search_queries[:2]:  # Thử 2 query đầu
                try:
                    encoded_query = urllib.parse.quote_plus(search_query)
                    url = f"https://www.google.com/search?q={encoded_query}&num=3&hl=vi&gl=vn"
                    
                    logger.info(f"🔍 Google search: {search_query}")
                    
                    response = requests.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    search_results = soup.find_all('div', class_='g')
                    
                    for result in search_results[:2]:  # Top 2 từ mỗi query
                        try:
                            title_elem = result.find('h3')
                            title = title_elem.get_text() if title_elem else ""
                            
                            link_elem = result.find('a')
                            link = link_elem.get('href', '') if link_elem else ""
                            
                            snippet_elem = result.find('span', class_='aCOpRe') or result.find('div', class_='VwiC3b')
                            snippet = snippet_elem.get_text() if snippet_elem else ""
                            
                            source_elem = result.find('cite')
                            source = source_elem.get_text() if source_elem else ""
                            
                            if title and link and snippet:
                                all_results.append({
                                    'title': title,
                                    'snippet': snippet,
                                    'link': link,
                                    'source': source,
                                    'published': 'Recent'
                                })
                                
                        except Exception as e:
                            logger.warning(f"Error parsing Google result: {e}")
                            continue
                    
                    # Nếu đã có kết quả tốt, break
                    if len(all_results) >= 2:
                        break
                        
                except Exception as e:
                    logger.warning(f"Google search query failed: {e}")
                    continue
            
            # Cache results
            self.cache[cache_key] = {
                'results': all_results[:num_results],
                'timestamp': datetime.now().timestamp()
            }
            
            logger.info(f"✅ Found {len(all_results)} Google results for: {query}")
            return all_results[:num_results]
            
        except Exception as e:
            logger.error(f"❌ Google search failed: {e}")
            return []
    
    async def search_bing(self, query: str, num_results: int = 3) -> List[Dict[str, Any]]:
        """DuckDuckGo search (reliable fallback)"""
        try:
            cache_key = self._get_cache_key(query, "duckduckgo")
            if self._is_cache_valid(cache_key):
                logger.info(f"📦 Using cached DuckDuckGo results for: {query}")
                return self.cache[cache_key]['results']
            
            # DuckDuckGo Instant Answer API
            url = "https://api.duckduckgo.com/"
            params = {
                'q': f"{query} 2024 2025",  # Add current year context
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            logger.info(f"🦆 DuckDuckGo search for: {query}")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Parse DuckDuckGo response
            if data.get('Abstract'):
                results.append({
                    'title': data.get('Heading', query),
                    'snippet': data.get('Abstract', ''),
                    'link': data.get('AbstractURL', ''),
                    'source': data.get('AbstractSource', 'DuckDuckGo'),
                    'published': 'Recent'
                })
            
            # Related topics
            for topic in data.get('RelatedTopics', [])[:num_results-1]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append({
                        'title': topic.get('Text', '').split(' - ')[0],
                        'snippet': topic.get('Text', ''),
                        'link': topic.get('FirstURL', ''),
                        'source': 'DuckDuckGo',
                        'published': 'Recent'
                    })
            
            self.cache[cache_key] = {
                'results': results,
                'timestamp': datetime.now().timestamp()
            }
            
            logger.info(f"✅ Found {len(results)} DuckDuckGo results for: {query}")
            return results
            
        except Exception as e:
            logger.error(f"❌ DuckDuckGo search failed: {e}")
            return []
    
    def _extract_key_info(self, search_results: List[Dict[str, Any]], query: str) -> str:
        """IMPROVED info extraction with current context priority"""
        if not search_results:
            return ""
        
        info_parts = []
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        for i, result in enumerate(search_results[:3]):
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            source = result.get('source', '')
            
            if snippet:
                # Prioritize snippets with current years
                if any(year in snippet for year in ['2024', '2025']) or 'hiện tại' in snippet.lower():
                    info_parts.insert(0, f"[{source}] {snippet}")  # Insert at beginning
                else:
                    info_parts.append(f"[{source}] {snippet}")
            elif title:
                info_parts.append(f"[{source}] {title}")
        
        if info_parts:
            combined_info = "\n".join(info_parts)
            
            search_summary = f"""Thông tin tìm kiếm mới nhất về '{query}':

{combined_info}

(Nguồn: Tìm kiếm thời gian thực ngày {current_date})"""
            
            return search_summary
        
        return ""
    
    async def search_and_get_info(self, user_query: str) -> Optional[str]:
        """
        MAIN METHOD: Improved search với better accuracy
        """
        try:
            if not self._should_search(user_query):
                logger.info(f"🚫 No realtime search needed for: {user_query}")
                return None
            
            logger.info(f"🚀 Starting IMPROVED realtime search for: {user_query}")
            
            search_query = self._optimize_search_query(user_query)
            all_results = []
            
            # Strategy 1: Wikipedia Vietnam (highest priority for Vietnamese content)
            logger.info("📚 Searching Wikipedia Vietnam...")
            wiki_results = await self.search_wikipedia_vietnam(search_query)
            all_results.extend(wiki_results)
            
            # Strategy 2: DuckDuckGo (reliable)
            logger.info("🦆 Searching DuckDuckGo...")
            duck_results = await self.search_bing(search_query, 2)
            all_results.extend(duck_results)
            
            # Strategy 3: Google scraping (if not enough results)
            if len(all_results) < 2:
                logger.info("🔍 Searching Google (backup)...")
                google_results = await self.search_google(search_query, 2)
                all_results.extend(google_results)
            
            if all_results:
                info = self._extract_key_info(all_results, user_query)
                if info:
                    logger.info(f"✅ FOUND CURRENT INFO: {len(info)} characters")
                    logger.debug(f"Search results preview: {info[:200]}...")
                    return info
            
            logger.warning(f"❌ No current search results found for: {user_query}")
            return None
            
        except Exception as e:
            logger.error(f"💥 Search and get info failed: {e}")
            return None
    
    def _optimize_search_query(self, user_query: str) -> str:
        """IMPROVED query optimization with current context"""
        
        # UPDATED optimizations với thông tin 2024-2025
        query_optimizations = {
            "chủ tịch nước việt nam": "Lương Cường chủ tịch nước Việt Nam 2024 2025",
            "chủ tịch nước vn": "Lương Cường chủ tịch nước Việt Nam 2024", 
            "thủ tướng việt nam": "Phạm Minh Chính thủ tướng Việt Nam 2024",
            "president vietnam": "Lương Cường president Vietnam 2024",
            "giá vàng": "giá vàng hôm nay Việt Nam",
            "tỷ giá usd": "tỷ giá USD VND hôm nay",
            "thời tiết hà nội": "thời tiết Hà Nội hôm nay",
            "thời tiết tp hồ chí minh": "thời tiết TP.HCM hôm nay",
            "bitcoin": "giá Bitcoin hôm nay"
        }
        
        query_lower = user_query.lower()
        
        # Tìm optimization phù hợp
        for key, optimized in query_optimizations.items():
            if key in query_lower:
                logger.info(f"🎯 Optimized query: '{user_query}' -> '{optimized}'")
                return optimized
        
        # Thêm context năm hiện tại
        if any(word in query_lower for word in ["hiện tại", "bây giờ", "ai là"]):
            optimized = f"{user_query} 2024 2025"
            logger.info(f"🎯 Added current context: '{user_query}' -> '{optimized}'")
            return optimized
        
        return user_query
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search statistics"""
        return {
            "cache_size": len(self.cache),
            "cache_ttl_seconds": self.cache_ttl,
            "search_methods": [
                "Wikipedia Vietnam (Priority)",
                "DuckDuckGo (Reliable)", 
                "Google Scraping (Backup)"
            ],
            "cost": "FREE",
            "improvements": [
                "Shorter cache TTL for political info",
                "Multiple search strategies",
                "Current year context addition",
                "Detailed Wikipedia content extraction"
            ]
        }

# Global instance
realtime_search_service = RealtimeSearchService()