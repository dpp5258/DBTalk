import json
import os
from pathlib import Path
import base64
from cryptography.fernet import Fernet

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".text_submission_system"
        self.config_file = self.config_dir / "config.json"
        self.key_file = self.config_dir / "key.key"
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(exist_ok=True)
    
    def _get_encryption_key(self):
        """获取或创建加密密钥"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key
    
    def save_config(self, mongodb_uri):
        """保存MongoDB连接配置（加密）"""
        try:
            key = self._get_encryption_key()
            cipher = Fernet(key)
            encrypted_uri = cipher.encrypt(mongodb_uri.encode())
            config = {
                'mongodb_uri_encrypted': base64.b64encode(encrypted_uri).decode('ascii')
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def load_config(self):
        """加载MongoDB连接配置"""
        try:
            if not self.config_file.exists():
                return None
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            if 'mongodb_uri_encrypted' in config:
                key = self._get_encryption_key()
                cipher = Fernet(key)
                encrypted_uri = base64.b64decode(config['mongodb_uri_encrypted'])
                mongodb_uri = cipher.decrypt(encrypted_uri).decode()
                return mongodb_uri
            return None
        except Exception as e:
            print(f"加载配置失败: {e}")
            return None
    
    def test_connection(self, mongodb_uri):
        """测试MongoDB连接"""
        try:
            from pymongo import MongoClient
            client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            return True, "连接成功！"
        except Exception as e:
            return False, f"连接失败: {e}"