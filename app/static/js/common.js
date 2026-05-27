function getCurrentUser() {
    return {
        id: localStorage.getItem('userId'),
        role: localStorage.getItem('userRole'),
        name: localStorage.getItem('userName')
    };
}

function setCurrentUser(userId, role, name) {
    localStorage.setItem('userId', userId);
    localStorage.setItem('userRole', role);
    localStorage.setItem('userName', name);
}

function clearCurrentUser() {
    localStorage.clear();
}

function isAuthenticated() {
    return !!localStorage.getItem('userId');
}

// ========== ПРОВЕРКА АВТОРИЗАЦИИ ДЛЯ ОРГАНИЗАТОРА ==========
function checkOrganizerAuth() {
    const userId = localStorage.getItem('userId');
    const userRole = localStorage.getItem('userRole');
    
    if (!userId || userRole !== 'organizer') {
        window.location.href = '/';
        return false;
    }
    return true;
}

function checkPlayerAuth() {
    const userId = localStorage.getItem('userId');
    const userRole = localStorage.getItem('userRole');
    
    if (!userId || userRole !== 'player') {
        window.location.href = '/';
        return false;
    }
    return true;
}

function logout() {
    clearCurrentUser();
    window.location.href = '/';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}