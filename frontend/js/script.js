document.addEventListener('DOMContentLoaded', () => {
    const inputText = document.getElementById('input-text');
    const charCount = document.getElementById('char-count');
    const convertBtn = document.getElementById('convert-btn');
    const outputText = document.getElementById('output-text');
    const copyBtn = document.getElementById('copy-btn');
    const feedbackMsg = document.getElementById('feedback-message');
    const spinner = convertBtn.querySelector('.spinner');
    const btnText = convertBtn.querySelector('.btn-text');

    // 1. 글자 수 세기 기능
    inputText.addEventListener('input', () => {
        const length = inputText.value.length;
        charCount.textContent = `${length} / 500`;
        
        if (length > 500) {
            charCount.style.color = 'var(--error-color)';
        } else {
            charCount.style.color = 'var(--text-secondary)';
        }
    });

    // 2. 변환 버튼 클릭 이벤트
    convertBtn.addEventListener('click', async () => {
        const text = inputText.value.trim();
        const target = document.querySelector('input[name="target"]:checked').value;

        if (!text) {
            alert('변환할 내용을 입력해 주세요.');
            return;
        }

        // 로딩 상태 시작
        setLoading(true);

        try {
            // Sprint 2에서는 백엔드 API 연동을 위한 Fetch API 로직 구현
            const response = await fetch('/api/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    keywords: text,
                    persona: target
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || '서버 응답 오류');
            }

            const data = await response.json();
            outputText.value = data.converted_message;
            showFeedback('변환이 완료되었습니다!', 'success');

        } catch (error) {
            console.error('Error:', error);
            showFeedback(error.message || '오류가 발생했습니다. 잠시 후 다시 시도해 주세요.', 'error');
        } finally {
            // 로딩 상태 종료
            setLoading(false);
        }
    });

    // 3. 복사하기 버튼 클릭 이벤트
    copyBtn.addEventListener('click', () => {
        const text = outputText.value;
        if (!text) return;

        navigator.clipboard.writeText(text).then(() => {
            showFeedback('복사되었습니다!', 'success');
        }).catch(err => {
            console.error('Copy failed:', err);
        });
    });

    // 로딩 상태 제어 함수
    function setLoading(isLoading) {
        if (isLoading) {
            convertBtn.disabled = true;
            spinner.classList.remove('hidden');
            btnText.textContent = '변환 중...';
        } else {
            convertBtn.disabled = false;
            spinner.classList.add('hidden');
            btnText.textContent = '변환하기';
        }
    }

    // 피드백 메시지 표시 함수
    function showFeedback(message, type = 'success') {
        feedbackMsg.textContent = message;
        feedbackMsg.classList.remove('hidden', 'success', 'error');
        feedbackMsg.classList.add(type);
        
        setTimeout(() => {
            feedbackMsg.classList.add('hidden');
        }, 3000);
    }
});
