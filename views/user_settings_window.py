import tkinter as tk
from tkinter import messagebox, filedialog
import os
import json
from utils.music_manager import MusicManager
from datetime import datetime
# 新增：导入 Pillow 用于图像处理
from PIL import Image, ImageTk

class UserSettingsWindow:
    def __init__(self, parent, user, user_service):
        self.parent = parent
        self.user = user
        self.user_service = user_service
        self.music_manager = MusicManager()
        
        self.window = tk.Toplevel(parent)
        self.window.title("账号设置")
        # 修改2：将账号设置窗口改为可伸缩窗口
        self.window.geometry("800x750")
        self.window.resizable(True, True) 
        self.window.transient(parent)
        self.window.grab_set()
        
        # 用于存储头像图片对象，防止被垃圾回收
        self.avatar_image_obj = None
        
        self.setup_ui()

    def toggle_music(self):
        """切换音乐状态"""
        is_on = self.music_var.get()
        self.music_manager.set_enabled(is_on)

    def backup_data(self):
        """执行本地数据备份"""
        try:
            # 1. 确定备份根目录
            # 优先尝试 D 盘，如果不存在则使用用户主目录
            backup_root = "D:\\DBTalk_Backups"
            if not os.path.exists("D:\\"):
                backup_root = os.path.join(os.path.expanduser("~"), "DBTalk_Backups")
            
            # 2. 创建用户专属文件夹
            user_backup_dir = os.path.join(backup_root, self.user['username'])
            os.makedirs(user_backup_dir, exist_ok=True)
            
            # 3. 获取数据
            messagebox.showinfo("提示", "正在从云端拉取数据...")
            self.window.update() # 刷新UI显示消息
            
            backup_data = self.user_service.get_user_backup_data(self.user['username'])
            
            # 4. 生成文件名 (带时间戳)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{timestamp}.json"
            filepath = os.path.join(user_backup_dir, filename)
            
            # 5. 写入 JSON 文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=4)
                
            messagebox.showinfo("成功", f"数据备份成功！\n保存位置:\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("备份失败", f"发生错误: {str(e)}")

    def change_avatar(self):
        """选择并预览头像"""
        file_path = filedialog.askopenfilename(
            title="选择头像图片",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp")]
        )
        
        if not file_path:
            return
        
        try:
            # 1. 打开图片
            img = Image.open(file_path)
            
            # 2. 转换为 RGB (处理 PNG 透明通道等)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 3. 裁剪为正方形 (居中裁剪)
            width, height = img.size
            min_dim = min(width, height)
            left = (width - min_dim) / 2
            top = (height - min_dim) / 2
            right = (width + min_dim) / 2
            bottom = (height + min_dim) / 2
            img_cropped = img.crop((left, top, right, bottom))
            
            # 4. Resize 到目标大小 (2000x2000 用于存储，保证高清)
            img_final = img_cropped.resize((2000, 2000), Image.LANCZOS)
            
            # 5. 弹出预览窗口
            self.show_preview_dialog(img_final)
                
        except Exception as e:
            messagebox.showerror("错误", f"处理图片失败: {str(e)}")

    def show_preview_dialog(self, img_final):
        """显示头像预览对话框"""
        preview_win = tk.Toplevel(self.window)
        preview_win.title("头像预览")
        preview_win.geometry("400x450")
        preview_win.transient(self.window)
        preview_win.grab_set()
        
        tk.Label(preview_win, text="请确认头像效果", font=("Arial", 12, "bold")).pack(pady=10)
        
        # 创建一个较大的预览图 (例如放大到 300x300 显示，更清晰)
        img_preview = img_final.resize((300, 300), Image.LANCZOS)
        
        photo = ImageTk.PhotoImage(img_preview)
        label = tk.Label(preview_win, image=photo)
        label.image = photo # 保持引用
        label.pack(pady=10)
        
        btn_frame = tk.Frame(preview_win)
        btn_frame.pack(pady=20)
        
        def confirm_upload():
            """确认上传"""
            try:
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                avatar_dir = os.path.join(project_root, "avatars")
                os.makedirs(avatar_dir, exist_ok=True)
                
                filename = f"{self.user['username']}.jpg"
                save_path = os.path.join(avatar_dir, filename)
                
                # 保存为 JPG
                img_final.save(save_path, "JPEG", quality=90) # 提高质量
                
                relative_path = os.path.join("avatars", filename)
                success, msg = self.user_service.update_avatar(self.user['username'], relative_path)
                
                if success:
                    messagebox.showinfo("成功", "头像修改成功！")
                    # 更新设置界面的预览
                    self.load_and_display_avatar(save_path)
                    # 通知父窗口刷新
                    if hasattr(self.parent, 'refresh_avatar'):
                        self.parent.refresh_avatar()
                    preview_win.destroy()
                else:
                    messagebox.showerror("错误", msg)
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")

        def cancel_upload():
            preview_win.destroy()

        tk.Button(btn_frame, text="确认使用", command=confirm_upload, bg="#4CAF50", fg="white", font=("Arial", 10), width=10).pack(side="left", padx=10)
        tk.Button(btn_frame, text="取消", command=cancel_upload, bg="#f44336", fg="white", font=("Arial", 10), width=10).pack(side="left", padx=10)

    def load_and_display_avatar(self, image_path):
        """加载并显示头像预览"""
        try:
            if os.path.exists(image_path):
                img = Image.open(image_path)
                # 调整为适合显示的大小，例如 400x400 (增大显示尺寸)
                img = img.resize((400, 400), Image.LANCZOS)
                self.avatar_image_obj = ImageTk.PhotoImage(img)

                # 如果已有标签则配置，否则创建（这里假设在 setup_ui 中已经创建了 self.avatar_label）
                if hasattr(self, 'avatar_label'):
                    self.avatar_label.config(image=self.avatar_image_obj)
            else:
                # 显示默认占位图或清空
                pass
        except Exception as e:
            print(f"加载头像预览失败: {e}")

    def setup_ui(self):
        # 标题
        tk.Label(self.window, text="账号安全设置", font=("Arial", 14, "bold")).pack(pady=15)
        
        # 分隔线
        tk.Frame(self.window, height=2, bg="#ddd").pack(fill="x", padx=20)

        # 新增：头像设置区域
        avatar_frame = tk.Frame(self.window, padx=20, pady=10)
        avatar_frame.pack(fill="x")
        tk.Label(avatar_frame, text="个人头像", font=("Arial", 11, "bold")).pack(anchor="w")
        tk.Label(avatar_frame, text="支持 JPG, PNG, WEBP 格式，将自动裁剪为高清正方形", 
                 font=("Arial", 9), fg="#666").pack(anchor="w")
        
        # 修改1：添加头像预览标签 (增大初始占位大小提示)
        self.avatar_label = tk.Label(avatar_frame, text="[暂无头像]", bg="#f0f0f0", width=20, height=10)
        self.avatar_label.pack(pady=5)
        
        # 加载当前头像
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        current_avatar_path = os.path.join(project_root, "avatars", f"{self.user['username']}.jpg")
        self.load_and_display_avatar(current_avatar_path)
        
        tk.Button(
            avatar_frame, 
            text="选择并上传头像", 
            command=self.change_avatar, 
            bg="#9C27B0", 
            fg="white",
            font=("Arial", 10)
        ).pack(anchor="w", pady=5)

        # 分隔线
        tk.Frame(self.window, height=2, bg="#ddd").pack(fill="x", padx=20, pady=10)

        # 新增：背景音乐设置
        music_frame = tk.Frame(self.window, padx=20, pady=10)
        music_frame.pack(fill="x")
        tk.Label(music_frame, text="背景音乐", font=("Arial", 11, "bold")).pack(anchor="w")
        
        # 修改：初始化时获取持久化的状态
        self.music_var = tk.BooleanVar(value=self.music_manager.get_status())
        tk.Checkbutton(
            music_frame, 
            text="开启背景音乐 (MP3)", 
            variable=self.music_var, 
            command=self.toggle_music,
            font=("Arial", 10)
        ).pack(anchor="w", pady=5)

        # 分隔线
        tk.Frame(self.window, height=2, bg="#ddd").pack(fill="x", padx=20, pady=10)

        # 新增：数据备份区域
        backup_frame = tk.Frame(self.window, padx=20, pady=10)
        backup_frame.pack(fill="x")
        tk.Label(backup_frame, text="数据管理", font=("Arial", 11, "bold")).pack(anchor="w")
        tk.Label(backup_frame, text="将您的提交记录和个人信息备份到本地 (JSON格式)", 
                 font=("Arial", 9), fg="#666").pack(anchor="w")
        
        tk.Button(
            backup_frame, 
            text="立即备份数据", 
            command=self.backup_data, 
            bg="#9C27B0", 
            fg="white",
            font=("Arial", 10)
        ).pack(anchor="w", pady=5)

        # 分隔线
        tk.Frame(self.window, height=2, bg="#ddd").pack(fill="x", padx=20, pady=10)

        # 修改邮箱部分
        email_frame = tk.Frame(self.window, padx=20, pady=10)
        email_frame.pack(fill="x")
        tk.Label(email_frame, text="修改邮箱", font=("Arial", 11, "bold")).pack(anchor="w")
        
        self.email_var = tk.StringVar()
        # 获取当前最新邮箱
        current_data = self.user_service.get_user_by_username(self.user['username'])
        if current_data:
            self.email_var.set(current_data.get('email', ''))
            
        tk.Entry(email_frame, textvariable=self.email_var, width=30).pack(pady=5, fill="x")
        tk.Button(email_frame, text="保存邮箱", command=self.save_email, bg="#2196F3", fg="white").pack(anchor="e")

        # 分隔线
        tk.Frame(self.window, height=2, bg="#ddd").pack(fill="x", padx=20, pady=10)

        # 修改密码部分
        pwd_frame = tk.Frame(self.window, padx=20, pady=10)
        pwd_frame.pack(fill="x")
        tk.Label(pwd_frame, text="修改密码", font=("Arial", 11, "bold")).pack(anchor="w")
        
        tk.Label(pwd_frame, text="新密码:", font=("Arial", 9)).pack(anchor="w")
        self.new_pwd_var = tk.StringVar()
        tk.Entry(pwd_frame, textvariable=self.new_pwd_var, show="*", width=30).pack(pady=2, fill="x")
        
        tk.Label(pwd_frame, text="确认密码:", font=("Arial", 9)).pack(anchor="w")
        self.confirm_pwd_var = tk.StringVar()
        tk.Entry(pwd_frame, textvariable=self.confirm_pwd_var, show="*", width=30).pack(pady=2, fill="x")
        
        tk.Button(pwd_frame, text="保存密码", command=self.save_password, bg="#FF9800", fg="white").pack(anchor="e", pady=5)

        # 底部关闭按钮
        tk.Button(self.window, text="关闭", command=self.window.destroy, bg="#9E9E9E", fg="white").pack(pady=10)

    def save_email(self):
        new_email = self.email_var.get().strip()
        success, msg = self.user_service.update_email(
            operator_username=self.user['username'],
            target_username=self.user['username'],
            new_email=new_email
        )
        messagebox.showinfo("结果", msg)
        if success:
            # 可选：通知父窗口刷新显示
            if hasattr(self.parent, 'email_label'):
                self.parent.email_label.config(text=new_email)

    def save_password(self):
        pwd = self.new_pwd_var.get()
        confirm_pwd = self.confirm_pwd_var.get()
        
        if pwd != confirm_pwd:
            messagebox.showerror("错误", "两次输入的密码不一致")
            return
        if not pwd or len(pwd) < 6:
            messagebox.showerror("错误", "密码长度至少为6位")
            return
            
        success, msg = self.user_service.reset_password(
            operator_username=self.user['username'],
            target_username=self.user['username'],
            new_password=pwd
        )
        messagebox.showinfo("结果", msg)
        if success:
            self.new_pwd_var.set("")
            self.confirm_pwd_var.set("")