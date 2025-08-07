import yaml
import pprint
from pathlib import Path

# 지정된 디렉토리에서 쿠버네티스 YAML Manifest 파일들을 파싱하여
# Python 객체 리스트로 변환하는 클래스.
class KubernetesParser:
    
    def parse(self, directory_path: str) -> list:
        
        # 디렉토리 내의 모든 .yaml 또는 .yml 파일을 읽고 파싱하여
        # 리소스 딕셔너리의 리스트로 반환합니다.

        # :param directory_path: 쿠버네티스 Manifest 파일들이 있는 디렉토리 경로
        # :return: 파싱된 리소스들을 담은 딕셔너리의 리스트
        
        print(f"🔍 Parsing Kubernetes manifests in '{directory_path}'...")
        all_resources = []
        
        # 디렉토리 경로를 Path 객체로 변환
        try:
            path = Path(directory_path)

            # .yaml과 .yml 파일을 모두 찾음
            yaml_files = list(path.glob('*.yaml')) + list(path.glob('*.yml'))

            if not yaml_files:
                print(f"[ERROR]: No YAML files found in '{directory_path}'.")
                return []

            for file_path in yaml_files:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # '---'로 구분된 여러 문서를 모두 로드하기 위해 safe_load_all 사용
                    # filter(None, ...)는 빈 문서(예: 파일 끝의 '---')를 걸러냄
                    resources_in_file = list(filter(None, yaml.safe_load_all(f)))
                    if resources_in_file:
                        print(f"  - Successfully parsed {len(resources_in_file)} resource(s) from '{file_path.name}'")
                        all_resources.extend(resources_in_file)
            
            print(f"✅ Total {len(all_resources)} Kubernetes resources parsed.")
            return all_resources

        except FileNotFoundError:
            print(f"[ERROR]: The directory '{directory_path}' was not found.")
            return None
        except Exception as e:
            print(f"[ERROR]: An unexpected error occurred: {e}")
            return None

# --- 실행 예시 ---
if __name__ == "__main__":
    k8s_manifest_dir = 'k8s'

    parser = KubernetesParser()
    parsed_resources = parser.parse(k8s_manifest_dir)

    if parsed_resources:
        print("\n======= Parsed Kubernetes Resources =======")
        pprint.pprint(parsed_resources)

        print("\n======= Accessing Specific Data Example =======")
        # 예시: 첫 번째 리소스(Deployment)의 이미지 정보에 접근
        first_resource = parsed_resources[0]
        if first_resource.get("kind") == "Deployment":
            try:
                image = first_resource["spec"]["template"]["spec"]["containers"][0]["image"]
                print(f"Deployment's container image: {image}")
            except (KeyError, IndexError):
                print("Could not access the image path.")