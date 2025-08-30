chatbot/
├── main.py                 # File chính - khởi tạo FastAPI app
├── config/
│   ├── settings.py         # Quản lý config và environment  
│   └── database.py         # Database connection và initialization
├── models/
│   └── schemas.py          # Pydantic models
├── services/
│   ├── ai_service.py       # AI/LangChain logic
│   ├── conversation_service.py  # Conversation management
│   ├── message_service.py  # Message handling
│   └── chat_service.py     # Chat processing
├── api/
│   ├── chat.py            # Chat endpoints
│   ├── conversations.py   # Conversation CRUD endpoints
│   ├── debug.py           # Debug endpoints
│   └── system.py          # Config, stats, health check
└── utils/
    └── logger.py          # Logging configuration