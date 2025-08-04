import copy
import pprint
from datetime import datetime, timezone, timedelta
from Dockerfile_Generator import DockerfileGenerator # Dockerfile 생성기 모듈을 임포트
    
# 태깅된 청사진 초안을 받아, 정책에 따라 최종 청사진을 오케스트레이션하고 생성합니다.
class HoneypotBlueprintGenerator:

    # Dockerfile 생성기 인스턴스를 내부적으로 소유합니다.
    def __init__(self):
        self.dockerfile_gen = DockerfileGenerator()

    # 태깅된 데이터에 기반하여 최종 청사진을 생성합니다.
    def generate(self, tagged_data: dict) -> dict:
    
        
        print("BlueprintGenerator: Starting final blueprint generation...")
        final_blueprint = copy.deepcopy(tagged_data)
        services = final_blueprint.get('services', {})

        # 1. 각 서비스의 정책 태그를 읽고 구체적인 변환 작업 수행
        for service_name, service_details in services.items():
            if 'x-honeypot-policy' in service_details:
                policy = service_details['x-honeypot-policy']
                policy_type = policy.get('type')
                payload = policy.get('payload', {})
                print(f"  - Processing policy '{policy_type}' for service '{service_name}'...")

                if policy_type == 'image_replace':
                    self._apply_image_replace(service_details, payload)
                elif policy_type == 'dynamic_build':
                    self._apply_dynamic_build(service_details, payload, service_name)
        
        # 2. 시스템 공통 서비스 주입 (기존 로직 재사용)
        self._inject_logging_service(final_blueprint)

        # 3. 관리용 메타데이터 주입 (기존 로직 재사용)
        self._inject_metadata(final_blueprint)
        
        print("BlueprintGenerator: Blueprint generation complete.")
        return final_blueprint

    # (내부 함수) image_replace 정책을 적용합니다.
    def _apply_image_replace(self, service: dict, payload: dict):
    
        if 'image' in payload:
            service['image'] = payload['image']
            # build 키가 있었다면 이미지 기반으로 바뀌므로 제거
            if 'build' in service:
                del service['build']
        
        if 'x-honeypot-policy' in service:
            del service['x-honeypot-policy']  # 정책 태그 제거

    # (내부 함수) dynamic_build 정책을 적용합니다.
    def _apply_dynamic_build(self, service: dict, payload: dict, service_name: str):
    
        build_info = service.get('build', {})
        context_path = build_info if isinstance(build_info, str) else build_info.get('context')

        if not context_path:
            print(f"  - ⚠️ Warning: No build context found for '{service_name}'. Skipping dynamic build.")
            return

        # Dockerfile 생성기 호출
        generated_dockerfile = self.dockerfile_gen.generate(payload, context_path)
        
        # 서비스의 build 설정을 새로 생성된 Dockerfile을 사용하도록 수정
        if generated_dockerfile:
            service['build'] = {
                'context': context_path,
                'dockerfile': generated_dockerfile.name # 파일명만 사용
            }

        if 'x-honeypot-policy' in service:
            del service['x-honeypot-policy']

    # _inject_logging_service 와 _inject_metadata 메서드는 이전과 동일하게 유지됩니다.
    def _inject_logging_service(self, blueprint: dict):

        print("  - Injecting unified logging service (fluentd) with health checks...")

        logging_service = {
            'image': 'fluent/fluentd:v1.16-1',
            'ports': ['24224:24224', '24224:24224/udp'],
            'volumes': ['./fluentd/conf:/fluentd/etc'],
            'restart': 'always',
            'healthcheck': {
                'test': [
                    "CMD-SHELL",
                    "nc -z 127.0.0.1 24224"
                ],
                'interval': '10s',
                'timeout': '5s',
                'retries': 5,
                'start_period': '10s'
            }
        }

        if 'services' not in blueprint:
            blueprint['services'] = {}
        blueprint['services']['logging'] = logging_service

        for service_name, service_details in blueprint['services'].items():
            if service_name == 'logging':
                continue
            
            service_details['logging'] = {
                'driver': 'fluentd',
                'options': {
                    'tag': f"honeypot.{service_name}"
                }
            }

            service_details['depends_on'] = {
                'logging': {
                    'condition': 'service_healthy'
                }
            }

    def _inject_metadata(self, blueprint: dict):
        print("  - Injecting metadata...")
        kst = timezone(timedelta(hours=9))
        timestamp = datetime.now(kst).isoformat()

        # Docker Compose 스펙 외의 커스텀 키는 'x-' 접두사를 사용하는 것이 관례입니다.
        blueprint['x-metadata'] = {
            'blueprint_version': '1.0',
            'generated_at': timestamp,
            'generator': 'HoneypotBlueprintGenerator'
        }

# --- 전체 파이프라인을 테스트하기 위한 실행 예시 ---
# main.py 또는 최상위 실행 스크립트로 분리하는 것을 권장합니다.
if __name__ == '__main__':
    from IaC_Parser import IaCParser
    from Policy_Engine import PolicyEngine

    # 1. [IaC 파서] 실행
    parser = IaCParser()
    original_data = parser.parse('docker-compose.yml')
    if not original_data:
        exit()

    # 2. [정책 엔진] 실행 -> 태깅된 데이터 생성
    policy_engine = PolicyEngine('policy.yml')
    tagged_data = policy_engine.apply(original_data)

    # 3. [허니팟 청사진 생성기] 실행 -> 최종 청사진 생성
    blueprint_generator = HoneypotBlueprintGenerator()
    final_blueprint = blueprint_generator.generate(tagged_data)

    # 4. 최종 결과물 확인
    print("\n======= [Final Blueprint] Generated by BlueprintGenerator ======\n")
    pprint.pprint(final_blueprint)