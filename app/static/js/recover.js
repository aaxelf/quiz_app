let resetToken = null;
let resetEmail = null;

function showSuccess(msg) {
    const div = document.getElementById('successMsg');
    div.textContent = msg;
    div.style.display = 'block';
    document.getElementById('errorMsg').style.display = 'none';
}

function showError(msg) {
    const div = document.getElementById('errorMsg');
    div.textContent = msg;
    div.style.display = 'block';
    document.getElementById('successMsg').style.display = 'none';
}

function hideMessages() {
    document.getElementById('successMsg').style.display = 'none';
    document.getElementById('errorMsg').style.display = 'none';
}

function togglePassword(inputId, button) {
    const input = document.getElementById(inputId);
    const svg = button.querySelector('svg');
    if (input.type === 'password') {
        input.type = 'text';
        svg.innerHTML = `
            <path d="M1 12C4 5 8 3 12 3s8 2 11 9" stroke="#999" stroke-width="1.5" fill="none"/>
            <path d="M23 12c-3 7-7 9-11 9s-8-2-11-9" stroke="#999" stroke-width="1.5" fill="none"/>
            <circle cx="12" cy="12" r="3" stroke="#999" stroke-width="1.5" fill="none"/>
            <line x1="3" y1="3" x2="21" y2="21" stroke="#999" stroke-width="1.5"/>
        `;
    } else {
        input.type = 'password';
        svg.innerHTML = `
            <path d="M1 12C4 5 8 3 12 3s8 2 11 9" stroke="#999" stroke-width="1.5" fill="none"/>
            <path d="M23 12c-3 7-7 9-11 9s-8-2-11-9" stroke="#999" stroke-width="1.5" fill="none"/>
            <circle cx="12" cy="12" r="3" stroke="#999" stroke-width="1.5" fill="none"/>
        `;
    }
}

async function requestReset() {
    hideMessages();
    
    const email = document.getElementById('email').value;
    
    if (!email) {
        showError('Введите email');
        return;
    }
    
    if (!email.includes('@') || !email.includes('.')) {
        showError('Введите корректный email');
        return;
    }
    
    try {
        const response = await fetch(`/auth/forgot-password?email=${encodeURIComponent(email)}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (data.reset_url) {
                const urlParams = new URLSearchParams(data.reset_url.split('?')[1]);
                resetToken = urlParams.get('token');
                resetEmail = email;
            }
            
            showSuccess('Инструкция отправлена. Введите новый пароль.');
            document.getElementById('step1').style.display = 'none';
            document.getElementById('step2').style.display = 'block';
        } else {
            showError(data.detail || 'Пользователь с таким email не найден');
        }
    } catch (err) {
        showError('Ошибка соединения с сервером');
    }
}

async function resetPassword() {
    hideMessages();
    
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (!newPassword || !confirmPassword) {
        showError('Заполните все поля пароля');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showError('Новый пароль и подтверждение не совпадают');
        return;
    }
    
    if (newPassword.length < 6) {
        showError('Пароль должен быть не менее 6 символов');
        return;
    }
    
    if (!resetToken) {
        showError('Токен не найден. Попробуйте снова.');
        console.log('resetToken is null, cannot proceed');
        return;
    }
    
    try {
        const response = await fetch(`/auth/reset-password?token=${resetToken}&new_password=${encodeURIComponent(newPassword)}`, {
            method: 'POST'
        });

        if (response.ok) {
            showSuccess('Пароль успешно изменён! Перенаправление...');
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        } else {
            const error = await response.json();
            showError(error.detail || 'Ошибка смены пароля');
        }
    } catch (err) {
        showError('Ошибка соединения');
    }
}