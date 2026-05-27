let sessionId = null;
let allQuestions = [];

function init() {
    if (!isAuthenticated()) {
        window.location.href = '/';
        return;
    }
    
    document.getElementById('userName').textContent = getCurrentUser().name || 'Игрок';
    
    const pathParts = window.location.pathname.split('/');
    sessionId = pathParts[pathParts.length - 1];
    
    loadDetails();
}

async function loadDetails() {
    const container = document.getElementById('content');
    container.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        // Получаем ответы пользователя
        const userId = getCurrentUser().id;
        const response = await fetch(`/history/user/${userId}`);
        
        if (response.ok) {
            const sessions = await response.json();
            const currentSession = sessions.find(s => s.game_session_id == sessionId);
            
            if (!currentSession) {
                container.innerHTML = '<div class="loading">Сессия не найдена</div>';
                return;
            }
            
            // Получаем детальные ответы
            const answersResponse = await fetch(`/history/session/${sessionId}/answers?user_id=${userId}`);
            
            if (answersResponse.ok) {
                const answers = await answersResponse.json();
                renderDetails(currentSession, answers);
            } else {
                renderDetails(currentSession, []);
            }
        } else {
            container.innerHTML = '<div class="loading">Ошибка загрузки</div>';
        }
    } catch (err) {
        console.error(err);
        container.innerHTML = '<div class="loading">Ошибка соединения</div>';
    }
}

function renderDetails(session, answers) {
    const totalQuestions = session.total_questions;
    const correctCount = session.correct_count;
    const percent = Math.round((correctCount / totalQuestions) * 100);
    
    let html = `
        <div class="quiz-header">
            <h1>📋 ${escapeHtml(session.quiz_title)}</h1>
            <div class="total-score">🏆 Итоговый счёт: ${session.total_score} очков</div>
            <div>✅ Правильных ответов: ${correctCount}/${totalQuestions} (${percent}%)</div>
        </div>
        <h3>📝 Детали ответов:</h3>
    `;
    
    if (answers.length === 0) {
        html += '<div class="loading">Нет данных об ответах</div>';
    } else {
        answers.forEach(answer => {
            // Форматируем ответ пользователя
            let userAnswerHtml = '';
            console.log('Данные ответа:', answer);
            if (answer.user_answer && answer.user_answer !== '') {
                userAnswerHtml = `<div class="user-answer">📌 Ваш ответ: ${escapeHtml(answer.user_answer)}</div>`;
            } else {
                userAnswerHtml = `<div class="user-answer">📌 Ваш ответ: <em>не выбран</em></div>`;
            }
            
            // Форматируем правильный ответ
            let correctAnswerHtml = '';
            if (answer.correct_answer && answer.correct_answer !== '') {
                correctAnswerHtml = `<div class="correct-answer">✓ Правильный ответ: ${escapeHtml(answer.correct_answer)}</div>`;
            }
            
            html += `
                <div class="question-item">
                    <div class="question-text">Вопрос ${answer.question_number}: ${escapeHtml(answer.question_text)}</div>
                    <div>
                        <span class="answer-status ${answer.is_correct ? 'status-correct' : 'status-incorrect'}">
                            ${answer.is_correct ? '✅ Правильно' : '❌ Неправильно'}
                        </span>
                        <span style="margin-left: 10px;">+${answer.points_awarded} очков</span>
                    </div>
                    ${userAnswerHtml}
                    ${correctAnswerHtml}
                </div>
            `;
        });
    }
    
    document.getElementById('content').innerHTML = html;
}

function goToLobby() {
    window.location.href = '/lobby';
}

function goToProfile() {
    window.location.href = '/profile';
}

function goBack() {
    window.history.back();
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