import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from utils.db import Database
from models.user import UserModel # 新增导入
from bson import ObjectId
from datetime import datetime

class AdminWindow:
    def __init__(self, root, admin):
        self.root = root
        self.admin = admin
        self.db = Database()
        
        self.window = tk.Toplevel(root)
        self.window.title(f"管理员面板 - {admin['username']}")
        self.window.geometry("900x700") # 稍微调大以适应更多控件
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
        
        # 1. 个人信息标签页 (基础菜单)
        profile_tab = tk.Frame(notebook)
        notebook.add(profile_tab, text="个人信息")
        self.setup_profile_tab(profile_tab)
        
        # 2. 公告/内容发布标签页 (管理员信息上传)
        announcement_tab = tk.Frame(notebook)
        notebook.add(announcement_tab, text="公告发布")
        self.setup_announcement_tab(announcement_tab)
        
        # 3. 提交审核标签页 (所有提交批准)
        submissions_tab = tk.Frame(notebook)
        notebook.add(submissions_tab, text="提交审核")
        self.setup_submissions_tab(submissions_tab)
        
        # 4. 用户管理标签页 (管理员专属)
        users_tab = tk.Frame(notebook)
        notebook.add(users_tab, text="用户管理")
        self.setup_users_tab(users_tab)
        
        # 删除原有的统计信息标签页，或将其整合，这里按需求移除以保持简洁，或保留在最后
        # stats_tab = tk.Frame(notebook)
        # notebook.add(stats_tab, text="统计信息")
        # self.setup_stats_tab(stats_tab)
    
    def setup_announcement_tab(self, parent):
        """管理员发布公告/内容"""
        tk.Label(parent, text="发布全局公告/内容", font=("Arial", 14, "bold")).pack(pady=10)
        form_frame = tk.Frame(parent, padx=20, pady=10)
        form_frame.pack(fill="both", expand=True)
        
        tk.Label(form_frame, text="标题:", font=("Arial", 11)).pack(anchor="w")
        self.ann_title_entry = tk.Entry(form_frame, font=("Arial", 11), width=50)
        self.ann_title_entry.pack(pady=5, fill="x")
        
        tk.Label(form_frame, text="内容:", font=("Arial", 11)).pack(anchor="w", pady=(10,0))
        self.ann_content_text = tk.Text(form_frame, height=10, font=("Arial", 11), wrap=tk.WORD)
        self.ann_content_text.pack(fill="both", expand=True, pady=5)
        
        tk.Button(
            form_frame,
            text="发布公告",
            command=self.post_announcement,
            bg="#FF9800",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15
        ).pack(pady=20)

    def post_announcement(self):
        title = self.ann_title_entry.get()
        content = self.ann_content_text.get("1.0", tk.END).strip()
        
        if not title or not content:
            messagebox.showwarning("提示", "标题和内容不能为空")
            return
            
        # 复用 create_submission，但在管理员视角下这是发布公告
        # 注意：实际生产中可能需要单独的 announcements 集合
        # 这里为了兼容现有 db.py，我们将其作为一条由管理员发出的提交，状态直接设为 approved
        if not self.db.is_connected:
            messagebox.showerror("错误", "数据库未连接")
            return
            
        try:
            # 构造文档，手动插入以控制状态为 approved，或者调用 create_submission 后更新
            # 由于 create_submission 默认是 pending，我们这里直接操作 db 或修改逻辑
            # 简单起见，调用 create_submission，然后立即批准它，或者直接插入
            from models.submission import SubmissionModel
            doc = SubmissionModel.create_document(self.admin['username'], f"[公告] {title}", content)
            doc['status'] = 'approved' # 公告自动通过
            doc['is_announcement'] = True # 标记
            
            self.db.db.submissions.insert_one(doc)
            messagebox.showinfo("成功", "公告发布成功！")
            self.ann_title_entry.delete(0, tk.END)
            self.ann_content_text.delete("1.0", tk.END)
        except Exception as e:
            messagebox.showerror("错误", f"发布失败: {str(e)}")

    def setup_submissions_tab(self, parent):
        toolbar = tk.Frame(parent, bg="#f0f0f0", height=40)
        toolbar.pack(fill="x", pady=5)
        tk.Label(toolbar, text="用户提交审核", font=("Arial", 12, "bold")).pack(side="left", padx=10)
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
        
        # 绑定选择事件以启用操作按钮
        self.submissions_tree.bind('<<TreeviewSelect>>', self.on_submission_select)
        # 绑定双击事件查看详情
        self.submissions_tree.bind('<Double-Button-1>', self.on_submission_double_click)
        self.refresh_submissions()
        
        # 底部操作栏
        action_frame = tk.Frame(parent, bg="#f0f0f0", height=50)
        action_frame.pack(fill="x", pady=5)
        
        self.approve_btn = tk.Button(action_frame, text="批准", command=self.approve_selected, bg="#4CAF50", fg="white", state="disabled")
        self.approve_btn.pack(side="left", padx=20, pady=10)
        
        self.reject_btn = tk.Button(action_frame, text="拒绝", command=self.reject_selected, bg="#f44336", fg="white", state="disabled")
        self.reject_btn.pack(side="left", padx=10, pady=10)

    def on_submission_select(self, event):
        selection = self.submissions_tree.selection()
        if selection:
            self.approve_btn.config(state="normal")
            self.reject_btn.config(state="normal")
        else:
            self.approve_btn.config(state="disabled")
            self.reject_btn.config(state="disabled")

    def on_submission_double_click(self, event):
        """双击提交列表项，查看详情并支持审核"""
        selection = self.submissions_tree.selection()
        if not selection:
            return
        
        item = self.submissions_tree.item(selection[0])
        sub_id = item['tags'][0]
        
        if not self.db.is_connected:
            messagebox.showerror("错误", "数据库未连接")
            return
            
        try:
            from bson.objectid import ObjectId
            sub_doc = self.db.db.submissions.find_one({"_id": ObjectId(sub_id)})
            if sub_doc:
                self.show_submission_detail_dialog(sub_doc)
            else:
                messagebox.showwarning("提示", "提交记录不存在或已被删除")
        except Exception as e:
            messagebox.showerror("错误", f"加载详情失败: {str(e)}")

    def show_submission_detail_dialog(self, sub_doc):
        """显示提交详情对话框，包含内容和审核按钮"""
        dialog = tk.Toplevel(self.window)
        dialog.title(f"审核提交 - {sub_doc['title']}")
        dialog.geometry("600x500")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # 头部信息
        header_frame = tk.Frame(dialog, bg="#e3f2fd", pady=10)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text=sub_doc['title'], font=("Arial", 14, "bold"), bg="#e3f2fd").pack()
        info_str = f"作者: {sub_doc['username']} | 时间: {sub_doc['created_at'].strftime('%Y-%m-%d %H:%M') if sub_doc['created_at'] else '未知'} | 状态: {sub_doc['status']}"
        tk.Label(header_frame, text=info_str, font=("Arial", 10), bg="#e3f2fd", fg="#666").pack()
        
        # 内容区域
        content_frame = tk.Frame(dialog, padx=10, pady=10)
        content_frame.pack(fill="both", expand=True)
        
        text_widget = scrolledtext.ScrolledText(content_frame, font=("Arial", 11), wrap=tk.WORD, state="disabled")
        text_widget.pack(fill="both", expand=True)
        
        # 插入内容并设置为只读
        text_widget.config(state="normal")
        text_widget.insert("1.0", sub_doc['content'])
        text_widget.config(state="disabled")
        
        # 底部按钮区域
        btn_frame = tk.Frame(dialog, pady=10)
        btn_frame.pack(fill="x")
        
        sub_id = str(sub_doc['_id'])
        current_status = sub_doc['status']

        def do_approve():
            if messagebox.askyesno("确认", "确定批准该提交吗？"):
                if self.db.update_submission_status(sub_id, "approved"):
                    messagebox.showinfo("成功", "已批准")
                    dialog.destroy()
                    self.refresh_submissions()
                else:
                    messagebox.showerror("错误", "更新失败")

        def do_reject():
            if messagebox.askyesno("确认", "确定拒绝该提交吗？"):
                if self.db.update_submission_status(sub_id, "rejected"):
                    messagebox.showinfo("成功", "已拒绝")
                    dialog.destroy()
                    self.refresh_submissions()
                else:
                    messagebox.showerror("错误", "更新失败")

        # 如果已经是最终状态，禁用对应按钮或提示
        if current_status == "approved":
            tk.Label(btn_frame, text="当前状态: 已批准", fg="#4CAF50", font=("Arial", 10)).pack(side="left", padx=20)
            tk.Button(btn_frame, text="重新拒绝", command=do_reject, bg="#f44336", fg="white").pack(side="right", padx=20)
        elif current_status == "rejected":
            tk.Label(btn_frame, text="当前状态: 已拒绝", fg="#f44336", font=("Arial", 10)).pack(side="left", padx=20)
            tk.Button(btn_frame, text="重新批准", command=do_approve, bg="#4CAF50", fg="white").pack(side="right", padx=20)
        else:
            tk.Button(btn_frame, text="拒绝", command=do_reject, bg="#f44336", fg="white", width=10).pack(side="left", padx=20, expand=True)
            tk.Button(btn_frame, text="批准", command=do_approve, bg="#4CAF50", fg="white", width=10).pack(side="right", padx=20, expand=True)
            
        tk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=5)

    def approve_selected(self):
        selection = self.submissions_tree.selection()
        if not selection:
            return
        item = self.submissions_tree.item(selection[0])
        sub_id = item['tags'][0]
        if messagebox.askyesno("确认", "确定批准该提交吗？"):
            if self.db.update_submission_status(sub_id, "approved"):
                messagebox.showinfo("成功", "已批准")
                self.refresh_submissions()
            else:
                messagebox.showerror("错误", "更新失败")

    def reject_selected(self):
        selection = self.submissions_tree.selection()
        if not selection:
            return
        item = self.submissions_tree.item(selection[0])
        sub_id = item['tags'][0]
        if messagebox.askyesno("确认", "确定拒绝该提交吗？"):
            if self.db.update_submission_status(sub_id, "rejected"):
                messagebox.showinfo("成功", "已拒绝")
                self.refresh_submissions()
            else:
                messagebox.showerror("错误", "更新失败")

    def refresh_submissions(self):
        """刷新提交审核列表"""
        for item in self.submissions_tree.get_children():
            self.submissions_tree.delete(item)
        submissions = self.db.get_all_submissions()
        for sub in submissions:
            time_str = sub['created_at'].strftime("%Y-%m-%d %H:%M") if sub['created_at'] else "未知"
            status = sub['status']
            # 区分公告和普通提交，虽然都在一个表，但可以在显示上做区分
            is_ann = sub.get('is_announcement', False)
            display_title = f"[公告] {sub['title']}" if is_ann else sub['title']
            
            self.submissions_tree.insert(
                "",
                "end",
                values=(time_str, sub['username'], display_title, status, "点击下方按钮操作"),
                tags=(str(sub['_id']),)
            )

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
        
        columns = ("用户名", "邮箱", "角色", "注册时间", "状态", "操作")
        self.users_tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        self.users_tree.heading("用户名", text="用户名")
        self.users_tree.heading("邮箱", text="邮箱")
        self.users_tree.heading("角色", text="角色")
        self.users_tree.heading("注册时间", text="注册时间")
        self.users_tree.heading("状态", text="状态")
        self.users_tree.heading("操作", text="操作")
        self.users_tree.column("用户名", width=100)
        self.users_tree.column("邮箱", width=200)
        self.users_tree.column("角色", width=80)
        self.users_tree.column("注册时间", width=150)
        self.users_tree.column("状态", width=80)
        self.users_tree.column("操作", width=80)
        
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        self.users_tree.pack(side="left", fill="both", expand=True, padx=(10,0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # 绑定双击事件或点击操作列事件来管理用户
        self.users_tree.bind('<Double-Button-1>', self.on_user_manage_click)
        
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
    
    def refresh_users(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        users = self.db.get_all_users()
        
        # 获取当前登录用户是否为初始管理员
        # 修改: 使用 UserModel.INITIAL_ADMIN_USERNAME
        is_initial_admin = (self.admin['username'] == UserModel.INITIAL_ADMIN_USERNAME)
        
        for user in users:
            reg_time = user['created_at'].strftime("%Y-%m-%d %H:%M") if user.get('created_at') else "未知"
            status = "活跃" if user.get('is_active', True) else "禁用"
            role = user.get('role', 'user')
            username = user['username']
            
            action_text = "管理"
            
            # 逻辑修改：
            # 1. 如果是本人，不可操作
            if username == self.admin['username']:
                action_text = "本人"
            # 2. 如果是初始管理员，任何人不可操作 (包括他自己，防止误删/降级自己，虽然后端也限制了)
            # 修改: 使用 UserModel.INITIAL_ADMIN_USERNAME
            elif username == UserModel.INITIAL_ADMIN_USERNAME:
                action_text = "锁定"
            # 3. 如果是其他管理员：
            elif role == 'admin':
                # 只有初始管理员可以管理其他管理员
                if is_initial_admin:
                    action_text = "管理"
                else:
                    action_text = "锁定"
            # 4. 普通用户，始终可管理
            else:
                action_text = "管理"
                
            self.users_tree.insert(
                "",
                "end",
                values=(username, user['email'], role, reg_time, status, action_text),
                tags=(username,) # 将用户名存入 tags 方便获取
            )

    def on_user_manage_click(self, event):
        """处理用户管理点击事件"""
        selection = self.users_tree.selection()
        if not selection:
            return
        
        item = self.users_tree.item(selection[0])
        target_username = item['tags'][0]
        current_role = item['values'][2] # 角色列
        action_text = item['values'][5] # 操作列文本
        
        # 修改逻辑：如果是本人，允许打开管理窗口进行个人信息修改（但不允许改角色/删除自己）
        # 如果是锁定（dpp被其他人看，或其他管理员被非dpp看），则禁止
        if action_text == "锁定":
            messagebox.showwarning("提示", f"无法操作该用户: 权限不足或受保护")
            return
            
        # 打开管理窗口
        self.open_user_manage_dialog(target_username, current_role)

    def open_user_manage_dialog(self, username, current_role):
        """打开用户管理对话框"""
        dialog = tk.Toplevel(self.window)
        dialog.title(f"管理用户: {username}")
        dialog.geometry("300x250") # 稍微调高一点以容纳更多信息
        dialog.transient(self.window)
        dialog.grab_set()
        
        tk.Label(dialog, text=f"正在管理用户: {username}", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(dialog, text=f"当前角色: {current_role}", font=("Arial", 10)).pack(pady=5)
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        is_self = (username == self.admin['username'])
        # 修改: 使用 UserModel.INITIAL_ADMIN_USERNAME
        is_initial_admin = (username == UserModel.INITIAL_ADMIN_USERNAME)
        # 修改: 使用 UserModel.INITIAL_ADMIN_USERNAME
        is_operator_initial_admin = (self.admin['username'] == UserModel.INITIAL_ADMIN_USERNAME)

        def do_promote():
            if messagebox.askyesno("确认", f"确定将 {username} 升级为管理员吗？"):
                success, msg = self.db.update_user_role(username, "admin", self.admin['username'])
                messagebox.showinfo("结果", msg)
                if success:
                    dialog.destroy()
                    self.refresh_users()
                    
        def do_demote():
            if messagebox.askyesno("确认", f"确定将 {username} 降级为普通用户吗？"):
                success, msg = self.db.update_user_role(username, "user", self.admin['username'])
                messagebox.showinfo("结果", msg)
                if success:
                    dialog.destroy()
                    self.refresh_users()
                    
        def do_delete():
            if messagebox.askyesno("危险操作", f"确定要永久删除用户 {username} 吗？此操作不可恢复！"):
                success, msg = self.db.delete_user(username, self.admin['username'])
                messagebox.showinfo("结果", msg)
                if success:
                    dialog.destroy()
                    self.refresh_users()
        
        def do_edit_profile():
            # 简单的编辑个人信息功能（仅邮箱）
            edit_win = tk.Toplevel(dialog)
            edit_win.title("编辑个人信息")
            edit_win.geometry("300x150")
            edit_win.transient(dialog)
            
            tk.Label(edit_win, text="邮箱:").pack(pady=5)
            email_var = tk.StringVar(value=self.get_user_email(username))
            entry = tk.Entry(edit_win, textvariable=email_var, width=30)
            entry.pack(pady=5)
            
            def save_email():
                new_email = email_var.get()
                if not new_email:
                    messagebox.showerror("错误", "邮箱不能为空")
                    return
                # 这里需要实现更新邮箱的逻辑，暂时简化处理，仅提示
                # 实际项目中应在 db.py 添加 update_user_email 方法
                messagebox.showinfo("提示", "更新邮箱功能待实现（需后端支持）")
                # 模拟更新成功关闭
                # edit_win.destroy()
                
            tk.Button(edit_win, text="保存", command=save_email).pack(pady=10)

        # 辅助方法获取邮箱（需要查询数据库，因为 treeview 里可能有缓存或不全）
        # 为了简化，我们假设刷新后数据是新的，或者直接从 treeview 取值（如果有的话）
        # 这里为了代码简洁，暂不深入实现编辑邮箱，重点解决“页面没了”的误解，
        # 实际上是通过增加“个人信息”Tab来解决。
        
        # 根据当前角色显示按钮
        # 如果是本人，不显示角色变更和删除按钮，或者禁用
        if is_self:
             tk.Label(btn_frame, text="当前登录账号，无法更改角色或删除自己", fg="#666").pack(pady=5)
             # 可以添加一个“修改密码”或“编辑资料”的按钮，这里简化为提示去个人信息页
             tk.Label(btn_frame, text="请前往【个人信息】标签页修改资料", fg="#2196F3").pack(pady=5)
        else:
            if current_role == "user":
                tk.Button(btn_frame, text="升级为管理员", command=do_promote, bg="#4CAF50", fg="white").pack(fill="x", padx=20, pady=5)
            
            if current_role == "admin":
                # 只有初始管理员可以管理其他管理员
                if is_operator_initial_admin and not is_initial_admin:
                     tk.Button(btn_frame, text="降级为普通用户", command=do_demote, bg="#FF9800", fg="white").pack(fill="x", padx=20, pady=5)
                elif not is_operator_initial_admin:
                     tk.Label(btn_frame, text="仅初始管理员可操作其他管理员", fg="#999").pack(pady=5)
                
            # 删除按钮：不能删除自己，不能删除初始管理员，非初始管理员不能删除其他管理员
            can_delete = True
            if is_initial_admin:
                can_delete = False
            elif current_role == "admin" and not is_operator_initial_admin:
                can_delete = False
            
            if can_delete:
                tk.Button(btn_frame, text="删除用户", command=do_delete, bg="#f44336", fg="white").pack(fill="x", padx=20, pady=5)
            else:
                 tk.Label(btn_frame, text="无权删除该用户", fg="#999").pack(pady=5)
        
        tk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)

    def get_user_email(self, username):
        # 简单辅助函数，实际应优化
        user = self.db.db.users.find_one({"username": username})
        return user.get('email', '') if user else ''

    def setup_profile_tab(self, parent):
        """个人信息标签页 - 只读"""
        info_frame = tk.Frame(parent, padx=30, pady=20)
        info_frame.pack(fill="both", expand=True)
        
        # 头像占位
        tk.Label(info_frame, text="👤", font=("Arial", 48), bg="#e0e0e0", width=4, height=2).pack(pady=20)
        
        # 获取最新数据
        email = '加载中...'
        reg_time = '加载中...'
        role = '加载中...'
        
        if self.db.is_connected:
            try:
                current_user_data = self.db.db.users.find_one({"username": self.admin['username']})
                if current_user_data:
                    email = current_user_data.get('email', '未设置')
                    db_reg_time = current_user_data.get('created_at')
                    reg_time = db_reg_time.strftime("%Y-%m-%d %H:%M") if db_reg_time else '未知'
                    role = current_user_data.get('role', 'user')
                else:
                    # 降级使用内存对象
                    email = self.admin.get('email', '未设置')
                    mem_reg_time = self.admin.get('created_at')
                    reg_time = mem_reg_time.strftime("%Y-%m-%d %H:%M") if mem_reg_time and mem_reg_time != '未知' else '未知'
                    role = self.admin.get('role', 'user')
            except Exception as e:
                print(f"获取用户信息失败: {e}")
                email = self.admin.get('email', '未设置')
                role = self.admin.get('role', 'user')
        else:
             email = self.admin.get('email', '未设置')
             role = self.admin.get('role', 'user')

        # 构建只读信息展示
        info_list = [
            ("用户名", self.admin['username']),
            ("邮箱", email),
            ("角色", role),
            ("注册时间", reg_time)
        ]
        
        for label_text, value_text in info_list:
            frame = tk.Frame(info_frame)
            frame.pack(fill="x", pady=5)
            tk.Label(frame, text=f"{label_text}:", font=("Arial", 11, "bold"), width=10, anchor="w").pack(side="left")
            tk.Label(frame, text=value_text, font=("Arial", 11), anchor="w").pack(side="left", fill="x", expand=True)

    def logout(self):
        if messagebox.askyesno("确认", "确定要登出吗？"):
            self.window.destroy()
            self.root.deiconify()
    
    def on_closing(self):
        self.logout()