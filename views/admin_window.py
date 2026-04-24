import tkinter as tk
from tkinter import messagebox, ttk
from utils.db import Database
from bson import ObjectId

class AdminWindow:
    def __init__(self, root, admin):
        self.root = root
        self.admin = admin
        self.db = Database()
        
        self.window = tk.Toplevel(root)
        self.window.title(f"管理员面板 - {admin['username']}")
        self.window.geometry("800x600")
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_ui()
    
    def setup_ui(self):
        # 顶部栏
        top_frame = tk.Frame(self.window, bg="#1e3c72", height=50)
        top_frame.pack(fill="x")
        tk.Label(
            top_frame,
            text=f"管理员: {self.admin['username']}",
            font=("Arial", 12, "bold"),
            bg="#1e3c72",
            fg="white"
        ).pack(side="left", padx=20, pady=15)
        tk.Button(
            top_frame,
            text="登出",
            command=self.logout,
            bg="#f44336",
            fg="white",
            font=("Arial", 10),
            width=8
        ).pack(side="right", padx=20, pady=10)
        
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 所有提交标签页
        submissions_tab = tk.Frame(notebook)
        notebook.add(submissions_tab, text="所有提交")
        self.setup_submissions_tab(submissions_tab)
        
        # 用户管理标签页
        users_tab = tk.Frame(notebook)
        notebook.add(users_tab, text="用户管理")
        self.setup_users_tab(users_tab)
        
        # 统计信息标签页
        stats_tab = tk.Frame(notebook)
        notebook.add(stats_tab, text="统计信息")
        self.setup_stats_tab(stats_tab)
    
    def setup_submissions_tab(self, parent):
        toolbar = tk.Frame(parent, bg="#f0f0f0", height=40)
        toolbar.pack(fill="x", pady=5)
        tk.Label(toolbar, text="所有用户提交", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        tk.Button(
            toolbar,
            text="刷新",
            command=self.refresh_submissions,
            bg="#2196F3",
            fg="white"
        ).pack(side="right", padx=10)
        
        columns = ("时间", "用户名", "标题", "状态", "操作")
        self.submissions_tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        self.submissions_tree.heading("时间", text="提交时间")
        self.submissions_tree.heading("用户名", text="用户名")
        self.submissions_tree.heading("标题", text="标题")
        self.submissions_tree.heading("状态", text="状态")
        self.submissions_tree.heading("操作", text="操作")
        self.submissions_tree.column("时间", width=150)
        self.submissions_tree.column("用户名", width=100)
        self.submissions_tree.column("标题", width=200)
        self.submissions_tree.column("状态", width=80)
        self.submissions_tree.column("操作", width=150)
        
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.submissions_tree.yview)
        self.submissions_tree.configure(yscrollcommand=scrollbar.set)
        self.submissions_tree.pack(side="left", fill="both", expand=True, padx=(10,0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        self.submissions_tree.bind('<Double-Button-1>', self.show_submission_detail)
        self.refresh_submissions()
    
    def setup_users_tab(self, parent):
        toolbar = tk.Frame(parent, bg="#f0f0f0", height=40)
        toolbar.pack(fill="x", pady=5)
        tk.Label(toolbar, text="用户列表", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        tk.Button(
            toolbar,
            text="刷新",
            command=self.refresh_users,
            bg="#2196F3",
            fg="white"
        ).pack(side="right", padx=10)
        
        columns = ("用户名", "邮箱", "角色", "注册时间", "状态")
        self.users_tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        self.users_tree.heading("用户名", text="用户名")
        self.users_tree.heading("邮箱", text="邮箱")
        self.users_tree.heading("角色", text="角色")
        self.users_tree.heading("注册时间", text="注册时间")
        self.users_tree.heading("状态", text="状态")
        self.users_tree.column("用户名", width=100)
        self.users_tree.column("邮箱", width=200)
        self.users_tree.column("角色", width=80)
        self.users_tree.column("注册时间", width=150)
        self.users_tree.column("状态", width=80)
        
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        self.users_tree.pack(side="left", fill="both", expand=True, padx=(10,0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        self.refresh_users()
    
    def setup_stats_tab(self, parent):
        stats = self.db.get_stats() or {}
        stats_frame = tk.Frame(parent, bg="#f5f5f5")
        stats_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.create_stat_card(stats_frame, "总用户数", stats.get("users", 0), 0, 0, "#2196F3")
        self.create_stat_card(stats_frame, "总提交数", stats.get("submissions", 0), 0, 1, "#4CAF50")
        self.create_stat_card(stats_frame, "待审核", stats.get("pending", 0), 1, 0, "#FF9800")
    
    def create_stat_card(self, parent, title, value, row, col, color):
        card = tk.Frame(parent, bg=color, width=200, height=120)
        card.grid(row=row, column=col, padx=10, pady=10)
        card.grid_propagate(False)
        tk.Label(card, text=title, font=("Arial", 12), bg=color, fg="white").pack(pady=(20,5))
        tk.Label(card, text=str(value), font=("Arial", 24, "bold"), bg=color, fg="white").pack()
    
    def refresh_submissions(self):
        for item in self.submissions_tree.get_children():
            self.submissions_tree.delete(item)
        submissions = self.db.get_all_submissions()
        for sub in submissions:
            time_str = sub['created_at'].strftime("%Y-%m-%d %H:%M") if sub['created_at'] else "未知"
            self.submissions_tree.insert(
                "",
                "end",
                values=(time_str, sub['username'], sub['title'], sub['status'], "双击查看详情"),
                tags=(str(sub['_id']),)
            )
    
    def refresh_users(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        users = self.db.get_all_users()
        for user in users:
            reg_time = user['created_at'].strftime("%Y-%m-%d %H:%M") if user.get('created_at') else "未知"
            status = "活跃" if user.get('is_active', True) else "禁用"
            self.users_tree.insert(
                "",
                "end",
                values=(user['username'], user['email'], user['role'], reg_time, status)
            )
    
    def show_submission_detail(self, event):
        selection = self.submissions_tree.selection()
        if not selection:
            return
        item = self.submissions_tree.item(selection[0])
        submission_id = item['tags'][0]
        submission = self.db.db.submissions.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            return
        
        detail_window = tk.Toplevel(self.window)
        detail_window.title(f"提交详情 - {submission['title']}")
        detail_window.geometry("500x400")
        
        tk.Label(detail_window, text="标题:", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(20,5))
        tk.Label(detail_window, text=submission['title'], font=("Arial", 11)).pack(anchor="w", padx=20)
        
        tk.Label(detail_window, text="用户名:", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(10,5))
        tk.Label(detail_window, text=submission['username'], font=("Arial", 11)).pack(anchor="w", padx=20)
        
        tk.Label(detail_window, text="内容:", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(10,5))
        content_text = tk.Text(detail_window, height=10, width=50, font=("Arial", 11))
        content_text.pack(padx=20, pady=5)
        content_text.insert("1.0", submission['content'])
        content_text.config(state="disabled")
        
        tk.Label(detail_window, text="当前状态:", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(10,5))
        tk.Label(detail_window, text=submission['status'], font=("Arial", 11)).pack(anchor="w", padx=20)
        
        button_frame = tk.Frame(detail_window)
        button_frame.pack(pady=20)
        
        def update_status(status):
            success = self.db.update_submission_status(submission['_id'], status)
            if success:
                messagebox.showinfo("成功", f"状态已更新为: {status}")
                detail_window.destroy()
                self.refresh_submissions()
            else:
                messagebox.showerror("错误", "更新失败")
        
        tk.Button(
            button_frame,
            text="批准",
            command=lambda: update_status("approved"),
            bg="#4CAF50",
            fg="white",
            width=8
        ).pack(side="left", padx=5)
        
        tk.Button(
            button_frame,
            text="拒绝",
            command=lambda: update_status("rejected"),
            bg="#f44336",
            fg="white",
            width=8
        ).pack(side="left", padx=5)
    
    def logout(self):
        if messagebox.askyesno("确认", "确定要登出吗？"):
            self.window.destroy()
            self.root.deiconify()
    
    def on_closing(self):
        self.logout()