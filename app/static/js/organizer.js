let currentUserId = null;
let quizzes = [];
let currentSort = 'date';
let sortOrder = 'desc';
let activeSessions = [];
let sessionsInterval = null;
let deleteQuizId = null;


function init() {
    if (!checkOrganizerAuth()) return;
    currentUserId = getCurrentUser().id;
    document.getElementById('userName').textContent = getCurrentUser().name || 'Организатор';
    loadQuizzes();
    startSessionsRefresh();
}

async function loadQuizzes() {
    const container = document.getElementById('quizzesList');
    container.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const response = await fetch(`/quizzes/my/${currentUserId}`);
        if (response.ok) {
            quizzes = await response.json();
            renderQuizzes();
        } else {
            container.innerHTML = '<div class="empty-state">Ошибка загрузки квизов</div>';
        }
    } catch (err) {
        container.innerHTML = '<div class="empty-state">Ошибка соединения</div>';
    }
}

function sortQuizzes() {
    const sorted = [...quizzes];
    
    switch(currentSort) {
        case 'name':
            sorted.sort((a, b) => {
                if (sortOrder === 'asc') {
                    return a.title.localeCompare(b.title);
                } else {
                    return b.title.localeCompare(a.title);
                }
            });
            break;
        case 'date':
            sorted.sort((a, b) => {
                const dateA = new Date(a.created_at);
                const dateB = new Date(b.created_at);
                if (sortOrder === 'asc') {
                    return dateA - dateB;
                } else {
                    return dateB - dateA;
                }
            });
            break;
        case 'plays':
            sorted.sort((a, b) => {
                const playsA = a.play_count || 0;
                const playsB = b.play_count || 0;
                if (sortOrder === 'asc') {
                    return playsA - playsB;
                } else {
                    return playsB - playsA;
                }
            });
            break;
    }
    
    return sorted;
}

function setSort(sortType) {
    if (currentSort === sortType) {
        sortOrder = sortOrder === 'desc' ? 'asc' : 'desc';
    } else {
        currentSort = sortType;
        sortOrder = 'desc';  // по умолчанию по убыванию
    }
    
    // Обновляем активную кнопку
    document.querySelectorAll('.sort-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.getElementById(`sort-${sortType}`);
    activeBtn.classList.add('active');
    
    // Обновляем стрелку
    let arrowSymbol = '';
    if (sortType === 'name') {
        arrowSymbol = sortOrder === 'asc' ? ' ↑ (А→Я)' : ' ↓ (Я→А)';
    } else if (sortType === 'date') {
        arrowSymbol = sortOrder === 'asc' ? ' ↑ (старые)' : ' ↓ (новые)';
    } else if (sortType === 'plays') {
        arrowSymbol = sortOrder === 'asc' ? ' ↑ (меньше)' : ' ↓ (больше)';
    }
    
    activeBtn.innerHTML = getSortButtonText(sortType) + arrowSymbol;
    
    renderQuizzes();
}

function getSortButtonText(sortType) {
    switch(sortType) {
        case 'name': return 'По названию';
        case 'date': return 'По дате';
        case 'plays': return 'По играм';
        default: return '';
    }
}

function renderQuizzes() {
    const container = document.getElementById('quizzesList');
    const sortedQuizzes = sortQuizzes();
    
    if (sortedQuizzes.length === 0) {
        container.innerHTML = '<div class="empty-state">У вас пока нет квизов. Создайте первый!</div>';
        return;
    }
    
    container.innerHTML = sortedQuizzes.map(quiz => `
        <div class="quiz-card" data-id="${quiz.id}">
            <button class="menu-btn" onclick="toggleMenu(event, ${quiz.id})">⋮</button>
            <div id="menu-${quiz.id}" class="menu-dropdown">
                <button onclick="createSession(${quiz.id}, '${escapeHtml(quiz.title)}')">
                    <svg width="16" height="16" viewBox="0 0 24 24" style="display: inline-block; margin-right: 8px;">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" stroke="#333" stroke-width="1.5" fill="none"/>
                        <line x1="3" y1="9" x2="21" y2="9" stroke="#333" stroke-width="1.5"/>
                        <circle cx="9" cy="15" r="1" fill="#333"/>
                        <circle cx="15" cy="15" r="1" fill="#333"/>
                    </svg>
                    Создать сессию
                </button>
                <button onclick="editQuiz(${quiz.id})">
                    <svg width="16" height="16" viewBox="0 0 24 24" style="display: inline-block; margin-right: 8px;">
                        <path d="M17 3l4 4-7 7H10v-4l7-7z" stroke="#333" stroke-width="1.5" fill="none"/>
                        <line x1="14" y1="6" x2="18" y2="10" stroke="#333" stroke-width="1.5"/>
                    </svg>
                    Редактировать
                </button>
                <button class="delete-btn" onclick="deleteQuiz(${quiz.id})">
                    <svg width="16" height="16" viewBox="0 0 24 24" style="display: inline-block; margin-right: 8px;">
                        <polyline points="3 6 5 6 21 6" stroke="#e74c3c" stroke-width="1.5" fill="none"/>
                        <path d="M8 6V4h8v2" stroke="#e74c3c" stroke-width="1.5" fill="none"/>
                        <rect x="6" y="10" width="12" height="12" stroke="#e74c3c" stroke-width="1.5" fill="none"/>
                        <line x1="10" y1="12" x2="10" y2="18" stroke="#e74c3c" stroke-width="1.5"/>
                        <line x1="14" y1="12" x2="14" y2="18" stroke="#e74c3c" stroke-width="1.5"/>
                    </svg>
                    Удалить
                </button>
            </div>
            <div class="quiz-title">${escapeHtml(quiz.title)}</div>
            <div class="quiz-meta">
                <span>
                    <svg width="14" height="14" viewBox="0 0 24 24" style="display: inline-block; margin-right: 4px;">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" stroke="#999" stroke-width="1.5" fill="none"/>
                        <line x1="8" y1="2" x2="8" y2="6" stroke="#999" stroke-width="1.5"/>
                        <line x1="16" y1="2" x2="16" y2="6" stroke="#999" stroke-width="1.5"/>
                        <line x1="3" y1="10" x2="21" y2="10" stroke="#999" stroke-width="1.5"/>
                    </svg>
                    ${new Date(quiz.created_at).toLocaleDateString()}
                </span>
                <span>
                    <svg width="14" height="14" viewBox="0 0 24 24" style="display: inline-block; margin-right: 4px;">
                        <circle cx="12" cy="12" r="10" stroke="#999" stroke-width="1.5" fill="none"/>
                        <circle cx="12" cy="12" r="3" stroke="#999" stroke-width="1.5" fill="none"/>
                        <line x1="12" y1="2" x2="12" y2="5" stroke="#999" stroke-width="1.5"/>
                        <line x1="12" y1="19" x2="12" y2="22" stroke="#999" stroke-width="1.5"/>
                        <line x1="2" y1="12" x2="5" y2="12" stroke="#999" stroke-width="1.5"/>
                        <line x1="19" y1="12" x2="22" y2="12" stroke="#999" stroke-width="1.5"/>
                    </svg>
                    ${quiz.play_count || 0} игр
                </span>
            </div>
        </div>
    `).join('');
}

function toggleMenu(event, quizId) {
    event.stopPropagation();
    
    // Закрываем все другие меню и сбрасываем z-index
    document.querySelectorAll('.quiz-card').forEach(card => {
        card.style.zIndex = '';
    });
    document.querySelectorAll('.menu-dropdown').forEach(m => {
        if (m.id !== `menu-${quizId}`) m.classList.remove('show');
    });
    
    const menu = document.getElementById(`menu-${quizId}`);
    menu.classList.toggle('show');
    
    // Поднимаем текущую карточку
    const card = menu.closest('.quiz-card');
    if (card && menu.classList.contains('show')) {
        card.style.zIndex = '10000';
    } else {
        card.style.zIndex = '';
    }
}

document.addEventListener('click', () => {
    document.querySelectorAll('.menu-dropdown').forEach(m => m.classList.remove('show'));
});

function createQuiz() {
    window.location.href = '/quiz/create';
}

function editQuiz(quizId) {
    window.location.href = `/quiz/${quizId}/edit`;
}

function deleteQuiz(quizId) {
    deleteQuizId = quizId;
    document.getElementById('deleteModal').classList.add('active');
}

function closeDeleteModal() {
    deleteQuizId = null;
    document.getElementById('deleteModal').classList.remove('active');
}

async function confirmDelete() {
    if (!deleteQuizId) return;
    try {
        const response = await fetch(`/quizzes/${deleteQuizId}`, { method: 'DELETE' });
        if (response.ok) {
            closeDeleteModal();
            loadQuizzes();
        } else {
            alert('Ошибка при удалении');
        }
    } catch (err) {
        alert('Ошибка соединения');
    }
}

function goToSettings() {
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

// Загрузка сессий с сервера
async function loadSessions() {
    try {
        const response = await fetch('/sessions/my');
        if (response.ok) {
            const newSessions = await response.json();
            
            // Проверяем, изменился ли статус какой-то сессии
            for (let i = 0; i < activeSessions.length; i++) {
                const oldSession = activeSessions[i];
                const newSession = newSessions.find(s => s.room_code === oldSession.room_code);
                if (newSession && oldSession.status !== newSession.status && newSession.status === 'finished') {
                    alert(`Сессия ${oldSession.room_code} завершена! Статус изменён на finished`);
                }
            }
            
            activeSessions = newSessions;
            renderSessions();
        }
    } catch (err) {
        console.error('Ошибка загрузки сессий');
    }
}

// Отображение сессий
function renderSessions() {
    const container = document.getElementById('sessionsList');
    
    if (activeSessions.length === 0) {
        container.innerHTML = '<div class="empty-state">Нет активных сессий</div>';
        return;
    }
    
    container.innerHTML = activeSessions.map((session, index) => `
        <div class="session-card" data-session-id="${session.id}">
            <div class="session-info">
                <span class="session-number">#${index + 1}</span>
                <span class="session-code">${session.room_code}</span>
                <span class="session-quiz">${escapeHtml(session.quiz_title || 'Квиз')}</span>
            </div>
            <div class="session-buttons">
                ${session.status === 'waiting' ? 
                    `<button class="session-btn session-start" data-room="${session.room_code}">▶ Старт</button>` : 
                    session.status === 'active' ? 
                    `<button class="session-btn session-start" disabled style="background: #ccc; cursor: not-allowed;">В процессе</button>` : 
                    ''
                }
            </div>
        </div>
    `).join('');

    document.querySelectorAll('.session-start').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const roomCode = btn.getAttribute('data-room');
            startSession(e, roomCode);
        });
    });
}

// Создание новой сессии 
async function createSession(quizId, quizTitle) {
    try {
        const response = await fetch('/sessions/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                quiz_id: quizId,
                quiz_title: quizTitle
            })
        });
        
        if (response.ok) {
            const session = await response.json();
            showSessionCodeModal(session.room_code, quizTitle);
            loadSessions();
        } else {
            alert('Ошибка создания сессии');
        }
    } catch (err) {
        alert('Ошибка соединения');
    }
}

// Показать модалку с кодом сессии
function showSessionCodeModal(code, quizTitle) {
    const modal = document.getElementById('sessionCodeModal');
    document.getElementById('sessionCodeDisplay').textContent = code;
    document.getElementById('sessionQuizTitle').textContent = quizTitle;
    modal.classList.add('active');
    document.body.classList.add('modal-open');
}

function closeSessionCodeModal() {
    document.getElementById('sessionCodeModal').classList.remove('active');
    document.body.classList.remove('modal-open');
}

function copySessionCode() {
    const code = document.getElementById('sessionCodeDisplay').textContent;
    navigator.clipboard.writeText(code);
}

async function startSession(event, roomCode) {
    const button = event?.target;
    
    if (button) {
        button.disabled = true;
        button.textContent = 'В процессе';
    }
    
    try {
        const response = await fetch(`/sessions/${roomCode}/start`, {
            method: 'POST'
        });
        
        if (response.ok) {
            await loadSessions();
        } else {
            if (button) {
                button.disabled = false;
                button.textContent = '▶ Старт';
            }
            const error = await response.json();
            alert('Ошибка: ' + (error.detail || 'Не удалось начать квиз'));
        }
    } catch (err) {
        if (button) {
            button.disabled = false;
            button.textContent = '▶ Старт';
        }
        alert('Ошибка соединения');
    }
}

function refreshSessions() {
    loadSessions();
}

init();

window.importQuiz = function() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        const userId = getCurrentUser().id;
        
        try {
            const response = await fetch(`/quizzes/import?organizer_id=${userId}`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                alert('Квиз успешно импортирован!');
                loadQuizzes();
            } else {
                const error = await response.json();
                // alert('Ошибка импорта: ' + (error.detail || 'Неизвестная ошибка'));
            }
        } catch (err) {
            alert('Ошибка соединения');
        }
    };
    
    input.click();
};

function startSessionsRefresh() {
    if (sessionsInterval) clearInterval(sessionsInterval);
    sessionsInterval = setInterval(() => {
        loadSessions();
    }, 5000);
}

async function exportAllQuizzes() {
    const userId = getCurrentUser().id;
    window.open(`/quizzes/export-all?organizer_id=${userId}`, '_blank');
}