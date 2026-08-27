import sys
import os
import time
import subprocess
import logging
import socket
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("runner.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

SINGLE_INSTANCE_PORT = 47829
_lock_socket = None

def ensure_single_instance():
    global _lock_socket
    try:
        _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _lock_socket.bind(('127.0.0.1', SINGLE_INSTANCE_PORT))
        _lock_socket.listen(1)
        logging.info("Single instance lock acquired successfully (port 47829).")
    except socket.error:
        logging.warning("Another instance of Bot Supervisor (run_bot.py) is already running! Exiting duplicate process.")
        sys.exit(0)

def prevent_sleep():
    """Prevents Windows system from going to sleep while bot is running"""
    try:
        import ctypes
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        logging.info("Windows Sleep Mode prevention enabled (System will remain awake).")
    except Exception as e:
        logging.warning(f"Could not set sleep prevention: {e}")

PYTHON_EXE = os.path.join(os.path.dirname(__file__), "win_venv", "Scripts", "python.exe")

if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable

BOT_SCRIPT = os.path.join(os.path.dirname(__file__), "bot.py")

def main():
    ensure_single_instance()
    prevent_sleep()
    logging.info("==========================================")
    logging.info("Starting Bot Auto-Restart Supervisor...")
    logging.info(f"Python binary: {PYTHON_EXE}")
    logging.info(f"Bot script: {BOT_SCRIPT}")
    logging.info("==========================================")
    
    restart_count = 0

    
    while True:
        try:
            start_time = time.time()
            logging.info(f"Launching bot.py (Attempt #{restart_count + 1})...")
            
            # Launch bot process
            process = subprocess.Popen([PYTHON_EXE, BOT_SCRIPT])
            process.wait()
            
            run_duration = time.time() - start_time
            exit_code = process.returncode
            
            logging.warning(f"bot.py stopped with exit code {exit_code} (Ran for {run_duration:.1f}s).")
            
            # Reset restart counter if it ran fine for over 5 minutes
            if run_duration > 300:
                restart_count = 0
            else:
                restart_count += 1
                
            logging.info("Restarting bot.py in 3 seconds...")
            time.sleep(3)
            
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt received. Stopping Bot Supervisor.")
            if 'process' in locals() and process.poll() is None:
                process.terminate()
            break
        except Exception as e:
            logging.error(f"Unexpected error in Bot Supervisor: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
