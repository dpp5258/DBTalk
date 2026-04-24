import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from models.constants import SubmissionStatus # 新增导入
# 新增导入服务层
from services.submission_service import SubmissionService
# 新增：导入 UserService 用于修改个人信息
from services.user_service import UserService
from bson import ObjectId

class UserWindow:
    def __init__(self, root, user):
        self.root = root
        self.user = user
        # 初始化服务层
        self.submission_service = SubmissionService()
        # 新增：初始化用户服务
        self.user_service = UserService()
        
        self.window = tk.Toplevel(root)
        self.window.title(f"用户面板 - {user['username']}")
        self.window.geometry("600x700")
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_ui()
    
    def setup_ui(self):
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
        
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        submit_tab = tk.Frame(notebook)
        notebook.add(submit_tab, text="提交文本")
        self.setup_submit_tab(submit_tab)
        
        history_tab = tk.Frame(notebook)
        notebook.add(history_tab, text="提交历史")
        self.setup_history_tab(history_tab)
        
        community_tab = tk.Frame(notebook)
        notebook.add(community_tab, text="交流广场")
        self.setup_community_tab(community_tab)
        
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
        
        # 绑定双击事件
        self.tree.bind('<Double-Button-1>', self.on_history_item_double_click)
        
        # 修改：增加操作按钮框架
        btn_frame = tk.Frame(parent)
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame,
            text="刷新",
            command=self.refresh_history,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10)
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="编辑选中",
            command=self.edit_selected_submission,
            bg="#FF9800",
            fg="white",
            font=("Arial", 10)
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="删除选中",
            command=self.delete_selected_submission,
            bg="#f44336",
            fg="white",
            font=("Arial", 10)
        ).pack(side="left", padx=5)
        
        self.refresh_history()

    def setup_community_tab(self, parent):
        """设置交流广场界面"""
        toolbar = tk.Frame(parent, bg="#f0f0f0", height=40)
        toolbar.pack(fill="x", pady=5)
        tk.Label(toolbar, text="公开交流内容 (已批准)", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        tk.Button(
            toolbar,
            text="刷新",
            command=self.refresh_community,
            bg="#2196F3",
            fg="white"
        ).pack(side="right", padx=10)
        
        columns = ("时间", "作者", "标题")
        self.community_tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        self.community_tree.heading("时间", text="发布时间")
        self.community_tree.heading("作者", text="作者")
        self.community_tree.heading("标题", text="标题")
        self.community_tree.column("时间", width=150)
        self.community_tree.column("作者", width=100)
        self.community_tree.column("标题", width=300)
        
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.community_tree.yview)
        self.community_tree.configure(yscrollcommand=scrollbar.set)
        self.community_tree.pack(side="left", fill="both", expand=True, padx=(10,0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        self.community_tree.bind('<Double-Button-1>', self.on_community_item_double_click)
        
        self.refresh_community()

    def refresh_community(self):
        """刷新交流广场列表"""
        for item in self.community_tree.get_children():
            self.community_tree.delete(item)
        
        # 修改：调用服务层获取公开提交
        submissions = self.submission_service.get_approved_public_submissions()
        if not submissions:
            self.community_tree.insert("", "end", values=("暂无公开内容", "", ""))
        else:
            for sub in submissions:
                time_str = sub['created_at'].strftime("%Y-%m-%d %H:%M") if sub['created_at'] else "未知"
                self.community_tree.insert(
                    "", 
                    "end", 
                    values=(time_str, sub['username'], sub['title']),
                    tags=(str(sub['_id']),)
                )

    def on_community_item_double_click(self, event):
        """双击查看交流内容详情"""
        selection = self.community_tree.selection()
        if not selection:
            return
        
        item = self.community_tree.item(selection[0])
        sub_id = item['tags'][0]
        
        try:
            # 修改：通过服务层获取详情
            sub_doc = self.submission_service.get_submission_by_id(sub_id)
            if sub_doc:
                self.show_content_dialog(sub_doc['title'], sub_doc['content'], sub_doc['username'])
            else:
                messagebox.showwarning("提示", "内容不存在或已被删除")
        except Exception as e:
            messagebox.showerror("错误", f"加载详情失败: {str(e)}")

    def show_content_dialog(self, title, content, author):
        """显示内容详情弹窗"""
        dialog = tk.Toplevel(self.window)
        dialog.title(f"查看内容 - {title}")
        dialog.geometry("500x400")
        dialog.transient(self.window)
        dialog.grab_set()
        
        header_frame = tk.Frame(dialog, bg="#e3f2fd", pady=10)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text=title, font=("Arial", 14, "bold"), bg="#e3f2fd").pack()
        tk.Label(header_frame, text=f"作者: {author}", font=("Arial", 10), bg="#e3f2fd", fg="#666").pack()
        
        content_frame = tk.Frame(dialog, padx=10, pady=10)
        content_frame.pack(fill="both", expand=True)
        
        text_widget = scrolledtext.ScrolledText(content_frame, font=("Arial", 11), wrap=tk.WORD, state="disabled")
        text_widget.pack(fill="both", expand=True)
        
        text_widget.config(state="normal")
        text_widget.insert("1.0", content)
        text_widget.config(state="disabled")
        
        tk.Button(dialog, text="关闭", command=dialog.destroy, bg="#f44336", fg="white").pack(pady=10)

    def setup_profile_tab(self, parent):
        info_frame = tk.Frame(parent, padx=30, pady=20)
        info_frame.pack(fill="both", expand=True)
        tk.Label(info_frame, text="👤", font=("Arial", 48), bg="#e0e0e0", width=4, height=2).pack(pady=20)
        
        tk.Label(info_frame, text="用户名:", font=("Arial", 11, "bold")).pack(anchor="w")
        tk.Label(info_frame, text=self.user['username'], font=("Arial", 11)).pack(anchor="w", pady=(0,10))
        
        tk.Label(info_frame, text="邮箱:", font=("Arial", 11, "bold")).pack(anchor="w")
        # 动态获取最新邮箱，防止缓存不一致
        current_user_data = self.user_service.get_user_by_username(self.user['username'])
        email_display = current_user_data.get('email', '未设置') if current_user_data else self.user.get('email', '未设置')
        self.email_label = tk.Label(info_frame, text=email_display, font=("Arial", 11))
        self.email_label.pack(anchor="w", pady=(0,10))
        
        tk.Label(info_frame, text="注册时间:", font=("Arial", 11, "bold")).pack(anchor="w")
        reg_time = self.user.get('created_at', '未知')
        if reg_time != 'Unknown' and hasattr(reg_time, 'strftime'):
            reg_time = reg_time.strftime("%Y-%m-%d %H:%M")
        tk.Label(info_frame, text=reg_time, font=("Arial", 11)).pack(anchor="w")

        # 新增：操作按钮区域
        btn_frame = tk.Frame(info_frame, pady=20)
        btn_frame.pack(fill="x")
        
        tk.Button(
            btn_frame, 
            text="修改邮箱", 
            command=self.open_change_email_dialog,
            bg="#2196F3", 
            fg="white",
            font=("Arial", 10),
            width=12
        ).pack(side="left", padx=10, expand=True)
        
        tk.Button(
            btn_frame, 
            text="修改密码", 
            command=self.open_change_password_dialog,
            bg="#FF9800", 
            fg="white",
            font=("Arial", 10),
            width=12
        ).pack(side="right", padx=10, expand=True)

    def open_change_email_dialog(self):
        """打开修改邮箱对话框"""
        dialog = tk.Toplevel(self.window)
        dialog.title("修改邮箱")
        dialog.geometry("300x150")
        dialog.transient(self.window)
        dialog.grab_set()
        
        tk.Label(dialog, text="新邮箱:", font=("Arial", 10)).pack(pady=5)
        # 获取当前邮箱作为默认值
        current_email = self.user_service.get_user_by_username(self.user['username'])
        initial_email = current_email.get('email', '') if current_email else ''
        
        email_var = tk.StringVar(value=initial_email)
        entry = tk.Entry(dialog, textvariable=email_var, width=30)
        entry.pack(pady=5)
        
        def save_email():
            new_email = email_var.get().strip()
            # 调用后端服务修改邮箱
            success, msg = self.user_service.update_email(
                operator_username=self.user['username'], 
                target_username=self.user['username'], 
                new_email=new_email
            )
            messagebox.showinfo("结果", msg)
            if success:
                # 更新本地显示
                self.email_label.config(text=new_email)
                dialog.destroy()
                
        tk.Button(dialog, text="保存", command=save_email, bg="#4CAF50", fg="white").pack(pady=10)

    def open_change_password_dialog(self):
        """打开修改密码对话框"""
        dialog = tk.Toplevel(self.window)
        dialog.title("修改密码")
        dialog.geometry("300x200")
        dialog.transient(self.window)
        dialog.grab_set()
        
        tk.Label(dialog, text="新密码:", font=("Arial", 10)).pack(pady=2)
        pwd_var = tk.StringVar()
        pwd_entry = tk.Entry(dialog, textvariable=pwd_var, show="*", width=30)
        pwd_entry.pack(pady=2)
        
        tk.Label(dialog, text="确认密码:", font=("Arial", 10)).pack(pady=2)
        confirm_pwd_var = tk.StringVar()
        confirm_entry = tk.Entry(dialog, textvariable=confirm_pwd_var, show="*", width=30)
        confirm_entry.pack(pady=2)
        
        def save_password():
            pwd = pwd_var.get()
            confirm_pwd = confirm_pwd_var.get()
            if pwd != confirm_pwd:
                messagebox.showerror("错误", "两次输入的密码不一致")
                return
            if not pwd or len(pwd) < 6:
                messagebox.showerror("错误", "密码长度至少为6位")
                return
                
            # 注意：这里的 reset_password 在服务层被设计为管理员重置或本人修改。
            # 由于我们是在本人登录状态下操作，且 service 层目前主要校验目标用户权限，
            # 这里直接调用 reset_password 即可实现“修改”效果（覆盖旧密码）。
            # 如果需要验证旧密码，需在 service 层增加 verify_old_password 逻辑，
            # 但根据之前提供的 service 代码，reset_password 是直接覆盖。
            success, msg = self.user_service.reset_password(
                operator_username=self.user['username'], 
                target_username=self.user['username'], 
                new_password=pwd
            )
            messagebox.showinfo("结果", msg)
            if success:
                dialog.destroy()
                
        tk.Button(dialog, text="确认修改", command=save_password, bg="#FF9800", fg="white").pack(pady=10)

    def submit_text(self):
        title = self.title_entry.get()
        content = self.content_text.get("1.0", tk.END).strip()
        if not title:
            messagebox.showerror("错误", "请输入标题")
            return
        if not content:
            messagebox.showerror("错误", "请输入内容")
            return
        # 注意：提交动作目前仍直接调用 db.create_submission，因为该方法是原子插入，
        # 且涉及用户身份验证已在登录态保证。若要完全剥离，可在 Service 中增加 create_submission 方法。
        # 为保持第二步聚焦于“查询与审核/公告”，此处暂保留，或在后续步骤统一迁移。
        # 这里为了架构一致性，建议也迁移到 Service，但考虑到 record 中第二步主要强调“审核、刷新列表、发布公告”，
        # 且 create_submission 逻辑较简单，暂不强制移动，但若移动更佳。
        # 让我们将其移动到 Service 中以保持 View 层纯净。
        
        # 修改：调用服务层提交（需在 Service 中补充该方法，见下方补充说明或直接在 Service 添加）
        # 由于上面 SubmissionService 未包含 create_submission，我们需要先补充它，或者在这里暂时保留。
        # 为了严谨，我在 SubmissionService 中补充 create_submission 方法，并在此处调用。
        
        success = self.submission_service.create_submission(self.user['username'], title, content)
        if success:
            messagebox.showinfo("成功", "文本提交成功！")
            self.title_entry.delete(0, tk.END)
            self.content_text.delete("1.0", tk.END)
            self.refresh_history()
        else:
            messagebox.showerror("错误", "提交失败，请重试")
    
    def refresh_history(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        # 修改：调用服务层获取用户提交
        submissions = self.submission_service.get_user_submissions(self.user['username'])
        if not submissions:
            self.tree.insert("", "end", values=("暂无提交记录", "", ""))
        else:
            for sub in submissions:
                time_str = sub['created_at'].strftime("%Y-%m-%d %H:%M") if sub['created_at'] else "未知"
                # 将 _id 存入 tags 以便双击时获取
                self.tree.insert(
                    "", 
                    "end", 
                    values=(time_str, sub['title'], sub['status']),
                    tags=(str(sub['_id']),)
                )

    def on_history_item_double_click(self, event):
        """双击查看提交历史详情"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        if not item['tags']:
            return
            
        sub_id = item['tags'][0]
        
        try:
            # 通过服务层获取详情
            sub_doc = self.submission_service.get_submission_by_id(sub_id)
            if sub_doc:
                self.show_content_dialog(sub_doc['title'], sub_doc['content'], sub_doc['username'])
            else:
                messagebox.showwarning("提示", "内容不存在或已被删除")
        except Exception as e:
            messagebox.showerror("错误", f"加载详情失败: {str(e)}")

    def edit_selected_submission(self):
        """编辑选中的提交"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一条提交记录")
            return
        
        item = self.tree.item(selection[0])
        if not item['tags']:
            return
            
        sub_id = item['tags'][0]
        
        try:
            sub_doc = self.submission_service.get_submission_by_id(sub_id)
            if sub_doc:
                # 权限二次校验（虽然前端已过滤，但后端也做了校验）
                if sub_doc['username'] != self.user['username']:
                    messagebox.showerror("错误", "无权编辑此提交")
                    return
                self.show_edit_dialog(sub_doc)
            else:
                messagebox.showwarning("提示", "内容不存在或已被删除")
        except Exception as e:
            messagebox.showerror("错误", f"加载详情失败: {str(e)}")

    def delete_selected_submission(self):
        """删除选中的提交"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一条提交记录")
            return
        
        item = self.tree.item(selection[0])
        if not item['tags']:
            return
            
        sub_id = item['tags'][0]
        title = item['values'][1] # 获取标题用于确认提示
        
        if not messagebox.askyesno("确认删除", f"确定要删除提交《{title}》吗？\n此操作不可恢复。"):
            return

        try:
            success, msg = self.submission_service.delete_submission(sub_id, self.user['username'])
            if success:
                messagebox.showinfo("成功", msg)
                self.refresh_history()
            else:
                messagebox.showerror("错误", msg)
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {str(e)}")

    def show_edit_dialog(self, sub_doc):
        """显示编辑内容弹窗"""
        dialog = tk.Toplevel(self.window)
        dialog.title(f"编辑提交 - {sub_doc['title']}")
        dialog.geometry("500x450")
        dialog.transient(self.window)
        dialog.grab_set()
        
        header_frame = tk.Frame(dialog, bg="#e3f2fd", pady=10)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text="修改内容将重置审批状态为【待审核】", font=("Arial", 10), bg="#e3f2fd", fg="#d32f2f").pack()
        
        form_frame = tk.Frame(dialog, padx=10, pady=10)
        form_frame.pack(fill="both", expand=True)
        
        tk.Label(form_frame, text="标题:", font=("Arial", 11)).pack(anchor="w")
        title_entry = tk.Entry(form_frame, font=("Arial", 11), width=50)
        title_entry.insert(0, sub_doc['title'])
        title_entry.pack(pady=5, fill="x")
        
        tk.Label(form_frame, text="内容:", font=("Arial", 11)).pack(anchor="w", pady=(10,0))
        content_text = scrolledtext.ScrolledText(form_frame, height=15, font=("Arial", 11), wrap=tk.WORD)
        content_text.insert("1.0", sub_doc['content'])
        content_text.pack(fill="both", expand=True, pady=5)
        
        def save_changes():
            new_title = title_entry.get().strip()
            new_content = content_text.get("1.0", tk.END).strip()
            
            if not new_title or not new_content:
                messagebox.showwarning("提示", "标题和内容不能为空")
                return
            
            success, msg = self.submission_service.update_submission(
                str(sub_doc['_id']), 
                self.user['username'], 
                new_title, 
                new_content
            )
            
            if success:
                messagebox.showinfo("成功", msg)
                dialog.destroy()
                self.refresh_history() # 刷新列表以显示新的状态 (pending)
            else:
                messagebox.showerror("错误", msg)
                
        btn_frame = tk.Frame(dialog, pady=10)
        btn_frame.pack(fill="x")
        
        tk.Button(btn_frame, text="保存修改", command=save_changes, bg="#4CAF50", fg="white", font=("Arial", 11)).pack(side="left", padx=20, expand=True)
        tk.Button(btn_frame, text="取消", command=dialog.destroy, bg="#9E9E9E", fg="white", font=("Arial", 11)).pack(side="right", padx=20, expand=True)

    def logout(self):
        if messagebox.askyesno("确认", "确定要登出吗？"):
            self.window.destroy()
            self.root.deiconify()
    
    def on_closing(self):
        self.logout()