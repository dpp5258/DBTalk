from utils.db import Database
from models.constants import UserRole, InitialAdmin
from models.user import UserModel

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
