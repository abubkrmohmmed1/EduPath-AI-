let currentFacts = {};
let progressCount = 0;
let isBackwardChaining = false;
let selectedGoalValue = "";

document.getElementById('start-btn').addEventListener('click', () => {
    startSession(false);
});

document.getElementById('goal-btn').addEventListener('click', () => {
    showView('goal-view');
});

document.getElementById('verify-goal-btn').addEventListener('click', () => {
    selectedGoalValue = document.getElementById('goal-select').value;
    startSession(true);
});

function startSession(backward) {
    currentFacts = {};
    progressCount = 0;
    isBackwardChaining = backward;
    showView('question-card');
    document.getElementById('progress').style.width = '0%';
    document.getElementById('inference-logs').innerHTML = '<p>> تم بدء جلسة استدلال جديدة...</p>';
    fetchNextStep();
}

function showView(viewId) {
    document.querySelectorAll('.view').forEach(v => {
        v.classList.add('hidden');
        v.style.opacity = 0;
    });
    const nextView = document.getElementById(viewId);
    nextView.classList.remove('hidden');
    setTimeout(() => {
        nextView.style.opacity = 1;
    }, 10);
}

async function fetchNextStep() {
    try {
        const endpoint = isBackwardChaining ? '/api/verify_goal' : '/api/infer';
        const body = isBackwardChaining
            ? { facts: currentFacts, goal_value: selectedGoalValue }
            : { facts: currentFacts };

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const result = await response.json();

        // Update explanations and logs
        updateExplanations(result.explanations || []);
        if (result.status === 'question') {
            addLog(`طلب معلومة: ${result.fact}`);
            displayQuestion(result);
        } else if (result.status === 'final' || result.status === 'success') {
            addLog(`تم الوصول لنتيجة: ${result.recommendation || 'تحقق الهدف'}`);
            displayResult(result);
        } else if (result.status === 'error') {
            addLog(`خطأ: ${result.message}`);
            alert(result.message || 'حدث خطأ في منطق الاستدلال.');
            window.location.reload();
        }
    } catch (err) {
        console.error(err);
        addLog(`فشل الاتصال بالخادم`);
        alert('فشل الاتصال بالخادم الذكي.');
    }
}

function addLog(msg) {
    const logDiv = document.getElementById('inference-logs');
    const p = document.createElement('p');
    const time = new Date().toLocaleTimeString('ar-EG', { hour12: false });
    p.textContent = `[${time}] > ${msg}`;
    logDiv.appendChild(p);
    logDiv.scrollTop = logDiv.scrollHeight;
}

function updateExplanations(explanations) {
    const explanationUl = document.getElementById('explanations-list');
    explanationUl.innerHTML = '';

    if (explanations.length === 0) {
        const li = document.createElement('li');
        li.style.fontSize = '0.9rem';
        li.style.color = 'rgba(255,255,255,0.6)';
        li.textContent = "ابدأ الجلسة لتظهر لك القواعد هنا.";
        explanationUl.appendChild(li);
        return;
    }

    explanations.forEach(exp => {
        const li = document.createElement('li');
        li.textContent = exp;
        explanationUl.appendChild(li);
    });
}

function displayQuestion(q) {
    const questionText = document.getElementById('question-text');
    const optionsDiv = document.getElementById('options');

    // Smooth transition for question text
    questionText.style.opacity = 0;
    setTimeout(() => {
        questionText.textContent = q.prompt;
        questionText.style.opacity = 1;
    }, 200);

    optionsDiv.innerHTML = '';

    if (q.type === 'boolean') {
        createOptionBtn(optionsDiv, 'نعم', true, q.fact);
        createOptionBtn(optionsDiv, 'لا', false, q.fact);
    } else if (q.type === 'choice') {
        q.options.forEach(opt => {
            createOptionBtn(optionsDiv, opt.label, opt.value, q.fact);
        });
    }

    // Update progress
    progressCount += 15;
    if (progressCount > 90) progressCount = 90;
    document.getElementById('progress').style.width = `${progressCount}%`;
}

function createOptionBtn(container, label, value, fact) {
    const btn = document.createElement('button');
    btn.className = 'option-btn';
    btn.textContent = label;
    btn.onclick = () => {
        currentFacts[fact] = value;
        fetchNextStep();
    };
    container.appendChild(btn);
}

function displayResult(res) {
    showView('result-card');
    document.getElementById('progress').style.width = '100%';

    const recText = document.getElementById('recommendation-text');
    const adviceText = document.getElementById('advice-text');

    if (isBackwardChaining) {
        recText.textContent = res.result ? `تحقق الهدف: نعم، أنت ملائم لمسار ${selectedGoalValue}` : "عذراً، لا يبدو هذا المسار ملائماً لميولك الحالية.";
        adviceText.textContent = res.advice || "";
    } else {
        recText.textContent = res.recommendation;
        adviceText.textContent = res.advice || "استمر في شغفك وتطوير مهاراتك في هذا المجال.";
    }
}
