# ========== 全局默认配置 ==========
# 视频与输出路径
VIDEO_PATH = "input.mp4"
OUTPUT_GIF = "output.gif"
# 1. 片段截取 开始/结束 秒数
START_TIME = 1.0
END_TIME = 8.0
# 2. 播放倍速 0.1 ~ 5.0
PLAY_SPEED = 1.2
# 3. 画面裁剪 (x1, y1, x2, y2) 不裁剪填 0,0,None,None
CROP_X1, CROP_Y1 = 0, 0
CROP_X2, CROP_Y2 = None, None
# 4. 调色：亮度(-100~100) 对比度(0~3) 饱和度(0~3)
BRIGHTNESS = 10
CONTRAST = 1.1
SATURATION = 1.2
# 5. 画面缩放 (None 为不缩放，单值自动等比例)
SCALE_WIDTH = 480
SCALE_HEIGHT = None
# 6. 帧抽取间隔
FRAME_INTERVAL = 1
# 7. 文字水印（空字符串=不加水印）
WATERMARK_TEXT = ""
WATERMARK_POS = "bottom_right"
# 新增：水印颜色，None=使用默认白色
WATERMARK_COLOR = None
# 8. GIF循环次数 0 = 无限循环
LOOP_TIMES = 0
# 9. 预览帧数
PREVIEW_FRAME_NUM = 3
# 10. RGB三通道调色默认值 (0.0~2.0)
RGB_RED = 1.0
RGB_GREEN = 1.0
RGB_BLUE = 1.0