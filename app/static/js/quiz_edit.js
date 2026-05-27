let quizId = null;
let questions = [];

function init() {
    if (!checkOrganizerAuth()) return;
    document.getElementById('userName').textContent = getCurrentUser().name || 'Организатор';
    
    const urlParts = window.location.pathname.split('/');
    quizId = parseInt(urlParts[urlParts.length - 2]);
    loadQuiz();
}

async function loadQuiz() {
    try {
        const response = await fetch(`/quizzes/${quizId}`);
        if (response.ok) {
            const quiz = await response.json();
            document.getElementById('title').value = quiz.title;
            document.getElementById('description').value = quiz.description || '';
            document.getElementById('category').value = quiz.category || '';
            document.getElementById('timePerQuestion').value = quiz.time_per_question_sec;
            document.getElementById('maxPlayers').value = quiz.max_players || 10;
            
            questions = quiz.questions.map((q, idx) => ({
                id: q.id,
                order_index: idx,
                question_text: q.question_text,
                image_url: q.image_url,
                answer_mode: q.answer_mode,
                points: q.points,
                options: q.options.map((opt, optIdx) => ({
                    id: opt.id,
                    option_text: opt.option_text,
                    is_correct: opt.is_correct,
                    order_index: optIdx
                }))
            }));
            
            renderQuestions();
            document.getElementById('loading').style.display = 'none';
            document.getElementById('quizForm').style.display = 'block';
        } else {
            alert('Квиз не найден');
            window.location.href = '/organizer';
        }
    } catch (err) {
        alert('Ошибка загрузки');
        window.location.href = '/organizer';
    }
}

function addQuestion() {
    questions.push({
        order_index: questions.length,
        question_text: '',
        image_url: null,
        answer_mode: 'single',
        points: 100,
        options: []
    });
    renderQuestions();
}

function removeQuestion(index) {
    if (confirm('Удалить этот вопрос?')) {
        questions.splice(index, 1);
        questions.forEach((q, i) => q.order_index = i);
        renderQuestions();
    }
}

function updateQuestionText(index, value) {
    questions[index].question_text = value;
}

function updateAnswerMode(index, value) {
    questions[index].answer_mode = value;
    if (value === 'single') {
        const hasCorrect = questions[index].options.some(opt => opt.is_correct);
        if (!hasCorrect && questions[index].options.length > 0) {
            questions[index].options[0].is_correct = true;
        }
    }
    renderQuestions();
}

function updatePoints(index, value) {
    let num = parseInt(value, 10);
    if (isNaN(num)) num = 100;
    questions[index].points = num;
}

function addOption(qIndex) {
    questions[qIndex].options.push({
        option_text: '',
        is_correct: false,
        order_index: questions[qIndex].options.length
    });
    renderQuestions();
}

function removeOption(qIndex, optIndex) {
    questions[qIndex].options.splice(optIndex, 1);
    questions[qIndex].options.forEach((opt, i) => opt.order_index = i);
    renderQuestions();
}

function updateOptionText(qIndex, optIndex, value) {
    questions[qIndex].options[optIndex].option_text = value;
}

function updateOptionCorrect(qIndex, optIndex, isCorrect) {
    if (questions[qIndex].answer_mode === 'single' && isCorrect) {
        questions[qIndex].options.forEach((opt, i) => {
            opt.is_correct = (i === optIndex);
        });
    } else {
        questions[qIndex].options[optIndex].is_correct = isCorrect;
    }
    renderQuestions();
}

// Загрузка изображения
async function uploadImage(qIndex, input) {
    const file = input.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/images/upload', { method: 'POST', body: formData });
        if (response.ok) {
            const data = await response.json();
            questions[qIndex].image_url = data.url;
            updateImagePreview(qIndex);
        } else {
            alert('Ошибка загрузки');
        }
    } catch (err) {
        alert('Ошибка соединения');
    }
}

function uploadImageFromUrl(qIndex) {
    const urlDiv = document.getElementById(`urlInput_${qIndex}`);
    urlDiv.style.display = 'block';
}

function saveImageUrl(qIndex) {
    const url = document.getElementById(`imageUrl_${qIndex}`).value;
    if (url) {
        questions[qIndex].image_url = url;
        updateImagePreview(qIndex);
        cancelImageUrl(qIndex);
    }
}

function cancelImageUrl(qIndex) {
    const urlDiv = document.getElementById(`urlInput_${qIndex}`);
    urlDiv.style.display = 'none';
    document.getElementById(`imageUrl_${qIndex}`).value = '';
}

function updateImagePreview(qIndex) {
    const previewDiv = document.getElementById(`preview_${qIndex}`);
    const imageUrl = questions[qIndex].image_url;
    
    if (imageUrl) {
        previewDiv.innerHTML = `
            <div style="position: relative; display: inline-block;">
                <img src="${imageUrl}" style="max-width: 200px; max-height: 150px; border-radius: 8px;">
                <button type="button" onclick="removeImage(${qIndex})" style="position: absolute; top: -8px; right: -8px; background: red; color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer;">✖</button>
            </div>
        `;
    } else {
        previewDiv.innerHTML = '';
    }
}

function removeImage(qIndex) {
    questions[qIndex].image_url = null;
    updateImagePreview(qIndex);
    const fileInput = document.querySelector(`input[type="file"][onchange*="uploadImage(${qIndex},"]`);
    if (fileInput) fileInput.value = '';
}

function renderQuestions() {
    const container = document.getElementById('questionsContainer');
    if (questions.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">Нет вопросов. Нажмите "Добавить вопрос"</div>';
        return;
    }

    container.innerHTML = questions.map((q, qIndex) => `
        <div class="question-card">
            <div class="question-header">
                <span class="question-title">Вопрос ${qIndex + 1}</span>
                <button type="button" class="remove-btn" onclick="removeQuestion(${qIndex})">
                    <svg width="18" height="18" viewBox="0 0 24 24">
                        <line x1="18" y1="6" x2="6" y2="18" stroke="#999" stroke-width="1.5"/>
                        <line x1="6" y1="6" x2="18" y2="18" stroke="#999" stroke-width="1.5"/>
                    </svg>
                </button>
            </div>

            <div class="form-group">
                <label>Текст вопроса *</label>
                <input type="text" value="${escapeHtml(q.question_text)}" onchange="updateQuestionText(${qIndex}, this.value)">
            </div>

            <div class="form-group">
                <label>Изображение (необязательно)</label>
                <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                    <input type="file" accept="image/*" onchange="uploadImage(${qIndex}, this)" style="flex: 1;">
                    <button type="button" class="btn-secondary" onclick="uploadImageFromUrl(${qIndex})">Загрузить по ссылке</button>
                </div>
                <div id="preview_${qIndex}" class="image-preview" style="margin-top: 10px;">
                    ${q.image_url ? `
                        <div style="position: relative; display: inline-block;">
                            <img src="${q.image_url}" style="max-width: 200px; max-height: 150px; border-radius: 8px;">
                            <button type="button" onclick="removeImage(${qIndex})" style="position: absolute; top: -8px; right: -8px; background: red; color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer;">✖</button>
                        </div>
                    ` : ''}
                </div>
                <div id="urlInput_${qIndex}" style="display: none; margin-top: 10px;">
                    <input type="text" id="imageUrl_${qIndex}" placeholder="Введите URL изображения" style="width: 100%; padding: 8px;">
                    <button type="button" class="btn-secondary" onclick="saveImageUrl(${qIndex})" style="margin-top: 5px;">Сохранить</button>
                    <button type="button" class="btn-secondary" onclick="cancelImageUrl(${qIndex})" style="margin-top: 5px;">Отмена</button>
                </div>
            </div>

            <div class="form-group">
                <label>Режим ответа</label>
                <select onchange="updateAnswerMode(${qIndex}, this.value)">
                    <option value="single" ${q.answer_mode === 'single' ? 'selected' : ''}>Одиночный выбор</option>
                    <option value="multiple" ${q.answer_mode === 'multiple' ? 'selected' : ''}>Множественный выбор</option>
                </select>
            </div>

            <div class="form-group">
                <label>Баллы за вопрос</label>
                <input type="text" value="${q.points}" onchange="updatePoints(${qIndex}, this.value)">
            </div>

            <label>Варианты ответов</label>
            ${q.options.map((opt, optIndex) => `
                <div class="option-row">
                    <input type="text" placeholder="Вариант ответа" value="${escapeHtml(opt.option_text)}" onchange="updateOptionText(${qIndex}, ${optIndex}, this.value)">
                    <label class="correct-check">
                        <input type="${q.answer_mode === 'single' ? 'radio' : 'checkbox'}" name="correct_${qIndex}" ${opt.is_correct ? 'checked' : ''} onchange="updateOptionCorrect(${qIndex}, ${optIndex}, this.checked)">
                        Правильный
                    </label>
                    <button type="button" class="remove-btn" onclick="removeOption(${qIndex}, ${optIndex})">
                        <svg width="16" height="16" viewBox="0 0 24 24">
                            <line x1="18" y1="6" x2="6" y2="18" stroke="#999" stroke-width="1.5"/>
                            <line x1="6" y1="6" x2="18" y2="18" stroke="#999" stroke-width="1.5"/>
                        </svg>
                    </button>
                </div>
            `).join('')}

            <button type="button" class="add-option-btn" onclick="addOption(${qIndex})">+ Добавить вариант ответа</button>
        </div>
    `).join('');
}

async function updateQuiz(event) {
    event.preventDefault();

    const title = document.getElementById('title').value;
    if (!title) { alert('Введите название квиза'); return; }

    for (let i = 0; i < questions.length; i++) {
        const q = questions[i];
        if (!q.question_text) { alert(`Введите текст вопроса ${i + 1}`); return; }
        if (q.options.length < 2) { alert(`В вопросе ${i + 1} минимум 2 варианта`); return; }
        if (!q.options.some(opt => opt.is_correct)) { alert(`В вопросе ${i + 1} не выбран правильный ответ`); return; }
    }

    const quizData = {
        organizer_id: parseInt(getCurrentUser().id),
        title: title,
        description: document.getElementById('description').value || null,
        category: document.getElementById('category').value || null,
        time_per_question_sec: parseInt(document.getElementById('timePerQuestion').value),
        max_players: parseInt(document.getElementById('maxPlayers').value),
        questions: questions.map(q => ({
            id: q.id,
            order_index: q.order_index,
            question_text: q.question_text,
            image_url: q.image_url || null,
            answer_mode: q.answer_mode,
            points: q.points,
            options: q.options.map(opt => ({
                option_text: opt.option_text,
                is_correct: opt.is_correct,
                order_index: opt.order_index
            }))
        }))
    };

    try {
        const response = await fetch(`/quizzes/${quizId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(quizData)
        });
        if (response.ok) {
            window.location.href = '/organizer';
        } else {
            alert('Ошибка при обновлении');
        }
    } catch (err) {
        alert('Ошибка соединения');
    }
}

function cancel() {
    document.getElementById('cancelModal').classList.add('active');
}

function closeCancelModal() {
    document.getElementById('cancelModal').classList.remove('active');
}

function confirmCancel() {
    closeCancelModal();
    window.location.href = '/organizer';
}

document.getElementById('quizForm')?.addEventListener('submit', updateQuiz);
window.updateQuiz = updateQuiz;
init();
