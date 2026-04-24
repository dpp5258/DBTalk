from utils.db import Database
from models.submission import SubmissionModel
from models.constants import SubmissionStatus
from bson import ObjectId

class SubmissionService:
    def __init__(self):
        self.db = Database()

    def get_all_submissions(self):
        """获取所有提交记录（供管理员）"""
        if not self.db.is_connected:
            return []
        # 修改：直接操作 DB，不再依赖 db.py 中的业务方法
        return list(self.db.db.submissions.find().sort("created_at", -1))

    def get_approved_public_submissions(self):
        """获取已批准且非公告的提交（供交流广场）"""
        if not self.db.is_connected:
            return []
        # 修改：直接操作 DB
        return list(self.db.db.submissions.find(
            {"status": SubmissionStatus.APPROVED, "is_announcement": {"$ne": True}}
        ).sort("created_at", -1))

    def get_user_submissions(self, username):
        """获取指定用户的提交历史"""
        if not self.db.is_connected:
            return []
        # 修改：直接操作 DB
        return list(self.db.db.submissions.find(
            {"username": username}
        ).sort("created_at", -1))

    def approve_submission(self, submission_id):
        """批准提交"""
        if not self.db.is_connected:
            return False
        # 修改：直接操作 DB
        try:
            result = self.db.db.submissions.update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": {"status": SubmissionStatus.APPROVED}}
            )
            return result.modified_count > 0
        except Exception:
            return False

    def reject_submission(self, submission_id):
        """拒绝提交"""
        if not self.db.is_connected:
            return False
        # 修改：直接操作 DB
        try:
            result = self.db.db.submissions.update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": {"status": SubmissionStatus.REJECTED}}
            )
            return result.modified_count > 0
        except Exception:
            return False

    def create_announcement(self, admin_username, title, content):
        """发布公告"""
        if not self.db.is_connected:
            raise Exception("数据库未连接")
        
        # 使用模型构建文档
        doc = SubmissionModel.create_document(admin_username, f"[公告] {title}", content, is_announcement=True)
        # 公告默认直接批准
        doc['status'] = SubmissionStatus.APPROVED
        
        try:
            self.db.db.submissions.insert_one(doc)
            return True
        except Exception as e:
            raise Exception(f"发布失败: {str(e)}")

    def get_submission_by_id(self, submission_id_str):
        """根据ID获取提交详情"""
        if not self.db.is_connected:
            return None
        try:
            return self.db.db.submissions.find_one({"_id": ObjectId(submission_id_str)})
        except Exception:
            return None

    def create_submission(self, username: str, title: str, content: str) -> bool:
        """
        创建新的文本提交
        :param username: 用户名
        :param title: 标题
        :param content: 内容
        :return: 是否成功
        """
        if not self.db.is_connected:
            return False
        
        try:
            # 使用模型构建标准文档
            doc = SubmissionModel.create_document(username, title, content)
            self.db.db.submissions.insert_one(doc)
            return True
        except Exception as e:
            print(f"创建提交失败: {e}")
            return False
