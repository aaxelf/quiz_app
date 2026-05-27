let currentUserId = null;

function init() {
    if (!isAuthenticated()) {
        window.location.href = '/';
        return;
    }
    currentUserId = getCurrentUser().id;
    document.getElementById('userName').textContent = getCurrentUser().name || 'Пользователь';

    const userRole = getCurrentUser().role;
    if (userRole === 'player') {
        document.getElementById('statsButton').style.display = 'block';
    }

    loadUserData();
}

async function loadUserData() {
    try {
        const response = await fetch(`/users/${currentUserId}`);
        if (response.ok) {
            const user = await response.json();
            document.getElementById('displayName').value = user.display_name;
            document.getElementById('email').value = user.email;
        }
    } catch (err) {
        showError('Ошибка загрузки данных');
    }
}

async function updateProfile() {
    const displayName = document.getElementById('displayName').value;
    const email = document.getElementById('email').value;

    if (!displayName || !email) {
        showError('Заполните все поля');
        return;
    }

    try {
        const response = await fetch(`/users/${currentUserId}?display_name=${encodeURIComponent(displayName)}&email=${encodeURIComponent(email)}`, {
            method: 'PUT'
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('userName', data.user.display_name);
            document.getElementById('userName').textContent = data.user.display_name;
            showSuccess('Профиль обновлён');
        } else {
            const error = await response.json();
            showError(error.detail || 'Ошибка обновления');
        }
    } catch (err) {
        showError('Ошибка соединения');
    }
}

async function changePassword() {
    const current = document.getElementById('currentPassword').value;
    const newPass = document.getElementById('newPassword').value;
    const confirm = document.getElementById('confirmPassword').value;

    if (!current || !newPass || !confirm) {
        showError('Заполните все поля пароля');
        return;
    }

    if (newPass !== confirm) {
        showError('Новый пароль и подтверждение не совпадают');
        return;
    }

    if (newPass.length < 6) {
        showError('Пароль должен быть не менее 6 символов');
        return;
    }

    try {
        const response = await fetch(`/auth/change-password?user_id=${currentUserId}&current_password=${encodeURIComponent(current)}&new_password=${encodeURIComponent(newPass)}`, {
            method: 'POST'
        });

        if (response.ok) {
            showSuccess('Пароль успешно изменён');
            document.getElementById('currentPassword').value = '';
            document.getElementById('newPassword').value = '';
            document.getElementById('confirmPassword').value = '';
        } else {
            const error = await response.json();
            showError(error.detail || 'Ошибка смены пароля');
        }
    } catch (err) {
        showError('Ошибка соединения');
    }
}

function showSuccess(msg) {
    const div = document.getElementById('successMsg');
    div.textContent = msg;
    div.style.display = 'block';
    setTimeout(() => div.style.display = 'none', 3000);
}

function showError(msg) {
    const div = document.getElementById('errorMsg');
    div.textContent = msg;
    div.style.display = 'block';
    setTimeout(() => div.style.display = 'none', 3000);
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

function goToOrganizer() {
    window.location.href = '/organizer';
}

function showLogoutConfirm() {
    document.getElementById('logoutModal').classList.add('active');
}

function closeLogoutModal() {
    document.getElementById('logoutModal').classList.remove('active');
}

function confirmLogout() {
    closeLogoutModal();
    logout();
}

function goBack() {
    const userRole = getCurrentUser().role;
    if (userRole === 'organizer') {
        window.location.href = '/organizer';
    } else {
        window.location.href = '/lobby';
    }
}

function goToHistory() {
    window.location.href = '/history';
}

init();