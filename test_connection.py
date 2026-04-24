#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MongoDB Atlas 连接测试脚本
直接运行此文件测试数据库连接
"""

import sys
from datetime import datetime
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import Config

def test_connection():
    """测试MongoDB Atlas连接"""
    print("=" * 50)
    print(" MongoDB Atlas 连接测试")
    print("=" * 50)
    
    # 检查配置
    if not Config.MONGODB_URI:
        print("❌ 错误: 未配置MongoDB连接字符串")
        print("\n请按以下步骤配置:")
        print("1. 在项目根目录创建 .env 文件")
        print("2. 添加以下内容:")
        print("  mongodb+srv://dpp:dpp5258@cluster0.75iw89g.mongodb.net/ ")
        print("   DATABASE_NAME=DBTalk1")
        return False
    
    print(f"📁 配置文件: {Config.__dict__}")
    print(f"🔗 连接字符串: {Config.MONGODB_URI[:50]}..." if len(Config.MONGODB_URI) > 50 else Config.MONGODB_URI)
    print()
    
    try:
        # 创建客户端
        print("⏳ 正在连接MongoDB Atlas...")
        client = MongoClient(
            Config.MONGODB_URI,
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=10000  # 10秒超时
        )
        
        # 发送ping命令测试连接
        client.admin.command('ping')
        print("✅ 成功连接到MongoDB Atlas!")
        
        # 获取数据库
        db = client[Config.DATABASE_NAME]
        
        # 显示数据库信息
        print(f"\n📊 数据库信息:")
        print(f"   - 数据库名称: {Config.DATABASE_NAME}")
        
        # 列出所有集合
        collections = db.list_collection_names()
        print(f"   - 现有集合: {collections if collections else '无'}")
        
        # 创建测试集合和文档
        print("\n🧪 执行写入测试...")
        
        test_collection = db.test_connection
        test_result = test_collection.insert_one({
            "test": "connection",
            "timestamp": datetime.now(),
            "message": "测试连接成功"
        })
        
        print(f"   ✅ 测试文档已插入, ID: {test_result.inserted_id}")
        
        # 读取测试
        test_doc = test_collection.find_one({"test": "connection"})
        print(f"   ✅ 测试文档已读取: {test_doc['message']}")
        
        # 清理测试数据
        test_collection.delete_many({"test": "connection"})
        print(f"   ✅ 测试数据已清理")
        
        # 创建必要的集合（如果不存在）
        if "users" not in collections:
            db.create_collection("users")
            print("   ✅ 已创建 users 集合")
        
        if "submissions" not in collections:
            db.create_collection("submissions")
            print("   ✅ 已创建 submissions 集合")
        
        print("\n" + "=" * 50)
        print("🎉 所有测试通过！数据库连接正常！")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        print("\n可能的原因:")
        print("1. 网络连接问题 - 检查是否能访问互联网")
        print("2. 连接字符串错误 - 检查用户名和密码")
        print("3. IP地址未授权 - 在MongoDB Atlas中添加当前IP")
        print("4. 防火墙阻止 - 检查防火墙设置")
        print("\n🔧 解决方案:")
        print("1. 登录 MongoDB Atlas")
        print("2. 进入 Network Access 页面")
        print("3. 点击 'Add IP Address'")
        print("4. 选择 'Add Current IP Address' 或添加 0.0.0.0/0（允许所有IP）")
        return False

def quick_test():
    """快速测试函数，可在Python交互环境中调用"""
    success = test_connection()
    if success:
        print("\n💡 现在可以运行主程序了: python main.py")
    else:
        print("\n⚠️  请先解决连接问题再运行主程序")

if __name__ == "__main__":
    # 运行测试
    test_connection()
    
    # 询问是否继续
    print("\n")
    input("按回车键退出...")