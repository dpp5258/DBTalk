import tkinter as tk
from views.login_window import LoginWindow
from utils.db import Database
from config import Config

def main():
    root = tk.Tk()
    root.title(f"{Config.APP_NAME} - {Config.APP_VERSION}")
    root.geometry("400x500")
    root.resizable(False, False)
    
    # 初始化数据库连接
    db = Database()
    if not db.is_connected:
        print("警告: 数据库未连接，部分功能将不可用")
    
    app = LoginWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()