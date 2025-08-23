
     // Quiz data with 10 questions for each subject
        const quizzes = {
            // STEM Quizzes
            'calculus': {
                title: "Calculus Fundamentals Quiz",
                category: "stem",
                duration: 15, // in minutes
                points: 10,
                questions: createCalculusQuiz()
            },
            'physics': {
                title: "Newtonian Physics Quiz",
                category: "stem",
                duration: 15,
                points: 10,
                questions: createPhysicsQuiz()
            },
            'chemistry': {
                title: "Advanced Chemistry Quiz",
                category: "stem",
                duration: 15,
                points: 10,
                questions: createChemistryQuiz()
            },

            // STEAM Quizzes
            'art-history': {
                title: "Art History Quiz",
                category: "steam",
                duration: 15,
                points: 10,
                questions: createArtHistoryQuiz()
            },
            'music-theory': {
                title: "Music Theory Quiz",
                category: "steam",
                duration: 15,
                points: 10,
                questions: createMusicTheoryQuiz()
            },
            'literature': {
                title: "World Literature Quiz",
                category: "steam",
                duration: 15,
                points: 10,
                questions: createLiteratureQuiz()
            },

            // General Quizzes
            'entrepreneurship': {
                title: "Entrepreneurship Basics Quiz",
                category: "general",
                duration: 15,
                points: 10,
                questions: createEntrepreneurshipQuiz()
            },
            'leadership': {
                title: "Leadership Skills Quiz",
                category: "general",
                duration: 15,
                points: 10,
                questions: createLeadershipQuiz()
            },
            'public-speaking': {
                title: "Public Speaking Quiz",
                category: "general",
                duration: 15,
                points: 10,
                questions: createPublicSpeakingQuiz()
            }
        };

        // Avatars definition
        const avatars = [
            { id: 'beginner', name: 'Beginner', pointsRequired: 0, iconClass: 'fas fa-seedling' },
            { id: 'explorer', name: 'Explorer', pointsRequired: 10, iconClass: 'fas fa-compass' },
            { id: 'scholar', name: 'Scholar', pointsRequired: 30, iconClass: 'fas fa-graduation-cap' },
            { id: 'master', name: 'Master', pointsRequired: 50, iconClass: 'fas fa-crown' },
            { id: 'grandmaster', name: 'Grand Master', pointsRequired: 100, iconClass: 'fas fa-trophy' },
            { id: 'scientist', name: 'Scientist', pointsRequired: 40, iconClass: 'fas fa-flask' },
            { id: 'artist', name: 'Artist', pointsRequired: 25, iconClass: 'fas fa-palette' },
            { id: 'thinker', name: 'Thinker', pointsRequired: 75, iconClass: 'fas fa-brain' }
        ];

        // User data
        let userData = {
            totalPoints: 0,
            unlockedAvatars: ['beginner'],
            currentAvatar: 'beginner',
            completedQuizzes: []
        };

        // Current quiz state
        let currentQuiz = null;
        let currentQuestionIndex = 0;
        let userAnswers = [];
        let markedQuestions = [];
        let answeredCount = 0;
        let quizStarted = false;
        let timeLeft = 0;
        let timerInterval;
        let charts = [];

        // DOM elements
        const dashboardView = document.getElementById('dashboard-view');
        const quizView = document.getElementById('quiz-view');
        const questionContent = document.getElementById('question-content');
        const questionGrid = document.getElementById('question-grid');
        const answeredCountEl = document.getElementById('answered-count');
        const quizTimer = document.getElementById('quiz-timer');
        const quizTitleEl = document.getElementById('quiz-title');
        const rulesModal = document.getElementById('rules-modal');
        const searchInput = document.getElementById('search-input');
        const quizCardContainer = document.getElementById('quiz-card-container');
        const categoryTabs = document.querySelectorAll('.category-tab');
        const avatarModal = document.getElementById('avatar-modal');
        const avatarGrid = document.getElementById('avatar-grid');
        const userPointsEl = document.getElementById('user-points');
        const currentAvatarEl = document.getElementById('current-avatar');
        const modalPointsEl = document.getElementById('modal-points');

        // Initialize the quiz system
        function initQuizSystem() {
            // Hide quiz view by default
            quizView.style.display = 'none';
            rulesModal.style.display = 'none';
            avatarModal.style.display = 'none';

            // Set up event listeners
            searchInput.addEventListener('input', filterQuizzesBySearch);

            // Set first tab as active
            categoryTabs[0].classList.add('active');

            // Load user data from localStorage
            loadUserData();

            // Initialize avatar display
            updateAvatarDisplay();
        }

        // Load user data from localStorage
        function loadUserData() {
            const savedData = localStorage.getItem('quizUserData');
            if (savedData) {
                userData = JSON.parse(savedData);
            } else {
                saveUserData();
            }
            updateUserPointsDisplay();
        }

        // Save user data to localStorage
        function saveUserData() {
            localStorage.setItem('quizUserData', JSON.stringify(userData));
        }

        // Update points display
        function updateUserPointsDisplay() {
            userPointsEl.textContent = `${userData.totalPoints} pts`;
            modalPointsEl.textContent = userData.totalPoints;
        }

        // Update avatar display
        function updateAvatarDisplay() {
            const currentAvatar = avatars.find(a => a.id === userData.currentAvatar);
            if (currentAvatar) {
                currentAvatarEl.innerHTML = `<i class="${currentAvatar.iconClass}"></i>`;
            }
        }

        // Show avatar selection modal
        function showAvatarModal() {
            avatarGrid.innerHTML = '';
            
            avatars.forEach(avatar => {
                const isUnlocked = userData.unlockedAvatars.includes(avatar.id);
                const isCurrent = avatar.id === userData.currentAvatar;
                
                const avatarEl = document.createElement('div');
                avatarEl.className = 'avatar-item';
                avatarEl.innerHTML = `
                    <div class="avatar-icon ${isUnlocked ? 'unlocked' : 'locked'}">
                        <i class="${avatar.iconClass}"></i>
                    </div>
                    <div class="avatar-name">${avatar.name}</div>
                    <div class="avatar-points">${avatar.pointsRequired} pts</div>
                `;
                
                if (isUnlocked) {
                    avatarEl.onclick = () => {
                        userData.currentAvatar = avatar.id;
                        saveUserData();
                        updateAvatarDisplay();
                        closeAvatarModal();
                    };
                    
                    if (isCurrent) {
                        avatarEl.querySelector('.avatar-icon').style.boxShadow = '0 0 0 3px var(--power-blue)';
                    }
                } else {
                    avatarEl.style.cursor = 'not-allowed';
                    avatarEl.querySelector('.avatar-icon').title = `Requires ${avatar.pointsRequired} points`;
                }
                
                avatarGrid.appendChild(avatarEl);
            });
            
            avatarModal.style.display = 'flex';
        }

        // Close avatar modal
        function closeAvatarModal() {
            avatarModal.style.display = 'none';
        }

        // Filter quizzes by category
        function filterQuizzes(category) {
            // Update active tab
            categoryTabs.forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');

            const quizCards = document.querySelectorAll('.quiz-card');

            if (category === 'all') {
                quizCards.forEach(card => card.style.display = 'block');
            } else {
                quizCards.forEach(card => {
                    if (card.dataset.category === category) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            }
        }

        // Filter quizzes by search term
        function filterQuizzesBySearch() {
            const searchTerm = searchInput.value.toLowerCase();
            const quizCards = document.querySelectorAll('.quiz-card');
            let hasResults = false;

            quizCards.forEach(card => {
                const searchData = card.dataset.search.toLowerCase();
                if (searchData.includes(searchTerm) || searchTerm === '') {
                    card.style.display = 'block';
                    hasResults = true;
                } else {
                    card.style.display = 'none';
                }
            });

            // Show no results message if needed
            const noQuizzesMessage = document.querySelector('.no-quizzes');
            if (!hasResults && searchTerm !== '') {
                if (!noQuizzesMessage) {
                    const message = document.createElement('div');
                    message.className = 'no-quizzes';
                    message.innerHTML = '<i class="fas fa-search" style="font-size: 24px; margin-bottom: 10px;"></i><p>No quizzes found matching your search</p>';
                    quizCardContainer.appendChild(message);
                }
            } else if (noQuizzesMessage) {
                noQuizzesMessage.remove();
            }
        }

        // Show quiz view
        function showQuiz(quizId) {
            currentQuiz = quizId;
            currentQuestionIndex = 0;
            userAnswers = Array(quizzes[quizId].questions.length).fill(null);
            markedQuestions = Array(quizzes[quizId].questions.length).fill(false);
            answeredCount = 0;
            timeLeft = quizzes[quizId].duration * 60;

            // Update UI
            dashboardView.style.display = 'none';
            quizView.style.display = 'block';
            quizTitleEl.textContent = quizzes[quizId].title;

            // Create question navigation buttons
            questionGrid.innerHTML = '';
            quizzes[quizId].questions.forEach((q, index) => {
                const btn = document.createElement('button');
                btn.className = 'question-btn';
                btn.textContent = q.id;
                btn.onclick = () => navigateToQuestion(index);
                questionGrid.appendChild(btn);
            });

            // Show rules modal
            rulesModal.style.display = 'flex';
        }

        // Start the quiz
        function startQuiz() {
            rulesModal.style.display = 'none';
            quizStarted = true;

            // Start timer
            timerInterval = setInterval(updateTimer, 1000);
            updateTimer(); // Initial update

            // Load first question
            loadQuestion(currentQuestionIndex);
        }

        // Return to dashboard
        function returnToDashboard() {
            if (confirm('Are you sure you want to return to the dashboard? Your progress will not be saved.')) {
                clearInterval(timerInterval);
                dashboardView.style.display = 'block';
                quizView.style.display = 'none';
                quizStarted = false;
            }
        }

        // Update the timer
        function updateTimer() {
            timeLeft--;

            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                submitQuiz();
                return;
            }

            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;

            quizTimer.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

            // Add warning class when time is running low
            if (timeLeft <= 300) { // 5 minutes
                quizTimer.classList.add('warning');
            }
        }

        // Navigate to a specific question
        function navigateToQuestion(index) {
            currentQuestionIndex = index;
            loadQuestion(index);
        }

        // Load a question
        function loadQuestion(index) {
            const quiz = quizzes[currentQuiz];
            const question = quiz.questions[index];

            // Update active question in navigation
            updateQuestionNavigation();

            let questionHTML = `
                <div class="question-header">
                    <div class="question-number">Question ${question.id}</div>
                    <div class="question-type">${formatQuestionType(question.type)}</div>
                </div>
                
                <div class="question-text">${question.question}</div>
            `;

            // Add question content based on type
            switch (question.type) {
                case 'multiple-choice':
                    questionHTML += `
                        <ul class="options-list">
                            ${question.options.map((option, i) => `
                                <li class="option-item ${userAnswers[index] === i ? 'selected' : ''}" 
                                    onclick="selectAnswer(${i})">
                                    ${option}
                                </li>
                            `).join('')}
                        </ul>
                    `;
                    break;

                case 'true-false':
                    questionHTML += `
                        <div class="true-false-options">
                            <div class="true-false-btn ${userAnswers[index] === true ? 'selected' : ''}" 
                                onclick="selectAnswer(true)">
                                True
                            </div>
                            <div class="true-false-btn ${userAnswers[index] === false ? 'selected' : ''}" 
                                onclick="selectAnswer(false)">
                                False
                            </div>
                        </div>
                    `;
                    break;

                case 'matching':
                    // Improved matching question interface
                    questionHTML += `
                        <div class="matching-container">
                            <div class="matching-column">
                                <h4>Items</h4>
                                ${question.leftItems.map((item, i) => `
                                    <div class="matching-item" id="left-${i}" draggable="true" ondragstart="drag(event)">
                                        ${item}
                                    </div>
                                `).join('')}
                            </div>
                            <div class="matching-column">
                                <h4>Matches</h4>
                                ${question.rightItems.map((item, i) => `
                                    <div class="matching-item" id="right-${i}" ondrop="drop(event, ${i})" ondragover="allowDrop(event)">
                                        ${item}
                                    </div>
                                `).join('')}
                        </div>
                        <div style="margin-top: 10px;">
                            <h4>Your Matches</h4>
                            <div class="matched-pairs-container" id="matched-pairs-container">
                                ${userAnswers[index] ? userAnswers[index].map(pair => `
                                    <div class="matched-pair" id="pair-${pair[0]}-${pair[1]}">
                                        <div class="matched-item">${question.leftItems[pair[0]]}</div>
                                        <div class="match-controls">
                                            <button class="match-btn" onclick="removeMatch(${index}, ${pair[0]}, ${pair[1]})">
                                                <i class="fas fa-times"></i>
                                            </button>
                                        </div>
                                        <div class="matched-item">${question.rightItems[pair[1]]}</div>
                                    </div>
                                `).join('') : ''}
                            </div>
                        </div>
                        <div style="font-size: 14px; color: var(--text-light); margin-top: 10px;">
                            <i class="fas fa-info-circle"></i> Drag items from the left column to the right column to make matches.
                        </div>
                    `;
                    break;

                case 'fill-blank':
                    questionHTML += `
                        <div class="fill-blank-container">
                            <input type="text" class="fill-blank-input" id="fill-answer" 
                                value="${userAnswers[index] || ''}" 
                                placeholder="Type your answer here" 
                                onchange="selectAnswer(this.value)">
                        </div>
                    `;
                    break;

                case 'essay':
                    const essayAnswer = userAnswers[index] || '';
                    const wordCount = essayAnswer ? essayAnswer.split(/\s+/).filter(word => word.length > 0).length : 0;
                    questionHTML += `
                        <div class="essay-container">
                            <textarea class="essay-textarea" id="essay-answer" 
                                placeholder="Type your response here (minimum ${question.minWords} words)..."
                                oninput="updateEssayWordCount(${index}, this)">${essayAnswer}</textarea>
                            <div class="word-count">Words: ${wordCount} (Minimum: ${question.minWords})</div>
                        </div>
                    `;
                    break;

                case 'case-study':
                    questionHTML += `
                        <div class="case-study-container">
                            <div class="case-study-text">${question.caseText}</div>
                        </div>
                        <ul class="options-list" style="margin-top: 15px;">
                            ${question.options.map((option, i) => `
                                <li class="option-item ${userAnswers[index] === i ? 'selected' : ''}" 
                                    onclick="selectAnswer(${i})">
                                    ${option}
                                </li>
                            `).join('')}
                        </ul>
                    `;
                    break;

                case 'chart-radar':
                case 'chart-pie':
                case 'chart-line':
                case 'chart-bar':
                case 'chart-doughnut':
                case 'chart-polar':
                    questionHTML += `
                        <div class="chart-row">
                            <div class="chart-box">
                                <canvas id="question-chart"></canvas>
                            </div>
                        </div>
                        <ul class="options-list" style="margin-top: 15px;">
                            ${question.chartData.labels.map((label, i) => `
                                <li class="option-item ${userAnswers[index] === i ? 'selected' : ''}" 
                                    onclick="selectAnswer(${i})">
                                    ${label}
                                </li>
                            `).join('')}
                        </ul>
                    `;
                    break;

                case 'calculation':
                    questionHTML += `
                        <div class="fill-blank-container">
                            <input type="text" class="fill-blank-input" id="calc-answer" 
                                value="${userAnswers[index] || ''}" 
                                placeholder="Enter your calculated answer" 
                                onchange="selectAnswer(this.value)">
                            <div style="font-size: 14px; color: var(--text-light); margin-top: 10px;">
                                <i class="fas fa-info-circle"></i> Enter numerical value only, without units.
                            </div>
                        </div>
                    `;
                    break;
            }

            // Add navigation buttons
            questionHTML += `
                <div class="question-actions">
                    <div>
                        ${index > 0 ? `
                            <button class="btn btn-outline" onclick="navigateToQuestion(${index - 1})">
                                <i class="fas fa-chevron-left"></i> Previous
                            </button>
                        ` : ''}
                    </div>
                    
                    <div>
                        <button class="btn mark-btn" onclick="toggleMarkQuestion()">
                            ${markedQuestions[index] ? '<i class="fas fa-flag"></i> Unmark' : '<i class="far fa-flag"></i> Mark'}
                        </button>
                        
                        ${index < quizzes[currentQuiz].questions.length - 1 ? `
                            <button class="btn btn-primary" onclick="navigateToQuestion(${index + 1})">
                                Next <i class="fas fa-chevron-right"></i>
                            </button>
                        ` : `
                            <button class="btn submit-btn" onclick="confirmSubmit()">
                                <i class="fas fa-paper-plane"></i> Submit Quiz
                            </button>
                        `}
                    </div>
                </div>
            `;

            questionContent.innerHTML = questionHTML;

            // Render chart if this is a chart question
            if (question.type.includes('chart')) {
                renderChart(question.type, question.chartData);
            }
        }

        // Format question type for display
        function formatQuestionType(type) {
            const typeMap = {
                'multiple-choice': 'Multiple Choice',
                'true-false': 'True/False',
                'matching': 'Matching',
                'fill-blank': 'Fill in the Blank',
                'essay': 'Essay',
                'case-study': 'Case Study',
                'chart-radar': 'Radar Chart',
                'chart-pie': 'Pie Chart',
                'chart-line': 'Line Chart',
                'chart-bar': 'Bar Chart',
                'chart-doughnut': 'Doughnut Chart',
                'chart-polar': 'Polar Chart',
                'calculation': 'Calculation'
            };
            return typeMap[type] || type;
        }

        // Render chart for chart questions
        function renderChart(chartType, chartData) {
            // Destroy previous charts
            charts.forEach(chart => chart.destroy());
            charts = [];

            const ctx = document.getElementById('question-chart').getContext('2d');
            let newChart;

            const chartTypeMap = {
                'chart-radar': 'radar',
                'chart-pie': 'pie',
                'chart-line': 'line',
                'chart-bar': 'bar',
                'chart-doughnut': 'doughnut',
                'chart-polar': 'polarArea'
            };

            newChart = new Chart(ctx, {
                type: chartTypeMap[chartType],
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                boxWidth: 12,
                                font: {
                                    size: 10
                                }
                            }
                        }
                    },
                    scales: chartType === 'chart-radar' ? {
                        r: {
                            angleLines: {
                                display: true
                            },
                            suggestedMin: 0,
                            suggestedMax: 100,
                            pointLabels: {
                                font: {
                                    size: 10
                                }
                            }
                        }
                    } : {}
                }
            });

            charts.push(newChart);
        }

        // Update question navigation buttons
        function updateQuestionNavigation() {
            const buttons = questionGrid.querySelectorAll('.question-btn');
            const quiz = quizzes[currentQuiz];

            buttons.forEach((btn, index) => {
                btn.classList.remove('active', 'answered', 'marked');

                if (index === currentQuestionIndex) {
                    btn.classList.add('active');
                }

                if (userAnswers[index] !== null) {
                    btn.classList.add('answered');
                }

                if (markedQuestions[index]) {
                    btn.classList.add('marked');
                }
            });

            // Update answered count
            answeredCount = userAnswers.filter(answer => answer !== null).length;
            answeredCountEl.textContent = `${answeredCount}/${quiz.questions.length}`;
        }

        // Select an answer
        function selectAnswer(answer) {
            userAnswers[currentQuestionIndex] = answer;
            updateQuestionNavigation();

            // For fill-blank and essay questions, we need to reload to update the selected state
            const question = quizzes[currentQuiz].questions[currentQuestionIndex];
            if (question.type === 'fill-blank' || question.type === 'essay' || question.type === 'calculation') {
                loadQuestion(currentQuestionIndex);
            }
        }

        // Update essay word count
        function updateEssayWordCount(index, textarea) {
            const answer = textarea.value;
            userAnswers[index] = answer;

            const wordCount = answer ? answer.split(/\s+/).filter(word => word.length > 0).length : 0;
            const wordCountEl = textarea.nextElementSibling;
            wordCountEl.textContent = `Words: ${wordCount} (Minimum: ${quizzes[currentQuiz].questions[index].minWords})`;

            updateQuestionNavigation();
        }

        // Toggle mark question
        function toggleMarkQuestion() {
            markedQuestions[currentQuestionIndex] = !markedQuestions[currentQuestionIndex];
            updateQuestionNavigation();
            loadQuestion(currentQuestionIndex); // Reload to update mark button text
        }

        // Drag and drop functions for matching questions
        function allowDrop(ev) {
            ev.preventDefault();
        }

        function drag(ev) {
            ev.dataTransfer.setData("text", ev.target.id);
        }

        function drop(ev, rightIndex) {
            ev.preventDefault();
            const leftId = ev.dataTransfer.getData("text");
            const leftIndex = parseInt(leftId.split('-')[1]);

            // Get the question
            const question = quizzes[currentQuiz].questions[currentQuestionIndex];

            // Initialize user answer if not already done
            if (!userAnswers[currentQuestionIndex]) {
                userAnswers[currentQuestionIndex] = [];
            }

            // Check if this left item is already matched
            const existingMatchIndex = userAnswers[currentQuestionIndex].findIndex(pair => pair[0] === leftIndex);

            if (existingMatchIndex >= 0) {
                // Remove existing match
                userAnswers[currentQuestionIndex].splice(existingMatchIndex, 1);
            }

            // Add new match
            userAnswers[currentQuestionIndex].push([leftIndex, rightIndex]);

            // Update the display
            loadQuestion(currentQuestionIndex);
        }

        // Remove a match
        function removeMatch(questionIndex, leftIndex, rightIndex) {
            const matchIndex = userAnswers[questionIndex].findIndex(
                pair => pair[0] === leftIndex && pair[1] === rightIndex
            );

            if (matchIndex >= 0) {
                userAnswers[questionIndex].splice(matchIndex, 1);
                loadQuestion(questionIndex);
            }
        }

        // Confirm before submitting quiz
        function confirmSubmit() {
            const unanswered = userAnswers.filter(answer => answer === null).length;

            if (unanswered > 0) {
                if (!confirm(`You have ${unanswered} unanswered questions. Are you sure you want to submit?`)) {
                    return;
                }
            } else {
                if (!confirm('Are you sure you want to submit your quiz?')) {
                    return;
                }
            }

            submitQuiz();
        }

        // Submit the quiz
        function submitQuiz() {
            clearInterval(timerInterval);
            quizStarted = false;

            // Calculate score
            let correctAnswers = 0;
            const quiz = quizzes[currentQuiz];

            quiz.questions.forEach((question, index) => {
                if (question.type === 'fill-blank' || question.type === 'calculation') {
                    if (userAnswers[index] && userAnswers[index].toString().toLowerCase() === question.correctAnswer.toLowerCase()) {
                        correctAnswers++;
                    }
                } else if (question.type === 'essay') {
                    // For essay questions, we'll just count them as answered
                    if (userAnswers[index]) {
                        correctAnswers++;
                    }
                } else if (question.type === 'matching') {
                    // For matching questions, check if all correct matches are present
                    if (userAnswers[index] && userAnswers[index].length === question.correctMatches.length) {
                        const allCorrect = question.correctMatches.every(correctPair =>
                            userAnswers[index].some(userPair =>
                                userPair[0] === correctPair[0] && userPair[1] === correctPair[1]
                            )
                        );
                        if (allCorrect) {
                            correctAnswers++;
                        }
                    }
                } else {
                    if (userAnswers[index] === question.correctAnswer) {
                        correctAnswers++;
                    }
                }
            });

            const score = Math.round((correctAnswers / quiz.questions.length) * 100);
            
            // Award points
            const pointsEarned = calculatePoints(score, quiz.points);
            awardPoints(pointsEarned);
            
            // Add to completed quizzes
            if (!userData.completedQuizzes.includes(currentQuiz)) {
                userData.completedQuizzes.push(currentQuiz);
            }
            
            // Save user data
            saveUserData();

            // Show results
            questionContent.innerHTML = `
                <div style="text-align: center; padding: 30px 15px;">
                    <h2 style="color: var(--power-blue); margin-bottom: 15px;">Quiz Submitted Successfully</h2>
                    <div style="font-size: 48px; color: var(--bright-yellow); font-weight: bold; margin: 20px 0;">${score}%</div>
                    <p style="font-size: 16px; margin-bottom: 20px;">
                        You answered ${correctAnswers} out of ${quiz.questions.length} questions correctly.
                    </p>
                    
                    <div style="margin: 20px auto; background-color: var(--light-yellow); 
                        padding: 15px; border-radius: 10px; max-width: 300px;">
                        <div style="font-size: 18px; font-weight: bold; color: var(--warm-orange);">
                            Points Earned: <span style="font-size: 24px;">${pointsEarned}</span>
                        </div>
                        <div style="margin-top: 10px; font-size: 14px;">
                            Total Points: ${userData.totalPoints}
                        </div>
                    </div>
                    
                    <div class="result-chart-container">
                        <canvas id="result-chart"></canvas>
                    </div>
                    
                    <div style="display: flex; justify-content: center; gap: 10px; margin-top: 20px;">
                        <button class="btn btn-primary" onclick="reviewQuiz()">
                            <i class="fas fa-search"></i> Review Answers
                        </button>
                        <button class="btn btn-outline" onclick="returnToDashboard()">
                            <i class="fas fa-home"></i> Return to Dashboard
                        </button>
                    </div>
                </div>
            `;

            // Show result chart
            const ctx = document.getElementById('result-chart').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Correct', 'Incorrect', 'Unanswered'],
                    datasets: [{
                        data: [
                            correctAnswers,
                            userAnswers.filter(a => a !== null).length - correctAnswers,
                            userAnswers.filter(a => a === null).length
                        ],
                        backgroundColor: [
                            'rgba(76, 175, 80, 0.7)',
                            'rgba(244, 67, 54, 0.7)',
                            'rgba(158, 158, 158, 0.7)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                boxWidth: 12,
                                font: {
                                    size: 10
                                }
                            }
                        }
                    }
                }
            });
        }

        // Calculate points earned based on score
        function calculatePoints(score, maxPoints) {
            // Points = maxPoints * (score/100) with minimum of 1
            const points = Math.max(1, Math.round(maxPoints * (score / 100)));
            return points;
        }

        // Award points to user
        function awardPoints(points) {
            userData.totalPoints += points;
            
            // Check for new avatar unlocks
            const unlockedAvatars = avatars.filter(avatar => 
                !userData.unlockedAvatars.includes(avatar.id) && 
                userData.totalPoints >= avatar.pointsRequired
            );
            
            if (unlockedAvatars.length > 0) {
                unlockedAvatars.forEach(avatar => {
                    userData.unlockedAvatars.push(avatar.id);
                });
                
                // Show unlocked notification
                const notification = document.createElement('div');
                notification.className = 'points-earned';
                notification.innerHTML = `
                    <i class="fas fa-star"></i>
                    Unlocked ${unlockedAvatars.length} new avatar${unlockedAvatars.length > 1 ? 's' : ''}!
                `;
                document.body.appendChild(notification);
                
                // Remove notification after animation
                setTimeout(() => {
                    notification.remove();
                }, 3000);
            }
            
            // Update UI
            updateUserPointsDisplay();
            
            // Show points earned notification
            const pointsNotification = document.createElement('div');
            pointsNotification.className = 'points-earned';
            pointsNotification.innerHTML = `
                <i class="fas fa-coins"></i>
                +${points} Points!
            `;
            document.body.appendChild(pointsNotification);
            
            // Remove notification after animation
            setTimeout(() => {
                pointsNotification.remove();
            }, 3000);
        }

        // Review quiz answers
        function reviewQuiz() {
            currentQuestionIndex = 0;
            loadQuestion(currentQuestionIndex);
        }

        // Initialize the system when page loads
        window.onload = initQuizSystem;
        
        // Quiz creation functions
        function createCalculusQuiz() {
            return [
                {
                    id: 1,
                    type: "multiple-choice",
                    question: "What is the derivative of f(x) = 3x² + 2x - 5?",
                    options: [
                        "6x + 2",
                        "3x + 2",
                        "6x² + 2",
                        "3x² + 2x"
                    ],
                    correctAnswer: 0
                },
                {
                    id: 2,
                    type: "true-false",
                    question: "The integral of a function represents the area under its curve.",
                    correctAnswer: true
                },
                {
                    id: 3,
                    type: "fill-blank",
                    question: "The limit as x approaches 0 of (sin x)/x is __________.",
                    correctAnswer: "1"
                },
                {
                    id: 4,
                    type: "multiple-choice",
                    question: "Which of these is NOT a technique for finding integrals?",
                    options: [
                        "Chain rule",
                        "Integration by parts",
                        "Partial fractions",
                        "Trigonometric substitution"
                    ],
                    correctAnswer: 0
                },
                {
                    id: 5,
                    type: "matching",
                    question: "Match the following calculus concepts to their definitions:",
                    leftItems: ["Derivative", "Integral", "Limit", "Chain rule"],
                    rightItems: [
                        "Instantaneous rate of change",
                        "Area under a curve",
                        "Value a function approaches",
                        "Derivative of composite functions"
                    ],
                    correctMatches: [[0, 0], [1, 1], [2, 2], [3, 3]]
                },
                {
                    id: 6,
                    type: "case-study",
                    question: "Based on the scenario below, what is the velocity at t=2 seconds?",
                    caseText: "The position of a particle is given by s(t) = t³ - 6t² + 9t, where t is in seconds and s is in meters.",
                    options: [
                        "-3 m/s",
                        "0 m/s",
                        "3 m/s",
                        "9 m/s"
                    ],
                    correctAnswer: 0
                },
                {
                    id: 7,
                    type: "chart-line",
                    question: "Based on the graph of f'(x), at which x-value does f(x) have a local maximum?",
                    chartData: {
                        labels: ['-2', '-1', '0', '1', '2'],
                        datasets: [{
                            label: "f'(x)",
                            data: [3, 1, -1, -3, -1],
                            borderColor: 'rgba(0, 102, 204, 1)',
                            backgroundColor: 'rgba(0, 102, 204, 0.1)'
                        }]
                    },
                    correctAnswer: 0 // x = -2
                },
                {
                    id: 8,
                    type: "true-false",
                    question: "The second derivative test can determine if a critical point is a maximum or minimum.",
                    correctAnswer: true
                },
                {
                    id: 9,
                    type: "multiple-choice",
                    question: "What is ∫(2x + 3) dx from 0 to 2?",
                    options: [
                        "10",
                        "8",
                        "6",
                        "4"
                    ],
                    correctAnswer: 0
                },
                {
                    id: 10,
                    type: "essay",
                    question: "Explain the Fundamental Theorem of Calculus and its significance in connecting differentiation and integration.",
                    minWords: 50
                }
            ];
        }

        function createPhysicsQuiz() {
            return [
                {
                    id: 1,
                    type: "multiple-choice",
                    question: "Which of Newton's Laws states that F = ma?",
                    options: [
                        "First Law",
                        "Second Law",
                        "Third Law",
                        "Law of Gravitation"
                    ],
                    correctAnswer: 1
                },
                {
                    id: 2,
                    type: "true-false",
                    question: "In the absence of air resistance, all objects fall with the same acceleration.",
                    correctAnswer: true
                },
                {
                    id: 3,
                    type: "fill-blank",
                    question: "The SI unit of force is the __________.",
                    correctAnswer: "newton"
                },
                {
                    id: 4,
                    type: "multiple-choice",
                    question: "What is the kinetic energy of a 2 kg object moving at 3 m/s?",
                    options: [
                        "6 J",
                        "9 J",
                        "12 J",
                        "18 J"
                    ],
                    correctAnswer: 1
                },
                {
                    id: 5,
                    type: "matching",
                    question: "Match the following physics concepts to their definitions:",
                    leftItems: ["Velocity", "Acceleration", "Momentum", "Work"],
                    rightItems: [
                        "Rate of change of displacement",
                        "Rate of change of velocity",
                        "Mass times velocity",
                        "Force times distance"
                    ],
                    correctMatches: [[0, 0], [1, 1], [2, 2], [3, 3]]
                },
                {
                    id: 6,
                    type: "case-study",
                    question: "Based on the scenario below, what is the net force acting on the box?",
                    caseText: "A 5 kg box is being pulled across a floor with a force of 20 N at an angle of 30° above the horizontal. The coefficient of kinetic friction is 0.2.",
                    options: [
                        "12.3 N",
                        "15.0 N",
                        "17.3 N",
                        "20.0 N"
                    ],
                    correctAnswer: 0
                },
                {
                    id: 7,
                    type: "chart-bar",
                    question: "Based on the bar chart showing energy transformations, which system has the greatest energy loss to heat?",
                    chartData: {
                        labels: ['Pendulum', 'Spring', 'Roller Coaster', 'Electric Motor'],
                        datasets: [{
                            label: "Useful Energy",
                            data: [70, 80, 60, 75],
                            backgroundColor: 'rgba(0, 102, 204, 0.7)'
                        },
                        {
                            label: "Lost to Heat",
                            data: [30, 20, 40, 25],
                            backgroundColor: 'rgba(255, 153, 51, 0.7)'
                        }]
                    },
                    correctAnswer: 2 // Roller Coaster
                },
                {
                    id: 8,
                    type: "true-false",
                    question: "According to Newton's Third Law, action and reaction forces act on the same object.",
                    correctAnswer: false
                },
                {
                    id: 9,
                    type: "multiple-choice",
                    question: "What is the power output if 100 J of work is done in 5 seconds?",
                    options: [
                        "5 W",
                        "20 W",
                        "100 W",
                        "500 W"
                    ],
                    correctAnswer: 1
                },
                {
                    id: 10,
                    type: "essay",
                    question: "Explain how Newton's Laws of Motion are applied in the design of automobile safety features like seatbelts and airbags.",
                    minWords: 60
                }
            ];
        }

        function createChemistryQuiz() {
            return [
                {
                    id: 1,
                    type: "multiple-choice",
                    question: "Which element has the atomic number 6?",
                    options: [
                        "Carbon",
                        "Oxygen",
                        "Nitrogen",
                        "Silicon"
                    ],
                    correctAnswer: 0
                },
                {
                    id: 2,
                    type: "true-false",
                    question: "Ionic bonds form between metals and nonmetals.",
                    correctAnswer: true
                },
                {
                    id: 3,
                    type: "fill-blank",
                    question: "The pH of a neutral solution is __________.",
                    correctAnswer: "7"
                },
                {
                    id: 4,
                    type: "multiple-choice",
                    question: "Which of these is NOT a state of matter?",
                    options: [
                        "Solid",
                        "Liquid",
                        "Gas",
                        "Energy"
                    ],
                    correctAnswer: 3
                },
                {
                    id: 5,
                    type: "matching",
                    question: "Match the following chemical concepts to their definitions:",
                    leftItems: ["Covalent bond", "Ion", "Catalyst", "Redox reaction"],
                    rightItems: [
                        "Shared electron pair",
                        "Charged atom",
                        "Speeds up reaction",
                        "Electron transfer"
                    ],
                    correctMatches: [[0, 0], [1, 1], [2, 2], [3, 3]]
                },
                {
                    id: 6,
                    type: "case-study",
                    question: "Based on the scenario below, what type of reaction is occurring?",
                    caseText: "When sodium metal is placed in water, it fizzes violently, producing hydrogen gas and sodium hydroxide solution.",
                    options: [
                        "Synthesis",
                        "Decomposition",
                        "Single displacement",
                        "Double displacement"
                    ],
                    correctAnswer: 2
                },
                {
                    id: 7,
                    type: "chart-pie",
                    question: "Based on the pie chart showing Earth's atmosphere composition, which gas makes up about 78%?",
                    chartData: {
                        labels: ['Nitrogen', 'Oxygen', 'Argon', 'Carbon Dioxide', 'Other'],
                        datasets: [{
                            data: [78, 21, 0.9, 0.04, 0.06],
                            backgroundColor: [
                                'rgba(0, 102, 204, 0.7)',
                                'rgba(76, 175, 80, 0.7)',
                                'rgba(158, 158, 158, 0.7)',
                                'rgba(244, 67, 54, 0.7)',
                                'rgba(255, 153, 51, 0.7)'
                            ]
                        }]
                    },
                    correctAnswer: 0 // Nitrogen
                },
                {
                    id: 8,
                    type: "true-false",
                    question: "Exothermic reactions release heat to the surroundings.",
                    correctAnswer: true
                },
                {
                    id: 9,
                    type: "multiple-choice",
                    question: "What is the molar mass of water (H₂O)?",
                    options: [
                        "16 g/mol",
                        "17 g/mol",
                        "18 g/mol",
                        "20 g/mol"
                    ],
                    correctAnswer: 2
                },
                {
                    id: 10,
                    type: "essay",
                    question: "Explain the periodic trends in atomic radius and ionization energy across periods and down groups in the periodic table.",
                    minWords: 70
                }
            ];
        }

        function createArtHistoryQuiz() {
            return [
                {
                    id: 1,
                    type: "multiple-choice",
                    question: "Which artist painted the Mona Lisa?",
                    options: [
                        "Leonardo da Vinci",
                        "Michelangelo",
                        "Raphael",
                        "Donatello"
                    ],
                    correctAnswer: 0
                },
                {
                    id: 2,
                    type: "true-false",
                    question: "Impressionism originated in France in the 19th century.",
                    correctAnswer: true
                },
                {
                    id: 3,
                    type: "fill-blank",
                    question: "The __________ was an art movement that emphasized emotion and individualism.",
                    correctAnswer: "Romanticism"
                },
                {
                    id: 4,
                    type: "multiple-choice",
                    question: "Which of these is NOT an element of art?",
                    options: [
                        "Line",
                        "Color",
                        "Texture",
                        "Inspiration"
                    ],
                    correctAnswer: 3
                },
                {
                    id: 5,
                    type: "matching",
                    question: "Match the following artists to their famous works:",
                    leftItems: ["Vincent van Gogh", "Pablo Picasso", "Salvador Dalí", "Frida Kahlo"],
                    rightItems: [
                        "The Starry Night",
                        "Guernica",
                        "The Persistence of Memory",
                        "The Two Fridas"
                    ],
                    correctMatches: [[0, 0], [1, 1], [2, 2], [3, 3]]
                },
                {
                    id: 6,
                    type: "case-study",
                    question: "Based on the description below, which art movement is being described?",
                    caseText: "This early 20th century movement sought to break objects into geometric forms and depict them from multiple viewpoints simultaneously.",
                    options: [
                        "Cubism",
                        "Surrealism",
                        "Expressionism",
                        "Fauvism"
                    ],
                    correctAnswer: 0
                },
                {
                    id: 7,
                    type: "chart-bar",
                    question: "Based on the bar chart showing art movement timelines, which movement came first?",
                    chartData: {
                        labels: ['Renaissance', 'Baroque', 'Romanticism', 'Impressionism'],
                        datasets: [{
                            label: "Start Year",
                            data: [1400, 1600, 1800, 1860],
                            backgroundColor: 'rgba(0, 102, 204, 0.7)'
                        }]
                    },
                    correctAnswer: 0 // Renaissance
                },
                {
                    id: 8,
                    type: "true-false",
                    question: "Andy Warhol was a leading figure in the Pop Art movement.",
                    correctAnswer: true
                },
                {
                    id: 9,
                    type: "multiple-choice",
                    question: "Which ancient civilization built the Parthenon?",
                    options: [
                        "Egyptians",
                        "Greeks",
                        "Romans",
                        "Persians"
                    ],
                    correctAnswer: 1
                },
                {
                    id: 10,
                    type: "essay",
                    question: "Compare and contrast the Renaissance and Baroque periods in terms of their artistic styles and cultural contexts.",
                    minWords: 80
                }
            ];
        }

        function createMusicTheoryQuiz() {
            return [
                {
                    id: 1,
                    type: "multiple-choice",
                    question: "How many beats does a whole note get in 4/4 time?",
                    options: [
                        "1",
                        "2",
                        "3",
                        "4"
                    ],
                    correctAnswer: 3
                },
                {
                    id: 2,
                    type: "true-false",
                    question: "A major scale follows the pattern: whole, whole, half, whole, whole, whole, half.",
                    correctAnswer: true
                },
                {
                    id: 3,
                    type: "fill-blank",
                    question: "The __________ clef is typically used for higher-pitched instruments.",
                    correctAnswer: "treble"
                },
                {
                    id: 4,
                    type: "multiple-choice",
                    question: "Which of these is NOT a musical dynamic marking?",
                    options: [
                        "Piano",
                        "Forte",
                        "Allegro",
                        "Mezzo"
                    ],
                    correctAnswer: 2
                },
                {
                    id: 5,
                    type: "matching",
                    question: "Match the following composers to their musical periods:",
                    leftItems: ["Johann Sebastian Bach", "Wolfgang Amadeus Mozart", "Ludwig van Beethoven", "Claude Debussy"],
                    rightItems: [
                        "Baroque",
                        "Classical",
                        "Romantic",
                        "Impressionist"
                    ],
                    correctMatches: [[0, 0], [1, 1], [2, 2], [3, 3]]
                },
                {
                    id: 6,
                    type: "case-study",
                    question: "Based on the description below, what chord is being described?",
                    caseText: "A chord consisting of a root, major third, and perfect fifth.",
                    options: [
                        "Major triad",
                        "Minor triad",
                        "Diminished triad",
                        "Augmented triad"
                    ],
                    correctAnswer: 0
                },
                {
                    id: 7,
                    type: "chart-pie",
                    question: "Based on the pie chart showing orchestra instrument sections, which section has the most players?",
                    chartData: {
                        labels: ['Strings', 'Woodwinds', 'Brass', 'Percussion'],
                        datasets: [{
                            data: [60, 15, 15, 10],
                            backgroundColor: [
                                'rgba(0, 102, 204, 0.7)',
                                'rgba(76, 175, 80, 0.7)',
                                'rgba(255, 153, 51, 0.7)',
                                'rgba(244, 67, 54, 0.7)'
                            ]
                        }]
                    },
                    correctAnswer: 0 // Strings
                },
                {
                    id: 8,
                    type: "true-false",
                    question: "A minor key typically sounds sadder than a major key.",
                    correctAnswer: true
                },
                {
                    id: 9,
                    type: "multiple-choice",
                    question: "What is the relative minor of C major?",
                    options: [
                        "A minor",
                        "E minor",
                        "G minor",
                        "D minor"
                    ],
                    correctAnswer: 0
                },
                {
                    id: 10,
                    type: "essay",
                    question: "Explain the difference between consonance and dissonance in music, and how composers use these concepts to create tension and resolution.",
                    minWords: 60
                }
            ];
        }

        function createLiteratureQuiz() {
            return [
                {
                    id: 1,
                    type: "multiple-choice",
                    question: "Who wrote 'Romeo and Juliet'?",
                    options: [
                        "William Shakespeare",
                        "Charles Dickens",
                        "Jane Austen",
                        "Mark Twain"
                    ],
                    correctAnswer: 0
                },
                {
                    id: 2,
                    type: "true-false",
                    question: "'1984' was written by George Orwell.",
                    correctAnswer: true
                },
                {
                    id: 3,
                    type: "fill-blank",
                    question: "The __________ is the main character in a literary work.",
                    correctAnswer: "protagonist"
                },
                {
                    id: 4,
                    type: "multiple-choice",
                    question: "Which of these is NOT a literary device?",
                    options: [
                        "Metaphor",
                        "Simile",
                        "Hyperbole",
                        "Equation"
                    ],
                    correctAnswer: 3
                },
                {
                    id: 5,
                    type: "matching",
                    question: "Match the following authors to their famous works:",
                    leftItems: ["F. Scott Fitzgerald", "Harper Lee", "J.K. Rowling", "Gabriel García Márquez"],
                    rightItems: [
                        "The Great Gatsby",
                        "To Kill a Mockingbird",
                        "Harry Potter",
                        "One Hundred Years of Solitude"
                    ],
                    correctMatches: [[0, 0], [1, 1], [2, 2], [3, 3]]
                },
                {
                    id: 6,
                    type: "case-study",
                    question: "Based on the excerpt below, what literary period is most likely represented?",
                    caseText: "'It was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness...'",
                    options: [
                        "Romanticism",
                        "Victorian",
                        "Modernism",
                        "Postmodernism"
                    ],
                    correctAnswer: 1
                },
                {
                    id: 7,
                    type: "chart-bar",
                    question: "Based on the bar chart showing Nobel Prize in Literature winners by continent, which continent has the most winners?",
                    chartData: {
                        labels: ['Europe', 'North America', 'Asia', 'Africa', 'South America'],
                        datasets: [{
                            label: "Winners",
                            data: [65, 15, 12, 5, 7],
                            backgroundColor: 'rgba(0, 102, 204, 0.7)'
                        }]
                    },
                    correctAnswer: 0 // Europe
                },
                {
                    id: 8,
                    type: "true-false",
                    question: "An epic poem is typically a long narrative about heroic deeds.",
                    correctAnswer: true
                },
                {
                    id: 9,
                    type: "multiple-choice",
                    question: "Which literary movement emphasized the unconscious mind and dream imagery?",
                    options: [
                        "Realism",
                        "Surrealism",
                        "Naturalism",
                        "Existentialism"
                    ],
                    correctAnswer: 1
                },
                {
                    id: 10,
                    type: "essay",
                    question: "Analyze how the theme of social class is portrayed in any novel you've studied, providing specific examples from the text.",
                    minWords: 100
                }
            ];
        }

        function createEntrepreneurshipQuiz() {
            return [
                {
                    id: 1,
                    type: "multiple-choice",
                    question: "What is the first step in starting a business?",
                    options: [
                        "Finding investors",
                        "Developing a business plan",
                        "Identifying a market need",
                        "Registering the business"
                    ],
                    correctAnswer: 2
                },
                {
                    id: 2,
                    type: "true-false",
                    question: "A SWOT analysis examines strengths, weaknesses, opportunities, and threats.",
                    correctAnswer: true
                },
                {
                    id: 3,
                    type: "fill-blank",
                    question: "The __________ is a document that outlines how a business plans to make money.",
                    correctAnswer: "business model"
                },
                {
                    id: 4,
                    type: "multiple-choice",
                    question: "Which of these is NOT a common source of startup funding?",
                    options: [
                        "Venture capital",
                        "Bootstrapping",
                        "Angel investors",
                        "Tax evasion"
                    ],
                    correctAnswer: 3
                },
                {
                    id: 5,
                    type: "matching",
                    question: "Match the following business terms to their definitions:",
                    leftItems: ["ROI", "USP", "B2B", "CRM"],
                    rightItems: [
                        "Return on investment",
                        "Unique selling proposition",
                        "Business to business",
                        "Customer relationship management"
                    ],
                    correctMatches: [[0, 0], [1, 1], [2, 2], [3, 3]]
                },
                {
                    id: 6,
                    type: "case-study",
                    question: "Based on the scenario below, what pricing strategy is being used?",
                    caseText: "A new tech company releases its product at a high initial price to maximize profits from early adopters, then gradually lowers the price.",
                    options: [
                        "Penetration pricing",
                        "Skimming pricing",
                        "Competitive pricing",
                        "Cost-plus pricing"
                    ],
                    correctAnswer: 1
                },
                {
                    id: 7,
                    type: "chart-line",
                    question: "Based on the revenue growth chart, in which year did the startup become profitable?",
                    chartData: {
                        labels: ['Year 1', 'Year 2', 'Year 3', 'Year 4'],
                        datasets: [{
                            label: "Revenue",
                            data: [100000, 250000, 500000, 1000000],
                            borderColor: 'rgba(0, 102, 204, 1)'
                        },
                        {
                            label: "Expenses",
                            data: [200000, 300000, 400000, 600000],
                            borderColor: 'rgba(244, 67, 54, 1)'
                        }]
                    },
                    correctAnswer: 2 // Year 3
                },
                {
                    id: 8,
                    type: "true-false",
                    question: "A mission statement describes what a company does, while a vision statement describes what it aspires to become.",
                    correctAnswer: true
                },
                {
                    id: 9,
                    type: "multiple-choice",
                    question: "What does MVP stand for in startup terminology?",
                    options: [
                        "Most valuable product",
                        "Minimum viable product",
                        "Maximum value proposition",
                        "Main venture partner"
                    ],
                    correctAnswer: 1
                },
                {
                    id: 10,
                    type: "essay",
                    question: "Explain the importance of market research in developing a successful business plan, and describe at least two methods for conducting market research.",
                    minWords: 80
                }
            ];
        }

        function createLeadershipQuiz() {
            return [
                {
                    id: 1,
                    type: "multiple-choice",
                    question: "Which leadership style involves making decisions without consulting the team?",
                    options: [
                        "Democratic",
                        "Autocratic",
                        "Laissez-faire",
                        "Transformational"
                    ],
                    correctAnswer: 1
                },
                {
                    id: 2,
                    type: "true-false",
                    question: "Emotional intelligence is an important quality for effective leaders.",
                    correctAnswer: true
                },
                {
                    id: 3,
                    type: "fill-blank",
                    question: "The ability to understand and share the feelings of others is called __________.",
                    correctAnswer: "empathy"
                },
                {
                    id: 4,
                    type: "multiple-choice",
                    question: "Which of these is NOT a key leadership skill?",
                    options: [
                        "Communication",
                        "Delegation",
                        "Micromanagement",
                        "Vision"
                    ],
                    correctAnswer: 2
                },
                {
                    id: 5,
                    type: "matching",
                    question: "Match the following leadership theories to their descriptions:",
                    leftItems: ["Trait Theory", "Situational Theory", "Transformational", "Servant Leadership"],
                    rightItems: [
                        "Leaders are born with certain traits",
                        "Leadership style depends on situation",
                        "Inspires and motivates followers",
                        "Focuses on serving others first"
                    ],
                    correctMatches: [[0, 0], [1, 1], [2, 2], [3, 3]]
                },
                {
                    id: 6,
                    type: "case-study",
                    question: "Based on the scenario below, what conflict resolution style is being used?",
                    caseText: "A team leader brings two arguing team members together to discuss their differences and find a mutually acceptable solution.",
                    options: [
                        "Avoiding",
                        "Accommodating",
                        "Collaborating",
                        "Competing"
                    ],
                    correctAnswer: 2
                },
                {
                    id: 7,
                    type: "chart-radar",
                    question: "Based on the leadership skills assessment chart, which skill needs the most improvement?",
                    chartData: {
                        labels: ['Communication', 'Decision Making', 'Delegation', 'Motivation', 'Vision'],
                        datasets: [{
                            label: "Skills Assessment",
                            data: [80, 65, 70, 75, 85],
                            backgroundColor: 'rgba(0, 102, 204, 0.2)'
                        }]
                    },
                    correctAnswer: 1 // Decision Making
                },
                {
                    id: 8,
                    type: "true-false",
                    question: "Effective leaders always have all the answers.",
                    correctAnswer: false
                },
                {
                    id: 9,
                    type: "multiple-choice",
                    question: "Which of these is a characteristic of a good team leader?",
                    options: [
                        "Assigning blame for failures",
                        "Taking credit for team successes",
                        "Encouraging team member development",
                        "Making all decisions personally"
                    ],
                    correctAnswer: 2
                },
                {
                    id: 10,
                    type: "essay",
                    question: "Compare and contrast transactional and transformational leadership styles, providing examples of when each might be most effective.",
                    minWords: 90
                }
            ];
        }

        function createPublicSpeakingQuiz() {
            return [
                {
                    id: 1,
                    type: "multiple-choice",
                    question: "What is the recommended maximum number of main points in a speech?",
                    options: [
                        "2-3",
                        "5-6",
                        "7-8",
                        "As many as needed"
                    ],
                    correctAnswer: 0
                },
                {
                    id: 2,
                    type: "true-false",
                    question: "Using filler words like 'um' and 'ah' should be completely eliminated from speeches.",
                    correctAnswer: false
                },
                {
                    id: 3,
                    type: "fill-blank",
                    question: "The __________ is the part of a speech designed to capture the audience's attention.",
                    correctAnswer: "hook"
                },
                {
                    id: 4,
                    type: "multiple-choice",
                    question: "Which of these is NOT a recommended way to reduce speaking anxiety?",
                    options: [
                        "Practice repeatedly",
                        "Visualize success",
                        "Memorize every word",
                        "Focus on breathing"
                    ],
                    correctAnswer: 2
                },
                {
                    id: 5,
                    type: "matching",
                    question: "Match the following speech types to their purposes:",
                    leftItems: ["Informative", "Persuasive", "Entertaining", "Demonstrative"],
                    rightItems: [
                        "Educate the audience",
                        "Change beliefs/actions",
                        "Amuse the audience",
                        "Show how to do something"
                    ],
                    correctMatches: [[0, 0], [1, 1], [2, 2], [3, 3]]
                },
                {
                    id: 6,
                    type: "case-study",
                    question: "Based on the scenario below, what organizational pattern is being used?",
                    caseText: "A speaker presents a problem with plastic pollution, then offers solutions like recycling and reusable products.",
                    options: [
                        "Chronological",
                        "Problem-Solution",
                        "Spatial",
                        "Topical"
                    ],
                    correctAnswer: 1
                },
                {
                    id: 7,
                    type: "chart-pie",
                    question: "Based on research about what audiences remember, which aspect of a speech is most memorable?",
                    chartData: {
                        labels: ['Words', 'Tone of Voice', 'Body Language'],
                        datasets: [{
                            data: [7, 38, 55],
                            backgroundColor: [
                                'rgba(0, 102, 204, 0.7)',
                                'rgba(255, 153, 51, 0.7)',
                                'rgba(76, 175, 80, 0.7)'
                            ]
                        }]
                    },
                    correctAnswer: 2 // Body Language
                },
                {
                    id: 8,
                    type: "true-false",
                    question: "Using stories and examples makes speeches more engaging and memorable.",
                    correctAnswer: true
                },
                {
                    id: 9,
                    type: "multiple-choice",
                    question: "What is the ideal speaking rate in words per minute?",
                    options: [
                        "100-120",
                        "120-150",
                        "150-180",
                        "180-200"
                    ],
                    correctAnswer: 1
                },
                {
                    id: 10,
                    type: "essay",
                    question: "Describe the key elements of an effective speech introduction and conclusion, and explain why each element is important.",
                    minWords: 100
                }
            ];
        }