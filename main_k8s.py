import pprint
from Kubernetes_Parser import KubernetesParser
from Policy_Engine import PolicyEngine

def main():
    print("🚀 Starting the Kubernetes Blueprint Generation pipeline...")

    k8s_manifest_dir = 'k8s'
    policy_file = 'policy_k8s.yml'

    # 1. 쿠버네티스 파서 실행
    parser = KubernetesParser()
    parsed_resources = parser.parse(k8s_manifest_dir)
    if not parsed_resources: return

    # 2. 업그레이드된 정책 엔진 실행
    policy_engine = PolicyEngine(policy_file)
    tagged_resources = policy_engine.apply(parsed_resources)

    # 3. 최종 결과물 확인
    print("\n--- [Result] Tagged Kubernetes Resources from Policy Engine ---")
    pprint.pprint(tagged_resources)

if __name__ == '__main__':
    main()