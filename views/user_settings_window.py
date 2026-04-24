import tkinter as tk
from tkinter import messagebox

class UserSettingsWindow:
    def __init__(self, parent, user, user_service):
        self.parent = parent
        self.user = user
        self.user_service = user_service
        
        self.window = tk.Toplevel(parent)
        self.window.title("账号设置")
        self.window.geometry("500x500")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()

    def setup_ui(self):
        # 标题
        tk.Label(self.window, text="账号安全设置", font=("Arial", 14, "bold")).pack(pady=15)
        
        # 分隔线
        tk.Frame(self.window, height=2, bg="#ddd").pack(fill="x", padx=20)

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