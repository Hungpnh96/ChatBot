"""
News Service - Lấy tin tức thực tế
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class NewsService:
    """Service để lấy tin tức từ các API"""
    
    def __init__(self):
        from config.settings import settings
        self.api_key = settings.news_api_key or ''
        self.base_url = "https://newsapi.org/v2"
        self.cache = {}
        self.cache_duration = timedelta(minutes=15)  # Cache 15 phút
        
    def get_top_headlines(self, country: str = "vn", category: str = None, page_size: int = 10) -> Dict[str, Any]:
        """Lấy tin tức hàng đầu"""
        try:
            # Kiểm tra cache
            cache_key = f"headlines_{country}_{category}_{page_size}"
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if datetime.now() - cached_data['timestamp'] < self.cache_duration:
                    logger.info(f"Using cached news data for {country}")
                    return cached_data['data']
            
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'News API key not configured',
                    'message': 'Em chưa được cấu hình để lấy tin tức thực tế.'
                }
            
            url = f"{self.base_url}/top-headlines"
            params = {
                'country': country,
                'pageSize': page_size,
                'apiKey': self.api_key,
                'language': 'vi'
            }
            
            if category:
                params['category'] = category
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['status'] == 'ok':
                    articles = []
                    for article in data['articles']:
                        if article['title'] and article['title'] != '[Removed]':
                            articles.append({
                                'title': article['title'],
                                'description': article['description'] or '',
                                'url': article['url'],
                                'source': article['source']['name'],
                                'published_at': article['publishedAt'],
                                'content': article['content'] or ''
                            })
                    
                    result = {
                        'success': True,
                        'total_results': data['totalResults'],
                        'articles': articles,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Cache kết quả
                    self.cache[cache_key] = {
                        'data': result,
                        'timestamp': datetime.now()
                    }
                    
                    return result
                else:
                    return {
                        'success': False,
                        'error': 'API returned error',
                        'message': 'Em không thể lấy tin tức lúc này.'
                    }
            else:
                logger.error(f"News API error: {response.status_code}")
                return {
                    'success': False,
                    'error': f'API error: {response.status_code}',
                    'message': 'Em không thể kết nối với dịch vụ tin tức.'
                }
                
        except requests.exceptions.Timeout:
            logger.error("News API timeout")
            return {
                'success': False,
                'error': 'API timeout',
                'message': 'Em không thể kết nối với dịch vụ tin tức.'
            }
        except Exception as e:
            logger.error(f"News service error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Em gặp lỗi khi lấy tin tức.'
            }
    
    def search_news(self, query: str, language: str = "vi", page_size: int = 10) -> Dict[str, Any]:
        """Tìm kiếm tin tức"""
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'News API key not configured',
                    'message': 'Em chưa được cấu hình để tìm kiếm tin tức.'
                }
            
            url = f"{self.base_url}/everything"
            params = {
                'q': query,
                'language': language,
                'pageSize': page_size,
                'apiKey': self.api_key,
                'sortBy': 'publishedAt'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['status'] == 'ok':
                    articles = []
                    for article in data['articles']:
                        if article['title'] and article['title'] != '[Removed]':
                            articles.append({
                                'title': article['title'],
                                'description': article['description'] or '',
                                'url': article['url'],
                                'source': article['source']['name'],
                                'published_at': article['publishedAt'],
                                'content': article['content'] or ''
                            })
                    
                    return {
                        'success': True,
                        'query': query,
                        'total_results': data['totalResults'],
                        'articles': articles,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {
                        'success': False,
                        'error': 'API returned error',
                        'message': 'Em không thể tìm kiếm tin tức.'
                    }
            else:
                return {
                    'success': False,
                    'error': f'API error: {response.status_code}',
                    'message': 'Em không thể kết nối với dịch vụ tin tức.'
                }
                
        except Exception as e:
            logger.error(f"News search error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Em gặp lỗi khi tìm kiếm tin tức.'
            }
    
    def format_news_response(self, news_data: Dict[str, Any], max_articles: int = 3) -> str:
        """Format tin tức thành text"""
        if not news_data.get('success'):
            return news_data.get('message', 'Em không thể lấy tin tức.')
        
        articles = news_data.get('articles', [])
        if not articles:
            return "Em không tìm thấy tin tức nào phù hợp."
        
        response = "Em đã tìm thấy tin tức mới nhất:\n\n"
        
        for i, article in enumerate(articles[:max_articles]):
            title = article['title']
            source = article['source']
            published_at = article['published_at']
            
            # Format thời gian
            try:
                dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                time_str = dt.strftime('%d/%m/%Y %H:%M')
            except:
                time_str = published_at
            
            response += f"{i+1}. {title}\n"
            response += f"   Nguồn: {source} - {time_str}\n\n"
        
        if len(articles) > max_articles:
            response += f"... và {len(articles) - max_articles} tin tức khác."
        
        return response

# Singleton instance
news_service = NewsService()
