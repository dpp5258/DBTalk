from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from utils.config_manager import ConfigManager
from utils.db import Database
from config import Config
from utils.music_manager import MusicManager

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.config_manager = ConfigManager()
        self.music_manager = MusicManager()

        self.setWindowTitle("云端数据库配置")
        self.resize(600, 450)
        self.setMinimumSize(500, 400)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)  # 模态窗口

        self.setup_ui()
        self.load_current_config()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(12)

        # 标题
        title = QLabel("MongoDB Atlas 云端配置")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976D2;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # 说明文字
        info_text = """请配置您的MongoDB Atlas云端数据库连接

1. 访问 https://www.mongodb.com/atlas 注册账号
2. 创建免费集群
3. 获取连接字符串"""
        info_label = QLabel(info_text)
        info_label.setStyleSheet("font-size: 10px; color: #666;")
        main_layout.addWidget(info_label)

        # 连接字符串区域
        main_layout.addWidget(QLabel("MongoDB连接字符串:"))

        example_label = QLabel("示例: mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority")
        example_label.setStyleSheet("font-size: 9px; color: #888;")
        main_layout.addWidget(example_label)

        self.uri_text = QTextEdit()
        self.uri_text.setFixedHeight(80)
        main_layout.addWidget(self.uri_text)

        # 背景音乐开关
        music_frame = QHBoxLayout()
        music_frame.addWidget(QLabel("背景音乐:"))
        self.music_var = QCheckBox("开启/关闭")
        self.music_var.toggled.connect(self.toggle_music)
        music_frame.addWidget(self.music_var)
        music_frame.addStretch()
        main_layout.addLayout(music_frame)

        # 按钮
        btn_layout = QHBoxLayout()
        self.test_btn = QPushButton("测试连接")
        self.test_btn.setStyleSheet("background-color: #2196F3; color: white;")
        self.test_btn.clicked.connect(self.test_connection)

        self.save_btn = QPushButton("保存配置")
        self.save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.save_btn.clicked.connect(self.save_config)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.cancel_btn.clicked.connect(self.close)

        btn_layout.addStretch()
        btn_layout.addWidget(self.test_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # 状态提示
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

    def toggle_music(self):
        is_on = self.music_var.isChecked()
        self.music_manager.set_enabled(is_on)

    def load_current_config(self):
        mongodb_uri = self.config_manager.load_config()
        if mongodb_uri:
            self.uri_text.setPlainText(mongodb_uri)
            self.status_label.setText("✓ 已加载现有配置")
            self.status_label.setStyleSheet("color: #4CAF50;")
        elif Config.MONGODB_URI:
            self.uri_text.setPlainText(Config.MONGODB_URI)

        self.music_var.setChecked(self.music_manager.get_status())

    def test_connection(self):
        uri = self.uri_text.toPlainText().strip()
        if not uri:
            QMessageBox.critical(self, "错误", "请输入MongoDB连接字符串")
            return

        self.status_label.setText("正在测试连接...")
        self.status_label.setStyleSheet("color: #2196F3;")
        QApplication.processEvents()

        success, msg = self.config_manager.test_connection(uri)
        if success:
            self.status_label.setText(f"✓ {msg}")
            self.status_label.setStyleSheet("color: #4CAF50;")
            QMessageBox.information(self, "成功", msg)
        else:
            self.status_label.setText(f"✗ {msg}")
            self.status_label.setStyleSheet("color: #f44336;")
            QMessageBox.critical(self, "连接失败", msg)

    def save_config(self):
        uri = self.uri_text.toPlainText().strip()
        if not uri:
            QMessageBox.critical(self, "错误", "请输入MongoDB连接字符串")
            return

        success, msg = self.config_manager.test_connection(uri)
        if not success:
            if not QMessageBox.question(self, "确认", "连接测试失败，确定要保存这个配置吗？"):
                return

        if self.config_manager.save_config(uri):
            import os
            os.environ['MONGODB_URI'] = uri
            Database._instance = None
            QMessageBox.information(self, "成功", "配置已保存！")
            self.close()
        else:
            QMessageBox.critical(self, "错误", "保存配置失败")