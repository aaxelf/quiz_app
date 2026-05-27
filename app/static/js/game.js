let ws = null;
let roomCode = null;
let currentQuestion = null;
let selectedOptions = [];
let timerInterval = null;
let questionStartTime = null;

function init() {
    if (!isAuthenticated()) {
        window.location.href = '/';
        return;
    }
    
    roomCode = localStorage.getItem('roomCode');
    if (!roomCode) {
        window.location.href = '/lobby';
        return;
    }
    
    document.getElementById('userName').textContent = getCurrentUser().name || 'Игрок';
    document.getElementById('roomCodeDisplay').textContent = roomCode;
    
    connectWebSocket();
}

function connectWebSocket() {
    const userId = getCurrentUser().id;
    const userName = getCurrentUser().name || 'Игрок';
    
    console.log('🔌 Подключение к WebSocket...');
    
    ws = new WebSocket(`ws://localhost:8000/ws/player/${userId}`);
    
    ws.onopen = () => {
        console.log('✅ WebSocket открыт');
        
        ws.send(JSON.stringify({
            action: 'join_room',
            code: roomCode,
            user_id: parseInt(userId),
            user_name: userName
        }));
        console.log('📤 Отправлено join_room');
    };
    
    ws.onmessage = (event) => {
        console.log('📨 Получено сообщение:', event.data);
        
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
    
    ws.onerror = (err) => {
        console.error('❌ WebSocket ошибка:', err);
    };
    
    ws.onclose = function(event) {
        console.log('WebSocket закрыт');
        // if (!window.location.pathname.includes('/lobby')) {
        //     alert('Соединение с сервером потеряно');
        //     window.location.href = '/lobby';
        // }
    };
}

function showFinalLeaderboard(leaderboard) {
    const modal = document.getElementById('resultModal');
    const container = modal.querySelector('#finalLeaderboard');
    
    container.innerHTML = `
        <h4>Финальные результаты:</h4>
        ${leaderboard.map((player, index) => `
            <div class="leaderboard-item">
                <span>${index + 1}. ${escapeHtml(player.name)}</span>
                <span><strong>${player.score}</strong> очков</span>
            </div>
        `).join('')}
    `;
    
    modal.classList.add('active');
    if (ws) ws.close();
}

function handleMessage(data) {
    console.log('Получено:', data);

    switch(data.type) {
        case 'joined':
            console.log('Присоединились к комнате');
            break;
            
        case 'new_question':
            showQuestion(data);
            break;
            
        case 'answer_result':
            handleAnswerResult(data);
            break;
            
        case 'leaderboard_update':
            updateLeaderboard(data.leaderboard);
            break;
            
        case 'quiz_finished':
            console.log('Финальный лидерборд:', data.leaderboard);
            showFinalLeaderboard(data.leaderboard);
            break;
            
        case 'error':
            alert(data.message);
            if (data.message.includes('заполнена') || data.message.includes('не найдена') || data.message.includes('уже начался')) {
                // Возвращаемся на страницу ввода кода
                window.location.href = '/lobby';
            }
            break;
    }
}

function showQuestion(question) {
    currentQuestion = question;
    selectedOptions = [];
    questionStartTime = Date.now();

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = false;
    submitBtn.textContent = 'Ответить';
    
    // Показываем игровой экран
    document.getElementById('waitingScreen').style.display = 'none';
    document.getElementById('gameScreen').style.display = 'block';
    
    // Устанавливаем текст вопроса
    document.getElementById('questionText').textContent = question.text;
    
    // Показываем изображение если есть
    const img = document.getElementById('questionImage');
    if (question.image_url) {
        img.src = question.image_url;
        img.style.display = 'block';
    } else {
        img.style.display = 'none';
    }
    
    // Отображаем варианты ответов
    const container = document.getElementById('optionsContainer');
    container.innerHTML = question.options.map(opt => `
        <div class="option" onclick="toggleOption(${opt.id})" data-id="${opt.id}">
            ${escapeHtml(opt.text)}
        </div>
    `).join('');
    
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }

    // Запускаем таймер
    let timeLeft = question.time_limit || 30;
    document.getElementById('timer').textContent = timeLeft;

    timerInterval = setInterval(() => {
        timeLeft--;
        document.getElementById('timer').textContent = timeLeft;
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            document.getElementById('submitBtn').disabled = true;
            submitAnswer();
        }
    }, 1000);
}

function toggleOption(optionId) {
    const optionDiv = document.querySelector(`.option[data-id="${optionId}"]`);
    
    if (currentQuestion.answer_mode === 'single') {
        // Одиночный выбор
        document.querySelectorAll('.option').forEach(opt => opt.classList.remove('selected'));
        selectedOptions = [optionId];
        optionDiv.classList.add('selected');
    } else {
        // Множественный выбор
        if (selectedOptions.includes(optionId)) {
            selectedOptions = selectedOptions.filter(id => id !== optionId);
            optionDiv.classList.remove('selected');
        } else {
            selectedOptions.push(optionId);
            optionDiv.classList.add('selected');
        }
    }
}

function submitAnswer() {
    if (!currentQuestion) return;
    
    if (selectedOptions.length === 0) {
        return;
    }
    
    document.getElementById('submitBtn').textContent = 'Отвечено';
    document.getElementById('submitBtn').disabled = true;
    
    ws.send(JSON.stringify({
        action: 'answer',
        question_id: currentQuestion.question_id,
        selected_option_ids: selectedOptions,
        start_time: questionStartTime
    }));
}

function handleAnswerResult(data) {
    const resultMsg = data.is_correct ? '✅ Правильно!' : '❌ Неправильно';
    console.log(resultMsg, `+${data.points_awarded} очков`);
}

function updateLeaderboard(leaderboard) {
    const container = document.getElementById('leaderboardList');
    
    if (!leaderboard || leaderboard.length === 0) {
        container.innerHTML = 'Нет игроков';
        return;
    }
    
    container.innerHTML = leaderboard.map((player, index) => `
        <div class="leaderboard-item">
            <span>${index + 1}. ${escapeHtml(player.name)}</span>
            <span>
                <strong>${player.score}</strong> очков
                ${player.time_ms ? `<span style="font-size: 10px; color: #999;"> (${(player.time_ms/1000).toFixed(1)} сек)</span>` : ''}
            </span>
        </div>
    `).join('');
}

function goToLobby() {
    localStorage.removeItem('roomCode');
    window.location.href = '/lobby';
}

function showLogoutConfirm() {
    document.getElementById('logoutModal').classList.add('active');
}

function closeLogoutModal() {
    document.getElementById('logoutModal').classList.remove('active');
}

function confirmLogout() {
    closeLogoutModal();
    if (ws) ws.close();
    logout();
}

function goToHistory() {
    window.location.href = '/history';
}

init();