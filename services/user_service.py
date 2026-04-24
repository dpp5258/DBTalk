from utils.db import Database
from models.constants import UserRole, InitialAdmin
from models.user import UserModel
from bson import ObjectId

class UserService:
    def __init__(self):
        self.db = Database()

    def get_all_users(self) -> list:
        """获取所有用户（脱敏）"""
        if not self.db.is_connected:
            return []
        return list(self.db.db.users.find({}, {"password": 0}))

    def update_role(self, operator_username: str, target_username: str, new_role: str) -> tuple:
        """
        更新用户角色
        :return: (success: bool, message: str)
        """
        if not self.db.is_connected:
            return False, "数据库未连接"
        
        # 权限校验
        is_initial_admin = (operator_username == InitialAdmin.USERNAME)
        target_is_initial_admin = (target_username == InitialAdmin.USERNAME)
        
        # 1. 不能操作自己
        if operator_username == target_username:
            return False, "不能修改自己的角色"
        
        # 2. 不能操作初始管理员
        if target_is_initial_admin:
            return False, "无法修改初始管理员的角色"
        
        # 3. 只有初始管理员可以管理其他管理员
        if not is_initial_admin:
            # 检查目标当前是否是管理员
            target_user = self.db.db.users.find_one({"username": target_username})
            if target_user and target_user.get('role') == UserRole.ADMIN:
                return False, "权限不足：仅初始管理员可管理其他管理员"

        try:
            result = self.db.db.users.update_one(
                {"username": target_username},
                {"$set": {"role": new_role}}
            )
            if result.modified_count > 0:
                return True, "角色更新成功"
            else:
                return False, "用户不存在或角色未变更"
        except Exception as e:
            return False, f"更新失败: {str(e)}"

    def delete_user(self, operator_username: str, target_username: str) -> tuple:
        """
        删除用户
        :return: (success: bool, message: str)
        """
        if not self.db.is_connected:
            return False, "数据库未连接"
        
        # 权限校验
        is_initial_admin = (operator_username == InitialAdmin.USERNAME)
        target_is_initial_admin = (target_username == InitialAdmin.USERNAME)
        
        # 1. 不能删除自己
        if operator_username == target_username:
            return False, "不能删除自己"
        
        # 2. 不能删除初始管理员
        if target_is_initial_admin:
            return False, "无法删除初始管理员"
        
        # 3. 只有初始管理员可以删除其他管理员
        if not is_initial_admin:
            target_user = self.db.db.users.find_one({"username": target_username})
            if target_user and target_user.get('role') == UserRole.ADMIN:
                return False, "权限不足：仅初始管理员可删除其他管理员"

        try:
            result = self.db.db.users.delete_one({"username": target_username})
            if result.deleted_count > 0:
                return True, "用户删除成功"
            else:
                return False, "用户不存在"
        except Exception as e:
            return False, f"删除失败: {str(e)}"

    def get_user_by_username(self, username: str) -> dict:
        """
        根据用户名获取用户信息（脱敏）
        :param username: 用户名
        :return: 用户字典或 None
        """
        if not self.db.is_connected:
            return None
        try:
            user = self.db.db.users.find_one({"username": username}, {"password": 0})
            return user
        except Exception:
            return None

    def update_email(self, operator_username: str, target_username: str, new_email: str) -> tuple:
        """
        更新用户邮箱
        :param operator_username: 操作者用户名
        :param target_username: 目标用户名
        :param new_email: 新邮箱
        :return: (success: bool, message: str)
        """
        if not self.db.is_connected:
            return False, "数据库未连接"
        
        # 简单权限校验：不能修改初始管理员的核心信息（可选，这里仅做基本保护）
        if target_username == InitialAdmin.USERNAME and operator_username != InitialAdmin.USERNAME:
             return False, "权限不足：仅初始管理员可修改自身信息"

        if not new_email or "@" not in new_email:
            return False, "邮箱格式不正确"

        try:
            result = self.db.db.users.update_one(
                {"username": target_username},
                {"$set": {"email": new_email}}
            )
            if result.modified_count > 0:
                return True, "邮箱更新成功"
            else:
                # 检查用户是否存在
                if self.db.db.users.find_one({"username": target_username}):
                    return True, "邮箱未变更"
                return False, "用户不存在"
        except Exception as e:
            return False, f"更新失败: {str(e)}"

    def reset_password(self, operator_username: str, target_username: str, new_password: str) -> tuple:
        """
        重置用户密码（通常由管理员执行，或用户本人通过旧密码验证后执行）
        此处实现为管理员直接重置
        :param operator_username: 操作者用户名
        :param target_username: 目标用户名
        :param new_password: 新明文密码
        :return: (success: bool, message: str)
        """
        if not self.db.is_connected:
            return False, "数据库未连接"
        
        # 权限校验：同删除/角色修改逻辑
        is_initial_admin = (operator_username == InitialAdmin.USERNAME)
        target_is_initial_admin = (target_username == InitialAdmin.USERNAME)
        
        if target_is_initial_admin and not is_initial_admin:
            return False, "权限不足：仅初始管理员可重置初始管理员密码"
            
        if not new_password or len(new_password) < 6:
            return False, "密码长度至少为6位"

        try:
            from services.auth_service import AuthService
            hashed_pwd = AuthService.hash_password(new_password)
            
            result = self.db.db.users.update_one(
                {"username": target_username},
                {"$set": {"password": hashed_pwd}}
            )
            if result.modified_count > 0:
                return True, "密码重置成功"
            else:
                if self.db.db.users.find_one({"username": target_username}):
                    return True, "密码未变更"
                return False, "用户不存在"
        except Exception as e:
            return False, f"重置失败: {str(e)}"

    def update_avatar(self, username: str, avatar_path: str) -> tuple:
        """
        更新用户头像路径
        :param username: 用户名
        :param avatar_path: 相对或绝对路径
        :return: (success: bool, message: str)
        """
        if not self.db.is_connected:
            return False, "数据库未连接"
        
        try:
            result = self.db.db.users.update_one(
                {"username": username},
                {"$set": {"avatar_path": avatar_path}}
            )
            if result.modified_count > 0:
                return True, "头像更新成功"
            else:
                # 检查用户是否存在
                if self.db.db.users.find_one({"username": username}):
                    return True, "头像路径未变更"
                return False, "用户不存在"
        except Exception as e:
            return False, f"更新失败: {str(e)}"

    def get_user_backup_data(self, username: str) -> dict:
        """
        获取用于本地备份的用户数据
        包含：用户基本信息（脱敏）、所有提交记录
        :param username: 用户名
        :return: 包含用户数据和提交列表的字典
        """
        if not self.db.is_connected:
            raise Exception("数据库未连接")
        
        # 1. 获取用户信息（脱敏）
        user_doc = self.db.db.users.find_one({"username": username}, {"password": 0})
        if not user_doc:
            raise Exception("用户不存在")
        
        # 转换 ObjectId 和 datetime 为字符串，以便 JSON 序列化
        def serialize_doc(doc):
            if doc is None:
                return None
            # 处理 ObjectId
            if isinstance(doc, ObjectId):
                return str(doc)
            # 处理 datetime
            if hasattr(doc, 'isoformat'):
                return doc.isoformat()
            # 处理字典
            if isinstance(doc, dict):
                new_doc = {}
                for k, v in doc.items():
                    new_doc[k] = serialize_doc(v)
                return new_doc
            # 处理列表
            if isinstance(doc, list):
                return [serialize_doc(item) for item in doc]
            # 其他基本类型直接返回
            return doc

        safe_user = serialize_doc(user_doc)
        
        # 2. 获取该用户的所有提交记录
        from services.submission_service import SubmissionService
        sub_service = SubmissionService()
        submissions = sub_service.get_user_submissions(username)
        
        safe_submissions = [serialize_doc(sub) for sub in submissions]
        
        from datetime import datetime
        return {
            "user_info": safe_user,
            "submissions": safe_submissions,
            "backup_time": datetime.now().isoformat()
        }
