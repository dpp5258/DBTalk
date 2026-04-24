from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import hashlib
from config import Config

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
            self._ensure_admin_exists()
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            self.is_connected = False
            return False
    
    def _ensure_admin_exists(self):
        """确保存在管理员账号"""
        if not self.is_connected:
            return
        admin = self.db.users.find_one({"role": "admin"})
        if not admin:
            default_admin = {
                "username": "dpp",
                "password": self.hash_password("dpp5258"),
                "email": "admin@example.com",
                "role": "admin",
                "created_at": datetime.now(),
                "is_active": True
            }
            self.db.users.insert_one(default_admin)
            print("✅ 已创建默认管理员: admin / admin123")
    
    def hash_password(self, password):
        """密码加密"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate_user(self, username, password):
        """用户认证"""
        if not self.is_connected:
            return None
        user = self.db.users.find_one({
            "username": username,
            "password": self.hash_password(password),
            "is_active": True
        })
        return user
    
    def create_user(self, username, password, email, role="user"):
        """创建新用户"""
        if not self.is_connected:
            return False, "数据库未连接"
        if self.db.users.find_one({"username": username}):
            return False, "用户名已存在"
        user = {
            "username": username,
            "password": self.hash_password(password),
            "email": email,
            "role": role,
            "created_at": datetime.now(),
            "is_active": True
        }
        self.db.users.insert_one(user)
        return True, "用户创建成功"
    
    def create_submission(self, username, title, content):
        """创建文本提交"""
        if not self.is_connected:
            return None
        submission = {
            "username": username,
            "title": title,
            "content": content,
            "created_at": datetime.now(),
            "status": "pending"
        }
        result = self.db.submissions.insert_one(submission)
        return result.inserted_id
    
    def get_user_submissions(self, username):
        """获取用户的提交记录"""
        if not self.is_connected:
            return []
        return list(self.db.submissions.find(
            {"username": username}
        ).sort("created_at", -1))
    
    def get_all_submissions(self):
        """获取所有提交"""
        if not self.is_connected:
            return []
        return list(self.db.submissions.find().sort("created_at", -1))
    
    def update_submission_status(self, submission_id, status):
        """更新提交状态"""
        if not self.is_connected:
            return False
        from bson.objectid import ObjectId
        result = self.db.submissions.update_one(
            {"_id": ObjectId(submission_id)},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0
    
    def get_all_users(self):
        """获取所有用户（不返回密码）"""
        if not self.is_connected:
            return []
        return list(self.db.users.find({}, {"password": 0}))
    
    def get_stats(self):
        """获取统计信息"""
        if not self.is_connected:
            return None
        return {
            "users": self.db.users.count_documents({}),
            "submissions": self.db.submissions.count_documents({}),
            "pending": self.db.submissions.count_documents({"status": "pending"})
        }

    def get_approved_submissions(self):
        """获取所有已批准且非公告的提交（用于交流广场）"""
        if not self.is_connected:
            return []
        # 排除公告 (is_announcement != True) 且状态为 approved
        return list(self.db.submissions.find(
            {"status": "approved", "is_announcement": {"$ne": True}}
        ).sort("created_at", -1))
