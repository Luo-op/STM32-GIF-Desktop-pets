import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import os
from video_gif_core import Video2Gif
import config

# 预设水印颜色 BGR 格式 (OpenCV 使用 BGR)
WATER_COLOR_LIST = [
    ("不设置(默认白色)", None),
    ("白色", (255, 255, 255)),
    ("黑色", (0, 0, 0)),
    ("红色", (0, 0, 255)),
    ("绿色", (0, 255, 0)),
    ("蓝色", (255, 0, 0)),
    ("黄色", (0, 255, 255)),
    ("紫色", (255, 0, 255)),
    ("青色", (255, 255, 0))
]


class Video2GifGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("视频转GIF - 开源工具 - 抖音号 yyyyyc18x - 感谢分享！感谢提供bug与意见！！！")
        self.root.geometry("1100x750")
        self.root.resizable(True, True)

        # 视频基础变量
        self.cap = None
        self.fps = 0
        self.total_frames = 0
        self.curr_frame_idx = 0
        self.start_frame = 0
        self.end_frame = 0
        self.is_playing = False
        self.play_after_id = None

        # 路径变量
        self.video_path = tk.StringVar(value=config.VIDEO_PATH)
        self.output_path = tk.StringVar(value=config.OUTPUT_GIF)

        # 裁剪变量
        self.is_crop_mode = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.rect_id = None
        self.orig_frame_h = 0
        self.orig_frame_w = 0
        self.show_canvas = None

        # 裁剪历史栈 - 撤销功能
        self.crop_history = []
        self.max_history = 20

        # 图片引用防空白
        self.canvas_img = None
        self._img_hold = None

        # RGB调色变量（从config读取默认值）
        self.r_red = tk.DoubleVar(value=config.RGB_RED)
        self.r_green = tk.DoubleVar(value=config.RGB_GREEN)
        self.r_blue = tk.DoubleVar(value=config.RGB_BLUE)

        # 水印颜色
        self.water_color_val = tk.StringVar()
        self.water_color_data = None

        self.create_widgets()
        self.bind_crop_event()

    def create_widgets(self):
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.Frame(main_pane, width=650)
        main_pane.add(left_frame, weight=3)

        self.show_canvas = tk.Canvas(left_frame, bg="#222222", relief=tk.SUNKEN)
        self.show_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        slider_frame = ttk.LabelFrame(left_frame, text="时间轴 & 截取片段（拖拽选帧）")
        slider_frame.pack(fill=tk.X, padx=5, pady=2)

        self.time_slider = ttk.Scale(
            slider_frame, from_=0, to=100, orient=tk.HORIZONTAL,
            command=self.on_slider_change
        )
        self.time_slider.pack(fill=tk.X, padx=5, pady=3)

        info_frame = ttk.Frame(slider_frame)
        info_frame.pack(fill=tk.X)
        self.lbl_curr = ttk.Label(info_frame, text="当前帧: 0 | 时间: 0.0s")
        self.lbl_start = ttk.Label(info_frame, text="起始帧: 0 | 起始时间: 0.0s")
        self.lbl_end = ttk.Label(info_frame, text="结束帧: 0 | 结束时间: 0.0s")
        self.lbl_curr.grid(row=0, column=0, padx=10)
        self.lbl_start.grid(row=0, column=1, padx=10)
        self.lbl_end.grid(row=0, column=2, padx=10)

        # 控制按钮区
        ctrl_frame = ttk.Frame(left_frame)
        ctrl_frame.pack(pady=5)
        ttk.Button(ctrl_frame, text="播放/暂停", command=self.toggle_play).grid(row=0, column=0, padx=3)
        ttk.Button(ctrl_frame, text="上一帧", command=self.prev_frame).grid(row=0, column=1, padx=3)
        ttk.Button(ctrl_frame, text="下一帧", command=self.next_frame).grid(row=0, column=2, padx=3)
        ttk.Button(ctrl_frame, text="设为起始点", command=self.set_start_point).grid(row=0, column=3, padx=3)
        ttk.Button(ctrl_frame, text="设为结束点", command=self.set_end_point).grid(row=0, column=4, padx=3)

        self.btn_crop = ttk.Button(ctrl_frame, text="鼠标框选裁剪", command=self.enter_crop_mode)
        self.btn_crop.grid(row=1, column=0, padx=3, pady=5)
        ttk.Button(ctrl_frame, text="撤销上一步裁剪", command=self.undo_crop).grid(row=1, column=1, padx=3, pady=5)
        ttk.Button(ctrl_frame, text="清空裁剪区域", command=self.clear_crop).grid(row=1, column=2, padx=3, pady=5)

        # 右侧面板
        right_frame = ttk.Frame(main_pane, width=400)
        main_pane.add(right_frame, weight=2)

        # 文件设置
        file_frame = ttk.LabelFrame(right_frame, text="文件设置")
        file_frame.pack(fill=tk.X, padx=5, pady=3)
        ttk.Label(file_frame, text="视频:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.video_path, width=28).grid(row=0, column=1)
        ttk.Button(file_frame, text="选择", command=self.select_video).grid(row=0, column=2)

        ttk.Label(file_frame, text="输出GIF:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.output_path, width=28).grid(row=1, column=1)
        ttk.Button(file_frame, text="保存", command=self.select_output).grid(row=1, column=2)

        # 倍速&帧间隔
        speed_frame = ttk.LabelFrame(right_frame, text="倍速 & 帧间隔")
        speed_frame.pack(fill=tk.X, padx=5, pady=3)
        ttk.Label(speed_frame, text="播放倍速:").grid(row=0, column=0)
        self.ent_speed = ttk.Entry(speed_frame, width=8)
        self.ent_speed.insert(0, config.PLAY_SPEED)
        self.ent_speed.grid(row=0, column=1)
        ttk.Label(speed_frame, text="帧间隔:").grid(row=0, column=2)
        self.ent_interval = ttk.Entry(speed_frame, width=6)
        self.ent_interval.insert(0, config.FRAME_INTERVAL)
        self.ent_interval.grid(row=0, column=3)

        # 裁剪坐标
        crop_frame = ttk.LabelFrame(right_frame, text="裁剪坐标(框选自动填充)")
        crop_frame.pack(fill=tk.X, padx=5, pady=3)
        ttk.Label(crop_frame, text="X1:").grid(row=0, column=0)
        self.ent_crop_x1 = ttk.Entry(crop_frame, width=6)
        self.ent_crop_x1.insert(0, config.CROP_X1)
        self.ent_crop_x1.grid(row=0, column=1)
        ttk.Label(crop_frame, text="Y1:").grid(row=0, column=2)
        self.ent_crop_y1 = ttk.Entry(crop_frame, width=6)
        self.ent_crop_y1.insert(0, config.CROP_Y1)
        self.ent_crop_y1.grid(row=0, column=3)
        ttk.Label(crop_frame, text="X2:").grid(row=0, column=4)
        self.ent_crop_x2 = ttk.Entry(crop_frame, width=6)
        self.ent_crop_x2.insert(0, config.CROP_X2 if config.CROP_X2 else "")
        self.ent_crop_x2.grid(row=0, column=5)
        ttk.Label(crop_frame, text="Y2:").grid(row=0, column=6)
        self.ent_crop_y2 = ttk.Entry(crop_frame, width=6)
        self.ent_crop_y2.insert(0, config.CROP_Y2 if config.CROP_Y2 else "")
        self.ent_crop_y2.grid(row=0, column=7)

        # 缩放尺寸
        scale_frame = ttk.LabelFrame(right_frame, text="尺寸缩放 (宽/高)")
        scale_frame.pack(fill=tk.X, padx=5, pady=3)
        ttk.Label(scale_frame, text="宽:").grid(row=0, column=0)
        self.ent_scale_w = ttk.Entry(scale_frame, width=8)
        self.ent_scale_w.insert(0, config.SCALE_WIDTH)
        self.ent_scale_w.grid(row=0, column=1)
        ttk.Label(scale_frame, text="高:").grid(row=0, column=2)
        self.ent_scale_h = ttk.Entry(scale_frame, width=8)
        self.ent_scale_h.insert(0, config.SCALE_HEIGHT if config.SCALE_HEIGHT else "")
        self.ent_scale_h.grid(row=0, column=3)

        # 基础调色
        color_frame = ttk.LabelFrame(right_frame, text="基础调色")
        color_frame.pack(fill=tk.X, padx=5, pady=3)
        ttk.Label(color_frame, text="亮度:").grid(row=0, column=0)
        self.ent_bright = ttk.Entry(color_frame, width=6)
        self.ent_bright.insert(0, config.BRIGHTNESS)
        self.ent_bright.grid(row=0, column=1)
        ttk.Label(color_frame, text="对比度:").grid(row=0, column=2)
        self.ent_contrast = ttk.Entry(color_frame, width=6)
        self.ent_contrast.insert(0, config.CONTRAST)
        self.ent_contrast.grid(row=0, column=3)
        ttk.Label(color_frame, text="饱和度:").grid(row=1, column=0)
        self.ent_sat = ttk.Entry(color_frame, width=6)
        self.ent_sat.insert(0, config.SATURATION)
        self.ent_sat.grid(row=1, column=1)

        # RGB三通道调色
        rgb_frame = ttk.LabelFrame(right_frame, text="RGB 三通道调色")
        rgb_frame.pack(fill=tk.X, padx=5, pady=3)
        rgb_frame.columnconfigure(1, weight=1)

        ttk.Label(rgb_frame, text="红(R):").grid(row=0, column=0, sticky=tk.W)
        s_red = ttk.Scale(rgb_frame, from_=0.0, to=2.0, orient=tk.HORIZONTAL,
                          variable=self.r_red, command=lambda v: self.rgb_refresh())
        s_red.grid(row=0, column=1, sticky=tk.EW, padx=3)
        ttk.Entry(rgb_frame, width=5, textvariable=self.r_red).grid(row=0, column=2)

        ttk.Label(rgb_frame, text="绿(G):").grid(row=1, column=0, sticky=tk.W)
        s_green = ttk.Scale(rgb_frame, from_=0.0, to=2.0, orient=tk.HORIZONTAL,
                            variable=self.r_green, command=lambda v: self.rgb_refresh())
        s_green.grid(row=1, column=1, sticky=tk.EW, padx=3)
        ttk.Entry(rgb_frame, width=5, textvariable=self.r_green).grid(row=1, column=2)

        ttk.Label(rgb_frame, text="蓝(B):").grid(row=2, column=0, sticky=tk.W)
        s_blue = ttk.Scale(rgb_frame, from_=0.0, to=2.0, orient=tk.HORIZONTAL,
                           variable=self.r_blue, command=lambda v: self.rgb_refresh())
        s_blue.grid(row=2, column=1, sticky=tk.EW, padx=3)
        ttk.Entry(rgb_frame, width=5, textvariable=self.r_blue).grid(row=2, column=2)

        # 水印&循环 【新增水印颜色下拉框】
        water_frame = ttk.LabelFrame(right_frame, text="水印 & 循环")
        water_frame.pack(fill=tk.X, padx=5, pady=3)
        # 第一行：文字、位置
        ttk.Label(water_frame, text="文字:").grid(row=0, column=0)
        self.ent_water = ttk.Entry(water_frame, width=15)
        self.ent_water.insert(0, config.WATERMARK_TEXT)
        self.ent_water.grid(row=0, column=1)
        self.cbx_water_pos = ttk.Combobox(water_frame, width=10, state="readonly")
        self.cbx_water_pos["values"] = ("top_left", "top_right", "bottom_left", "bottom_right")
        self.cbx_water_pos.set(config.WATERMARK_POS)
        self.cbx_water_pos.grid(row=0, column=2)

        # 第二行：水印颜色
        ttk.Label(water_frame, text="水印颜色:").grid(row=1, column=0)
        self.cbx_water_color = ttk.Combobox(water_frame, width=12, state="readonly", textvariable=self.water_color_val)
        color_names = [item[0] for item in WATER_COLOR_LIST]
        self.cbx_water_color["values"] = color_names
        # 默认选中第一项：不设置(白色)
        self.cbx_water_color.current(0)
        self.water_color_data = WATER_COLOR_LIST[0][1]
        self.cbx_water_color.bind("<<ComboboxSelected>>", self.on_water_color_change)
        self.cbx_water_color.grid(row=1, column=1, columnspan=2, sticky=tk.W)

        # 第三行：循环次数
        ttk.Label(water_frame, text="循环:").grid(row=2, column=0)
        self.ent_loop = ttk.Entry(water_frame, width=6)
        self.ent_loop.insert(0, config.LOOP_TIMES)
        self.ent_loop.grid(row=2, column=1)

        # 功能按钮
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="重置RGB", command=self.reset_rgb).grid(row=0, column=0, padx=3)
        ttk.Button(btn_frame, text="应用参数刷新", command=self.refresh_preview).grid(row=0, column=1, padx=3)
        ttk.Button(btn_frame, text="开始转GIF", command=self.convert_gif).grid(row=0, column=2, padx=3)

        # 日志
        log_frame = ttk.LabelFrame(right_frame, text="运行日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=3)
        self.log_text = tk.Text(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # 水印颜色下拉切换事件
    def on_water_color_change(self, event):
        idx = self.cbx_water_color.current()
        self.water_color_data = WATER_COLOR_LIST[idx][1]
        self.refresh_preview()

    # 绑定鼠标裁剪事件
    def bind_crop_event(self):
        self.show_canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.show_canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.show_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    def rgb_refresh(self):
        self.show_current_frame()

    def reset_rgb(self):
        self.r_red.set(1.0)
        self.r_green.set(1.0)
        self.r_blue.set(1.0)
        self.show_current_frame()
        self.log("RGB通道已重置为默认值")

    def log(self, msg):
        self.log_text.insert(tk.END, f"{msg}\n")
        self.log_text.see(tk.END)
        self.root.update()

    # 裁剪历史、撤销、清空
    def save_crop_history(self):
        try:
            x1 = self.ent_crop_x1.get().strip()
            y1 = self.ent_crop_y1.get().strip()
            x2 = self.ent_crop_x2.get().strip()
            y2 = self.ent_crop_y2.get().strip()
            self.crop_history.append((x1, y1, x2, y2))
            if len(self.crop_history) > self.max_history:
                self.crop_history.pop(0)
        except:
            pass

    def undo_crop(self):
        if not self.crop_history:
            self.log("暂无可撤销的裁剪记录")
            return
        last = self.crop_history.pop()
        x1, y1, x2, y2 = last
        self.ent_crop_x1.delete(0, tk.END)
        self.ent_crop_x1.insert(0, x1)
        self.ent_crop_y1.delete(0, tk.END)
        self.ent_crop_y1.insert(0, y1)
        self.ent_crop_x2.delete(0, tk.END)
        self.ent_crop_x2.insert(0, x2)
        self.ent_crop_y2.delete(0, tk.END)
        self.ent_crop_y2.insert(0, y2)
        self.log("已撤销上一步裁剪操作")
        self.refresh_preview()

    def clear_crop(self):
        self.save_crop_history()
        self.ent_crop_x1.delete(0, tk.END)
        self.ent_crop_y1.delete(0, tk.END)
        self.ent_crop_x2.delete(0, tk.END)
        self.ent_crop_y2.delete(0, tk.END)
        self.log("已清空裁剪坐标")
        self.refresh_preview()

    # 鼠标框选裁剪
    def enter_crop_mode(self):
        if not self.cap:
            messagebox.showwarning("提示", "请先加载视频！")
            return
        self.is_crop_mode = True
        self.btn_crop.config(text="框选模式(拖动鼠标选区域)")
        self.log("已进入框选裁剪模式，在画面上按住鼠标拖拽选择区域")

    def on_mouse_down(self, event):
        if not self.is_crop_mode:
            return
        if self.rect_id:
            self.show_canvas.delete(self.rect_id)
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_mouse_move(self, event):
        if not self.is_crop_mode:
            return
        if self.rect_id:
            self.show_canvas.delete(self.rect_id)
        self.rect_id = self.show_canvas.create_rectangle(
            self.drag_start_x, self.drag_start_y,
            event.x, event.y,
            outline="#ff0000", width=2
        )

    def on_mouse_up(self, event):
        if not self.is_crop_mode:
            return
        self.is_crop_mode = False
        self.btn_crop.config(text="鼠标框选裁剪")
        self.save_crop_history()

        x1_can = min(self.drag_start_x, event.x)
        y1_can = min(self.drag_start_y, event.y)
        x2_can = max(self.drag_start_x, event.x)
        y2_can = max(self.drag_start_y, event.y)

        cvs_w = self.show_canvas.winfo_width()
        cvs_h = self.show_canvas.winfo_height()
        if self.orig_frame_w == 0 or self.orig_frame_h == 0 or cvs_w == 0 or cvs_h == 0:
            self.log("画面尺寸异常，框选失败")
            return

        scale_x = self.orig_frame_w / cvs_w
        scale_y = self.orig_frame_h / cvs_h

        x1 = int(x1_can * scale_x)
        y1 = int(y1_can * scale_y)
        x2 = int(x2_can * scale_x)
        y2 = int(y2_can * scale_y)

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(self.orig_frame_w, x2)
        y2 = min(self.orig_frame_h, y2)

        self.ent_crop_x1.delete(0, tk.END)
        self.ent_crop_x1.insert(0, x1)
        self.ent_crop_y1.delete(0, tk.END)
        self.ent_crop_y1.insert(0, y1)
        self.ent_crop_x2.delete(0, tk.END)
        self.ent_crop_x2.insert(0, x2)
        self.ent_crop_y2.delete(0, tk.END)
        self.ent_crop_y2.insert(0, y2)

        self.log(f"框选完成，自动填充坐标：X1={x1}, Y1={y1}, X2={x2}, Y2={y2}")
        if self.rect_id:
            self.show_canvas.delete(self.rect_id)
            self.rect_id = None
        self.refresh_preview()

    # 视频选择、加载
    def select_video(self):
        path = filedialog.askopenfilename(
            title="选择视频",
            filetypes=[("视频", "*.mp4 *.avi *.mov *.mkv"), ("全部", "*.*")]
        )
        if not path:
            return
        self.video_path.set(path)
        self.load_video(path)

    def select_output(self):
        path = filedialog.asksaveasfilename(
            title="保存GIF", defaultextension=".gif",
            filetypes=[("GIF", "*.gif")]
        )
        if path:
            self.output_path.set(path)

    def load_video(self, path):
        if self.cap:
            self.cap.release()
        # 修复：去掉 CAP_FFMPEG，规避 SharedMemory 报错
        self.cap = cv2.VideoCapture(path)

        if not self.cap.isOpened():
            messagebox.showerror("错误", "无法打开视频")
            self.cap = None
            return

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.curr_frame_idx = 0
        self.start_frame = 0
        self.end_frame = self.total_frames - 1

        self.time_slider.config(to=self.total_frames - 1)
        self.time_slider.set(0)
        self.update_frame_info()
        self.log(f"加载视频成功 | 总帧数:{self.total_frames} | 帧率:{self.fps:.1f}")

        self.root.update_idletasks()
        self.show_current_frame()

    def update_frame_info(self):
        curr_t = self.curr_frame_idx / self.fps if self.fps else 0
        start_t = self.start_frame / self.fps if self.fps else 0
        end_t = self.end_frame / self.fps if self.fps else 0
        self.lbl_curr.config(text=f"当前帧: {self.curr_frame_idx} | 时间: {curr_t:.2f}s")
        self.lbl_start.config(text=f"起始帧: {self.start_frame} | 起始时间: {start_t:.2f}s")
        self.lbl_end.config(text=f"结束帧: {self.end_frame} | 结束时间: {end_t:.2f}s")

    def on_slider_change(self, val):
        if not self.cap:
            return
        idx = int(float(val))
        self.curr_frame_idx = idx
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        self.show_current_frame()
        self.update_frame_info()

    def prev_frame(self):
        if not self.cap:
            return
        if self.curr_frame_idx > 0:
            self.curr_frame_idx -= 1
            self.time_slider.set(self.curr_frame_idx)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.curr_frame_idx)
            self.show_current_frame()
            self.update_frame_info()

    def next_frame(self):
        if not self.cap:
            return
        if self.curr_frame_idx < self.total_frames - 1:
            self.curr_frame_idx += 1
            self.time_slider.set(self.curr_frame_idx)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.curr_frame_idx)
            self.show_current_frame()
            self.update_frame_info()

    def set_start_point(self):
        if not self.cap:
            return
        self.start_frame = self.curr_frame_idx
        self.update_frame_info()
        self.log(f"已设置截取起始帧: {self.start_frame}")

    def set_end_point(self):
        if not self.cap:
            return
        self.end_frame = self.curr_frame_idx
        self.update_frame_info()
        self.log(f"已设置截取结束帧: {self.end_frame}")

    def toggle_play(self):
        if not self.cap:
            return
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_loop()
        else:
            if self.play_after_id:
                self.root.after_cancel(self.play_after_id)
                self.play_after_id = None

    def play_loop(self):
        if not self.is_playing or not self.cap:
            self.is_playing = False
            return

        # 修复播放逻辑：手动设置帧位置，避免read()跳帧
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.curr_frame_idx)
        ret, _ = self.cap.read()
        if not ret or self.curr_frame_idx >= self.total_frames - 1:
            self.is_playing = False
            return

        self.curr_frame_idx += 1
        self.time_slider.set(self.curr_frame_idx)
        self.show_current_frame()
        self.update_frame_info()

        # 应用播放倍速
        try:
            speed = float(self.ent_speed.get())
        except:
            speed = 1.0
        delay = int(1000 / (self.fps * speed)) if self.fps > 0 else 30
        self.play_after_id = self.root.after(delay, self.play_loop)

    def get_current_processed_frame(self):
        if not self.cap:
            return None
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.curr_frame_idx)
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return None

        self.orig_frame_h, self.orig_frame_w = frame.shape[:2]

        try:
            x1 = int(self.ent_crop_x1.get()) if self.ent_crop_x1.get().strip() else 0
            y1 = int(self.ent_crop_y1.get()) if self.ent_crop_y1.get().strip() else 0
            x2 = int(self.ent_crop_x2.get()) if self.ent_crop_x2.get().strip() else None
            y2 = int(self.ent_crop_y2.get()) if self.ent_crop_y2.get().strip() else None
            w = int(self.ent_scale_w.get()) if self.ent_scale_w.get().strip() else None
            h = int(self.ent_scale_h.get()) if self.ent_scale_h.get().strip() else None
            bright = int(self.ent_bright.get()) if self.ent_bright.get().strip() else 0
            contrast = float(self.ent_contrast.get()) if self.ent_contrast.get().strip() else 1.0
            sat = float(self.ent_sat.get()) if self.ent_sat.get().strip() else 1.0
            water_txt = self.ent_water.get().strip()
            water_pos = self.cbx_water_pos.get()
            water_color = self.water_color_data
            r_gain = self.r_red.get()
            g_gain = self.r_green.get()
            b_gain = self.r_blue.get()
        except Exception as e:
            self.log(f"参数解析错误: {e}")
            return frame

        hh, ww = frame.shape[:2]
        x2 = ww if x2 is None else x2
        y2 = hh if y2 is None else y2
        frame = frame[y1:y2, x1:x2]
        if frame.size == 0:
            return None

        # 亮度、对比度
        frame = cv2.convertScaleAbs(frame, alpha=contrast, beta=bright)

        # RGB 通道调整
        b, g, r = cv2.split(frame)
        r = np.clip(r * r_gain, 0, 255).astype(np.uint8)
        g = np.clip(g * g_gain, 0, 255).astype(np.uint8)
        b = np.clip(b * b_gain, 0, 255).astype(np.uint8)
        frame = cv2.merge((b, g, r))

        # 饱和度修复
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[..., 1] *= sat
        hsv[..., 1] = np.clip(hsv[..., 1], 0, 255)
        frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # 缩放
        if w or h:
            fh, fw = frame.shape[:2]
            if not w:
                w = int(fw * h / fh)
            if not h:
                h = int(fh * w / fw)
            frame = cv2.resize(frame, (w, h), cv2.INTER_AREA)

        # 水印
        if water_txt:
            fh, fw = frame.shape[:2]
            font = cv2.FONT_HERSHEY_SIMPLEX
            (tw, th), _ = cv2.getTextSize(water_txt, font, 0.6, 1)
            if water_pos == "bottom_right":
                pos = (fw - tw - 10, fh - 10)
            elif water_pos == "bottom_left":
                pos = (10, fh - 10)
            elif water_pos == "top_right":
                pos = (fw - tw - 10, th + 10)
            else:
                pos = (10, th + 10)
            text_color = water_color if water_color is not None else (255, 255, 255)
            cv2.putText(frame, water_txt, pos, font, 0.6, text_color, 1)
        return frame

    def show_current_frame(self):
        frame = self.get_current_processed_frame()
        if frame is None:
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)

        cvs_w = self.show_canvas.winfo_width()
        cvs_h = self.show_canvas.winfo_height()
        if cvs_w < 50 or cvs_h < 50:
            cvs_w, cvs_h = 580, 450

        img.thumbnail((cvs_w - 10, cvs_h - 10), Image.Resampling.LANCZOS)
        self.canvas_img = ImageTk.PhotoImage(img)
        self._img_hold = self.canvas_img  # 防止GC回收

        self.show_canvas.delete("all")
        self.show_canvas.create_image(cvs_w // 2, cvs_h // 2, image=self.canvas_img, anchor=tk.CENTER)

    def refresh_preview(self):
        self.show_current_frame()
        self.log("参数已应用，预览已刷新")

    def get_all_params(self):
        try:
            v_path = self.video_path.get().strip()
            o_path = self.output_path.get().strip()
            if not os.path.exists(v_path):
                messagebox.showerror("错误", "视频文件不存在")
                return None

            speed = float(self.ent_speed.get()) if self.ent_speed.get().strip() else 1.0
            interval = int(self.ent_interval.get()) if self.ent_interval.get().strip() else 1
            loop = int(self.ent_loop.get()) if self.ent_loop.get().strip() else 0

            x1 = int(self.ent_crop_x1.get()) if self.ent_crop_x1.get().strip() else 0
            y1 = int(self.ent_crop_y1.get()) if self.ent_crop_y1.get().strip() else 0
            x2 = int(self.ent_crop_x2.get()) if self.ent_crop_x2.get().strip() else None
            y2 = int(self.ent_crop_y2.get()) if self.ent_crop_y2.get().strip() else None

            sw = int(self.ent_scale_w.get()) if self.ent_scale_w.get().strip() else None
            sh = int(self.ent_scale_h.get()) if self.ent_scale_h.get().strip() else None

            bright = int(self.ent_bright.get()) if self.ent_bright.get().strip() else 0
            contrast = float(self.ent_contrast.get()) if self.ent_contrast.get().strip() else 1.0
            sat = float(self.ent_sat.get()) if self.ent_sat.get().strip() else 1.0
            r_gain = self.r_red.get()
            g_gain = self.r_green.get()
            b_gain = self.r_blue.get()

            w_txt = self.ent_water.get().strip()
            w_pos = self.cbx_water_pos.get()
            w_color = self.water_color_data

            start_t = self.start_frame / self.fps if self.fps else 0
            end_t = self.end_frame / self.fps if self.fps else 0

            return {
                "v_path": v_path, "o_path": o_path,
                "s_t": start_t, "e_t": end_t,
                "speed": speed, "interval": interval,
                "crop": (x1, y1, x2, y2),
                "scale": (sw, sh),
                "color": (bright, contrast, sat),
                "rgb": (r_gain, g_gain, b_gain),
                "water": (w_txt, w_pos),
                "water_color": w_color,
                "loop": loop
            }
        except Exception as e:
            messagebox.showerror("参数错误", f"请检查输入格式（必须为数字）：{e}")
            return None

    def convert_gif(self):
        params = self.get_all_params()
        if not params:
            return
        try:
            self.log("开始生成GIF...")
            converter = Video2Gif(params["v_path"])
            converter.set_rgb_adjust(*params["rgb"])
            converter.set_clip_range(params["s_t"], params["e_t"])
            converter.set_speed(params["speed"])
            converter.set_crop(*params["crop"])
            converter.set_color_adjust(*params["color"])
            converter.set_resize(*params["scale"])
            converter.set_frame_interval(params["interval"])
            converter.set_watermark(*params["water"])
            # 传入水印颜色
            converter.set_watermark_color(params["water_color"])
            converter.generate_gif(params["o_path"], params["loop"])
            self.log("GIF生成完成！")
            messagebox.showinfo("完成", "转换成功！")
        except Exception as e:
            self.log(f"转换失败: {str(e)}")
            messagebox.showerror("异常", str(e))

    def __del__(self):
        if self.cap:
            self.cap.release()


if __name__ == "__main__":
    root = tk.Tk()
    app = Video2GifGUI(root)
    root.mainloop()