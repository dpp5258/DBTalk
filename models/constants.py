"""
全局常量定义
消除魔法字符串，统一数据标准
"""

class UserRole:
    ADMIN = 'admin'
    USER = 'user'

class SubmissionStatus:
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

class InitialAdmin:
    USERNAME = 'dpp'
    # 注意：实际生产中密码不应硬编码在常量中，这里仅用于首次初始化参考
    # 建议在 service 层处理默认密码生成
    DEFAULT_PASSWORD = 'dpp5258'