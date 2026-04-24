from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PIL import Image, ImageQt
from bson import ObjectId
import os
from models.constants import SubmissionStatus
from services.submission_service import SubmissionService
from services.user_service import UserService
from views.user_settings_window import UserSettingsWindow

class UserWindow(QMainWindow):
    def __init__(self, parent, user):
        super().__init__()
        self.parent = parent
        self.user = user
        self.submission_service = SubmissionService()
        self.user_service = UserService()
        self.avatar_pixmap = None

        self.setWindowTitle(f"用户面板 - {user['username']}")
        self.resize(600, 700)
        self.setMinimumSize(500, 600)

        self.setup_menu()
        self.setup_ui()

    def setup_menu(self):
        menubar = QMenuBar()
        self.setMenuBar(menubar)

        settings_menu = menubar.addMenu("设置")
        settings_action = settings_menu.addAction("账号设置")
        settings_action.triggered.connect(self.open_settings)
        settings_menu.addSeparator()
        logout_action = settings_menu.addAction("登出")
        logout_action.triggered.connect(self.logout)

    def open_settings(self):
        self.settings_win = UserSettingsWindow(self, self.user, self.user_service)
        self.settings_win.show()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 欢迎栏
        welcome = QFrame()
        welcome.setStyleSheet("background-color: #e3f2fd;")
        welcome.setFixedHeight(60)
        welcome_layout = QHBoxLayout(welcome)
        welcome_label = QLabel(f"欢迎，{self.user['username']}!")
        welcome_label.setStyleSheet("font-size:14px; font-weight:bold;")
        welcome_layout.addWidget(welcome_label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(welcome)

        # 标签页
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # 提交页面
        submit_tab = QWidget()
        tabs.addTab(submit_tab, "提交文本")
        self.setup_submit_tab(submit_tab)

        # 历史页面
        history_tab = QWidget()
        tabs.addTab(history_tab, "提交历史")
        self.setup_history_tab(history_tab)

        # 广场页面
        community_tab = QWidget()
        tabs.addTab(community_tab, "交流广场")
        self.setup_community_tab(community_tab)

        # 个人信息
        profile_tab = QWidget()
        tabs.addTab(profile_tab, "个人信息")
        self.setup_profile_tab(profile_tab)

    # ------------------------------
    # 提交文本页面
    # ------------------------------
    def setup_submit_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.addWidget(QLabel("提交新文本"), alignment=Qt.AlignmentFlag.AlignCenter)

        form = QFormLayout()
        self.title_input = QLineEdit()
        self.content_input = QTextEdit()
        form.addRow("标题:", self.title_input)
        form.addRow("内容:", self.content_input)
        layout.addLayout(form)

        submit_btn = QPushButton("提交")
        submit_btn.setStyleSheet("background:#4CAF50; color:white; font-weight:bold;")
        submit_btn.clicked.connect(self.submit_text)
        layout.addWidget(submit_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def submit_text(self):
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()

        if not title:
            QMessageBox.critical(self, "错误", "请输入标题")
            return
        if not content:
            QMessageBox.critical(self, "错误", "请输入内容")
            return

        ok = self.submission_service.create_submission(self.user['username'], title, content)
        if ok:
            QMessageBox.information(self, "成功", "提交成功！")
            self.title_input.clear()
            self.content_input.clear()
            self.refresh_history()
        else:
            QMessageBox.critical(self, "错误", "提交失败")

    # ------------------------------
    # 提交历史页面
    # ------------------------------
    def setup_history_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.addWidget(QLabel("提交历史"), alignment=Qt.AlignmentFlag.AlignCenter)

        self.history_tree = QTreeWidget()
        self.history_tree.setColumnCount(3)
        self.history_tree.setHeaderLabels(["提交时间", "标题", "状态"])
        self.history_tree.setColumnWidth(0, 150)
        self.history_tree.setColumnWidth(1, 250)
        self.history_tree.setColumnWidth(2, 80)
        layout.addWidget(self.history_tree)

        # 按钮
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet("background:#2196F3; color:white;")
        refresh_btn.clicked.connect(self.refresh_history)

        edit_btn = QPushButton("编辑选中")
        edit_btn.setStyleSheet("background:#FF9800; color:white;")
        edit_btn.clicked.connect(self.edit_selected)

        del_btn = QPushButton("删除选中")
        del_btn.setStyleSheet("background:#f44336; color:white;")
        del_btn.clicked.connect(self.delete_selected)

        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        layout.addLayout(btn_layout)

        self.history_tree.itemDoubleClicked.connect(self.show_history_detail)
        self.refresh_history()

    def refresh_history(self):
        self.history_tree.clear()
        subs = self.submission_service.get_user_submissions(self.user['username'])
        if not subs:
            return
        for s in subs:
            t = s['created_at'].strftime("%Y-%m-%d %H:%M") if s.get('created_at') else "未知"
            item = QTreeWidgetItem([t, s['title'], s['status']])
            item.setData(0, Qt.ItemDataRole.UserRole, str(s['_id']))
            self.history_tree.addTopLevelItem(item)

    def show_history_detail(self, item):
        sub_id = item.data(0, Qt.ItemDataRole.UserRole)
        doc = self.submission_service.get_submission_by_id(sub_id)
        if doc:
            self.show_content_dialog(doc['title'], doc['content'], doc['username'])

    def edit_selected(self):
        item = self.history_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请选择记录")
            return
        sub_id = item.data(0, Qt.ItemDataRole.UserRole)
        doc = self.submission_service.get_submission_by_id(sub_id)
        if doc and doc['username'] == self.user['username']:
            self.show_edit_dialog(doc)

    def delete_selected(self):
        item = self.history_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请选择记录")
            return
        sub_id = item.data(0, Qt.ItemDataRole.UserRole)
        title = item.text(1)
        if QMessageBox.question(self, "确认", f"确定删除《{title}》？") == QMessageBox.StandardButton.Yes:
            ok, msg = self.submission_service.delete_submission(sub_id, self.user['username'])
            QMessageBox.information(self, "结果", msg)
            self.refresh_history()

    def show_edit_dialog(self, doc):
        dlg = QDialog(self)
        dlg.setWindowTitle("编辑提交")
        dlg.resize(500, 450)
        dlg.setMinimumSize(400, 350)
        layout = QVBoxLayout(dlg)

        title = QLineEdit(doc['title'])
        content = QTextEdit(doc['content'])
        layout.addWidget(QLabel("标题:"))
        layout.addWidget(title)
        layout.addWidget(QLabel("内容:"))
        layout.addWidget(content)

        def save():
            t = title.text().strip()
            c = content.toPlainText().strip()
            if not t or not c:
                QMessageBox.warning(dlg, "提示", "不能为空")
                return
            ok, msg = self.submission_service.update_submission(str(doc['_id']), self.user['username'], t, c)
            QMessageBox.information(dlg, "结果", msg)
            if ok:
                dlg.accept()
                self.refresh_history()

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("background:#4CAF50; color:white;")
        save_btn.clicked.connect(save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dlg.close)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        dlg.exec()

    # ------------------------------
    # 交流广场页面
    # ------------------------------
    def setup_community_tab(self, parent):
        layout = QVBoxLayout(parent)
        toolbar = QFrame()
        toolbar.setStyleSheet("background:#f0f0f0;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.addWidget(QLabel("公开交流内容（已批准）"))
        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet("background:#2196F3; color:white;")
        refresh_btn.clicked.connect(self.refresh_community)
        toolbar_layout.addWidget(refresh_btn)
        layout.addWidget(toolbar)

        self.comm_tree = QTreeWidget()
        self.comm_tree.setColumnCount(3)
        self.comm_tree.setHeaderLabels(["发布时间", "作者", "标题"])
        self.comm_tree.setColumnWidth(0, 150)
        self.comm_tree.setColumnWidth(1, 100)
        self.comm_tree.setColumnWidth(2, 300)
        layout.addWidget(self.comm_tree)

        self.comm_tree.itemDoubleClicked.connect(self.show_community_detail)
        self.refresh_community()

    def refresh_community(self):
        self.comm_tree.clear()
        subs = self.submission_service.get_approved_public_submissions()
        if not subs:
            return
        for s in subs:
            t = s['created_at'].strftime("%Y-%m-%d %H:%M") if s.get('created_at') else "未知"
            item = QTreeWidgetItem([t, s['username'], s['title']])
            item.setData(0, Qt.ItemDataRole.UserRole, str(s['_id']))
            self.comm_tree.addTopLevelItem(item)

    def show_community_detail(self, item):
        sub_id = item.data(0, Qt.ItemDataRole.UserRole)
        doc = self.submission_service.get_submission_by_id(sub_id)
        if doc:
            self.show_content_dialog(doc['title'], doc['content'], doc['username'])

    def show_content_dialog(self, title, content, author):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"查看 - {title}")
        dlg.resize(500, 400)
        dlg.setMinimumSize(400, 300)
        layout = QVBoxLayout(dlg)

        header = QFrame()
        header.setStyleSheet("background:#e3f2fd;")
        h_layout = QVBoxLayout(header)
        h_layout.addWidget(QLabel(title))
        h_layout.addWidget(QLabel(f"作者: {author}"))
        layout.addWidget(header)

        text = QTextEdit()
        text.setPlainText(content)
        text.setReadOnly(True)
        layout.addWidget(text)

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("background:#f44336; color:white;")
        close_btn.clicked.connect(dlg.close)
        layout.addWidget(close_btn)
        dlg.exec()

    # ------------------------------
    # 个人信息页面
    # ------------------------------
    def setup_profile_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(30, 20, 30, 20)

        # 头像
        self.avatar_label = QLabel("[暂无头像]")
        self.avatar_label.setStyleSheet("background:#f0f0f0;")
        self.avatar_label.setFixedSize(300, 300)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 信息
        user_data = self.user_service.get_user_by_username(self.user['username'])
        email = user_data.get('email', '未设置') if user_data else '未设置'
        reg = self.user.get('created_at', '未知')
        if hasattr(reg, 'strftime'):
            reg = reg.strftime("%Y-%m-%d %H:%M")

        layout.addWidget(QLabel(f"用户名：{self.user['username']}"))
        layout.addWidget(QLabel(f"邮箱：{email}"))
        layout.addWidget(QLabel(f"注册时间：{reg}"))

        tip = QLabel("💡 修改信息请前往：设置 → 账号设置")
        tip.setStyleSheet("color:#666;")
        layout.addWidget(tip)

        self.refresh_avatar()

    def refresh_avatar(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, "avatars", f"{self.user['username']}.jpg")
        if os.path.exists(path):
            img = Image.open(path).resize((300, 300), Image.LANCZOS)
            self.avatar_pixmap = ImageQt.toqpixmap(img)
            self.avatar_label.setPixmap(self.avatar_pixmap)
        else:
            self.avatar_label.setText("[暂无头像]")

    # ------------------------------
    # 登出
    # ------------------------------
    def logout(self):
        if QMessageBox.question(self, "确认", "确定登出？") == QMessageBox.StandardButton.Yes:
            self.close()
            self.parent.show()

    def closeEvent(self, event):
        self.logout()
        event.ignore()