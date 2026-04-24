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



            

