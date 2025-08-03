import yaml
import pprint
import copy # 딕셔너리 원본을 보존하기 위해 deepcopy를 사용합니다

class PolicyEngine:
    # 정책 파일을 로드하고, 파싱된 IaC 데이터에 변환 규칙을 적용합니다.
    
    def __init__(self, policy_file_path: str):
        
        # 정책 엔진을 초기화하고 규칙 파일을 로드합니다.
        # :param policy_file_path: policy.yml 파일의 경로
        
        try:
            with open(policy_file_path, 'r', encoding='utf-8') as f:
                self.policy_data = yaml.safe_load(f)
                self.rules = self.policy_data.get('rules', [])
                print(f"Successfully loaded {len(self.rules)} rules from '{policy_file_path}'")
        except Exception as e:
            print(f"ERROR: Loading policy file: {e}")
            self.rules = []

    def apply(self, parsed_data: dict) -> dict:
        
        # 파싱된 데이터에 정책 규칙을 적용하여 변환된 딕셔너리를 반환합니다.
        # :param parsed_data: IaCParser가 반환한 원본 딕셔너리
        # :return: 규칙이 적용된 새로운 딕셔너리

        if not self.rules:
            print("NO RULES TO APPLY.: Returning original data.")
            return parsed_data

        # 원본 데이터를 직접 수정하지 않기 위해 깊은 복사(deep copy)를 사용합니다.
        transformed_data = copy.deepcopy(parsed_data)

        services = transformed_data.get('services', {})
        for service_name, service_details in services.items():
            # 각 서비스마다 모든 규칙을 순회하며 확인합니다.
            for rule in self.rules:
                condition = rule.get('condition', {})
                image_name_contains = condition.get('image_name_contains')

                # 이미지 이름이 정의되어 있고, 조건에 부합하는 경우
                if image_name_contains and image_name_contains in service_details.get('image', ''):
                    print(f"APPLYING RULE... '{rule.get('name')}' to service '{service_name}'...")
                    
                    # 'action'에 정의된 내용으로 기존 서비스 정의를 완전히 교체합니다.
                    transformed_data['services'][service_name] = rule.get('action', {})
                    
                    # 하나의 서비스에 하나의 규칙만 적용하고 다음 서비스로 넘어갑니다.
                    break 

        return transformed_data

# --- 이전 모듈(IaCParser)과 연동하여 실행하는 예시 ---
if __name__ == '__main__':
    # 이전 단계에서 만든 IaCParser를 가져옵니다.
    from IaC_Parser import IaCParser

    # 1. IaC 파서로 원본 docker-compose.yml을 파싱합니다.
    parser = IaCParser()
    original_parsed_data = parser.parse('docker-compose.yml')
    
    if original_parsed_data:
        # 2. 정책 엔진을 생성하고 정책 파일을 로드합니다.
        policy_engine = PolicyEngine('policy.yml')
        
        # 3. 파싱된 데이터에 정책을 적용합니다.
        transformed_data = policy_engine.apply(original_parsed_data)

        # 4. 원본과 변환된 결과를 비교하여 출력합니다.
        print("\n======= [BEFORE] Original Parsed Data =======")
        pprint.pprint(original_parsed_data)

        print("\n======= [AFTER] Transformed Data =======")
        pprint.pprint(transformed_data)