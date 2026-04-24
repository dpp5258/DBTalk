from datetime import datetime
from .constants import SubmissionStatus

class SubmissionModel:
    def __init__(self, title, content, username, status=SubmissionStatus.PENDING, is_announcement=False, created_at=None, submission_id=None):
        self.title = title
        self.content = content
        self.username = username
        self.status = status
        self.is_announcement = is_announcement
        self.created_at = created_at or datetime.now()
        self.submission_id = submission_id # ObjectId

    @staticmethod
    def create_document(username, title, content, is_announcement=False):
        """
        构建标准的 MongoDB 提交文档
        :param username: 提交者用户名
        :param title: 标题
        :param content: 内容
        :param is_announcement: 是否为公告
        :return: dict
        """
        return {
            "username": username,
            "title": title,
            "content": content,
            "status": SubmissionStatus.APPROVED if is_announcement else SubmissionStatus.PENDING,
            "is_announcement": is_announcement,
            "created_at": datetime.now()
        }

    def to_dict(self):
        """转换为字典用于数据库插入或更新"""
        doc = {
            "username": self.username,
            "title": self.title,
            "content": self.content,
            "status": self.status,
            "is_announcement": self.is_announcement,
            "created_at": self.created_at
        }
        if self.submission_id:
            doc["_id"] = self.submission_id
        return doc