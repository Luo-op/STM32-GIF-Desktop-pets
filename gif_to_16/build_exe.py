import os
import shutil
import subprocess
import sys


def get_venv_site_packages():
    """自动识别虚拟环境/全局环境的 site-packages 路径"""
    # 优先取当前Python解释器路径
    python_exe = sys.executable
    python_dir = os.path.dirname(python_exe)

    # Windows 虚拟环境结构: venv/Scripts/python.exe
    if "Scripts" in python_dir:
        site_pkgs = os.path.join(os.path.dirname(python_dir), "Lib", "site-packages")
    else:
        # 全局Python
        import site
        site_pkgs = site.getsitepackages()[0]
    return site_pkgs


def clean_old_build():
    """清理旧打包缓存"""
    project_dir = os.getcwd()
    del_list = ["build", "dist", "main.spec"]
    for name in del_list:
        path = os.path.join(project_dir, name)
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
            print(f"已删除目录: {path}")
        elif os.path.isfile(path):
            os.remove(path)
            print(f"已删除文件: {path}")


def main():
    print("===== 开始自动打包 GIF转OLED工具 =====")
    # 1. 清理旧文件
    clean_old_build()

    # 2. 获取虚拟环境下的 site-packages
    site_pkgs = get_venv_site_packages()
    print(f"识别到依赖目录: {site_pkgs}")

    imageio_src = os.path.join(site_pkgs, "imageio")
    if not os.path.exists(imageio_src):
        print(f"\n❌ 错误：未找到 imageio，请在虚拟环境执行：")
        print("pip install imageio")
        input("\n按回车退出...")
        return

    print(f"✅ imageio 路径: {imageio_src}")

    # 3. 打包命令
    cmd = [
        "pyinstaller",
        "-F",
        "-w",
        f"--add-data={imageio_src};imageio",
        "redo.py"
    ]

    print("\n开始打包，请稍候...")
    print("-" * 60)

    # 执行打包
    ret = subprocess.run(cmd, shell=True, encoding="utf-8")

    print("-" * 60)
    exe_path = os.path.join(os.getcwd(), "dist", "main.exe")
    if ret.returncode == 0 and os.path.exists(exe_path):
        print(f"✅ 打包成功！")
        print(f"EXE 文件：{exe_path}")
    else:
        print("❌ 打包失败，请检查上方日志")

    input("\n按回车键关闭窗口...")


if __name__ == "__main__":
    main()