# main.py
import tkinter as tk
from views.login_window import LoginWindow
from utils.db import Database
from config import Config
import sys
import os
import tkinter.font as tkfont

def main():
    root = tk.Tk()
    root.title(f"{Config.APP_NAME} - {Config.APP_VERSION}")
    root.geometry("400x500")
    root.resizable(False, False)

    # 加载并注册自定义字体
    # 使用 os.path.dirname(os.path.abspath(__file__)) 获取当前脚本所在目录的路径
    font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "07.ttf")
    
    # 将字体对象保存在 root 上，防止被垃圾回收
    custom_font = None
    
    if os.path.exists(font_path):
        try:
            # 加载字体文件
            # 注意：tkfont.Font 返回的对象需要被引用，否则可能失效
            custom_font = tkfont.Font(root=root, file=font_path, size=12)
            font_family = custom_font.actual('family')
            
            # 设置默认字体
            root.option_add("*Font", font_family)
            
            # 也可以显式设置特定控件的字体，如果需要
            # root.option_add("*Label.Font", font_family)
            # root.option_add("*Button.Font", font_family)
            
            print(f"✅ 已加载自定义字体: {font_path}")
            print(f"   字体家族名称: {font_family}")
        except Exception as e:
            print(f"⚠️ 加载字体失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"⚠️ 未找到字体文件: {font_path}")
        print(f"   请确保 07.ttf 位于: {os.path.dirname(os.path.abspath(__file__))}")

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