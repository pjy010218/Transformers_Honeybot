import os
import shutil # 파일/디렉토리 복사를 위해 shutil 라이브러리를 임포트
from pathlib import Path

# 정책에 따라 허니팟용 Dockerfile을 동적으로 생성합니다.
class DockerfileGenerator:

    # (내부 함수) 원본 Dockerfile에서 특정 지시어(FROM, EXPOSE 등)를 파싱합니다.
    def _get_original_info(self, original_context_path: str, instruction: str):
        try:
            original_dockerfile_path = Path(original_context_path) / 'Dockerfile'
            with open(original_dockerfile_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().upper().startswith(instruction.upper()):
                        return line.strip()
        except FileNotFoundError:
            return None
        return None

    # 주어진 정책에 따라 Dockerfile.honeypot 파일을 생성합니다.
    def generate(self, build_policy: dict, original_context_path: str, output_filename: str = "Dockerfile.honeypot"):
        
        print(f"DockerfileGenerator: Generating '{output_filename}' for context '{original_context_path}'...")
        
        # --- 1. 가짜 앱을 빌드 컨텍스트 안으로 복사 ---
        fake_app_path_str = build_policy.get('fake_app_path')
        if not fake_app_path_str:
            print("❌ DockerfileGenerator: 'fake_app_path' not defined in policy.")
            return None
            
        fake_app_source = Path(fake_app_path_str)
        # 빌드 컨텍스트 내부에 복사될 경로 (예: ./api/_honeypot_app)
        honeypot_app_in_context = Path(original_context_path) / "_honeypot_app"

        try:
            # 대상 폴더가 이미 있으면 삭제 후 다시 복사
            if honeypot_app_in_context.exists():
                shutil.rmtree(honeypot_app_in_context)
            shutil.copytree(fake_app_source, honeypot_app_in_context)
            print(f"  - Copied fake app to '{honeypot_app_in_context}'")
        except Exception as e:
            print(f"❌ DockerfileGenerator: Failed to copy fake app. Error: {e}")
            return None
        # --- 복사 로직 끝 ---

        dockerfile_lines = []
        
        # 2. 기반 이미지(FROM) 결정
        # ... (이전 코드와 동일) ...
        base_image_line = "FROM python:3.9-slim"
        if build_policy.get('use_original_base_image'):
            original_from = self._get_original_info(original_context_path, 'FROM')
            if original_from:
                base_image_line = original_from
        dockerfile_lines.append(base_image_line)

        # 3. 작업 디렉토리(WORKDIR) 설정
        dockerfile_lines.append("WORKDIR /app")

        # 4. 의존성 파일 복사 및 설치
        dependencies = build_policy.get('copy_dependencies', [])
        if dependencies:
            for dep_file in dependencies:
                dockerfile_lines.append(f"COPY {dep_file} .")
            dockerfile_lines.append("RUN pip install -r requirements.txt")

        # --- 5. 가짜 애플리케이션 복사 (단순화된 경로) ---
        dockerfile_lines.append(f"COPY {honeypot_app_in_context.name} .")
        # --- 수정 끝 ---
        
        # 6. 실행 명령어(CMD) 설정
        dockerfile_lines.append('CMD ["python", "app.py"]')

        # 7. 파일 생성
        try:
            output_path = Path(original_context_path) / output_filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(dockerfile_lines))
            print(f"[SUCCESS] DockerfileGenerator: Successfully created '{output_path}'")
            return output_path
        except Exception as e:
            print(f"[FAILED] DockerfileGenerator: Failed to create file. Error: {e}")
            return None

if __name__ == '__main__':
    # 테스트를 위한 정책 페이로드 정의 (policy.yml의 action.payload 부분)
    test_policy_payload = {
        "use_original_base_image": True,
        "fake_app_path": "./fake_apps/python-flask-generic",
        "copy_dependencies": ["requirements.txt"]
    }
    
    # 원본 서비스의 컨텍스트 경로
    test_context_path = "./api"
    
    # 생성기 인스턴스화 및 실행
    generator = DockerfileGenerator()
    generated_file_path = generator.generate(test_policy_payload, test_context_path)

    # 생성된 파일 내용 출력 확인
    if generated_file_path:
        print("\n--- Generated Dockerfile.honeypot content ---")
        with open(generated_file_path, 'r', encoding='utf-8') as f:
            print(f.read())