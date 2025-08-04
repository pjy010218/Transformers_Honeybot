import yaml
import copy
import pprint

class PolicyEngine:
    def __init__(self, policy_file_path: str):
        try:
            with open(policy_file_path, 'r', encoding='utf-8') as f:
                self.policy_data = yaml.safe_load(f)
                self.rules = self.policy_data.get('rules', [])
                print(f"PolicyEngine: Successfully loaded {len(self.rules)} rules from '{policy_file_path}'")
        except Exception as e:
            print(f"ERROR: PolicyEngine failed loading policy file: {e}")
            self.rules = []

    def apply(self, parsed_data: dict) -> dict:
        
        #파싱된 데이터의 각 서비스에 어떤 정책을 적용해야 하는지 '태깅'합니다.
        #이 메서드는 서비스 설정을 직접 변경하지 않습니다.
        
        print("PolicyEngine: Applying policies by tagging services...")
        tagged_data = copy.deepcopy(parsed_data)
        services = tagged_data.get('services', {})

        for service_name, service_details in services.items():
            for rule in self.rules:
                condition = rule.get('condition', {})
                action = rule.get('action', {})

                # 조건 매칭 로직 (이미지 기반 또는 빌드 기반)
                match = False
                if 'image_name_contains' in condition and condition['image_name_contains'] in service_details.get('image', ''):
                    match = True
                elif 'build_context' in condition:
                    build_info = service_details.get('build', {})
                    # build: ./api 와 build: {context: ./api} 형태 모두 지원
                    build_context = build_info if isinstance(build_info, str) else build_info.get('context')
                    if condition['build_context'] == build_context:
                        match = True

                # 조건이 일치하면, 'action' 전체를 태깅하고 다음 서비스로 넘어감
                if match:
                    # 'x-honeypot-policy' 키에 action 내용을 그대로 주입
                    service_details['x-honeypot-policy'] = action
                    print(f"  - Tagged policy '{rule.get('name')}' on service '{service_name}'")
                    break
        
        return tagged_data

if __name__ == '__main__':
    from IaC_Parser import IaCParser
    
    parser = IaCParser()
    original_data = parser.parse('docker-compose.yml')

    if original_data:
        policy_engine = PolicyEngine('policy.yml')
        tagged_blueprint = policy_engine.apply(original_data)

        print("\n======= [Result] Tagged Blueprint from Policy Engine =======\n")
        pprint.pprint(tagged_blueprint)