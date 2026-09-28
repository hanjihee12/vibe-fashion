/**
 * VIBE-FASHION 프론트엔드 인터랙션 스크립트
 * 장바구니 카운트, 토스트 알림, 위시리스트 토글 기능 등을 제공합니다.
 */

// 장바구니 담긴 개수 상태
let cartItemCount = 0;

/**
 * 상품을 장바구니에 담았을 때 호출되는 함수
 * @param {string} productName - 담을 상품명
 * @param {string} productPrice - 상품 가격
 */
function addToCart(productName, productPrice) {
    cartItemCount++;
    
    // 네비게이션 바의 장바구니 숫자 뱃지 갱신
    const cartCountBadge = document.getElementById('cartCount');
    if (cartCountBadge) {
        cartCountBadge.innerText = cartItemCount;
        // 깜빡임 애니메이션 효과
        cartCountBadge.classList.add('animate__animated', 'animate__pulse');
        setTimeout(() => {
            cartCountBadge.classList.remove('animate__animated', 'animate__pulse');
        }, 500);
    }

    // 토스트 팝업 메시지 내용 변경
    const toastMessage = document.getElementById('toastMessage');
    if (toastMessage) {
        toastMessage.innerHTML = `<strong>${productName}</strong> 상품이 장바구니에 담겼습니다! (${productPrice})`;
    }

    // Bootstrap Toast 띄우기
    const toastElement = document.getElementById('cartToast');
    if (toastElement && window.bootstrap) {
        const toastInstance = bootstrap.Toast.getOrCreateInstance(toastElement, {
            delay: 3000
        });
        toastInstance.show();
    }
}

/**
 * 위시리스트(하트) 토글 함수
 * @param {HTMLElement} btn - 클릭된 버튼 엘리먼트
 */
function toggleWishlist(btn) {
    const icon = btn.querySelector('i');
    if (!icon) return;

    if (icon.classList.contains('bi-heart')) {
        icon.classList.remove('bi-heart');
        icon.classList.add('bi-heart-fill');
        btn.classList.add('btn-danger');
        btn.classList.remove('btn-light');
        icon.classList.remove('text-danger');
        icon.classList.add('text-white');
    } else {
        icon.classList.remove('bi-heart-fill');
        icon.classList.add('bi-heart');
        btn.classList.remove('btn-danger');
        btn.classList.add('btn-light');
        icon.classList.add('text-danger');
        icon.classList.remove('text-white');
    }
}

/**
 * 문의글 답변 내용 토글 함수 (비밀글인 경우 비밀번호 확인)
 * @param {HTMLElement} element - 클릭된 제목 링크
 */
function toggleInquiryDetail(element) {
    const answerDiv = element.nextElementSibling;
    if (!answerDiv) return;

    const postPassword = answerDiv.dataset.pwd;
    if (postPassword) {
        if (!answerDiv.classList.contains('d-none')) {
            answerDiv.classList.add('d-none');
            return;
        }
        const inputPw = prompt('비밀글입니다. 작성 시 등록한 비밀번호를 입력해주세요:');
        if (inputPw === null) return;
        if (inputPw !== postPassword) {
            alert('비밀번호가 일치하지 않습니다.');
            return;
        }
    }
    answerDiv.classList.toggle('d-none');
}

/**
 * 1:1 문의글 작성 제출 처리
 * @param {Event} event - form submit 이벤트
 */
function submitInquiry(event) {
    event.preventDefault();

    const category = document.getElementById('inquiryCategory').value;
    const author = document.getElementById('inquiryAuthor').value.trim();
    const password = document.getElementById('inquiryPassword') ? document.getElementById('inquiryPassword').value.trim() : '';
    const title = document.getElementById('inquiryTitle').value.trim();
    const content = document.getElementById('inquiryContent').value.trim();
    const isSecret = document.getElementById('inquirySecret').checked;

    if (!author || !title || !content) {
        alert('모든 필드를 입력해주세요.');
        return;
    }

    if (!password || password.length < 4) {
        alert('비밀번호를 4자리 이상 입력해주세요.');
        return;
    }

    // 작성자 마스킹 (예: 홍길동 -> 홍*동)
    let maskedAuthor = author;
    if (author.length === 2) {
        maskedAuthor = author[0] + '*';
    } else if (author.length >= 3) {
        maskedAuthor = author[0] + '*'.repeat(author.length - 2) + author.slice(-1);
    }

    const today = new Date().toISOString().slice(0, 10);
    const tableBody = document.getElementById('inquiryTableBody');

    if (tableBody) {
        const nextIndex = tableBody.children.length + 1;
        const newRow = document.createElement('tr');
        newRow.innerHTML = `
            <td class="text-secondary fw-semibold">${nextIndex}</td>
            <td><span class="badge bg-light text-dark border">${category}</span></td>
            <td class="text-start">
                <a href="javascript:void(0)" class="text-decoration-none text-dark fw-semibold" onclick="toggleInquiryDetail(this)">
                    ${isSecret ? '<i class="bi bi-lock-fill text-muted me-1"></i>' : ''} ${title}
                </a>
                <div class="inquiry-answer text-muted small mt-2 p-3 bg-light rounded d-none" ${isSecret ? `data-pwd="${password}"` : ''}>
                    <p class="mb-1 text-dark"><strong>[문의내용]</strong> ${content}</p>
                    <i class="bi bi-clock-history me-1 text-warning"></i><em>담당자가 내용을 확인 중입니다. 곧 답변이 등록됩니다.</em>
                </div>
            </td>
            <td class="text-secondary">${maskedAuthor}</td>
            <td class="text-secondary small">${today}</td>
            <td><span class="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle px-2 py-1">답변대기</span></td>
        `;
        tableBody.insertBefore(newRow, tableBody.firstChild);
    }
                    <i class="bi bi-clock-history me-1 text-warning"></i><em>담당자가 내용을 확인 중입니다. 곧 답변이 등록됩니다.</em>
                </div>
            </td>
            <td class="text-secondary">${maskedAuthor}</td>
            <td class="text-secondary small">${today}</td>
            <td><span class="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle px-2 py-1">답변대기</span></td>
        `;
        tableBody.insertBefore(newRow, tableBody.firstChild);
    }

    // 모달 닫기 및 폼 리셋
    const modalElement = document.getElementById('inquiryModal');
    if (modalElement && window.bootstrap) {
        const modalInstance = bootstrap.Modal.getInstance(modalElement);
        if (modalInstance) {
            modalInstance.hide();
        }
    }
    document.getElementById('inquiryForm').reset();

    // 토스트 알림 표시
    const toastMessage = document.getElementById('toastMessage');
    if (toastMessage) {
        toastMessage.innerHTML = '<strong>문의글이 성공적으로 등록되었습니다!</strong>';
    }
    const toastElement = document.getElementById('cartToast');
    if (toastElement && window.bootstrap) {
        const toastInstance = bootstrap.Toast.getOrCreateInstance(toastElement);
        toastInstance.show();
    }
}

// DOM 로드 완료 후 실행
document.addEventListener('DOMContentLoaded', () => {
    console.log('[VIBE-FASHION] 프론트엔드 모듈이 성공적으로 로드되었습니다.');
});
