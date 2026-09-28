/**
 * VIBE-FASHION 프론트엔드 인터랙션 스크립트
 * 장바구니 상태 관리, 토스트 알림, 주문 모달 및 결제 완료 처리
 */

// 장바구니 상태 저장소 (localStorage 연동)
let cartItems = [];
try {
    const savedCart = localStorage.getItem('vibe_cart');
    if (savedCart) {
        cartItems = JSON.parse(savedCart);
    }
} catch (e) {
    cartItems = [];
}

/**
 * 가격 문자열에서 숫자 추출 (예: '19,900원' -> 19900)
 */
function parsePrice(priceStr) {
    if (typeof priceStr === 'number') return priceStr;
    const cleaned = String(priceStr).replace(/[^0-9]/g, '');
    return parseInt(cleaned, 10) || 0;
}

/**
 * 숫자를 한국 원화 포맷으로 변환 (예: 19900 -> '19,900원')
 */
function formatKRW(num) {
    return Number(num).toLocaleString('ko-KR') + '원';
}

/**
 * 장바구니 저장 및 UI 갱신
 */
function saveCart() {
    try {
        localStorage.setItem('vibe_cart', JSON.stringify(cartItems));
    } catch (e) {
        console.error(e);
    }
    updateCartUI();
}

/**
 * 네비게이션 및 장바구니 뷰 UI 업데이트
 */
function updateCartUI() {
    const totalCount = cartItems.reduce((acc, item) => acc + item.quantity, 0);
    const cartCountBadge = document.getElementById('cartCount');
    if (cartCountBadge) {
        cartCountBadge.innerText = totalCount;
        if (totalCount > 0) {
            cartCountBadge.classList.add('animate__animated', 'animate__pulse');
            setTimeout(() => {
                cartCountBadge.classList.remove('animate__animated', 'animate__pulse');
            }, 500);
        }
    }

    // 모달 내부 장바구니 목록 렌더링
    renderCartModalList();
}

/**
 * 상품을 장바구니에 담았을 때 호출되는 함수
 * @param {string} productName - 담을 상품명
 * @param {string} productPrice - 상품 가격
 * @param {string} productImg - 상품 이미지 (옵션)
 */
function addToCart(productName, productPrice, productImg = '') {
    const numericPrice = parsePrice(productPrice);
    const existingIndex = cartItems.findIndex(item => item.name === productName);

    if (existingIndex > -1) {
        cartItems[existingIndex].quantity += 1;
    } else {
        cartItems.push({
            name: productName,
            price: numericPrice,
            priceStr: typeof productPrice === 'string' ? productPrice : formatKRW(numericPrice),
            quantity: 1,
            image: productImg
        });
    }

    saveCart();

    // 토스트 팝업 메시지 내용 변경 및 표시
    const toastMessage = document.getElementById('toastMessage');
    if (toastMessage) {
        toastMessage.innerHTML = `🛒 <strong>${productName}</strong> 이(가) 장바구니에 담겼습니다! <br><span class="text-warning small">${typeof productPrice === 'string' ? productPrice : formatKRW(numericPrice)} (수량: ${cartItems.find(i=>i.name===productName).quantity}개)</span>`;
    }

    const toastElement = document.getElementById('cartToast');
    if (toastElement && window.bootstrap) {
        const toastInstance = bootstrap.Toast.getOrCreateInstance(toastElement, {
            delay: 3500
        });
        toastInstance.show();
    }
}

/**
 * 장바구니 수량 변경
 */
function changeCartQuantity(index, delta) {
    if (!cartItems[index]) return;
    cartItems[index].quantity += delta;
    if (cartItems[index].quantity <= 0) {
        cartItems.splice(index, 1);
    }
    saveCart();
}

/**
 * 장바구니 단일 항목 삭제
 */
function removeFromCart(index) {
    if (!cartItems[index]) return;
    cartItems.splice(index, 1);
    saveCart();
}

/**
 * 장바구니 모달 열기
 */
function openCartModal() {
    renderCartModalList();
    const cartModalEl = document.getElementById('cartModal');
    if (cartModalEl && window.bootstrap) {
        const modal = bootstrap.Modal.getOrCreateInstance(cartModalEl);
        modal.show();
    }
}

/**
 * 장바구니 모달 목록 렌더링
 */
function renderCartModalList() {
    const listContainer = document.getElementById('cartModalItems');
    const emptyNotice = document.getElementById('cartModalEmpty');
    const orderBtn = document.getElementById('cartModalOrderBtn');
    const subtotalEl = document.getElementById('cartModalSubtotal');
    const shippingEl = document.getElementById('cartModalShipping');
    const totalEl = document.getElementById('cartModalTotal');

    if (!listContainer) return;

    if (cartItems.length === 0) {
        listContainer.innerHTML = '';
        if (emptyNotice) emptyNotice.classList.remove('d-none');
        if (orderBtn) orderBtn.disabled = true;
        if (subtotalEl) subtotalEl.innerText = '0원';
        if (shippingEl) shippingEl.innerText = '0원';
        if (totalEl) totalEl.innerText = '0원';
        return;
    }

    if (emptyNotice) emptyNotice.classList.add('d-none');
    if (orderBtn) orderBtn.disabled = false;

    let subtotal = 0;
    listContainer.innerHTML = cartItems.map((item, idx) => {
        const itemTotal = item.price * item.quantity;
        subtotal += itemTotal;
        return `
            <div class="d-flex align-items-center justify-content-between p-3 mb-2 bg-light rounded-3 border">
                <div class="d-flex align-items-center gap-3">
                    <span class="badge bg-dark rounded-circle px-2 py-1">${idx + 1}</span>
                    <div>
                        <h6 class="fw-bold mb-1 text-dark">${item.name}</h6>
                        <span class="text-secondary small">${formatKRW(item.price)}</span>
                    </div>
                </div>
                <div class="d-flex align-items-center gap-3">
                    <div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-outline-secondary px-2" onclick="changeCartQuantity(${idx}, -1)">-</button>
                        <span class="btn btn-light disabled px-3 fw-bold text-dark">${item.quantity}</span>
                        <button type="button" class="btn btn-outline-secondary px-2" onclick="changeCartQuantity(${idx}, 1)">+</button>
                    </div>
                    <span class="fw-bold fs-6 text-dark text-end" style="min-width: 85px;">${formatKRW(itemTotal)}</span>
                    <button type="button" class="btn btn-outline-danger btn-sm rounded-circle p-1" title="삭제" onclick="removeFromCart(${idx})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');

    const shipping = subtotal >= 50000 || subtotal === 0 ? 0 : 3000;
    const finalTotal = subtotal + shipping;

    if (subtotalEl) subtotalEl.innerText = formatKRW(subtotal);
    if (shippingEl) shippingEl.innerText = shipping === 0 ? '무료 (5만원 이상)' : formatKRW(shipping);
    if (totalEl) totalEl.innerText = formatKRW(finalTotal);
}

/**
 * 장바구니에서 주문서 작성 모달로 이동
 */
function proceedToOrderModal() {
    if (cartItems.length === 0) {
        alert('장바구니가 비어 있습니다.');
        return;
    }

    // 장바구니 모달 닫기
    const cartModalEl = document.getElementById('cartModal');
    if (cartModalEl && window.bootstrap) {
        const cartModal = bootstrap.Modal.getInstance(cartModalEl);
        if (cartModal) cartModal.hide();
    }

    // 주문 요약 채우기
    let subtotal = 0;
    const orderItemsSummary = document.getElementById('orderItemsSummary');
    if (orderItemsSummary) {
        orderItemsSummary.innerHTML = cartItems.map(item => {
            const itemTotal = item.price * item.quantity;
            subtotal += itemTotal;
            return `
                <div class="d-flex justify-content-between align-items-center py-2 border-bottom small">
                    <div>
                        <strong class="text-dark">${item.name}</strong>
                        <span class="text-muted ms-1">x ${item.quantity}</span>
                    </div>
                    <span class="fw-semibold">${formatKRW(itemTotal)}</span>
                </div>
            `;
        }).join('');
    }

    const shipping = subtotal >= 50000 ? 0 : 3000;
    const totalAmount = subtotal + shipping;

    const summarySubtotal = document.getElementById('orderSummarySubtotal');
    const summaryShipping = document.getElementById('orderSummaryShipping');
    const summaryTotal = document.getElementById('orderSummaryTotal');
    if (summarySubtotal) summarySubtotal.innerText = formatKRW(subtotal);
    if (summaryShipping) summaryShipping.innerText = shipping === 0 ? '무료' : formatKRW(shipping);
    if (summaryTotal) summaryTotal.innerText = formatKRW(totalAmount);

    // 주문서 모달 열기
    const orderModalEl = document.getElementById('orderModal');
    if (orderModalEl && window.bootstrap) {
        const orderModal = bootstrap.Modal.getOrCreateInstance(orderModalEl);
        orderModal.show();
    }
}

/**
 * 주문 폼 제출 및 완료 처리
 */
function submitOrder(event) {
    event.preventDefault();

    if (cartItems.length === 0) {
        alert('주문할 상품이 없습니다.');
        return;
    }

    const buyerName = document.getElementById('orderBuyerName').value.trim();
    const buyerId = document.getElementById('orderBuyerId').value.trim();
    const buyerPhone = document.getElementById('orderBuyerPhone').value.trim();
    const buyerAddress = document.getElementById('orderBuyerAddress').value.trim();
    const refundBank = document.getElementById('orderRefundBank').value;
    const refundAccount = document.getElementById('orderRefundAccount').value.trim();
    const payMethod = document.querySelector('input[name="paymentMethod"]:checked')?.value || '무통장입금';

    let subtotal = 0;
    cartItems.forEach(i => subtotal += (i.price * i.quantity));
    const shipping = subtotal >= 50000 ? 0 : 3000;
    const finalAmount = subtotal + shipping;

    // 고유 주문번호 생성 (예: ORD20260928-1234)
    const now = new Date();
    const orderNumber = 'ORD' + now.getFullYear() +
        String(now.getMonth() + 1).padStart(2, '0') +
        String(now.getDate()).padStart(2, '0') + '-' +
        Math.floor(1000 + Math.random() * 9000);

    const orderData = {
        orderNumber: orderNumber,
        date: now.toLocaleString('ko-KR'),
        buyerName: buyerName,
        buyerId: buyerId,
        buyerPhone: buyerPhone,
        buyerAddress: buyerAddress,
        refundBank: refundBank,
        refundAccount: refundAccount,
        payMethod: payMethod,
        items: [...cartItems],
        totalAmount: finalAmount
    };

    // 주문 완료 모달에 세부 정보 바인딩
    document.getElementById('completeOrderNumber').innerText = orderData.orderNumber;
    document.getElementById('completeOrderDate').innerText = orderData.date;
    document.getElementById('completeBuyerName').innerText = orderData.buyerName;
    document.getElementById('completeBuyerId').innerText = orderData.buyerId;
    document.getElementById('completeBuyerPhone').innerText = orderData.buyerPhone;
    document.getElementById('completeBuyerAddress').innerText = orderData.buyerAddress;
    document.getElementById('completeRefundAccount').innerText = `${orderData.refundBank} ${orderData.refundAccount}`;
    document.getElementById('completePayMethod').innerText = orderData.payMethod;
    document.getElementById('completeTotalAmount').innerText = formatKRW(orderData.totalAmount);

    const completeItemsList = document.getElementById('completeItemsList');
    if (completeItemsList) {
        completeItemsList.innerHTML = orderData.items.map(item => `
            <li class="list-group-item d-flex justify-content-between align-items-center px-0">
                <span>${item.name} <span class="badge bg-secondary ms-1">${item.quantity}개</span></span>
                <span class="fw-bold">${formatKRW(item.price * item.quantity)}</span>
            </li>
        `).join('');
    }

    // 주문서 모달 닫기
    const orderModalEl = document.getElementById('orderModal');
    if (orderModalEl && window.bootstrap) {
        const orderModal = bootstrap.Modal.getInstance(orderModalEl);
        if (orderModal) orderModal.hide();
    }

    // 장바구니 비우기 및 저장
    cartItems = [];
    saveCart();

    // 폼 리셋
    document.getElementById('orderForm').reset();

    // 주문 완료 모달 표시
    const completeModalEl = document.getElementById('orderCompleteModal');
    if (completeModalEl && window.bootstrap) {
        const completeModal = bootstrap.Modal.getOrCreateInstance(completeModalEl);
        completeModal.show();
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
    updateCartUI();
});
