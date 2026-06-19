from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QSystemTrayIcon, QMenu
)
from PyQt6.QtGui import QMovie, QIcon
from PyQt6.QtCore import Qt, QPoint
import sys

class GifPet(QWidget):
    def __init__(self):
        super().__init__()

        # ========== 可自由修改的配置项 ==========
        # 尺寸列表 (宽,高)，自行增删
        self.size_list = [
            (80, 80),
            (120, 120),
            (160, 160),
            (200, 200),
            (240, 240),
            (280, 280),
            (320, 320)
        ]
        self.cur_size_idx = 2  # 默认尺寸索引

        # 速度列表：数值越小越慢，数值越大越快，100=原速
        self.speed_list = [30, 50, 80, 100, 130, 160, 200, 400]
        self.cur_speed_idx = 3  # 默认速度索引(100原速)
        # =====================================

        # 窗口样式：透明、无边框、置顶
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # GIF 播放器
        self.label = QLabel(self)
        self.movie = QMovie("pet.gif")
        self.movie.setSpeed(self.speed_list[self.cur_speed_idx])
        self.label.setMovie(self.movie)
        self.movie.start()
        self.label.setScaledContents(True)
        self.update_size()

        # 拖动变量
        self.drag = False
        self.drag_pos = QPoint()

        # 托盘初始化
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon.fromTheme("computer"))
        self.tray.setToolTip("GIF桌宠")

        # 构建托盘主菜单
        main_menu = QMenu()

        # -------- 子菜单：调整大小 --------
        size_menu = main_menu.addMenu("调整大小")
        for idx, (w, h) in enumerate(self.size_list):
            act = size_menu.addAction(f"{w} × {h}")
            act.triggered.connect(lambda ch, i=idx: self.set_size(i))

        main_menu.addSeparator()

        # -------- 子菜单：播放速度（红色狂暴模式，HTML实现） --------
        speed_menu = main_menu.addMenu("播放速度")
        for idx, val in enumerate(self.speed_list):
            act = speed_menu.addAction("")
            act.triggered.connect(lambda ch, i=idx: self.set_speed(i))

            # 狂暴模式：红色字体
            if val == 400:
                act.setText('狂暴模式')
            else:
                if val < 60:
                    txt = f"{val} (极慢)"
                elif val < 100:
                    txt = f"{val} (较慢)"
                elif val == 100:
                    txt = f"{val} (原速)"
                elif val < 150:
                    txt = f"{val} (较快)"
                else:
                    txt = f"{val} (极快)"
                act.setText(txt)

        main_menu.addSeparator()
        # 退出选项
        exit_act = main_menu.addAction("退出程序")
        exit_act.triggered.connect(self.quit_app)

        self.tray.setContextMenu(main_menu)
        self.tray.show()

    def update_size(self):
        """刷新窗口尺寸"""
        w, h = self.size_list[self.cur_size_idx]
        self.label.setFixedSize(w, h)
        self.resize(w, h)

    def set_size(self, idx):
        """切换尺寸"""
        self.cur_size_idx = idx
        self.update_size()

    def set_speed(self, idx):
        """切换播放速度"""
        self.cur_speed_idx = idx
        speed_val = self.speed_list[self.cur_speed_idx]
        self.movie.setSpeed(speed_val)

    def quit_app(self):
        """退出程序"""
        self.tray.hide()
        self.close()
        QApplication.quit()

    # 左键拖动
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag = True
            self.drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self.drag:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        self.drag = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = GifPet()
    pet.show()
    sys.exit(app.exec())