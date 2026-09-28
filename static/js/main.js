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

// DOM 로드 완료 후 실행
document.addEventListener('DOMContentLoaded', () => {
    console.log('[VIBE-FASHION] 프론트엔드 모듈이 성공적으로 로드되었습니다.');
});
