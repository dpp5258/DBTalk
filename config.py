import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # MongoDB配置
    MONGODB_URI = os.getenv("MONGODB_URI", "")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "text_submission_db")
    
    # 应用配置
    APP_NAME = "文本提交系统"
    APP_VERSION = "1.0.0"
    
    @classmethod
    def is_configured(cls):
        """检查是否已配置MongoDB连接"""
        return bool(cls.MONGODB_URI and cls.MONGODB_URI.startswith("mongodb+srv://"))