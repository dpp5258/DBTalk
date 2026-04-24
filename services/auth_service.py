import hashlib
from datetime import datetime
from utils.db import Database
from models.constants import UserRole, InitialAdmin

class AuthService:
    def __init__(self):
        self.db = Database()
        # 在初始化时确保初始管理员存在
        self.ensure_initial_admin()

    @staticmethod
    def hash_password(password: str) -> str:
        """密码 SHA256 哈希"""
        return hashlib.sha256(password.encode()).hexdigest()

    def ensure_initial_admin(self):
        """确保初始管理员账号存在"""
        if not self.db.is_connected:
            return
        
        # 检查是否存在任何管理员，或者特指初始管理员
        # 这里我们检查是否存在初始管理员用户，如果不存在则创建
        admin = self.db.db.users.find_one({"username": InitialAdmin.USERNAME})
        if not admin:
            default_admin = {
                "username": InitialAdmin.USERNAME,
                "password": self.hash_password(InitialAdmin.DEFAULT_PASSWORD),
                "email": "admin@example.com",
                "role": UserRole.ADMIN,
                "created_at": datetime.now(),
                "is_active": True
            }
            try:
                self.db.db.users.insert_one(default_admin)
                print(f"✅ 已创建默认初始管理员: {InitialAdmin.USERNAME} / {InitialAdmin.DEFAULT_PASSWORD}")
            except Exception as e:
                print(f"⚠️ 创建初始管理员失败: {e}")

    def login(self, username: str, password: str) -> dict:
        """
        用户登录
        :return: 用户字典如果成功，否则 None
        """
        if not self.db.is_connected:
            return None
        
        hashed_pwd = self.hash_password(password)
        user = self.db.db.users.find_one({
            "username": username,
            "password": hashed_pwd,
            "is_active": True
        })
        # 移除密码字段后返回
        if user:
            user.pop('password', None)
        return user

    def register(self, username: str, password: str, email: str, role: str = UserRole.USER) -> tuple:
        """
        用户注册
        :return: (success: bool, message: str)
        """
        if not self.db.is_connected:
            return False, "数据库未连接"
        
        if self.db.db.users.find_one({"username": username}):
            return False, "用户名已存在"
        
        try:
            user_doc = {
                "username": username,
                "password": self.hash_password(password),
                "email": email,
                "role": role,
                "is_active": True,
                "created_at": self.db.db.command('eval', 'new Date()') # 简单获取服务器时间，或使用 python datetime
            }
            # 修正：使用 python datetime 更稳妥
            from datetime import datetime
            user_doc['created_at'] = datetime.now()
            
            self.db.db.users.insert_one(user_doc)
            return True, "注册成功"
        except Exception as e:
            return False, f"注册失败: {str(e)}"