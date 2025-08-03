import yaml
import pprint

class IaCRenderer:
    # Python 딕셔너리 형태의 청사진을 실제 YAML 파일로 변환(렌더링)합니다.
    def render(self, blueprint: dict, output_path: str):
        
        # 주어진 청사진 딕셔너리를 지정된 경로에 YAML 파일로 저장합니다.

        # :param blueprint: 최종 청사진 딕셔너리
        # :param output_path: 저장할 파일 경로 (e.g., 'deception-compose.yml')
        print(f"Rendering final blueprint to '{output_path}'...")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # yaml.dump를 사용하여 딕셔너리를 YAML 형식으로 파일에 씁니다.
                yaml.dump (
                    blueprint, 
                    f, 
                    sort_keys=False,        # 키를 알파벳순으로 정렬하지 않아 'version'이 위로 오게 함
                    indent=2,               # 가독성을 위해 들여쓰기 2칸 적용
                    allow_unicode=True      # 한글 등 유니코드 문자 허용
                )
            print(f"Successfully saved the final blueprint to '{output_path}'")
        except Exception as e:
            print(f"ERROR: Rendering YAML file: {e}")

# --- 전체 모듈을 연동하여 실행하는 최종 예시 ---
if __name__ == '__main__':
    from IaC_Parser import IaCParser
    from Policy_Engine import PolicyEngine
    from Blueprint_Generator import HoneypotBlueprintGenerator

    # 1. [IaC 파서] 실행
    parser = IaCParser()
    original_data = parser.parse('docker-compose.yml')
    if not original_data:
        exit()

    # 2. [정책 엔진] 실행
    policy_engine = PolicyEngine('policy.yml')
    transformed_data = policy_engine.apply(original_data)

    # 3. [허니팟 청사진 생성기] 실행
    blueprint_generator = HoneypotBlueprintGenerator()
    final_blueprint = blueprint_generator.generate(transformed_data)
    
    # 4. [IaC 렌더러] 실행
    renderer = IaCRenderer()
    output_filename = 'deception-compose.yml'
    renderer.render(final_blueprint, output_filename)

    print("\n======= Final Blueprint Dictionary (for verification) =======")
    pprint.pprint(final_blueprint)