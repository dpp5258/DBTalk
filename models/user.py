class UserModel:
    def __init__(self, username, password, email=None, role='user', created_at=None, is_active=True, avatar_path=None):
        self.username = username
        self.password = password
        self.email = email
        self.role = role
        self.created_at = created_at
        self.is_active = is_active
        self.avatar_path = avatar_path