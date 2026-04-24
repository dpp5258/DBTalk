import tkinter as tk
from tkinter import messagebox, ttk
from utils.config_manager import ConfigManager
from utils.db import Database
from config import Config

class SettingsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.config_manager = ConfigManager()
        
        self.window = tk.Toplevel(parent)
        self.window.title("云端数据库配置")
        self.window.geometry("600x400")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
        self.load_current_config()
    
    def setup_ui(self):
        title_label = tk.Label(
            self.window,
            text="MongoDB Atlas 云端配置",
            font=("Arial", 16, "bold"),
            fg="#1976D2"
        )
        title_label.pack(pady=20)
        
        info_text = """请配置您的MongoDB Atlas云端数据库连接
        
1. 访问 https://www.mongodb.com/atlas 注册账号
2. 创建免费集群
3. 获取连接字符串"""
        
        info_label = tk.Label(
            self.window,
            text=info_text,
            font=("Arial", 10),
            fg="#666",
            justify=tk.LEFT
        )
        info_label.pack(pady=10, padx=30)
        
        main_frame = tk.Frame(self.window, padx=30, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        tk.Label(
            main_frame,
            text="MongoDB连接字符串:",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")
        
        example_label = tk.Label(
            main_frame,
            text="示例: mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority",
            font=("Arial", 9),
            fg="#888"
        )
        example_label.pack(anchor="w", pady=(0,5))
        
        self.uri_text = tk.Text(main_frame, height=4, font=("Arial", 10))
        self.uri_text.pack(fill="x", pady=5)
        
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        tk.Button(
            button_frame,
            text="测试连接",
            command=self.test_connection,
            bg="#2196F3",
            fg="white",
            font=("Arial", 11),
            width=12
        ).pack(side="left", padx=5)
        
        tk.Button(
            button_frame,
            text="保存配置",
            command=self.save_config,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11),
            width=12
        ).pack(side="left", padx=5)
        
        tk.Button(
            button_frame,
            text="取消",
            command=self.window.destroy,
            bg="#f44336",
            fg="white",
            font=("Arial", 11),
            width=12
        ).pack(side="left", padx=5)
        
        self.status_label = tk.Label(
            main_frame,
            text="",
            font=("Arial", 10)
        )
        self.status_label.pack(pady=10)
    
    def load_current_config(self):
        mongodb_uri = self.config_manager.load_config()
        if mongodb_uri:
            self.uri_text.insert("1.0", mongodb_uri)
            self.status_label.config(text="✓ 已加载现有配置", fg="#4CAF50")
        elif Config.MONGODB_URI:
            self.uri_text.insert("1.0", Config.MONGODB_URI)
    
    def test_connection(self):
        mongodb_uri = self.uri_text.get("1.0", tk.END).strip()
        if not mongodb_uri:
            messagebox.showerror("错误", "请输入MongoDB连接字符串")
            return
        self.status_label.config(text="正在测试连接...", fg="#2196F3")
        self.window.update()
        success, message = self.config_manager.test_connection(mongodb_uri)
        if success:
            self.status_label.config(text=f"✓ {message}", fg="#4CAF50")
            messagebox.showinfo("成功", message)
        else:
            self.status_label.config(text=f"✗ {message}", fg="#f44336")
            messagebox.showerror("连接失败", message)
    
    def save_config(self):
        mongodb_uri = self.uri_text.get("1.0", tk.END).strip()
        if not mongodb_uri:
            messagebox.showerror("错误", "请输入MongoDB连接字符串")
            return
        success, message = self.config_manager.test_connection(mongodb_uri)
        if not success:
            if not messagebox.askyesno("确认", "连接测试失败，确定要保存这个配置吗？"):
                return
        if self.config_manager.save_config(mongodb_uri):
            # 更新环境变量以便当前会话使用
            import os
            os.environ['MONGODB_URI'] = mongodb_uri
            # 重置数据库连接
            Database._instance = None
            messagebox.showinfo("成功", "配置已保存！")
            self.window.destroy()
        else:
            messagebox.showerror("错误", "保存配置失败")