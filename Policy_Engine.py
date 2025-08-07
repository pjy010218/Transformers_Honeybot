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

    # (내부 헬퍼 함수) 점 표기법 경로를 사용하여 딕셔너리의 값을 가져옵니다.
    def _get_value_by_path(self, data: dict, path: str):
        keys = path.split('.')
        current = data
        for key in keys:
            if key.isdigit(): # 키가 숫자면 리스트 인덱스로 처리
                key = int(key)
                if not isinstance(current, list) or key >= len(current):
                    return None
            elif not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current

    # 도커 컴포즈 데이터에 정책을 적용합니다.
    def _apply_docker_compose_rules(self, data: dict) -> dict:
        
        services = data.get('services', {})
        for service_name, service_details in services.items():
            for rule in self.rules:
                condition = rule.get('condition', {})
                action = rule.get('action', {})
                match = False

                # 도커 컴포즈 규칙 조건 매칭
                if 'image_name_contains' in condition and condition['image_name_contains'] in service_details.get('image', ''):
                    match = True
                elif 'build_context' in condition:
                    build_info = service_details.get('build', {})
                    build_context = build_info if isinstance(build_info, str) else build_info.get('context')
                    if condition['build_context'] == build_context:
                        match = True
                
                if match:
                    service_details['x-honeypot-policy'] = action
                    print(f"  - Tagged policy '{rule.get('name')}' on service '{service_name}'")
                    break
        return data

    # 쿠버네티스 리소스 리스트에 정책을 적용합니다.
    def _apply_kubernetes_rules(self, resource_list: list) -> list:
        
        for resource in resource_list:
            for rule in self.rules:
                condition = rule.get('condition', {})
                action = rule.get('action', {})
                match = False

                # 쿠버네티스 규칙 조건 매칭
                if 'kubernetes_resource' in condition:
                    k8s_cond = condition['kubernetes_resource']
                    if resource.get('kind') == k8s_cond.get('kind'):
                        value = self._get_value_by_path(resource, k8s_cond.get('path', ''))
                        
                        # Fixed part: 논리적으로 잘못된 비교 구문 수정
                        # 'value'가 존재하고, 'value_contains' 문자열을 포함하는지 확인
                        if value and k8s_cond.get('value_contains', '') in str(value):
                            match = True
                
                if match:
                    resource['x-honeypot-policy'] = action
                    # Fixed part: 'metedata' 오타 수정
                    resource_name = resource.get('metadata', {}).get('name', '[unknown]')
                    print(f"  - Tagged policy '{rule.get('name')}' on resource '{resource_name}'")
                    break
        return resource_list

    def apply(self, parsed_data) -> any:
        
        # 파싱된 데이터의 각 서비스/리소스에 어떤 정책을 적용해야 하는지 '태깅'합니다.
        # 입력 데이터의 유형(dict 또는 list)을 감지하여 적절한 규칙을 적용합니다.
        
        print("PolicyEngine: Applying policies by tagging...")
        
        # Fixed part: 입력 데이터 유형에 따라 다른 처리 로직을 호출하도록 전체 구조 변경
        tagged_data = copy.deepcopy(parsed_data)

        if isinstance(tagged_data, list):
            # 입력이 리스트이면 쿠버네티스 데이터로 간주
            return self._apply_kubernetes_rules(tagged_data)
        elif isinstance(tagged_data, dict) and 'services' in tagged_data:
            # 입력이 'services' 키를 가진 딕셔너리이면 도커 컴포즈 데이터로 간주
            return self._apply_docker_compose_rules(tagged_data)
        else:
            print("Warning: Unrecognized data structure. No policies applied.")
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