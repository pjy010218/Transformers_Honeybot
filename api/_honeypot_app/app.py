from flask import Flask, request
import logging

# 기본 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def catch_all(path):
    # 모든 요청에 대한 상세 정보 로깅
    log_message = (
        f"Request from {request.remote_addr}: "
        f"{request.method} {request.url} | "
        f"Headers: {dict(request.headers)} | "
        f"Body: {request.get_data(as_text=True)}"
    )
    logging.info(log_message)
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)