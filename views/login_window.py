import tkinter as tk
from tkinter import messagebox, ttk
from utils.db import Database
from views.user_window import UserWindow
from views.admin_window import AdminWindow
from views.settings_window import SettingsWindow
from datetime import datetime


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.db = Database()
        self.setup_menu()
        self.setup_ui()
        self.check_database_connection()
    
    def setup_menu(self):
        """设置菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="云端配置", command=self.open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def open_settings(self):
        """打开配置窗口"""
        SettingsWindow(self.root)
    
    def show_about(self):
        """显示关于信息"""
        about_text = f"""{Config.APP_NAME} v{Config.APP_VERSION}
        
一个简单的文本提交管理系统
使用 MongoDB Atlas 云端数据库
        
© 2024 版权所有"""
        messagebox.showinfo("关于", about_text)
    
    def check_database_connection(self):
        """检查数据库连接"""
        if self.db.is_connected:
            self.connection_status.config(text="● 已连接到云端", fg="#4CAF50")
        else:
            self.connection_status.config(
                text="● 未连接到云端 (点击文件->云端配置设置)",
                fg="#f44336"
            )
    
    def setup_ui(self):
        """设置UI界面"""
        self.root.title("文本提交系统 - 登录")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        
        # 标题
        title_label = tk.Label(
            self.root,
            text="文本提交系统",
            font=("Arial", 20, "bold"),
            fg="#333"
        )
        title_label.pack(pady=30)
        
        # 登录框
        login_frame = tk.Frame(self.root, bg="#f0f0f0", padx=20, pady=20)
        login_frame.pack(padx=40, pady=20, fill="both")
        
        tk.Label(login_frame, text="用户名:", bg="#f0f0f0", font=("Arial", 12)).pack(pady=5)
        self.username_entry = tk.Entry(login_frame, font=("Arial", 12), width=25)
        self.username_entry.pack(pady=5)
        
        tk.Label(login_frame, text="密码:", bg="#f0f0f0", font=("Arial", 12)).pack(pady=5)
        self.password_entry = tk.Entry(login_frame, show="*", font=("Arial", 12), width=25)
        self.password_entry.pack(pady=5)
        
        button_frame = tk.Frame(login_frame, bg="#f0f0f0")
        button_frame.pack(pady=20)
        
        login_btn = tk.Button(
            button_frame,
            text="登录",
            command=self.login,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12),
            width=10
        )
        login_btn.pack(side="left", padx=5)
        
        register_btn = tk.Button(
            button_frame,
            text="注册",
            command=self.show_register,
            bg="#2196F3",
            fg="white",
            font=("Arial", 12),
            width=10
        )
        register_btn.pack(side="left", padx=5)
        
        self.root.bind('<Return>', lambda event: self.login())
        
        # 连接状态
        status_frame = tk.Frame(self.root, bg="#f0f0f0", height=30)
        status_frame.pack(fill="x", side="bottom")
        self.connection_status = tk.Label(
            status_frame,
            text="正在检查连接...",
            bg="#f0f0f0",
            font=("Arial", 9)
        )
        self.connection_status.pack(side="left", padx=10)
    
    def login(self):
        """登录功能"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("错误", "请输入用户名和密码")
            return
        user = self.db.authenticate_user(username, password)
        if user:
            messagebox.showinfo("成功", f"欢迎回来, {username}!")
            self.root.withdraw()
            if user.get("role") == "admin":
                AdminWindow(self.root, user)
            else:
                UserWindow(self.root, user)
        else:
            messagebox.showerror("错误", "用户名或密码错误")
    
    def show_register(self):
        """显示注册窗口"""
        register_window = tk.Toplevel(self.root)
        register_window.title("用户注册")
        register_window.geometry("350x450")
        register_window.resizable(False, False)
        register_window.transient(self.root)
        register_window.grab_set()
        
        tk.Label(register_window, text="用户注册", font=("Arial", 16, "bold")).pack(pady=20)
        form_frame = tk.Frame(register_window, padx=20, pady=20)
        form_frame.pack()
        
        tk.Label(form_frame, text="用户名:", font=("Arial", 11)).pack(anchor="w")
        username_entry = tk.Entry(form_frame, font=("Arial", 11), width=25)
        username_entry.pack(pady=5)
        
        tk.Label(form_frame, text="密码:", font=("Arial", 11)).pack(anchor="w")
        password_entry = tk.Entry(form_frame, show="*", font=("Arial", 11), width=25)
        password_entry.pack(pady=5)
        
        tk.Label(form_frame, text="确认密码:", font=("Arial", 11)).pack(anchor="w")
        confirm_entry = tk.Entry(form_frame, show="*", font=("Arial", 11), width=25)
        confirm_entry.pack(pady=5)
        
        tk.Label(form_frame, text="邮箱:", font=("Arial", 11)).pack(anchor="w")
        email_entry = tk.Entry(form_frame, font=("Arial", 11), width=25)
        email_entry.pack(pady=5)
        
        def do_register():
            username = username_entry.get()
            password = password_entry.get()
            confirm = confirm_entry.get()
            email = email_entry.get()
            if not all([username, password, confirm, email]):
                messagebox.showerror("错误", "请填写所有字段")
                return
            if password != confirm:
                messagebox.showerror("错误", "两次输入的密码不一致")
                return
            success, message = self.db.create_user(username, password, email)
            if success:
                messagebox.showinfo("成功", message)
                register_window.destroy()
            else:
                messagebox.showerror("错误", message)
        
        tk.Button(
            form_frame,
            text="注册",
            command=do_register,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11),
            width=15
        ).pack(pady=20)