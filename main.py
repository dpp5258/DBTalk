import tkinter as tk
from views.login_window import LoginWindow
from utils.db import Database
from config import Config
import sys

def main():
    root = tk.Tk()
    root.title(f"{Config.APP_NAME} - {Config.APP_VERSION}")
    root.geometry("400x500")
    root.resizable(False, False)
    
    db = None
    try:
        # 初始化数据库连接
        db = Database()
        if not db.is_connected:
            print("警告: 数据库未连接，部分功能将不可用")
        
        app = LoginWindow(root)
        root.mainloop()
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        sys.exit(1)
    finally:
        # 确保在程序退出前关闭数据库连接
        if db and hasattr(db, 'close'):
            try:
                db.close()
            except Exception as e:
                print(f"关闭数据库连接时出错: {e}")

if __name__ == "__main__":
    main()