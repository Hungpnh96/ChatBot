# System Prompts Directory

Thư mục này chứa các system prompts được phân loại theo chức năng và mức độ cần độ chính xác thực tế.

## Cấu trúc thư mục

```
system_prompts/
├── README.md                    # File này
├── base/                        # Prompts cơ bản
│   ├── general_chat.txt         # Chat chung
│   └── personality.txt          # Tính cách Bixby
├── high_accuracy/               # Cần độ chính xác cao - sử dụng API thực tế
│   ├── weather.txt              # Thời tiết
│   ├── news.txt                 # Tin tức
│   ├── government_info.txt      # Thông tin chính phủ
│   ├── current_events.txt       # Sự kiện hiện tại
│   └── real_time_data.txt       # Dữ liệu thời gian thực
├── medium_accuracy/             # Độ chính xác trung bình
│   ├── knowledge_base.txt       # Kiến thức chung
│   └── recommendations.txt      # Gợi ý
└── low_accuracy/                # Độ chính xác thấp - AI tự trả lời
    ├── creative.txt             # Sáng tạo
    └── entertainment.txt        # Giải trí
```

## Phân loại theo mức độ cần API thực tế

### 🔴 HIGH ACCURACY (Cần API thực tế)
- **Thời tiết**: Cần API weather service
- **Tin tức**: Cần API news service  
- **Thông tin chính phủ**: Cần API government data
- **Sự kiện hiện tại**: Cần API events service
- **Dữ liệu thời gian thực**: Cần các API real-time

### 🟡 MEDIUM ACCURACY (Có thể dùng cache)
- **Kiến thức chung**: Có thể cache trong thời gian ngắn
- **Gợi ý**: Dựa trên dữ liệu có sẵn

### 🟢 LOW ACCURACY (AI tự trả lời)
- **Sáng tạo**: AI có thể tự tạo nội dung
- **Giải trí**: Không cần dữ liệu thực tế

## Cách sử dụng

1. **Load prompt theo context**: Khi user hỏi về thời tiết, load `high_accuracy/weather.txt`
2. **Call API tương ứng**: Sử dụng service tương ứng để lấy dữ liệu thực tế
3. **Combine với AI response**: Kết hợp dữ liệu thực tế với AI response

## API Services cần implement

### Weather Service
- OpenWeatherMap API
- AccuWeather API
- Weather.gov API

### News Service  
- NewsAPI.org
- GNews API
- RSS feeds

### Government Info Service
- Government APIs
- Official websites scraping
- Public data APIs

### Real-time Data Service
- Stock market APIs
- Currency exchange APIs
- Traffic APIs
- Social media APIs
