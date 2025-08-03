import subprocess
import sys

class DeploymentActuator:
    # 생성된 docker-compose 파일을 사용하여 컨테이너 환경을
    # 실행, 중지, 관리하는 액츄에이터 클래스.

    def __init__(self, compose_file_path: str):
        
        # 액츄에이터를 초기화합니다.
        # :param compose_file_path: 제어할 docker-compose.yml 파일의 경로
        
        self.compose_file_path = compose_file_path
        print(f"Deployer initialized for '{self.compose_file_path}'")

    def _run_command(self, command: list):
        # (내부 함수) subprocess를 사용하여 docker-compose 명령을 실행합니다.
        try:
            # check=True: 명령 실행 실패 시 예외 발생
            # text=True: stdout, stderr를 텍스트로 다룸
            # capture_output=True: stdout, stderr를 캡쳐함
            result = subprocess.run (
                command, 
                check=True, 
                text=True, 
                capture_output=True,
                encoding='utf-8'
            )
            print("Command successful.")
            print(result.stdout)
            return True
        except FileNotFoundError:
            print("ERROR: 'docker-compose' command not found.")
            print("Please ensure Docker and Docker Compose are installed and in your PATH.")
            return False
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Command failed with exit code {e.returncode}")
            print("--- Stderr ---")
            print(e.stderr)
            return False

    # docker-compose up 명령을 실행하여 환경을 시작합니다.
    def up(self, detach=True):
        
        print("\nStarting deception environment...")
        command = ['docker-compose', '-f', self.compose_file_path, 'up']
        if detach:
            command.append('-d') # -d: 백그라운드에서 실행
        self._run_command(command)

    # docker-compose down 명령을 실행하여 환경을 중지하고 리소스를 제거합니다.
    def down(self):

        print("\nStopping deception environment...")
        command = ['docker-compose', '-f', self.compose_file_path, 'down']
        self._run_command(command)

    # docker-compose ps 명령을 실행하여 서비스 상태를 확인합니다.
    def status(self):
    
        print("\nChecking deception environment status...")
        command = ['docker-compose', '-f', self.compose_file_path, 'ps']
        self._run_command(command)


# --- 사용자가 직접 제어할 수 있는 대화형 실행 예시 ---
if __name__ == '__main__':
    # 렌더링된 최종 결과물 파일명을 지정
    final_compose_file = 'D:\Github\Transformers_Honeybot\Transformers_Honeybot\deception-compose.yml'
    
    actuator = DeploymentActuator(final_compose_file)

    while True:
        print("\n======= Deception Environment Control =======")
        action = input("Enter command (up / down / status / exit): ").strip().lower()

        if action == 'up':
            actuator.up()
        elif action == 'down':
            actuator.down()
        elif action == 'status':
            actuator.status()
        elif action == 'exit':
            print("Exiting controller.")
            break
        else:
            print(f"Unknown command: '{action}'")