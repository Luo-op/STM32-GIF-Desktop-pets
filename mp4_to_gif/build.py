import os
import shutil
import subprocess

def clean_old_files():
    """清理旧打包文件"""
    print("=== 清理旧打包缓存 ===")
    # 删除 build、dist 文件夹
    for folder in ("build", "dist"):
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"已删除文件夹: {folder}")
    # 删除 .spec 文件
    for f in os.listdir("."):
        if f.endswith(".spec"):
            os.remove(f)
            print(f"已删除文件: {f}")
    print()

def build_exe():
    """调用 PyInstaller 打包"""
    print("=== 开始打包 EXE ===")
    # 打包命令，不带图标
    cmd = [
        "pyinstaller",
        "-F",          # 打包为单个exe
        "-w",          # 隐藏控制台黑窗口
        "-n", "视频转GIF工具",  # exe名称
        "main_gui.py"  # 主程序入口
    ]

    # 如果你有 app.ico 图标，启用下面这行，注释上面cmd
    # cmd = [
    #     "pyinstaller",
    #     "-F",
    #     "-w",
    #     "--icon=app.ico",
    #     "-n", "视频转GIF工具",
    #     "main_gui.py"
    # ]

    # 执行命令
    ret = subprocess.run(cmd, shell=True)
    if ret.returncode == 0:
        print("\n✅ 打包成功！")
        print("📁 程序位置: dist/视频转GIF工具.exe")
    else:
        print("\n❌ 打包失败，请检查环境和代码！")

if __name__ == "__main__":
    clean_old_files()
    build_exe()
    input("\n按回车键退出...")