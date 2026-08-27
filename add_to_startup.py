import os
import sys

def add_to_windows_startup():
    try:
        appdata = os.getenv('APPDATA')
        startup_dir = os.path.join(appdata, 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        vbs_path = os.path.join(os.path.dirname(__file__), 'start_bot_background.vbs')
        shortcut_path = os.path.join(startup_dir, 'TelegramChecklistBot.vbs')
        
        # Copy or create runner script in Startup folder
        with open(vbs_path, 'r', encoding='utf-8') as src:
            content = src.read()
            
        bot_dir = os.path.dirname(__file__)
        # Adjusted VBScript for startup execution with absolute paths
        startup_vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{bot_dir}"
WshShell.Run "{bot_dir}\\win_venv\\Scripts\\python.exe run_bot.py", 0, False
'''
        with open(shortcut_path, 'w', encoding='utf-8') as dst:
            dst.write(startup_vbs_content)
            
        print(f"Successfully added bot to Windows Startup: {shortcut_path}")
    except Exception as e:
        print(f"Failed to add to Windows Startup: {e}")

if __name__ == "__main__":
    add_to_windows_startup()
