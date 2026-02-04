from flask import Flask, send_from_directory, request, jsonify
import os
import logging
from groq import Groq, APIError, RateLimitError, APIConnectionError
from dotenv import load_dotenv
from flask_cors import CORS

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq 클라이언트를 초기화합니다.
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not found. Groq API calls will fail.")
    client = None
else:
    client = Groq(api_key=GROQ_API_KEY)

# 현재 app.py 파일이 있는 디렉토리 경로를 가져옵니다.
basedir = os.path.abspath(os.path.dirname(__file__))
# frontend 디렉토리의 절대 경로를 계산합니다.
frontend_dir = os.path.join(basedir, '..', 'frontend')

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    """메인 HTML 파일을 제공합니다."""
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    """CSS, JS, 이미지 등 정적 파일들을 제공합니다."""
    return send_from_directory(frontend_dir, filename)

@app.route('/api/convert', methods=['POST'])
def convert_message():
    """
    프론트엔드로부터 키워드와 페르소나를 받아 Groq AI를 호출하고,
    변환된 메시지를 JSON 형식으로 반환합니다.
    """
    if not client:
        logger.error("Groq API client not initialized.")
        return jsonify({"error": "서비스 설정 오류가 발생했습니다. 관리자에게 문의하세요."}), 500

    data = request.get_json()
    keywords = data.get('keywords')
    persona = data.get('persona')

    # 입력값 검증
    if not keywords:
        return jsonify({"error": "변환할 내용을 입력해주세요."}), 400
    
    if len(keywords) > 500:
        return jsonify({"error": "입력 내용은 500자를 초과할 수 없습니다."}), 400

    if not persona:
        return jsonify({"error": "대상을 선택해주세요."}), 400

    logger.info(f"Received conversion request. Persona: {persona}, Length: {len(keywords)}")

    # 페르소나별 시스템 프롬프트 정의 (개선됨: 단일 결과 및 영어 배제 강조)
    base_instruction = "당신은 한국 비즈니스 커뮤니케이션 전문가입니다. 사용자의 핵심 내용을 바탕으로 상황과 대상에 맞는 가장 적절한 '단 하나'의 비즈니스 메시지를 한국어로 작성하세요."
    output_instruction = "반드시 한국어로만 응답하세요. 영어 서술, 'Here is...', 'Or...' 등 모든 불필요한 서술과 선택지를 배제하고, 오직 변환된 단 하나의 한국어 메시지만 출력하세요."

    persona_instructions = {
        "upward": f"{base_instruction} 대상은 '직장 상사'입니다. 보고의 명확성, 격식, 신뢰성을 중시하며, 결론부터 제시하는 두괄식 하십시오체를 사용하세요. {output_instruction}",
        "lateral": f"{base_instruction} 대상은 '타팀 동료'입니다. 협업의 원활함과 요청의 명확성을 중시하며, 친절하고 상호 존중하는 해요체를 사용하세요. {output_instruction}",
        "external": f"{base_instruction} 대상은 '외부 고객'입니다. 서비스의 신뢰도와 친절함을 중시하며, 극존칭 하십시오체를 사용하세요. {output_instruction}"
    }

    # 알 수 없는 페르소나의 경우 기본값(lateral) 사용
    system_prompt = persona_instructions.get(persona, persona_instructions["lateral"])

    # 사용자 메시지 구성
    user_message = f"다음 내용을 비즈니스 말투로 변환해줘 (한국어로 한 가지만 출력):\n\n{keywords}"

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
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.3, # 다양성보다는 정확하고 일관된 결과를 위해 낮춤
            max_tokens=500,
            top_p=1,
            stop=None,
            stream=False,
        )

        converted_message = chat_completion.choices[0].message.content.strip()
        
        # 불필요한 따옴표 제거
        if converted_message.startswith('"') and converted_message.endswith('"'):
            converted_message = converted_message[1:-1]
        if converted_message.startswith("'") and converted_message.endswith("'"):
            converted_message = converted_message[1:-1]

        logger.info("Conversion successful.")
        return jsonify({"converted_message": converted_message})

    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {e}")
        return jsonify({"error": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."}), 429
    except APIConnectionError as e:
        logger.error(f"API connection error: {e}")
        return jsonify({"error": "AI 서버와 연결할 수 없습니다. 잠시 후 다시 시도해주세요."}), 503
    except APIError as e:
        logger.error(f"Groq API error: {e}")
        return jsonify({"error": "변환 중 오류가 발생했습니다. 다시 시도해주세요."}), 500
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return jsonify({"error": "알 수 없는 오류가 발생했습니다."}), 500

if __name__ == '__main__':
    # Flask 개발 서버를 포트 5000번으로 실행합니다.
    app.run(debug=True, port=5000)
