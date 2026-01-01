# -*- coding: utf-8 -*-
"""
SmartShopSaver 智能啟動腳本
自動檢查並安裝缺少的套件，然後執行主程式
"""

import subprocess
import sys
import os
from pathlib import Path

# 設定專案目錄
PROJECT_DIR = Path(__file__).parent.resolve()
os.chdir(PROJECT_DIR)
sys.path.insert(0, str(PROJECT_DIR))

print("=" * 60)
print("SmartShopSaver 智能啟動程式")
print("=" * 60)
print(f"專案目錄: {PROJECT_DIR}")

# 必要的套件列表
REQUIRED_PACKAGES = {
    'flask': 'flask',
    'linebot': 'line-bot-sdk',
    'dotenv': 'python-dotenv',
    'pymongo': 'pymongo',
    'requests': 'requests',
    'bs4': 'beautifulsoup4',
    'cloudscraper': 'cloudscraper',
    'openai': 'openai',
}

# 可選的套件（不是必須的）
OPTIONAL_PACKAGES = {
    'smolagents': 'smolagents',
    'litellm': 'litellm',
}

def check_and_install_package(import_name, install_name):
    """檢查套件是否已安裝，如果沒有則安裝"""
    try:
        __import__(import_name)
        print(f"✓ {import_name} 已安裝")
        return True
    except ImportError:
        print(f"✗ {import_name} 未安裝，正在安裝 {install_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", install_name])
            print(f"  ✓ {install_name} 安裝成功")
            return True
        except subprocess.CalledProcessError:
            print(f"  ✗ {install_name} 安裝失敗")
            return False

print("\n檢查必要套件...")
print("-" * 40)

# 檢查並安裝必要套件
all_installed = True
for import_name, install_name in REQUIRED_PACKAGES.items():
    if not check_and_install_package(import_name, install_name):
        all_installed = False

print("\n檢查可選套件...")
print("-" * 40)

# 檢查可選套件（不影響主程式執行）
for import_name, install_name in OPTIONAL_PACKAGES.items():
    check_and_install_package(import_name, install_name)

if not all_installed:
    print("\n⚠ 警告：部分必要套件安裝失敗")
    print("建議手動執行：")
    print("pip install flask line-bot-sdk python-dotenv pymongo requests beautifulsoup4 cloudscraper openai")
    input("\n按 Enter 繼續嘗試執行...")

print("\n" + "=" * 60)
print("啟動 SmartShopSaver...")
print("=" * 60)

# 執行主程式
try:
    # 方法 1：使用 subprocess 執行
    # subprocess.run([sys.executable, "app.py"], cwd=PROJECT_DIR)
    
    # 方法 2：直接執行（在同一個進程中）
    app_file = PROJECT_DIR / "app.py"
    if app_file.exists():
        print(f"\n執行 {app_file}...\n")
        with open(app_file, 'r', encoding='utf-8') as f:
            app_code = f.read()
        
        # 執行 app.py
        exec(compile(app_code, str(app_file), 'exec'), {'__name__': '__main__', '__file__': str(app_file)})
    else:
        print(f"錯誤：找不到 {app_file}")
        
except KeyboardInterrupt:
    print("\n\n程式被使用者中斷")
except Exception as e:
    print(f"\n執行錯誤: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("除錯建議：")
    print("1. 檢查 .env 檔案是否存在並設定正確")
    print("2. 確認 MongoDB 連線字串是否正確")
    print("3. 檢查 LINE Bot 的 Channel Access Token 和 Secret")
    print("=" * 60)
    
    input("\n按 Enter 結束...")
