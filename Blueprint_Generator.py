import copy
import pprint
from datetime import datetime, timezone, timedelta

class HoneypotBlueprintGenerator:
    
    # 정책 엔진이 변환한 초안을 받아, 시스템 공통 서비스를 주입하고
    # 최종 배포용 청사진(Blueprint)을 생성합니다.
    
    def generate(self, transformed_data: dict) -> dict:
        
        # 변환된 데이터에 시스템 레벨의 구성을 추가합니다.
        # :param transformed_data: PolicyEngine이 반환한 딕셔너리
        # :return: 최종 구성이 완료된 청사진 딕셔너리
        
        print("Generating final blueprint...")

        # 이전과 마찬가지로 원본 수정을 방지하기 위해 깊은 복사를 사용합니다.
        final_blueprint = copy.deepcopy(transformed_data)

        # 1. 공통 로그 수집기(Fluentd) 서비스 주입
        self._inject_logging_service(final_blueprint)

        # 2. 관리용 메타데이터 주입
        self._inject_metadata(final_blueprint)

        # 3. (향후 확장) 최종 청사진 유효성 검증
        self._validate_blueprint(final_blueprint)
        
        print("[COMPLETE] Blueprint generation complete.")
        return final_blueprint

    def _inject_logging_service(self, blueprint: dict):
        # (내부 함수) 모든 서비스의 로그를 수집할 fluentd 서비스를 추가합니다.
        print("  - Injecting unified logging service (fluentd)...")
        
        # fluentd 서비스 정의
        logging_service = {
            'image': 'fluent/fluentd:v1.16-1',
            'ports': ['24224:24224', '24224:24224/udp'],
            'volumes': ['./fluentd/conf:/fluentd/etc'],
            'restart': 'always'
        }

        # 청사진의 services 섹션에 'logging' 이라는 이름으로 추가
        if 'services' not in blueprint:
            blueprint['services'] = {}
        blueprint['services']['logging'] = logging_service

        # 기존 모든 서비스들이 fluentd 로거를 사용하도록 설정 변경
        for service_name, service_details in blueprint['services'].items():
            # 스스로에게는 적용하지 않음
            if service_name == 'logging':
                continue
            
            service_details['logging'] = {
                'driver': 'fluentd',
                'options': {
                    'tag': f"honeypot.{service_name}"
                }
            }

    def _inject_metadata(self, blueprint: dict):
        # (내부 함수) 청사진에 관리용 메타데이터를 추가합니다.
        print("  - Injecting metadata...")
        kst = timezone(timedelta(hours=9))
        timestamp = datetime.now(kst).isoformat()

        # Docker Compose 스펙 외의 커스텀 키는 'x-' 접두사를 사용하는 것이 관례입니다.
        blueprint['x-metadata'] = {
            'blueprint_version': '1.0',
            'generated_at': timestamp,
            'generator': 'HoneypotBlueprintGenerator'
        }

    def _validate_blueprint(self, blueprint: dict):
        # (내부 함수) 향후 구현될 유효성 검증 로직의 위치입니다.
        # 예: 전체 서비스들의 ports를 검사하여 중복되는 포트가 있는지 확인
        print("  - Blueprint validation check (placeholder)...")
        pass


# --- 전체 모듈을 연동하여 실행하는 예시 ---
if __name__ == '__main__':
    from IaC_Parser import IaCParser
    from Policy_Engine import PolicyEngine

    # 1. [IaC 파서]가 원본 IaC를 파싱
    parser = IaCParser()
    original_data = parser.parse('docker-compose.yml')
    if not original_data:
        exit()
    
    # 2. [정책 엔진]이 파싱된 데이터에 규칙을 적용하여 초안 생성
    policy_engine = PolicyEngine('policy.yml')
    transformed_data = policy_engine.apply(original_data)

    # 3. [허니팟 청사진 생성기]가 초안을 받아 최종본 생성
    blueprint_generator = HoneypotBlueprintGenerator()
    final_blueprint = blueprint_generator.generate(transformed_data)

    # 4. 최종 결과물 확인
    print("\n======= [Final Blueprint] =======")
    pprint.pprint(final_blueprint)