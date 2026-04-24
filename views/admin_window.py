import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from utils.db import Database
from models.constants import UserRole, SubmissionStatus, InitialAdmin
from models.submission import SubmissionModel
from services.submission_service import SubmissionService
from services.user_service import UserService
from bson import ObjectId
from datetime import datetime
import os
import tkinter.font as tkfont

class AdminWindow:
    def __init__(self, root, admin):
        self.root = root
        self.admin = admin
        self.db = Database()
        self.submission_service = SubmissionService()
        self.user_service = UserService()
        
        # 加载自定义字体
        self.custom_font_family = self._load_custom_font()
        
        self.window = tk.Toplevel(root)
        self.window.title(f"管理员面板 - {admin['username']}")
        self.window.geometry("900x700")
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_ui()
    
    def _load_custom_font(self):
        """加载自定义字体并返回家族名称"""
        font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "07.ttf")
        if os.path.exists(font_path):
            try:
                font = tkfont.Font(file=font_path, size=12)
                return font.actual('family')
            except Exception:
                pass
        return "Arial" #  fallback
    
    def setup_ui(self):
        # 顶部栏
        top_frame = tk.Frame(self.window, bg="#1e3c72", height=50)
        top_frame.pack(fill="x")
        tk.Label(
            top_frame,
            text=f"管理员: {self.admin['username']}",
            font=(self.custom_font_family, 12, "bold"),
            bg="#1e3c72",
            fg="white"
        ).pack(side="left", padx=20, pady=15)
        tk.Button(
            top_frame,
            text="登出",
            command=self.logout,
            bg="#f44336",
            fg="white",
            font=(self.custom_font_family, 10),
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
        
    def setup_announcement_tab(self, parent):
        """管理员发布公告/内容"""
        tk.Label(parent, text="发布全局公告/内容", font=(self.custom_font_family, 14, "bold")).pack(pady=10)
        form_frame = tk.Frame(parent, padx=20, pady=10)
        form_frame.pack(fill="both", expand=True)
        
        tk.Label(form_frame, text="标题:", font=(self.custom_font_family, 11)).pack(anchor="w")
        self.ann_title_entry = tk.Entry(form_frame, font=(self.custom_font_family, 11), width=50)
        self.ann_title_entry.pack(pady=5, fill="x")
        
        tk.Label(form_frame, text="内容:", font=(self.custom_font_family, 11)).pack(anchor="w", pady=(10,0))
        self.ann_content_text = tk.Text(form_frame, height=10, font=(self.custom_font_family, 11), wrap=tk.WORD)
        self.ann_content_text.pack(fill="both", expand=True, pady=5)
        
        tk.Button(
            form_frame,
            text="发布公告",
            command=self.post_announcement,
            bg="#FF9800",
            fg="white",
            font=(self.custom_font_family, 12, "bold"),
            width=15
        ).pack(pady=20)

    def post_announcement(self):
        title = self.ann_title_entry.get()
        content = self.ann_content_text.get("1.0", tk.END).strip()
        
        if not title or not content:
            messagebox.showwarning("提示", "标题和内容不能为空")
            return
            
        try:
            self.submission_service.create_announcement(self.admin['username'], title, content)
            messagebox.showinfo("成功", "公告发布成功！")
            self.ann_title_entry.delete(0, tk.END)
            self.ann_content_text.delete("1.0", tk.END)
        except Exception as e:
            messagebox.showerror("错误", f"发布失败: {str(e)}")

    def setup_submissions_tab(self, parent):
        toolbar = tk.Frame(parent, bg="#f0f0f0", height=40)
        toolbar.pack(fill="x", pady=5)
        tk.Label(toolbar, text="用户提交审核", font=(self.custom_font_family, 12, "bold")).pack(side="left", padx=10)
        tk.Button(
            toolbar,
            text="刷新",
            command=self.refresh_submissions,
            bg="#2196F3",
            fg="white",
            font=(self.custom_font_family, 10)
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
        self.submissions_tree.bind('<Double-Button-1>', self.on_submission_double_click)
        self.refresh_submissions()
        
        # 底部操作栏
        action_frame = tk.Frame(parent, bg="#f0f0f0", height=50)
        action_frame.pack(fill="x", pady=5)
        
        self.approve_btn = tk.Button(action_frame, text="批准", command=self.approve_selected, bg="#4CAF50", fg="white", state="disabled", font=(self.custom_font_family, 10))
        self.approve_btn.pack(side="left", padx=20, pady=10)
        
        self.reject_btn = tk.Button(action_frame, text="拒绝", command=self.reject_selected, bg="#f44336", fg="white", state="disabled", font=(self.custom_font_family, 10))
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
        
        try:
            sub_doc = self.submission_service.get_submission_by_id(sub_id)
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
        tk.Label(header_frame, text=sub_doc['title'], font=(self.custom_font_family, 14, "bold"), bg="#e3f2fd").pack()
        info_str = f"作者: {sub_doc['username']} | 时间: {sub_doc['created_at'].strftime('%Y-%m-%d %H:%M') if sub_doc['created_at'] else '未知'} | 状态: {sub_doc['status']}"
        tk.Label(header_frame, text=info_str, font=(self.custom_font_family, 10), bg="#e3f2fd", fg="#666").pack()
        
        # 内容区域
        content_frame = tk.Frame(dialog, padx=10, pady=10)
        content_frame.pack(fill="both", expand=True)
        
        text_widget = scrolledtext.ScrolledText(content_frame, font=(self.custom_font_family, 11), wrap=tk.WORD, state="disabled")
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
                if self.submission_service.approve_submission(sub_id):
                    messagebox.showinfo("成功", "已批准")
                    dialog.destroy()
                    self.refresh_submissions()
                else:
                    messagebox.showerror("错误", "更新失败")

        def do_reject():
            if messagebox.askyesno("确认", "确定拒绝该提交吗？"):
                if self.submission_service.reject_submission(sub_id):
                    messagebox.showinfo("成功", "已拒绝")
                    dialog.destroy()
                    self.refresh_submissions()
                else:
                    messagebox.showerror("错误", "更新失败")

        if current_status == SubmissionStatus.APPROVED:
            tk.Label(btn_frame, text="当前状态: 已批准", fg="#4CAF50", font=(self.custom_font_family, 10)).pack(side="left", padx=20)
            tk.Button(btn_frame, text="重新拒绝", command=do_reject, bg="#f44336", fg="white", font=(self.custom_font_family, 10)).pack(side="right", padx=20)
        elif current_status == SubmissionStatus.REJECTED:
            tk.Label(btn_frame, text="当前状态: 已拒绝", fg="#f44336", font=(self.custom_font_family, 10)).pack(side="left", padx=20)
            tk.Button(btn_frame, text="重新批准", command=do_approve, bg="#4CAF50", fg="white", font=(self.custom_font_family, 10)).pack(side="right", padx=20)
        else:
            tk.Button(btn_frame, text="拒绝", command=do_reject, bg="#f44336", fg="white", width=10, font=(self.custom_font_family, 10)).pack(side="left", padx=20, expand=True)
            tk.Button(btn_frame, text="批准", command=do_approve, bg="#4CAF50", fg="white", width=10, font=(self.custom_font_family, 10)).pack(side="right", padx=20, expand=True)
            
        tk.Button(dialog, text="关闭", command=dialog.destroy, font=(self.custom_font_family, 10)).pack(pady=5)

    def approve_selected(self):
        selection = self.submissions_tree.selection()
        if not selection:
            return
        item = self.submissions_tree.item(selection[0])
        sub_id = item['tags'][0]
        if messagebox.askyesno("确认", "确定批准该提交吗？"):
            if self.submission_service.approve_submission(sub_id):
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
            if self.submission_service.reject_submission(sub_id):
                messagebox.showinfo("成功", "已拒绝")
                self.refresh_submissions()
            else:
                messagebox.showerror("错误", "更新失败")

    def refresh_submissions(self):
        """刷新提交审核列表"""
        for item in self.submissions_tree.get_children():
            self.submissions_tree.delete(item)
        submissions = self.submission_service.get_all_submissions()
        for sub in submissions:
            time_str = sub['created_at'].strftime("%Y-%m-%d %H:%M") if sub['created_at'] else "未知"
            status = sub['status']
            # 区分公告和普通提交
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
        tk.Label(toolbar, text="用户列表", font=(self.custom_font_family, 12, "bold")).pack(side="left", padx=10)
        tk.Button(
            toolbar,
            text="刷新",
            command=self.refresh_users,
            bg="#2196F3",
            fg="white",
            font=(self.custom_font_family, 10)
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
    
    def refresh_users(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        users = self.user_service.get_all_users()
        
        # 获取当前登录用户是否为初始管理员
        is_initial_admin = (self.admin['username'] == InitialAdmin.USERNAME)
        
        for user in users:
            reg_time = user['created_at'].strftime("%Y-%m-%d %H:%M") if user.get('created_at') else "未知"
            status = "活跃" if user.get('is_active', True) else "禁用"
            role = user.get('role', UserRole.USER)
            username = user['username']
            
            action_text = "管理"
            
            # 逻辑简化：视图层只负责显示状态，具体权限由 Service 控制或在点击时校验
            # 这里保留简单的视觉提示，但实际操作由 Service 决定
            if username == self.admin['username']:
                action_text = "本人"
            elif username == InitialAdmin.USERNAME:
                action_text = "锁定"
            elif role == UserRole.ADMIN:
                if not is_initial_admin:
                    action_text = "锁定"
            
            self.users_tree.insert(
                "",
                "end",
                values=(username, user['email'], role, reg_time, status, action_text),
                tags=(username,)
            )

    def on_user_manage_click(self, event):
        """处理用户管理点击事件"""
        selection = self.users_tree.selection()
        if not selection:
            return
        
        item = self.users_tree.item(selection[0])
        target_username = item['tags'][0]
        current_role = item['values'][2]
        action_text = item['values'][5]
        
        if action_text == "锁定":
            messagebox.showwarning("提示", f"无法操作该用户: 权限不足或受保护")
            return
            
        self.open_user_manage_dialog(target_username, current_role)

    def open_user_manage_dialog(self, username, current_role):
        """打开用户管理对话框"""
        dialog = tk.Toplevel(self.window)
        dialog.title(f"管理用户: {username}")
        dialog.geometry("350x350") # 调整大小以容纳新按钮
        dialog.transient(self.window)
        dialog.grab_set()
        
        tk.Label(dialog, text=f"正在管理用户: {username}", font=(self.custom_font_family, 12, "bold")).pack(pady=10)
        tk.Label(dialog, text=f"当前角色: {current_role}", font=(self.custom_font_family, 10)).pack(pady=5)
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        is_self = (username == self.admin['username'])
        is_initial_admin = (username == InitialAdmin.USERNAME)
        is_operator_initial_admin = (self.admin['username'] == InitialAdmin.USERNAME)

        def do_promote():
            if messagebox.askyesno("确认", f"确定将 {username} 升级为管理员吗？"):
                success, msg = self.user_service.update_role(self.admin['username'], username, UserRole.ADMIN)
                messagebox.showinfo("结果", msg)
                if success:
                    dialog.destroy()
                    self.refresh_users()
                    
        def do_demote():
            if messagebox.askyesno("确认", f"确定将 {username} 降级为普通用户吗？"):
                success, msg = self.user_service.update_role(self.admin['username'], username, UserRole.USER)
                messagebox.showinfo("结果", msg)
                if success:
                    dialog.destroy()
                    self.refresh_users()
                    
        def do_delete():
            if messagebox.askyesno("危险操作", f"确定要永久删除用户 {username} 吗？此操作不可恢复！"):
                success, msg = self.user_service.delete_user(self.admin['username'], username)
                messagebox.showinfo("结果", msg)
                if success:
                    dialog.destroy()
                    self.refresh_users()
        
        def do_edit_email():
            # 获取当前邮箱
            current_email = self.get_user_email(username)
            edit_win = tk.Toplevel(dialog)
            edit_win.title("修改邮箱")
            edit_win.geometry("300x150")
            edit_win.transient(dialog)
            edit_win.grab_set()
            
            tk.Label(edit_win, text="新邮箱:", font=(self.custom_font_family, 10)).pack(pady=5)
            email_var = tk.StringVar(value=current_email)
            entry = tk.Entry(edit_win, textvariable=email_var, width=30)
            entry.pack(pady=5)
            
            def save_email():
                new_email = email_var.get().strip()
                success, msg = self.user_service.update_email(self.admin['username'], username, new_email)
                messagebox.showinfo("结果", msg)
                if success:
                    edit_win.destroy()
                    # 刷新主列表以显示新邮箱（如果需要）
                    self.refresh_users()
                    
            tk.Button(edit_win, text="保存", command=save_email, bg="#4CAF50", fg="white", font=(self.custom_font_family, 10)).pack(pady=10)

        def do_reset_password():
            reset_win = tk.Toplevel(dialog)
            reset_win.title("重置密码")
            reset_win.geometry("300x180")
            reset_win.transient(dialog)
            reset_win.grab_set()
            
            tk.Label(reset_win, text=f"为用户 [{username}] 设置新密码", font=(self.custom_font_family, 10)).pack(pady=5)
            tk.Label(reset_win, text="新密码:", font=(self.custom_font_family, 10)).pack(pady=2)
            pwd_var = tk.StringVar()
            pwd_entry = tk.Entry(reset_win, textvariable=pwd_var, show="*", width=30)
            pwd_entry.pack(pady=2)
            
            tk.Label(reset_win, text="确认密码:", font=(self.custom_font_family, 10)).pack(pady=2)
            confirm_pwd_var = tk.StringVar()
            confirm_entry = tk.Entry(reset_win, textvariable=confirm_pwd_var, show="*", width=30)
            confirm_entry.pack(pady=2)
            
            def save_password():
                pwd = pwd_var.get()
                confirm_pwd = confirm_pwd_var.get()
                if pwd != confirm_pwd:
                    messagebox.showerror("错误", "两次输入的密码不一致")
                    return
                if not pwd:
                    messagebox.showerror("错误", "密码不能为空")
                    return
                    
                success, msg = self.user_service.reset_password(self.admin['username'], username, pwd)
                messagebox.showinfo("结果", msg)
                if success:
                    reset_win.destroy()
                    
            tk.Button(reset_win, text="确认重置", command=save_password, bg="#FF9800", fg="white", font=(self.custom_font_family, 10)).pack(pady=10)

        if is_self:
             tk.Label(btn_frame, text="当前登录账号，无法更改角色或删除自己", fg="#666", font=(self.custom_font_family, 10)).pack(pady=5)
             # 允许自己修改邮箱和密码
             tk.Button(btn_frame, text="修改我的邮箱", command=do_edit_email, bg="#2196F3", fg="white", font=(self.custom_font_family, 10)).pack(fill="x", padx=20, pady=2)
             tk.Button(btn_frame, text="修改我的密码", command=do_reset_password, bg="#2196F3", fg="white", font=(self.custom_font_family, 10)).pack(fill="x", padx=20, pady=2)
        else:
            if current_role == UserRole.USER:
                tk.Button(btn_frame, text="升级为管理员", command=do_promote, bg="#4CAF50", fg="white", font=(self.custom_font_family, 10)).pack(fill="x", padx=20, pady=2)
            
            if current_role == UserRole.ADMIN:
                if is_operator_initial_admin and not is_initial_admin:
                     tk.Button(btn_frame, text="降级为普通用户", command=do_demote, bg="#FF9800", fg="white", font=(self.custom_font_family, 10)).pack(fill="x", padx=20, pady=2)
                elif not is_operator_initial_admin:
                     tk.Label(btn_frame, text="仅初始管理员可操作其他管理员", fg="#999", font=(self.custom_font_family, 10)).pack(pady=2)
                
            # 管理员可以修改其他用户的邮箱和密码
            tk.Button(btn_frame, text="修改用户邮箱", command=do_edit_email, bg="#2196F3", fg="white", font=(self.custom_font_family, 10)).pack(fill="x", padx=20, pady=2)
            tk.Button(btn_frame, text="重置用户密码", command=do_reset_password, bg="#FF9800", fg="white", font=(self.custom_font_family, 10)).pack(fill="x", padx=20, pady=2)

            can_delete = True
            if is_initial_admin:
                can_delete = False
            elif current_role == UserRole.ADMIN and not is_operator_initial_admin:
                can_delete = False
            
            if can_delete:
                tk.Button(btn_frame, text="删除用户", command=do_delete, bg="#f44336", fg="white", font=(self.custom_font_family, 10)).pack(fill="x", padx=20, pady=2)
            else:
                 tk.Label(btn_frame, text="无权删除该用户", fg="#999", font=(self.custom_font_family, 10)).pack(pady=2)
        
        tk.Button(dialog, text="关闭", command=dialog.destroy, font=(self.custom_font_family, 10)).pack(pady=10)

    def get_user_email(self, username):
        # 修改：通过 UserService 获取用户信息，而不是直接操作 DB
        user = self.user_service.get_user_by_username(username)
        return user.get('email', '') if user else ''

    def setup_profile_tab(self, parent):
        """个人信息标签页 - 只读"""
        info_frame = tk.Frame(parent, padx=30, pady=20)
        info_frame.pack(fill="both", expand=True)
        
        tk.Label(info_frame, text="👤", font=(self.custom_font_family, 48), bg="#e0e0e0", width=4, height=2).pack(pady=20)
        
        # 新增：通过 UserService 获取最新用户信息
        current_user_data = self.user_service.get_user_by_username(self.admin['username'])
        
        if current_user_data:
            email = current_user_data.get('email', '未设置')
            db_reg_time = current_user_data.get('created_at')
            reg_time = db_reg_time.strftime("%Y-%m-%d %H:%M") if db_reg_time else '未知'
            role = current_user_data.get('role', UserRole.USER)
        else:
            # 降级方案：使用登录时缓存的信息
            email = self.admin.get('email', '未设置')
            mem_reg_time = self.admin.get('created_at')
            reg_time = mem_reg_time.strftime("%Y-%m-%d %H:%M") if mem_reg_time and mem_reg_time != '未知' else '未知'
            role = self.admin.get('role', UserRole.USER)

        info_list = [
            ("用户名", self.admin['username']),
            ("邮箱", email),
            ("角色", role),
            ("注册时间", reg_time)
        ]
        
        for label_text, value_text in info_list:
            frame = tk.Frame(info_frame)
            frame.pack(fill="x", pady=5)
            tk.Label(frame, text=f"{label_text}:", font=(self.custom_font_family, 11, "bold"), width=10, anchor="w").pack(side="left")
            tk.Label(frame, text=value_text, font=(self.custom_font_family, 11), anchor="w").pack(side="left", fill="x", expand=True)

    def logout(self):
        if messagebox.askyesno("确认", "确定要登出吗？"):
            self.window.destroy()
            self.root.deiconify()
    
    def on_closing(self):
        self.logout()