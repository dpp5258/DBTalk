import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase, QFont  # 1. 导入 QFont
from views.login_window import LoginWindow
from utils.db import Database
from config import Config

def main():
 app = QApplication(sys.argv)
 app.setApplicationName(f"{Config.APP_NAME}")
 
 # --------------------------
 # 加载自定义字体（07.ttf）
 # --------------------------
 font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "07.ttf")
 if os.path.exists(font_path):
  try:
   font_id = QFontDatabase.addApplicationFont(font_path)
   if font_id != -1:
    font_families = QFontDatabase.applicationFontFamilies(font_id)
    if font_families:
     font_name = font_families[0]
     print(f"✅ 已加载自定义字体: {font_path}")
     print(f"   字体家族名称: {font_name}")
     
     # 2. 修复：创建 QFont 对象而不是直接传递字符串
     custom_font = QFont(font_name)
     app.setFont(custom_font)
    else:
     print(f"⚠️ 字体文件存在但无法提取字体家族: {font_path}")
   else:
    print(f"⚠️ 字体加载失败 (ID=-1)，可能字体文件损坏: {font_path}")
  except Exception as e:
   print(f"⚠️ 加载字体异常: {e}")
 else:
  print(f"ℹ️ 未找到自定义字体文件: {font_path} (将使用系统默认字体)")

 # --------------------------
 # 初始化数据库
 # --------------------------
 db_instance = None
 try:
  # 获取单例数据库实例
  db_instance = Database()
  
  if not db_instance.is_connected:
   print("⚠️ 警告: 数据库未连接。请检查网络连接或点击登录界面的'文件->云端配置'进行设置。")
   # 即使未连接，也允许启动程序，以便用户去配置

  # 启动登录窗口
  window = LoginWindow()
  window.show()
  
  # 进入主事件循环
  sys.exit(app.exec())

 except Exception as e:
  print(f"❌ 应用程序启动失败: {e}")
  import traceback
  traceback.print_exc()
  sys.exit(1)

 finally:
  # 安全关闭数据库连接
  if db_instance and db_instance.client:
   try:
    db_instance.client.close()
    print("✅ 数据库连接已关闭")
   except Exception as e:
    print(f"⚠️ 关闭数据库连接时出错: {e}")

if __name__ == "__main__":
 main()