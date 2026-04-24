from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PIL import Image, ImageQt
import os
import json
from utils.music_manager import MusicManager
from datetime import datetime

class UserSettingsWindow(QDialog):
    def __init__(self, parent, user, user_service):
        super().__init__(parent)
        self.parent = parent
        self.user = user
        self.user_service = user_service
        self.music_manager = MusicManager()

        self.setWindowTitle("账号设置")
        self.resize(800, 750)
        self.setMinimumSize(600, 600)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.avatar_pixmap = None

        self.setup_ui()

    def toggle_music(self):
        is_on = self.music_switch.isChecked()
        self.music_manager.set_enabled(is_on)

    def backup_data(self):
        try:
            backup_root = "D:\\DBTalk_Backups"
            if not os.path.exists("D:\\"):
                backup_root = os.path.join(os.path.expanduser("~"), "DBTalk_Backups")

            user_backup_dir = os.path.join(backup_root, self.user['username'])
            os.makedirs(user_backup_dir, exist_ok=True)

            QMessageBox.information(self, "提示", "正在从云端拉取数据...")
            QApplication.processEvents()

            backup_data = self.user_service.get_user_backup_data(self.user['username'])
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{timestamp}.json"
            filepath = os.path.join(user_backup_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=4)

            QMessageBox.information(self, "成功", f"数据备份成功！\n保存位置:\n{filepath}")

        except Exception as e:
            QMessageBox.critical(self, "备份失败", f"发生错误: {str(e)}")

    def change_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择头像图片", "",
            "Image Files (*.jpg *.jpeg *.png *.webp)"
        )
        if not file_path:
            return

        try:
            img = Image.open(file_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            width, height = img.size
            min_dim = min(width, height)
            left = (width - min_dim) // 2
            top = (height - min_dim) // 2
            right = left + min_dim
            bottom = top + min_dim
            img_cropped = img.crop((left, top, right, bottom))
            img_final = img_cropped.resize((2000, 2000), Image.LANCZOS)

            self.show_preview_dialog(img_final)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理图片失败: {str(e)}")

    def show_preview_dialog(self, img_final):
        preview = QDialog(self)
        preview.setWindowTitle("头像预览")
        preview.resize(400, 450)
        preview.setMinimumSize(300, 350)
        preview.setWindowModality(Qt.WindowModality.WindowModal)

        layout = QVBoxLayout(preview)
        layout.addWidget(QLabel("请确认头像效果"), alignment=Qt.AlignmentFlag.AlignCenter)

        img_preview = img_final.resize((300, 300), Image.LANCZOS)
        qt_img = ImageQt.toqpixmap(img_preview)

        label = QLabel()
        label.setPixmap(qt_img)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        btn_layout = QHBoxLayout()

        def confirm_upload():
            try:
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                avatar_dir = os.path.join(project_root, "avatars")
                os.makedirs(avatar_dir, exist_ok=True)
                filename = f"{self.user['username']}.jpg"
                save_path = os.path.join(avatar_dir, filename)
                img_final.save(save_path, "JPEG", quality=90)

                rel_path = os.path.join("avatars", filename)
                ok, msg = self.user_service.update_avatar(self.user['username'], rel_path)
                if ok:
                    QMessageBox.information(preview, "成功", "头像修改成功！")
                    self.load_and_display_avatar(save_path)
                    if hasattr(self.parent, 'refresh_avatar'):
                        self.parent.refresh_avatar()
                    preview.accept()
                else:
                    QMessageBox.critical(preview, "错误", msg)
            except Exception as e:
                QMessageBox.critical(preview, "错误", f"保存失败: {str(e)}")

        confirm_btn = QPushButton("确认使用")
        confirm_btn.setStyleSheet("background:#4CAF50; color:white;")
        confirm_btn.clicked.connect(confirm_upload)

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("background:#f44336; color:white;")
        cancel_btn.clicked.connect(preview.close)

        btn_layout.addWidget(confirm_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        preview.exec()

    def load_and_display_avatar(self, path):
        if not os.path.exists(path):
            return
        try:
            img = Image.open(path)
            img = img.resize((400, 400), Image.LANCZOS)
            self.avatar_pixmap = ImageQt.toqpixmap(img)
            self.avatar_label.setPixmap(self.avatar_pixmap)
        except:
            pass

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 10)
        layout.setSpacing(10)

        # 标题
        title = QLabel("账号安全设置")
        title.setStyleSheet("font-size:14px; font-weight:bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 分割线
        layout.addWidget(QLabel("-" * 80))

        # 头像区域
        layout.addWidget(QLabel("个人头像"), alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(QLabel("支持 JPG, PNG, WEBP 格式，自动裁剪为正方形"))

        self.avatar_label = QLabel("[暂无头像]")
        self.avatar_label.setStyleSheet("background:#f0f0f0;")
        self.avatar_label.setFixedSize(200, 200)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)

        avatar_btn = QPushButton("选择并上传头像")
        avatar_btn.setStyleSheet("background:#9C27B0; color:white;")
        avatar_btn.clicked.connect(self.change_avatar)
        layout.addWidget(avatar_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # 分割线
        layout.addWidget(QLabel("-" * 80))

        # 音乐开关
        layout.addWidget(QLabel("背景音乐"))
        self.music_switch = QCheckBox("开启背景音乐 (MP3)")
        self.music_switch.setChecked(self.music_manager.get_status())
        self.music_switch.toggled.connect(self.toggle_music)
        layout.addWidget(self.music_switch)

        # 分割线
        layout.addWidget(QLabel("-" * 80))

        # 备份数据
        layout.addWidget(QLabel("数据管理"))
        layout.addWidget(QLabel("备份提交记录与个人信息到本地 JSON"))
        backup_btn = QPushButton("立即备份数据")
        backup_btn.setStyleSheet("background:#9C27B0; color:white;")
        backup_btn.clicked.connect(self.backup_data)
        layout.addWidget(backup_btn)

        # 分割线
        layout.addWidget(QLabel("-" * 80))

        # 修改邮箱
        layout.addWidget(QLabel("修改邮箱"))
        user_data = self.user_service.get_user_by_username(self.user['username'])
        self.email_edit = QLineEdit()
        if user_data:
            self.email_edit.setText(user_data.get('email', ''))
        layout.addWidget(self.email_edit)

        save_email_btn = QPushButton("保存邮箱")
        save_email_btn.setStyleSheet("background:#2196F3; color:white;")
        save_email_btn.clicked.connect(self.save_email)
        layout.addWidget(save_email_btn, alignment=Qt.AlignmentFlag.AlignRight)

        # 分割线
        layout.addWidget(QLabel("-" * 80))

        # 修改密码
        layout.addWidget(QLabel("修改密码"))
        self.pwd_edit = QLineEdit()
        self.pwd_edit.setPlaceholderText("新密码")
        self.pwd_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.pwd_edit)

        self.confirm_pwd_edit = QLineEdit()
        self.confirm_pwd_edit.setPlaceholderText("确认密码")
        self.confirm_pwd_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm_pwd_edit)

        save_pwd_btn = QPushButton("保存密码")
        save_pwd_btn.setStyleSheet("background:#FF9800; color:white;")
        save_pwd_btn.clicked.connect(self.save_password)
        layout.addWidget(save_pwd_btn, alignment=Qt.AlignmentFlag.AlignRight)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("background:#9E9E9E; color:white;")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # 加载头像
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        avatar_path = os.path.join(project_root, "avatars", f"{self.user['username']}.jpg")
        self.load_and_display_avatar(avatar_path)

    def save_email(self):
        new_email = self.email_edit.text().strip()
        ok, msg = self.user_service.update_email(
            operator_username=self.user['username'],
            target_username=self.user['username'],
            new_email=new_email
        )
        QMessageBox.information(self, "结果", msg)

    def save_password(self):
        pwd = self.pwd_edit.text()
        confirm = self.confirm_pwd_edit.text()

        if pwd != confirm:
            QMessageBox.critical(self, "错误", "两次密码不一致")
            return
        if len(pwd) < 6:
            QMessageBox.critical(self, "错误", "密码至少 6 位")
            return

        ok, msg = self.user_service.reset_password(
            operator_username=self.user['username'],
            target_username=self.user['username'],
            new_password=pwd
        )
        QMessageBox.information(self, "结果", msg)
        if ok:
            self.pwd_edit.clear()
            self.confirm_pwd_edit.clear()