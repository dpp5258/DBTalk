import pygame
import os
import threading

class MusicManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.is_playing = False
        self.music_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qhc.mp3')
        
        # 修改：默认开启音乐，不再加载持久化状态
        self.enabled = True

        # 尝试初始化 mixer
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception as e:
            print(f"音频系统初始化失败: {e}")
            self.is_playing = False
            self.enabled = False
            return




    def set_enabled(self, enabled: bool):
        """设置音乐是否启用，并自动处理播放/停止"""
        self.enabled = enabled
        if enabled:
            self.play()
        else:
            self.stop()

    def get_status(self):
        """获取当前启用状态"""
        return self.enabled

    def set_music_path(self, path):
        """设置音乐文件路径"""
        if os.path.exists(path):
            self.music_path = path
        else:
            print(f"音乐文件不存在: {path}")

    def play(self):
        """开始/继续播放音乐"""
        # 只有当启用且未在播放时才播放
        if self.enabled and not self.is_playing:
            try:
                if os.path.exists(self.music_path):
                    pygame.mixer.music.load(self.music_path)
                    # loops=-1 表示无限循环
                    pygame.mixer.music.play(loops=-1) 
                    self.is_playing = True
                    print("背景音乐已开启")
                else:
                    print(f"未找到音乐文件: {self.music_path}")
            except Exception as e:
                print(f"播放音乐失败: {e}")

    def stop(self):
        """停止播放音乐"""
        if self.is_playing:
            try:
                pygame.mixer.music.stop()
                self.is_playing = False
                print("背景音乐已关闭")
            except Exception as e:
                print(f"停止音乐失败: {e}")

    def toggle(self):
        """切换播放状态"""
        new_state = not self.enabled
        self.set_enabled(new_state)
        return new_state
