from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import hashlib
from config import Config
# 新增：引入模型常量
from models.constants import UserRole, SubmissionStatus, InitialAdmin

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.client = None
        self.db = None
        self.is_connected = False
        self.connect()
    
    def connect(self):
        """连接到MongoDB"""
        try:
            if not Config.MONGODB_URI:
                print("错误: 未配置MongoDB连接字符串")
                return False
            print("正在连接到MongoDB Atlas...")
            self.client = MongoClient(
                Config.MONGODB_URI,
                server_api=ServerApi('1'),
                serverSelectionTimeoutMS=5000
            )
            self.client.admin.command('ping')
            self.db = self.client[Config.DATABASE_NAME]
            self.is_connected = True
            print("✅ 成功连接到MongoDB Atlas!")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            self.is_connected = False
            return False

