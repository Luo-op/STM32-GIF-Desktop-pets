import os
import subprocess

def build_exe():
    # 打包命令：单文件 + 无控制台窗口
    cmd = [
        "pyinstaller",
        "-F",
        "-w",
        "main.py"
    ]
    print("开始打包，请稍等...")
    try:
        # 执行打包
        subprocess.run(cmd, check=True)
        print("✅ 打包完成！")
        print("\n使用步骤：")
        print("1. 进入 dist 文件夹，找到 main.exe")
        print("2. 将 origin.gif 复制到 dist 文件夹内（和 exe 放一起）")
        print("3. 双击 main.exe 运行桌宠")
    except Exception as e:
        print(f"❌ 打包失败：{e}")

if __name__ == "__main__":
    build_exe()