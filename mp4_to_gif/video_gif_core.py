import cv2
import numpy as np
from PIL import Image


class Video2Gif:
    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise FileNotFoundError("无法打开视频文件，请检查路径！")

        # 视频基础信息
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration = self.total_frames / self.fps

        print("===== 视频基础信息 =====")
        print(f"分辨率: {self.width} x {self.height}")
        print(f"总帧数: {self.total_frames} | 帧率: {self.fps:.1f}")
        print(f"总时长: {self.duration:.2f} 秒\n")

        # 初始化默认参数
        self.start_frame = 0
        self.end_frame = self.total_frames
        self.speed = 1.0
        self.crop = (0, 0, self.width, self.height)
        self.brightness = 0
        self.contrast = 1.0
        self.saturation = 1.0
        self.resize_w = None
        self.resize_h = None
        self.frame_interval = 1
        self.watermark_text = ""
        self.wm_pos = "bottom_right"
        self.wm_color = None   # 水印颜色: None=默认白色, (B,G,R)元组
        # 新增RGB三通道参数
        self.r_gain = 1.0
        self.g_gain = 1.0
        self.b_gain = 1.0

    def set_clip_range(self, start_sec=0.0, end_sec=None):
        """设置截取片段时间"""
        self.start_frame = int(start_sec * self.fps)
        if end_sec is None or end_sec >= self.duration:
            self.end_frame = self.total_frames
        else:
            self.end_frame = int(end_sec * self.fps)
        print(f"截取片段：{start_sec}s ~ {end_sec if end_sec else self.duration:.2f}s")

    def set_speed(self, speed=1.0):
        """设置播放倍速"""
        self.speed = max(0.1, min(5.0, speed))
        print(f"播放倍速: {self.speed}x")

    def set_crop(self, x1=0, y1=0, x2=None, y2=None):
        """画面裁剪"""
        x2 = self.width if x2 is None else x2
        y2 = self.height if y2 is None else y2
        self.crop = (int(x1), int(y1), int(x2), int(y2))
        print(f"裁剪区域: {self.crop}")

    def set_color_adjust(self, brightness=0, contrast=1.0, saturation=1.0):
        """亮度、对比度、饱和度调色"""
        self.brightness = np.clip(brightness, -100, 100)
        self.contrast = np.clip(contrast, 0.0, 3.0)
        self.saturation = np.clip(saturation, 0.0, 3.0)
        print(f"调色参数: 亮度{self.brightness} | 对比度{self.contrast} | 饱和度{self.saturation}")

    # 新增RGB调色方法
    def set_rgb_adjust(self, r_gain=1.0, g_gain=1.0, b_gain=1.0):
        """RGB三通道调色"""
        self.r_gain = np.clip(r_gain, 0.0, 2.0)
        self.g_gain = np.clip(g_gain, 0.0, 2.0)
        self.b_gain = np.clip(b_gain, 0.0, 2.0)
        print(f"RGB调色: R{self.r_gain:.2f} | G{self.g_gain:.2f} | B{self.b_gain:.2f}")

    def set_resize(self, new_width=None, new_height=None):
        """画面缩放"""
        self.resize_w = new_width
        self.resize_h = new_height
        if new_width or new_height:
            print(f"目标缩放尺寸: {new_width} x {new_height}")

    def set_frame_interval(self, interval=1):
        """帧抽取间隔"""
        self.frame_interval = max(1, int(interval))
        print(f"帧抽取间隔: 每{self.frame_interval}帧取1帧")

    def set_watermark(self, text="", pos="bottom_right"):
        """设置文字水印"""
        self.watermark_text = text
        self.wm_pos = pos
        if text:
            print(f"水印文字: {text} | 位置: {pos}")

    # 新增：设置水印颜色
    def set_watermark_color(self, color=None):
        """color: None=默认白色, 或 (B,G,R) 颜色元组"""
        self.wm_color = color
        if color:
            print(f"水印颜色: {color}")

    def adjust_single_frame(self, frame):
        """单帧统一处理：裁剪 → 调色 → 缩放 → 水印 → 转RGB"""
        # 裁剪
        x1, y1, x2, y2 = self.crop
        frame = frame[y1:y2, x1:x2]

        # 亮度+对比度
        frame = cv2.convertScaleAbs(frame, alpha=self.contrast, beta=self.brightness)

        # RGB三通道调整
        b, g, r = cv2.split(frame)
        r = np.clip(r * self.r_gain, 0, 255).astype(np.uint8)
        g = np.clip(g * self.g_gain, 0, 255).astype(np.uint8)
        b = np.clip(b * self.b_gain, 0, 255).astype(np.uint8)
        frame = cv2.merge((b, g, r))

        # 饱和度
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[..., 1] *= self.saturation
        hsv[..., 1] = np.clip(hsv[..., 1], 0, 255)
        frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # 等比例缩放
        h, w = frame.shape[:2]
        if self.resize_w or self.resize_h:
            if not self.resize_w:
                self.resize_w = int(w * self.resize_h / h)
            if not self.resize_h:
                self.resize_h = int(h * self.resize_w / w)
            frame = cv2.resize(frame, (self.resize_w, self.resize_h), interpolation=cv2.INTER_AREA)

        # 添加水印
        if self.watermark_text:
            h, w = frame.shape[:2]
            font = cv2.FONT_HERSHEY_SIMPLEX
            thickness = 1
            (tw, th), _ = cv2.getTextSize(self.watermark_text, font, 0.6, thickness)
            if self.wm_pos == "bottom_right":
                pos = (w - tw - 10, h - 10)
            elif self.wm_pos == "bottom_left":
                pos = (10, h - 10)
            elif self.wm_pos == "top_right":
                pos = (w - tw - 10, th + 10)
            else:
                pos = (10, th + 10)
            # 颜色判断
            text_color = self.wm_color if self.wm_color is not None else (255, 255, 255)
            cv2.putText(frame, self.watermark_text, pos, font, 0.6, text_color, thickness)

        # BGR 转 RGB 给 PIL 使用
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame_rgb)

    def preview_frames(self, preview_num=5):
        """逐帧预览，用于参数微调"""
        print(f"\n===== 预览前{preview_num}帧 =====")
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)
        for i in range(preview_num):
            ret, frame = self.cap.read()
            if not ret:
                break
            img = self.adjust_single_frame(frame)
            img.show(title=f"预览帧 {i+1}")
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)

    def generate_gif(self, output_gif, loop=0):
        """生成并保存GIF"""
        frames = []
        current_frame = self.start_frame
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

        print("\n===== 正在生成GIF，请稍候 =====")
        while current_frame <= self.end_frame:
            ret, frame = self.cap.read()
            if not ret:
                break

            if (current_frame - self.start_frame) % self.frame_interval == 0:
                pil_img = self.adjust_single_frame(frame)
                frames.append(pil_img)

            current_frame += 1

        if not frames:
            raise RuntimeError("未读取到有效视频帧！")

        # 计算帧延迟
        original_delay = 1000 / self.fps
        gif_delay = int(original_delay / self.speed)

        # 保存GIF
        frames[0].save(
            output_gif,
            save_all=True,
            append_images=frames[1:],
            duration=gif_delay,
            loop=loop,
            optimize=True
        )
        print(f"✅ 生成完成！共 {len(frames)} 帧，文件：{output_gif}")
        self.cap.release()