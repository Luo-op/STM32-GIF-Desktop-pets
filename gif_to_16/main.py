import imageio
from PIL import Image, ImageDraw
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import time

class GIF2OLEDConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF转SSD1306 OLED帧数据 - 开源工具 - 抖音号 yyyyyc18x - 感谢分享！感谢提供bug与意见！！！")
        self.root.geometry("650x520")

        # OLED 固定参数
        self.W_PX = 128
        self.H_PX = 64
        self.PAGE_NUM = 8
        self.BYTE_PER_PAGE = 128
        self.TOTAL = self.PAGE_NUM * self.BYTE_PER_PAGE

        # 默认配置
        self.default_frame_prefix = "const uint8_t frame_"
        self.default_header_text = ""
        self.save_img_default = False  # 默认不保存预览图片

        self._create_widgets()

    def _create_widgets(self):
        # 1. 文件选择区域
        frame_file = ttk.LabelFrame(self.root, text="文件选择")
        frame_file.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_file, text="GIF 文件:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_gif_path = ttk.Entry(frame_file, state="readonly")
        self.entry_gif_path.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        ttk.Button(frame_file, text="浏览", command=self._select_gif).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(frame_file, text="输出目录:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_out_dir = ttk.Entry(frame_file)
        self.entry_out_dir.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        ttk.Button(frame_file, text="选择目录", command=self._select_out_dir).grid(row=1, column=2, padx=5, pady=5)

        # 2. 功能开关区域
        frame_switch = ttk.LabelFrame(self.root, text="功能选项")
        frame_switch.pack(fill="x", padx=10, pady=5)
        self.var_save_img = tk.BooleanVar(value=self.save_img_default)
        ttk.Checkbutton(frame_switch, text="保存每帧预览图片", variable=self.var_save_img).grid(row=0, column=0, padx=5, pady=5)

        # 3. 自定义文本配置
        frame_config = ttk.LabelFrame(self.root, text="自定义文本")
        frame_config.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_config, text="帧数组前缀:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_frame_prefix = ttk.Entry(frame_config)
        self.entry_frame_prefix.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        self.entry_frame_prefix.insert(0, self.default_frame_prefix)

        ttk.Label(frame_config, text="文件头部内容:").grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        self.text_header = tk.Text(frame_config, height=3, width=55)
        self.text_header.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        self.text_header.insert("1.0", self.default_header_text)

        # 4. 日志区域
        frame_log = ttk.LabelFrame(self.root, text="转换日志")
        frame_log.pack(fill="both", padx=10, pady=5, expand=True)
        self.text_log = tk.Text(frame_log, height=12)
        scrollbar = ttk.Scrollbar(frame_log, orient="vertical", command=self.text_log.yview)
        self.text_log.configure(yscrollcommand=scrollbar.set)
        self.text_log.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y")

        # 5. 转换按钮
        ttk.Button(self.root, text="开始转换", command=self._convert).pack(pady=10)

        # 列权重适配
        for frm in [frame_file, frame_config]:
            frm.columnconfigure(1, weight=1)

    def _select_gif(self):
        path = filedialog.askopenfilename(
            title="选择 GIF 动图",
            filetypes=[("GIF 文件", "*.gif"), ("所有文件", "*.*")]
        )
        if not path:
            return
        self.entry_gif_path.config(state="normal")
        self.entry_gif_path.delete(0, tk.END)
        self.entry_gif_path.insert(0, path)
        self.entry_gif_path.config(state="readonly")

        # 自动填充输出目录为GIF所在目录
        gif_dir = os.path.dirname(path)
        self.entry_out_dir.delete(0, tk.END)
        self.entry_out_dir.insert(0, gif_dir)

    def _select_out_dir(self):
        path = filedialog.askdirectory(title="选择输出根目录")
        if path:
            self.entry_out_dir.delete(0, tk.END)
            self.entry_out_dir.insert(0, path)

    def _log(self, msg):
        self.text_log.insert(tk.END, f"{msg}\n")
        self.text_log.see(tk.END)
        self.root.update()

    def _convert(self):
        # 读取参数
        gif_path = self.entry_gif_path.get().strip()
        root_out_dir = self.entry_out_dir.get().strip()
        frame_prefix = self.entry_frame_prefix.get().strip()
        header_text = self.text_header.get("1.0", tk.END).strip()
        save_preview_img = self.var_save_img.get()

        # 基础校验
        if not gif_path or not os.path.isfile(gif_path):
            messagebox.showerror("错误", "请选择有效的 GIF 文件！")
            return
        if not root_out_dir or not os.path.isdir(root_out_dir):
            messagebox.showerror("错误", "请选择有效的输出根目录！")
            return

        # 生成独立文件夹：GIF名称_时间戳
        gif_name = os.path.splitext(os.path.basename(gif_path))[0]
        time_str = time.strftime("%Y%m%d_%H%M%S")
        work_dir = os.path.join(root_out_dir, f"{gif_name}_{time_str}")
        os.makedirs(work_dir, exist_ok=True)
        self._log(f"创建工作目录：{work_dir}")

        # 输出h文件路径
        h_file_path = os.path.join(work_dir, "oled_frames.h")

        try:
            self._log("正在读取 GIF 帧...")
            frames = imageio.mimread(gif_path)
            total_frame = len(frames)
            self._log(f"读取完成，共 {total_frame} 帧")

            with open(h_file_path, "w", encoding="utf-8") as f:
                # 写入头部文本
                if header_text:
                    f.write(header_text + "\n\n")

                for idx, np_frame in enumerate(frames, 1):
                    self._log(f"处理第 {idx}/{total_frame} 帧")

                    # 图像预处理
                    img = Image.fromarray(np_frame).convert("L")
                    img.thumbnail((80, 40))
                    w, h = img.size
                    buf = bytearray([0x00] * self.TOTAL)
                    ox = (self.W_PX - w) // 2
                    oy = (self.H_PX - h) // 2

                    # 像素转OLED数据
                    for y in range(h):
                        disp_y = oy + y
                        if disp_y >= self.H_PX:
                            continue
                        page = disp_y // 8
                        bit = disp_y % 8
                        for x in range(w):
                            disp_x = ox + x
                            if disp_x >= self.W_PX:
                                continue
                            gray = img.getpixel((x, y))
                            if gray < 170:
                                pos = page * self.BYTE_PER_PAGE + disp_x
                                buf[pos] |= (1 << bit)

                    # 生成并保存预览图（根据开关判断）
                    if save_preview_img:
                        preview = Image.new("1", (self.W_PX, self.H_PX), 0)
                        dr = ImageDraw.Draw(preview)
                        for y_pre in range(self.H_PX):
                            for x_pre in range(self.W_PX):
                                pg = y_pre // 8
                                bt = y_pre % 8
                                idx_b = pg * self.BYTE_PER_PAGE + x_pre
                                if (buf[idx_b] >> bt) & 1:
                                    dr.point((x_pre, y_pre), fill=1)
                        img_path = os.path.join(work_dir, f"frame_{idx}.bmp")
                        preview.save(img_path)
                        self._log(f"第 {idx} 帧预览图已保存")

                    # 写入C数组
                    hexarr = [f"0x{v:02X}" for v in buf]
                    lines = []
                    for i in range(0, self.TOTAL, 16):
                        lines.append(",".join(hexarr[i:i+16]))
                    content = ",\n".join(lines)
                    f.write(f"{frame_prefix}{idx}[1024] = {{\n{content}\n}};\n\n")

            self._log("=" * 30)
            self._log(f"转换全部完成！")
            self._log(f"数据文件：{h_file_path}")
            if save_preview_img:
                self._log(f"预览图片、数据文件均保存在：{work_dir}")
            else:
                self._log(f"仅生成数据文件，未保存预览图片")

            messagebox.showinfo("完成", f"转换成功！\n文件目录：{work_dir}")

        except Exception as e:
            err_msg = f"转换失败：{str(e)}"
            self._log(err_msg)
            messagebox.showerror("异常", err_msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = GIF2OLEDConverter(root)
    root.mainloop()