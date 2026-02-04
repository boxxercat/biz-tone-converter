from flask import Flask, send_from_directory, request, jsonify
import os
from groq import Groq
from dotenv import load_dotenv
from flask_cors import CORS # CORS 임포트 추가

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq 클라이언트를 초기화합니다. API 키가 없으면 오류가 발생할 수 있습니다.
if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY not found. Groq API calls will fail.")
    client = None
else:
    client = Groq(api_key=GROQ_API_KEY)

# 현재 app.py 파일이 있는 디렉토리 경로를 가져옵니다.
basedir = os.path.abspath(os.path.dirname(__file__))
# frontend 디렉토리의 절대 경로를 계산합니다.
# 'frontend' 디렉토리가 'backend' 디렉토리의 상위 디렉토리에 있다고 가정합니다.
frontend_dir = os.path.join(basedir, '..', 'frontend')

app = Flask(__name__)
CORS(app) # CORS 초기화 추가

@app.route('/')
def index():
    """메인 HTML 파일을 제공합니다."""
    # frontend 디렉토리에서 index.html 파일을 찾아 반환합니다.
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    """CSS, JS, 이미지 등 정적 파일들을 제공합니다."""
    # frontend 디렉토리 내의 파일만 제공하도록 합니다.
    # 예를 들어, 사용자가 '/backend/app.py' 와 같이 잘못된 경로를 요청하는 것을 방지합니다.
    return send_from_directory(frontend_dir, filename)

@app.route('/api/convert', methods=['POST'])
def convert_message():
    """
    프론트엔드로부터 키워드와 페르소나를 받아 Groq AI를 호출하고,
    변환된 메시지를 JSON 형식으로 반환합니다.
    """
    if not client:
        return jsonify({"error": "Groq API client not initialized. API key might be missing."}), 500

    data = request.get_json()
    keywords = data.get('keywords')
    persona = data.get('persona')

    if not keywords or not persona:
        return jsonify({"error": "Missing keywords or persona in request."}), 400

    # 페르소나별 시스템 프롬프트 정의 (한국어)
    persona_instructions = {
        "upward": "다음 핵심 메시지를 상사에게 적합한 정중하고 전문적인 비즈니스 메시지로 변환해주세요. 명확성, 간결성, 존중을 중시하며 결론부터 시작하세요.",
        "lateral": "다음 핵심 메시지를 동료에게 적합한 친절하고 협력적인 비즈니스 메시지로 변환해주세요. 명확한 요청과 협력을 강조하세요.",
        "external": "다음 핵심 메시지를 외부 고객에게 적합한 매우 정중하고 전문적인 비즈니스 메시지로 변환해주세요. 격식 있는 언어를 사용하고 서비스와 신뢰성을 강조하세요."
    }

    # 알 수 없는 페르소나의 경우 기본값(lateral) 사용
    system_prompt = persona_instructions.get(persona, persona_instructions["lateral"])

    # 사용자 메시지 구성
    user_message = f"Convert this message: '{keywords}'" # Groq 모델이 한국어 프롬프트를 이해하고 한국어로 응답할 것으로 기대합니다.

    try:
        # Groq API 호출
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct", # model명은 변경하지 말아 줘  
            #model="mixtral-8x7b-32768", # mixtral-8x7b-32768 은 오래된 model이야 
            temperature=0.7,
            max_tokens=300,
            top_p=1,
            stop=None,
            stream=False,
        )

        converted_message = chat_completion.choices[0].message.content

        return jsonify({"converted_message": converted_message})

    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return jsonify({"error": f"An error occurred while processing your request: {e}"}), 500

if __name__ == '__main__':
    # Flask 개발 서버를 포트 5000번으로 실행합니다.
    app.run(debug=True, port=5000)
