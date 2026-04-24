import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from utils.db import Database
from bson import ObjectId

class UserWindow:
    def __init__(self, root, user):
        self.root = root
        self.user = user
        self.db = Database()
        
        self.window = tk.Toplevel(root)
        self.window.title(f"用户面板 - {user['username']}")
        self.window.geometry("600x700")
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_ui()
    
    def setup_ui(self):
        # 欢迎栏
        welcome_frame = tk.Frame(self.window, bg="#e3f2fd", height=60)
        welcome_frame.pack(fill="x")
        tk.Label(
            welcome_frame,
            text=f"欢迎，{self.user['username']}!",
            font=("Arial", 14, "bold"),
            bg="#e3f2fd"
        ).pack(side="left", padx=20, pady=15)
        tk.Button(
            welcome_frame,
            text="登出",
            command=self.logout,
            bg="#f44336",
            fg="white",
            font=("Arial", 10),
            width=8
        ).pack(side="right", padx=20, pady=15)
        
        # 使用Notebook
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 提交标签页
        submit_tab = tk.Frame(notebook)
        notebook.add(submit_tab, text="提交文本")
        self.setup_submit_tab(submit_tab)
        
        # 历史标签页
        history_tab = tk.Frame(notebook)
        notebook.add(history_tab, text="提交历史")
        self.setup_history_tab(history_tab)
        
        # 个人信息标签页
        profile_tab = tk.Frame(notebook)
        notebook.add(profile_tab, text="个人信息")
        self.setup_profile_tab(profile_tab)
    
    def setup_submit_tab(self, parent):
        tk.Label(parent, text="提交新文本", font=("Arial", 14, "bold")).pack(pady=10)
        form_frame = tk.Frame(parent, padx=20, pady=10)
        form_frame.pack(fill="both", expand=True)
        
        tk.Label(form_frame, text="标题:", font=("Arial", 11)).pack(anchor="w")
        self.title_entry = tk.Entry(form_frame, font=("Arial", 11), width=50)
        self.title_entry.pack(pady=5, fill="x")
        
        tk.Label(form_frame, text="内容:", font=("Arial", 11)).pack(anchor="w", pady=(10,0))
        text_frame = tk.Frame(form_frame)
        text_frame.pack(fill="both", expand=True, pady=5)
        self.content_text = scrolledtext.ScrolledText(
            text_frame,
            height=15,
            font=("Arial", 11),
            wrap=tk.WORD
        )
        self.content_text.pack(fill="both", expand=True)
        
        tk.Button(
            form_frame,
            text="提交",
            command=self.submit_text,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15
        ).pack(pady=20)
    
    def setup_history_tab(self, parent):
        tk.Label(parent, text="提交历史", font=("Arial", 14, "bold")).pack(pady=10)
        columns = ("时间", "标题", "状态")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        self.tree.heading("时间", text="提交时间")
        self.tree.heading("标题", text="标题")
        self.tree.heading("状态", text="状态")
        self.tree.column("时间", width=150)
        self.tree.column("标题", width=250)
        self.tree.column("状态", width=80)
        
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(10,0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        tk.Button(
            parent,
            text="刷新",
            command=self.refresh_history,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10)
        ).pack(pady=10)
        self.refresh_history()
    
    def setup_profile_tab(self, parent):
        info_frame = tk.Frame(parent, padx=30, pady=20)
        info_frame.pack(fill="both", expand=True)
        tk.Label(info_frame, text="👤", font=("Arial", 48), bg="#e0e0e0", width=4, height=2).pack(pady=20)
        
        tk.Label(info_frame, text="用户名:", font=("Arial", 11, "bold")).pack(anchor="w")
        tk.Label(info_frame, text=self.user['username'], font=("Arial", 11)).pack(anchor="w", pady=(0,10))
        
        tk.Label(info_frame, text="邮箱:", font=("Arial", 11, "bold")).pack(anchor="w")
        tk.Label(info_frame, text=self.user.get('email', '未设置'), font=("Arial", 11)).pack(anchor="w", pady=(0,10))
        
        tk.Label(info_frame, text="注册时间:", font=("Arial", 11, "bold")).pack(anchor="w")
        reg_time = self.user.get('created_at', '未知')
        if reg_time != '未知':
            reg_time = reg_time.strftime("%Y-%m-%d %H:%M")
        tk.Label(info_frame, text=reg_time, font=("Arial", 11)).pack(anchor="w")
    
    def submit_text(self):
        title = self.title_entry.get()
        content = self.content_text.get("1.0", tk.END).strip()
        if not title:
            messagebox.showerror("错误", "请输入标题")
            return
        if not content:
            messagebox.showerror("错误", "请输入内容")
            return
        submission_id = self.db.create_submission(self.user['username'], title, content)
        if submission_id:
            messagebox.showinfo("成功", "文本提交成功！")
            self.title_entry.delete(0, tk.END)
            self.content_text.delete("1.0", tk.END)
            self.refresh_history()
        else:
            messagebox.showerror("错误", "提交失败，请重试")
    
    def refresh_history(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        submissions = self.db.get_user_submissions(self.user['username'])
        if not submissions:
            self.tree.insert("", "end", values=("暂无提交记录", "", ""))
        else:
            for sub in submissions:
                time_str = sub['created_at'].strftime("%Y-%m-%d %H:%M") if sub['created_at'] else "未知"
                self.tree.insert("", "end", values=(time_str, sub['title'], sub['status']))
    
    def logout(self):
        if messagebox.askyesno("确认", "确定要登出吗？"):
            self.window.destroy()
            self.root.deiconify()
    
    def on_closing(self):
        self.logout()