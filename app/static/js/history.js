let currentUserId = null;

function init() {
    if (!isAuthenticated()) {
        window.location.href = '/';
        return;
    }
    currentUserId = getCurrentUser().id;
    document.getElementById('userName').textContent = getCurrentUser().name || 'Игрок';
    loadHistory();
}

function loadHistory() {
    const container = document.getElementById('historyList');
    container.innerHTML = '<div class="loading">Загрузка...</div>';
    
    fetch(`/history/user/${currentUserId}`)
        .then(response => response.json())
        .then(sessions => {
            if (sessions.length === 0) {
                container.innerHTML = '<div class="empty-state">У вас пока нет пройденных квизов</div>';
                return;
            }
            
            container.innerHTML = sessions.map(session => {
                const correctCount = session.correct_count || 0;
                const totalQuestions = session.total_questions || 1;
                const percent = Math.round((correctCount / totalQuestions) * 100);
                const position = session.position || '?';
                const isWin = position === 1;
                
                return `
                    <div class="history-card" onclick="viewDetails('${session.game_session_id}')">
                        <div class="history-title">📋 ${escapeHtml(session.quiz_title)}</div>
                        <div class="history-details">
                            <span>📅 ${new Date(session.date).toLocaleDateString()}</span>
                            <span>📊 ${correctCount}/${totalQuestions} правильных (${percent}%)</span>
                            <span class="history-score">🏆 ${session.total_score} очков</span>
                            <span class="badge ${isWin ? 'badge-win' : 'badge-loss'}">#${position} место</span>
                        </div>
                    </div>
                `;
            }).join('');
        })
        .catch(err => {
            console.error('Error:', err);
            container.innerHTML = '<div class="empty-state">Ошибка загрузки истории</div>';
        });
}

function viewDetails(gameSessionId) {
    window.location.href = `/history/${gameSessionId}`;
}

function goToLobby() {
    window.location.href = '/lobby';
}

function showLogoutConfirm() {
    document.getElementById('logoutModal').classList.add('active');
}

function closeLogoutModal() {
    document.getElementById('logoutModal').classList.remove('active');
}

function goToProfile() {
    window.location.href = '/profile';
}

function confirmLogout() {
    closeLogoutModal();
    logout();
}

init();