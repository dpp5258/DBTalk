from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from utils.db import Database
from models.constants import UserRole, SubmissionStatus, InitialAdmin
from models.submission import SubmissionModel
from services.submission_service import SubmissionService
from services.user_service import UserService
from bson import ObjectId
from datetime import datetime
import os

class AdminWindow(QMainWindow):
    def __init__(self, parent, admin):
        super().__init__(parent)
        self.parent = parent
        self.admin = admin
        self.db = Database()
        self.submission_service = SubmissionService()
        self.user_service = UserService()

        self.setWindowTitle(f"管理员面板 - {admin['username']}")
        self.resize(900, 700)
        self.setMinimumSize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        # 主部件 + 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ================== 顶部栏 ==================
        top_frame = QFrame()
        top_frame.setStyleSheet("background-color: #1e3c72;")
        top_frame.setFixedHeight(50)
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(20, 0, 20, 0)

        user_label = QLabel(f"管理员: {self.admin['username']}")
        user_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")

        logout_btn = QPushButton("登出")
        logout_btn.setStyleSheet("background-color: #f44336; color: white; font-size: 10px;")
        logout_btn.setFixedWidth(80)
        logout_btn.clicked.connect(self.logout)

        top_layout.addWidget(user_label)
        top_layout.addStretch()
        top_layout.addWidget(logout_btn)
        main_layout.addWidget(top_frame)

        # ================== 标签页 ==================
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # 1. 个人信息
        profile_tab = QWidget()
        tab_widget.addTab(profile_tab, "个人信息")
        self.setup_profile_tab(profile_tab)

        # 2. 公告发布
        announcement_tab = QWidget()
        tab_widget.addTab(announcement_tab, "公告发布")
        self.setup_announcement_tab(announcement_tab)

        # 3. 提交审核
        submissions_tab = QWidget()
        tab_widget.addTab(submissions_tab, "提交审核")
        self.setup_submissions_tab(submissions_tab)

        # 4. 用户管理
        users_tab = QWidget()
        tab_widget.addTab(users_tab, "用户管理")
        self.setup_users_tab(users_tab)

    # ================== 公告发布 ==================
    def setup_announcement_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 10, 20, 10)

        title = QLabel("发布全局公告/内容")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(QLabel("标题:"))
        self.ann_title_entry = QLineEdit()
        self.ann_title_entry.setFixedHeight(30)
        layout.addWidget(self.ann_title_entry)

        layout.addWidget(QLabel("内容:"))
        self.ann_content_text = QTextEdit()
        self.ann_content_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self.ann_content_text)

        post_btn = QPushButton("发布公告")
        post_btn.setStyleSheet("background-color: #FF9800; color: white; font-size: 12px; font-weight: bold;")
        post_btn.clicked.connect(self.post_announcement)
        post_btn.setFixedWidth(150)
        layout.addWidget(post_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def post_announcement(self):
        title = self.ann_title_entry.text().strip()
        content = self.ann_content_text.toPlainText().strip()

        if not title or not content:
            QMessageBox.warning(self, "提示", "标题和内容不能为空")
            return

        try:
            self.submission_service.create_announcement(self.admin['username'], title, content)
            QMessageBox.information(self, "成功", "公告发布成功！")
            self.ann_title_entry.clear()
            self.ann_content_text.clear()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发布失败: {str(e)}")

    # ================== 提交审核 ==================
    def setup_submissions_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(10, 5, 10, 5)

        # 工具栏
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #f0f0f0;")
        toolbar.setFixedHeight(40)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(10, 0, 10, 0)
        tb_layout.addWidget(QLabel("用户提交审核"))
        tb_layout.addStretch()

        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet("background-color: #2196F3; color: white;")
        refresh_btn.clicked.connect(self.refresh_submissions)
        tb_layout.addWidget(refresh_btn)
        layout.addWidget(toolbar)

        # 表格
        self.submissions_tree = QTableWidget()
        self.submissions_tree.setColumnCount(5)
        self.submissions_tree.setHorizontalHeaderLabels(["提交时间", "用户名", "标题", "状态", "操作"])
        self.submissions_tree.setColumnWidth(0, 150)
        self.submissions_tree.setColumnWidth(1, 100)
        self.submissions_tree.setColumnWidth(2, 200)
        self.submissions_tree.setColumnWidth(3, 80)
        self.submissions_tree.setColumnWidth(4, 150)
        self.submissions_tree.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.submissions_tree.itemSelectionChanged.connect(self.on_submission_select)
        self.submissions_tree.doubleClicked.connect(self.on_submission_double_click)
        layout.addWidget(self.submissions_tree)

        # 操作按钮
        action_frame = QFrame()
        action_frame.setStyleSheet("background-color: #f0f0f0;")
        action_frame.setFixedHeight(50)
        af_layout = QHBoxLayout(action_frame)
        af_layout.setContentsMargins(20, 0, 20, 0)

        self.approve_btn = QPushButton("批准")
        self.approve_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.approve_btn.setEnabled(False)
        self.approve_btn.clicked.connect(self.approve_selected)

        self.reject_btn = QPushButton("拒绝")
        self.reject_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.reject_btn.setEnabled(False)
        self.reject_btn.clicked.connect(self.reject_selected)

        af_layout.addWidget(self.approve_btn)
        af_layout.addWidget(self.reject_btn)
        af_layout.addStretch()
        layout.addWidget(action_frame)

        self.refresh_submissions()

    def on_submission_select(self):
        has_selection = len(self.submissions_tree.selectedItems()) > 0
        self.approve_btn.setEnabled(has_selection)
        self.reject_btn.setEnabled(has_selection)

    def on_submission_double_click(self, index):
        row = index.row()
        sub_id = self.submissions_tree.item(row, 0).data(Qt.ItemDataRole.UserRole)
        try:
            sub_doc = self.submission_service.get_submission_by_id(sub_id)
            if sub_doc:
                self.show_submission_detail_dialog(sub_doc)
            else:
                QMessageBox.warning(self, "提示", "提交记录不存在或已被删除")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载详情失败: {str(e)}")

    def show_submission_detail_dialog(self, sub_doc):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"审核提交 - {sub_doc['title']}")
        dialog.resize(600, 500)
        dialog.setMinimumSize(500, 400)
        layout = QVBoxLayout(dialog)

        # 头部
        header = QFrame()
        header.setStyleSheet("background-color: #e3f2fd;")
        h_layout = QVBoxLayout(header)
        title_label = QLabel(sub_doc['title'])
        title_label.setStyleSheet("font-size:14px; font-weight:bold;")
        time_str = sub_doc['created_at'].strftime('%Y-%m-%d %H:%M') if sub_doc['created_at'] else "未知"
        info_label = QLabel(f"作者: {sub_doc['username']} | 时间: {time_str} | 状态: {sub_doc['status']}")
        h_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(info_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # 内容
        content = QTextEdit()
        content.setPlainText(sub_doc['content'])
        content.setReadOnly(True)
        layout.addWidget(content)

        # 按钮
        btn_layout = QHBoxLayout()
        sub_id = str(sub_doc['_id'])
        status = sub_doc['status']

        def do_approve():
            if QMessageBox.question(dialog, "确认", "确定批准？") == QMessageBox.StandardButton.Yes:
                if self.submission_service.approve_submission(sub_id):
                    QMessageBox.information(dialog, "成功", "已批准")
                    dialog.accept()
                    self.refresh_submissions()

        def do_reject():
            if QMessageBox.question(dialog, "确认", "确定拒绝？") == QMessageBox.StandardButton.Yes:
                if self.submission_service.reject_submission(sub_id):
                    QMessageBox.information(dialog, "成功", "已拒绝")
                    dialog.accept()
                    self.refresh_submissions()

        if status == SubmissionStatus.APPROVED:
            btn_layout.addWidget(QLabel("已批准"))
            rej = QPushButton("重新拒绝")
            rej.setStyleSheet("background:#f44336; color:white;")
            rej.clicked.connect(do_reject)
            btn_layout.addWidget(rej)
        elif status == SubmissionStatus.REJECTED:
            btn_layout.addWidget(QLabel("已拒绝"))
            app = QPushButton("重新批准")
            app.setStyleSheet("background:#4CAF50; color:white;")
            app.clicked.connect(do_approve)
            btn_layout.addWidget(app)
        else:
            rej = QPushButton("拒绝")
            rej.setStyleSheet("background:#f44336; color:white;")
            rej.clicked.connect(do_reject)
            app = QPushButton("批准")
            app.setStyleSheet("background:#4CAF50; color:white;")
            app.clicked.connect(do_approve)
            btn_layout.addWidget(rej)
            btn_layout.addWidget(app)

        layout.addLayout(btn_layout)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        dialog.exec()

    def approve_selected(self):
        row = self.submissions_tree.currentRow()
        sub_id = self.submissions_tree.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(self, "确认", "确定批准？") == QMessageBox.StandardButton.Yes:
            if self.submission_service.approve_submission(sub_id):
                QMessageBox.information(self, "成功", "已批准")
                self.refresh_submissions()

    def reject_selected(self):
        row = self.submissions_tree.currentRow()
        sub_id = self.submissions_tree.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(self, "确认", "确定拒绝？") == QMessageBox.StandardButton.Yes:
            if self.submission_service.reject_submission(sub_id):
                QMessageBox.information(self, "成功", "已拒绝")
                self.refresh_submissions()

    def refresh_submissions(self):
        self.submissions_tree.setRowCount(0)
        subs = self.submission_service.get_all_submissions()
        for sub in subs:
            row = self.submissions_tree.rowCount()
            self.submissions_tree.insertRow(row)
            time_str = sub['created_at'].strftime("%Y-%m-%d %H:%M") if sub['created_at'] else "未知"
            is_ann = sub.get('is_announcement', False)
            title = f"[公告] {sub['title']}" if is_ann else sub['title']

            items = [
                time_str,
                sub['username'],
                title,
                sub['status'],
                "双击查看"
            ]
            for col, txt in enumerate(items):
                item = QTableWidgetItem(txt)
                item.setData(Qt.ItemDataRole.UserRole, str(sub['_id']))
                self.submissions_tree.setItem(row, col, item)

    # ================== 用户管理 ==================
    def setup_users_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(10, 5, 10, 5)

        # 工具栏
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #f0f0f0;")
        toolbar.setFixedHeight(40)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(10, 0, 10, 0)
        tb_layout.addWidget(QLabel("用户列表"))
        tb_layout.addStretch()
        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet("background-color: #2196F3; color: white;")
        refresh_btn.clicked.connect(self.refresh_users)
        tb_layout.addWidget(refresh_btn)
        layout.addWidget(toolbar)

        # 表格
        self.users_tree = QTableWidget()
        self.users_tree.setColumnCount(6)
        self.users_tree.setHorizontalHeaderLabels(["用户名", "邮箱", "角色", "注册时间", "状态", "操作"])
        self.users_tree.setColumnWidth(0, 100)
        self.users_tree.setColumnWidth(1, 200)
        self.users_tree.setColumnWidth(2, 80)
        self.users_tree.setColumnWidth(3, 150)
        self.users_tree.setColumnWidth(4, 80)
        self.users_tree.setColumnWidth(5, 80)
        self.users_tree.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.users_tree.doubleClicked.connect(self.on_user_manage_click)
        layout.addWidget(self.users_tree)
        self.refresh_users()

    def refresh_users(self):
        self.users_tree.setRowCount(0)
        users = self.user_service.get_all_users()
        is_initial_admin = self.admin['username'] == InitialAdmin.USERNAME

        for user in users:
            row = self.users_tree.rowCount()
            self.users_tree.insertRow(row)
            reg_time = user['created_at'].strftime("%Y-%m-%d %H:%M") if user.get('created_at') else "未知"
            status = "活跃" if user.get('is_active', True) else "禁用"
            role = user.get('role', UserRole.USER)
            username = user['username']
            action = "管理"

            if username == self.admin['username']:
                action = "本人"
            elif username == InitialAdmin.USERNAME:
                action = "锁定"
            elif role == UserRole.ADMIN and not is_initial_admin:
                action = "锁定"

            items = [username, user['email'], role, reg_time, status, action]
            for col, txt in enumerate(items):
                item = QTableWidgetItem(txt)
                item.setData(Qt.ItemDataRole.UserRole, username)
                self.users_tree.setItem(row, col, item)

    def on_user_manage_click(self, index):
        row = index.row()
        username = self.users_tree.item(row, 0).data(Qt.ItemDataRole.UserRole)
        action = self.users_tree.item(row, 5).text()
        if action == "锁定":
            QMessageBox.warning(self, "提示", "无法操作该用户: 权限不足或受保护")
            return
        current_role = self.users_tree.item(row, 2).text()
        self.open_user_manage_dialog(username, current_role)

    def open_user_manage_dialog(self, username, current_role):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"管理用户: {username}")
        dialog.resize(350, 350)
        dialog.setMinimumSize(300, 300)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(f"用户: {username}"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(QLabel(f"角色: {current_role}"), alignment=Qt.AlignmentFlag.AlignCenter)

        btn_layout = QVBoxLayout()
        is_self = username == self.admin['username']

        # 功能按钮（升级、降级、删用户、改邮箱、重置密码）逻辑完全不变
        def do_promote():
            if QMessageBox.question(dialog, "确认", "升级为管理员？") == QMessageBox.StandardButton.Yes:
                ok, msg = self.user_service.update_role(self.admin['username'], username, UserRole.ADMIN)
                QMessageBox.information(dialog, "结果", msg)
                if ok:
                    dialog.accept()
                    self.refresh_users()

        def do_demote():
            if QMessageBox.question(dialog, "确认", "降级为普通用户？") == QMessageBox.StandardButton.Yes:
                ok, msg = self.user_service.update_role(self.admin['username'], username, UserRole.USER)
                QMessageBox.information(dialog, "结果", msg)
                if ok:
                    dialog.accept()
                    self.refresh_users()

        def do_delete():
            if QMessageBox.warning(dialog, "危险", "确定删除？不可恢复！") == QMessageBox.StandardButton.Yes:
                ok, msg = self.user_service.delete_user(self.admin['username'], username)
                QMessageBox.information(dialog, "结果", msg)
                if ok:
                    dialog.accept()
                    self.refresh_users()

        def do_edit_email():
            email, ok = QInputDialog.getText(dialog, "修改邮箱", "新邮箱:", text=self.get_user_email(username))
            if ok and email.strip():
                res, msg = self.user_service.update_email(self.admin['username'], username, email.strip())
                QMessageBox.information(dialog, "结果", msg)
                self.refresh_users()

        def do_reset_pwd():
            pwd, ok1 = QInputDialog.getText(dialog, "重置密码", "新密码:", QLineEdit.EchoMode.Password)
            confirm, ok2 = QInputDialog.getText(dialog, "确认密码", "再次输入:", QLineEdit.EchoMode.Password)
            if ok1 and ok2 and pwd == confirm and pwd:
                res, msg = self.user_service.reset_password(self.admin['username'], username, pwd)
                QMessageBox.information(dialog, "结果", msg)

        # 按钮显示逻辑和原代码完全一致
        if is_self:
            btn_layout.addWidget(QLabel("当前账号，无法修改角色/删除"))
            e = QPushButton("修改我的邮箱")
            e.clicked.connect(do_edit_email)
            btn_layout.addWidget(e)
            p = QPushButton("修改我的密码")
            p.clicked.connect(do_reset_pwd)
            btn_layout.addWidget(p)
        else:
            if current_role == UserRole.USER:
                a = QPushButton("升级为管理员")
                a.clicked.connect(do_promote)
                btn_layout.addWidget(a)
            e = QPushButton("修改用户邮箱")
            e.clicked.connect(do_edit_email)
            btn_layout.addWidget(e)
            p = QPushButton("重置用户密码")
            p.clicked.connect(do_reset_pwd)
            btn_layout.addWidget(p)
            d = QPushButton("删除用户")
            d.clicked.connect(do_delete)
            btn_layout.addWidget(d)

        layout.addLayout(btn_layout)
        c = QPushButton("关闭")
        c.clicked.connect(dialog.close)
        layout.addWidget(c)
        dialog.exec()

    def get_user_email(self, username):
        u = self.user_service.get_user_by_username(username)
        return u.get('email', '') if u else ''

    # ================== 个人信息 ==================
    def setup_profile_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.addStretch()

        avatar = QLabel("👤")
        avatar.setStyleSheet("background-color:#e0e0e0; font-size:48px;")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(120, 120)
        layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        user_data = self.user_service.get_user_by_username(self.admin['username']) or self.admin
        email = user_data.get('email', '未设置')
        reg = user_data.get('created_at')
        reg_str = reg.strftime("%Y-%m-%d %H:%M") if reg else "未知"
        role = user_data.get('role', UserRole.USER)

        info = [
            ("用户名", self.admin['username']),
            ("邮箱", email),
            ("角色", role),
            ("注册时间", reg_str)
        ]

        for k, v in info:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{k}:"))
            row.addWidget(QLabel(v))
            layout.addLayout(row)

        layout.addStretch()

    # ================== 登出 ==================
    def logout(self):
        if QMessageBox.question(self, "确认", "确定登出？") == QMessageBox.StandardButton.Yes:
            self.close()
            self.parent.show()

    def closeEvent(self, event):
        self.logout()
        event.ignore()