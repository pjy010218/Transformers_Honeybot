import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- 새로운 import ---
# 수동 제어 모드 전환을 위해 main.py의 함수를 직접 임포트
from main import start_interactive_control 
# 자동 재배포를 위해 DeploymentActuator 임포트
from Deployer import DeploymentActuator 

PIPELINE_SCRIPT = "main.py"
TARGET_FILE = "docker-compose.yml"
OUTPUT_FILE = "deception-compose.yml"

# 파일 변경 시 자동 재배포까지 수행하는 핸들러
class ChangeHandler(FileSystemEventHandler):
    
    def __init__(self, filename):
        self.filename_to_watch = filename
        # 액츄에이터를 미리 생성해 둠
        self.actuator = DeploymentActuator(OUTPUT_FILE)
        print(f"Watching for changes in: {self.filename_to_watch}")

    def on_modified(self, event):
        if not event.is_directory and Path(event.src_path).name == self.filename_to_watch:
            print(f"\n[CHANGE]: Change detected in '{self.filename_to_watch}'!")
            
            # 1. 설계도 재생성 (main.py --no-interactive 호출)
            print("STEP 1/3: Regenerating blueprint...")
            try:
                subprocess.run(
                    ["python", PIPELINE_SCRIPT, "--no-interactive"], 
                    check=True, text=True, encoding='utf-8'
                )
                print("[SUCCESS]: Blueprint regenerated successfully.")
            except Exception as e:
                print(f"[ERROR]: Blueprint generation failed: {e}")
                print("\nWatching for changes again...")
                return # 실패 시 재배포 중단

            # 2. 기존 환경 중지
            print("\nSTEP 2/3: Shutting down the old environment...")
            self.actuator.down()

            # 3. 새로운 환경 시작
            print("\nSTEP 3/3: Deploying the new environment...")
            self.actuator.up(build=True)
            
            print("\nAuto re-deployment finished successfully!")
            print(f"\nWatching for changes again...")

def main():
    path = "."
    event_handler = ChangeHandler(TARGET_FILE)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    
    observer.start()
    print("====== Sync Controller Started (Auto-Deploy Mode) ======")
    print(f"Watching for modifications in '{TARGET_FILE}'. Press Ctrl+C to switch to manual control.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n======= Sync Controller Stopped =======")
        print(" handing over to manual control mode. =======")
        
        # --- 컨트롤러 종료 후 수동 제어 모드 시작 ---
        start_interactive_control(OUTPUT_FILE)
    
    observer.join()
    print("\nExited manual control. Program finished.")


if __name__ == "__main__":
    main()