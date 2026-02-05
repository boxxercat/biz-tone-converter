document.addEventListener('DOMContentLoaded', () => {
    const inputText = document.getElementById('input-text');
    const charCount = document.getElementById('char-count');
    const convertBtn = document.getElementById('convert-btn');
    const outputText = document.getElementById('output-text');
    const copyBtn = document.getElementById('copy-btn');
    const toastContainer = document.getElementById('toast-container');
    const spinner = convertBtn.querySelector('.spinner');
    const btnText = convertBtn.querySelector('.btn-text');

    // 1. 글자 수 세기 기능
    inputText.addEventListener('input', () => {
        const length = inputText.value.length;
        charCount.textContent = `${length} / 500`;
        
        if (length > 500) {
            charCount.classList.add('text-red-500');
            charCount.classList.remove('text-slate-400');
        } else {
            charCount.classList.remove('text-red-500');
            charCount.classList.add('text-slate-400');
        }
    });

    // 2. 변환 버튼 클릭 이벤트
    convertBtn.addEventListener('click', async () => {
        const text = inputText.value.trim();
        const targetElement = document.querySelector('input[name="target"]:checked');
        const target = targetElement ? targetElement.value : 'upward';

        if (!text) {
            showToast('변환할 내용을 입력해 주세요.', 'error');
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
            showToast('성공적으로 변환되었습니다!', 'success');

        } catch (error) {
            console.error('Error:', error);
            showToast(error.message || '오류가 발생했습니다. 잠시 후 다시 시도해 주세요.', 'error');
        } finally {
            // 로딩 상태 종료
            setLoading(false);
        }
    });

    // 3. 복사하기 버튼 클릭 이벤트
    copyBtn.addEventListener('click', () => {
        const text = outputText.value;
        if (!text) {
            showToast('복사할 내용이 없습니다.', 'error');
            return;
        }

        navigator.clipboard.writeText(text).then(() => {
            showToast('클립보드에 복사되었습니다!', 'success');
        }).catch(err => {
            console.error('Copy failed:', err);
            showToast('복사에 실패했습니다.', 'error');
        });
    });

    // 로딩 상태 제어 함수
    function setLoading(isLoading) {
        if (isLoading) {
            convertBtn.disabled = true;
            spinner.classList.remove('hidden');
            btnText.classList.add('opacity-0');
        } else {
            convertBtn.disabled = false;
            spinner.classList.add('hidden');
            btnText.classList.remove('opacity-0');
        }
    }

    // Toast 메시지 표시 함수
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        
        // Toast 스타일 설정
        const baseClasses = 'px-6 py-4 rounded-2xl shadow-xl text-white text-sm font-bold flex items-center gap-3 animate-slide-in';
        const typeClasses = type === 'success' ? 'bg-indigo-600' : 'bg-red-500';
        
        toast.className = `${baseClasses} ${typeClasses}`;
        
        // 아이콘 추가 (SVG)
        const icon = type === 'success' 
            ? '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>'
            : '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"></path></svg>';
        
        toast.innerHTML = `${icon}<span>${message}</span>`;
        
        toastContainer.appendChild(toast);

        // 3초 후 제거 (애니메이션 포함)
        setTimeout(() => {
            toast.classList.replace('animate-slide-in', 'animate-slide-out');
            toast.addEventListener('animationend', () => {
                toast.remove();
            });
        }, 3000);
    }
});