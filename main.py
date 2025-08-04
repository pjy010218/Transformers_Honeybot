import pprint
from IaC_Parser import IaCParser
from Policy_Engine import PolicyEngine
from Blueprint_Generator import HoneypotBlueprintGenerator
from IaC_Renderer import IaCRenderer
from Deployer import DeploymentActuator # 배포 액츄에이터 임포트

def main():
    
    # 자기 구성형 허니팟 기술의 전체 파이프라인을 실행하고,
    # 생성된 환경을 제어할 수 있는 컨트롤러를 시작합니다.
    
    print("Starting the Self-Configuring Honeypot pipeline...")

    # --- 입력 파일 및 출력 파일 정의 ---
    source_iac_file = 'docker-compose.yml'
    policy_file = 'policy.yml'
    output_iac_file = 'deception-compose.yml'

    # 1. ~ 4. 설계도 생성 파이프라인 (기존과 동일)
    parser = IaCParser()
    original_data = parser.parse(source_iac_file)
    if not original_data:
        print("Pipeline stopped due to parsing error.")
        return

    policy_engine = PolicyEngine(policy_file)
    tagged_data = policy_engine.apply(original_data)

    blueprint_generator = HoneypotBlueprintGenerator()
    final_blueprint = blueprint_generator.generate(tagged_data)

    renderer = IaCRenderer()
    render_success = renderer.render(final_blueprint, output_iac_file)
    
    if not render_success:
        print("Pipeline stopped due to rendering error.")
        return

    print("\nBlueprint generation pipeline finished successfully!")
    print(f"Final configuration file saved as '{output_iac_file}'")
    
    # --- 5. 배포 액츄에이터 연동 및 대화형 제어 시작 ---
    actuator = DeploymentActuator(output_iac_file)

    while True:
        print("\n======= Deception Environment Control =======")
        action = input("Enter command (up / down / status / exit): ").strip().lower()

        if action == 'up':
            # --build 플래그를 추가하여 dynamic_build 이미지를 빌드하도록 보장
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
    main()