# iac_parser.py
import yaml
import pprint # 딕셔너리를 예쁘게 출력하기 위해 사용

class IaCParser:
    # IaC 파일을 파싱하여 Python 객체로 변환하는 클래스.
    def parse(self, file_path: str) -> dict:

        # 지정된 경로의 YAML 파일을 읽고 파싱하여 딕셔너리로 반환합니다.

        # :param file_path: docker-compose.yml 파일의 경로
        # :return: 파싱된 데이터를 담은 딕셔너리

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # yaml.safe_load()를 사용하여 안전하게 YAML 파일을 로드합니다.
                data = yaml.safe_load(f)
                print(f"Successfully parsed: \n'{file_path}'\n")
                return data
        except FileNotFoundError:
            print(f"ERROR: The file '{file_path}' was not found.")
            return None
        except yaml.YAMLError as e:
            print(f"ERROR: Failed to parse YAML file '{file_path}'.\n{e}")
            return None

if __name__ == "__main__":

    # 1. 파싱할 파일 경로 지정
    compose_file = 'D:\Github\Transformers_Honeybot\Transformers_Honeybot\docker-compose.yml'

    # 2. 파서 객체 생성 및 파싱 실행
    parser = IaCParser()
    parsed_data = parser.parse(compose_file)

    # 3. 파싱된 결과 확인
    if parsed_data:
        print("\n--- Parsed IaC Data ---")
        pprint.pprint(parsed_data)

        print("\n--- Accessing Specific Data ---")
        # 예시: 'database' 서비스의 이미지 정보에 접근
        db_image = parsed_data.get('services', {}).get('database', {}).get('image')
        
        print(f"Database service image: {db_image}")