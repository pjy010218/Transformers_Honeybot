# generate_test_files.py
import os
import yaml

def generate_files():
    print("🧪 Generating complex test files for scalability experiment...")

    # 1. Create a complex Docker Compose file
    compose_data = {'services': {}}
    for i in range(1, 25): # 24개의 간단한 서비스 생성
        compose_data['services'][f'service-{i}'] = {
            'image': f'alpine:3.{i%10+10}' # 다양한 이미지 버전 흉내
        }

    # 1개의 빌드 가능한 서비스 추가 (총 25개)
    compose_data['services']['buildable-service'] = {
        'build': './buildable_service_context'
    }

    with open('docker-compose.complex.yml', 'w') as f:
        yaml.dump(compose_data, f, sort_keys=False)
    print("  - Created 'docker-compose.complex.yml' with 25 services.")

    # 2. Create a corresponding complex policy file
    policy_data = {'rules': []}
    for i in range(1, 10): # 9개의 image_replace 규칙 생성
        rule = {
            'name': f'Replace service-{i}',
            'condition': {'image_name_contains': f'alpine:3.{i+9}'},
            'action': {
                'type': 'image_replace',
                'payload': {'image': f'honeypot/dummy:{i}.0'}
            }
        }
        policy_data['rules'].append(rule)

    # 1개의 dynamic_build 규칙 추가 (총 10개)
    policy_data['rules'].append({
        'name': 'Dynamic build for buildable-service',
        'condition': {'build_context': './buildable_service_context'},
        'action': {
            'type': 'dynamic_build',
            'payload': {
                'use_original_base_image': True,
                'fake_app_path': './fake_apps/python-flask-generic',
                'copy_dependencies': ['requirements.txt']
            }
        }
    })

    with open('policy.complex.yml', 'w') as f:
        yaml.dump(policy_data, f, sort_keys=False)
    print("  - Created 'policy.complex.yml' with 10 rules.")

    # 3. Create dummy directory and files for the buildable service
    context_dir = 'buildable_service_context'
    os.makedirs(context_dir, exist_ok=True)
    with open(os.path.join(context_dir, 'Dockerfile'), 'w') as f:
        f.write("FROM python:3.9-slim\nWORKDIR /app\nCOPY . .\nCMD [\"echo\", \"hello\"]")
    with open(os.path.join(context_dir, 'requirements.txt'), 'w') as f:
        f.write("flask\n")
    print(f"  - Created dummy build context '{context_dir}'.")
    print("✅ Test file generation complete.")

if __name__ == '__main__':
    generate_files()