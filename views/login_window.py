from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from views.user_window import UserWindow
from views.admin_window import AdminWindow
from views.settings_window import SettingsWindow
from models.constants import UserRole
from config import Config
from services.auth_service import AuthService
from utils.db import Database
import os

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.auth_service = AuthService()

        self.setWindowTitle("文本提交系统 - 登录")
        self.resize(400, 500)
        self.setMinimumSize(350, 450)

        self.setup_menu()
        self.setup_ui()
        self.check_database_connection()

    def setup_menu(self):
        menubar = QMenuBar()
        self.setMenuBar(menubar)

        file_menu = menubar.addMenu("文件")
        settings_action = file_menu.addAction("云端配置")
        settings_action.triggered.connect(self.open_settings)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)

        help_menu = menubar.addMenu("帮助")
        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)

    def open_settings(self):
        self.settings_win = SettingsWindow(self)
        self.settings_win.show()

    def show_about(self):
        about_text = f"""{Config.APP_NAME} v{Config.APP_VERSION}

一个简单的文本提交管理系统
使用 MongoDB Atlas 云端数据库

© 2024 版权所有"""
        QMessageBox.information(self, "关于", about_text)

    def check_database_connection(self):
        if self.db.is_connected:
            self.connection_status.setText("● 已连接到云端")
            self.connection_status.setStyleSheet("color: #4CAF50;")
        else:
            self.connection_status.setText("● 未连接到云端 (点击文件->云端配置设置)")
            self.connection_status.setStyleSheet("color: #f44336;")

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title = QLabel("文本提交系统")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addSpacing(30)
        main_layout.addWidget(title)

        # 登录框
        login_frame = QFrame()
        login_frame.setStyleSheet("background-color: #f0f0f0;")
        login_frame.setContentsMargins(20, 20, 20, 20)
        frame_layout = QVBoxLayout(login_frame)

        frame_layout.addWidget(QLabel("用户名:"))
        self.username_entry = QLineEdit()
        self.username_entry.setFixedHeight(30)
        frame_layout.addWidget(self.username_entry)

        frame_layout.addWidget(QLabel("密码:"))
        self.password_entry = QLineEdit()
        self.password_entry.setFixedHeight(30)
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        frame_layout.addWidget(self.password_entry)

        # 按钮
        btn_layout = QHBoxLayout()
        login_btn = QPushButton("登录")
        login_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        login_btn.clicked.connect(self.login)
        register_btn = QPushButton("注册")
        register_btn.setStyleSheet("background-color: #2196F3; color: white;")
        register_btn.clicked.connect(self.show_register)
        btn_layout.addWidget(login_btn)
        btn_layout.addWidget(register_btn)
        frame_layout.addLayout(btn_layout)

        main_layout.addWidget(login_frame, stretch=1)

        # 状态栏
        status_bar = QFrame()
        status_bar.setStyleSheet("background-color: #f0f0f0;")
        status_bar.setFixedHeight(30)
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(10, 0, 10, 0)
        self.connection_status = QLabel("正在检查连接...")
        self.connection_status.setStyleSheet("font-size: 9px;")
        status_layout.addWidget(self.connection_status)
        main_layout.addWidget(status_bar)

        # 回车登录
        self.username_entry.returnPressed.connect(self.login)
        self.password_entry.returnPressed.connect(self.login)

    def login(self):
        username = self.username_entry.text().strip()
        password = self.password_entry.text().strip()

        if not username or not password:
            QMessageBox.critical(self, "错误", "请输入用户名和密码")
            return

        user = self.auth_service.login(username, password)
        if user:
            QMessageBox.information(self, "成功", f"欢迎回来, {username}!")

            try:
                from utils.music_manager import MusicManager
                music_mgr = MusicManager()
                music_mgr.play()
            except:
                pass

            self.hide()
            if user.get("role") == UserRole.ADMIN:
                self.next_win = AdminWindow(self, user)
            else:
                self.next_win = UserWindow(self, user)
            self.next_win.show()
        else:
            QMessageBox.critical(self, "错误", "用户名或密码错误")

    def show_register(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("用户注册")
        dialog.resize(350, 450)
        dialog.setMinimumSize(300, 400)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("用户注册"), alignment=Qt.AlignmentFlag.AlignCenter)

        form = QFormLayout()
        self.reg_user = QLineEdit()
        self.reg_pwd = QLineEdit()
        self.reg_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_cfm = QLineEdit()
        self.reg_cfm.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_email = QLineEdit()

        form.addRow("用户名:", self.reg_user)
        form.addRow("密码:", self.reg_pwd)
        form.addRow("确认密码:", self.reg_cfm)
        form.addRow("邮箱:", self.reg_email)
        layout.addLayout(form)

        def do_register():
            u = self.reg_user.text().strip()
            p = self.reg_pwd.text().strip()
            c = self.reg_cfm.text().strip()
            e = self.reg_email.text().strip()

            if not all([u, p, c, e]):
                QMessageBox.critical(dialog, "错误", "请填写所有字段")
                return
            if p != c:
                QMessageBox.critical(dialog, "错误", "两次密码不一致")
                return

            ok, msg = self.auth_service.register(u, p, e)
            if ok:
                QMessageBox.information(dialog, "成功", msg)
                dialog.accept()
            else:
                QMessageBox.critical(dialog, "错误", msg)

        reg_btn = QPushButton("注册")
        reg_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        reg_btn.clicked.connect(do_register)
        layout.addWidget(reg_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        dialog.exec()