function switchTab(tab) {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(t => t.classList.remove('active'));
    if (tab === 'login') {
        tabs[0].classList.add('active');
        document.getElementById('loginForm').classList.add('active');
        document.getElementById('registerForm').classList.remove('active');
    } else {
        tabs[1].classList.add('active');
        document.getElementById('registerForm').classList.add('active');
        document.getElementById('loginForm').classList.remove('active');
    }
    hideMessages();
}

function hideMessages() {
    document.getElementById('error').style.display = 'none';
    document.getElementById('success').style.display = 'none';
}

function showError(msg) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = msg;
    errorDiv.style.display = 'block';
}

function showSuccess(msg) {
    const successDiv = document.getElementById('success');
    successDiv.textContent = msg;
    successDiv.style.display = 'block';
}

function togglePassword(inputId, button) {
    const input = document.getElementById(inputId);
    const svg = button.querySelector('svg');
    
    if (input.type === 'password') {
        input.type = 'text';
        svg.innerHTML = `
            <path d="M1 12C4 5 8 3 12 3s8 2 11 9" />
            <path d="M23 12c-3 7-7 9-11 9s-8-2-11-9" />
            <circle cx="12" cy="12" r="3" />
            <line x1="3" y1="3" x2="21" y2="21" />
        `;
    } else {
        input.type = 'password';
        svg.innerHTML = `
            <path d="M1 12C4 5 8 3 12 3s8 2 11 9" />
            <path d="M23 12c-3 7-7 9-11 9s-8-2-11-9" />
            <circle cx="12" cy="12" r="3" />
        `;
    }
}

async function login(event) {
    event.preventDefault();
    hideMessages();

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem('userId', data.user_id);
            localStorage.setItem('userRole', data.role);
            localStorage.setItem('userName', data.display_name);
            
            if (data.role === 'organizer') {
                window.location.href = '/organizer';
            } else {
                window.location.href = '/lobby';
            }
        } else {
            showError(data.detail || 'Ошибка входа');
        }
    } catch (err) {
        showError('Ошибка соединения с сервером');
    }
}

async function register(event) {
    event.preventDefault();
    hideMessages();

    const name = document.getElementById('regName').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const role = document.getElementById('regRole').value;

    if (password.length < 6) {
        showError('Пароль должен быть не менее 6 символов');
        return;
    }

    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                display_name: name,
                email: email,
                password: password,
                role: role
            })
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess('Регистрация успешна! Теперь войдите в систему');
            switchTab('login');
            document.getElementById('loginEmail').value = email;
        } else {
            showError(data.detail || 'Ошибка регистрации');
        }
    } catch (err) {
        showError('Ошибка соединения с сервером');
    }
}