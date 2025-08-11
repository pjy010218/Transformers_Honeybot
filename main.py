import sys # 명령줄 인자를 읽기 위해 sys 모듈을 임포트
import pprint
from IaC_Parser import IaCParser
from Policy_Engine import PolicyEngine
from Blueprint_Generator import HoneypotBlueprintGenerator
from IaC_Renderer import IaCRenderer
from Deployer import DeploymentActuator
import time

def run_pipeline_generation():
    
    # 설계도 생성 파이프라인(1~4단계)만 실행하고,
    # 생성된 파일의 경로를 반환합니다.
    start_time = time.time()
    print("Starting the Blueprint Generation pipeline...")

    source_iac_file = 'docker-compose.yml'
    policy_file = 'policy.yml'
    output_iac_file = 'deception-compose.yml'

    parser = IaCParser()
    original_data = parser.parse(source_iac_file)
    if not original_data: return None

    policy_engine = PolicyEngine(policy_file)
    tagged_data = policy_engine.apply(original_data)

    blueprint_generator = HoneypotBlueprintGenerator()
    final_blueprint = blueprint_generator.generate(tagged_data)

    renderer = IaCRenderer()
    render_success = renderer.render(final_blueprint, output_iac_file)
    
    if not render_success: return None

    end_time = time.time()
    duration = end_time - start_time
    print(f"Pipeline completed in {duration:.3f} seconds.")

    print(f"\n[SUCCESS] Blueprint generation finished successfully! File saved as '{output_iac_file}'")
    return output_iac_file

# 대화형 배포 액츄에이터를 시작합니다.
def start_interactive_control(compose_file_path):
    actuator = DeploymentActuator(compose_file_path)

    while True:
        print("\n======= Deception Environment Control =======")
        action = input("Enter command (up / down / status / exit): ").strip().lower()

        if action == 'up':
            actuator.up(build=True)
        elif action == 'down':
            actuator.down()
        elif action == 'status':
            actuator.status()
        elif action == 'exit':
            print("Exiting controller.")
            break
        else:
            print(f"Unknown command: '{action}'")

if __name__ == '__main__':

    # '--no-interactive' 인자가 있으면 파이프라인 생성만 하고 종료
    if '--no-interactive' in sys.argv:
        run_pipeline_generation()
        
    # 인자가 없으면, 파이프라인 생성 후 대화형 제어 시작
    else:
        output_file = run_pipeline_generation()
        if output_file:
            start_interactive_control(output_file)