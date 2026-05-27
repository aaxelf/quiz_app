let isChecking = false;

function init() {
    if (!isAuthenticated()) {
        window.location.href = '/';
        return;
    }
    document.getElementById('userName').textContent = getCurrentUser().name || 'Игрок';
}

async function joinRoom() {
    if (isChecking) return;
    
    const roomCode = document.getElementById('roomCode').value.trim();
    const errorDiv = document.getElementById('errorMsg');
    
    // Очищаем предыдущее сообщение
    errorDiv.style.display = 'none';
    
    if (!roomCode) {
        errorDiv.textContent = 'Введите код комнаты';
        errorDiv.style.display = 'block';
        return;
    }
    
    if (roomCode.length !== 6 || !/^\d+$/.test(roomCode)) {
        errorDiv.textContent = 'Код должен состоять из 6 цифр';
        errorDiv.style.display = 'block';
        return;
    }
    
    errorDiv.textContent = 'Проверка комнаты...';
    errorDiv.style.display = 'block';
    isChecking = true;
    
    try {
        const response = await fetch(`/sessions/check/${roomCode}`);
        const data = await response.json();
        
        console.log('Ответ сервера:', data);
        
        console.log('Данные от сервера:', data);
        if (!data.exists) {
            errorDiv.textContent = 'Комната не найдена';
            isChecking = false;
            return;
        }
        
        if (data.is_active) {
            errorDiv.textContent = 'Игра уже началась';
            isChecking = false;
            return;
        }
        console.log('is_full:', data.is_full, 'players_count:', data.players_count);
        if (data.is_full) {
            errorDiv.textContent = 'Комната заполнена';
            isChecking = false;
            return;
        }
        
        // Всё хорошо
        localStorage.setItem('roomCode', roomCode);
        window.location.href = '/game';
        
    } catch (err) {
        console.error('Ошибка:', err);
        errorDiv.textContent = 'Ошибка соединения с сервером';
        isChecking = false;
    }
}

function goToHistory() {
    window.location.href = '/history';
}

function goToProfile() {
    window.location.href = '/profile';
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

init();