// filepath: c:\Users\bjmba\STEM_Application\main\static\js\translation.js
// Translation dictionaries for each supported language
window.translations = {
    en: {
        profile: "Profile",
        subtitle: "Let's get to know you",
        myProfile: "My Profile",
        sessions: "Sessions",
        avgQuizScore: "Avg. Quiz Score",
        dayStreak: "Day Streak",
        points: "Points",
        saveProfile: "Save Profile",
        changePassword: "Change Password",
        deleteAccount: "Delete Account",
        firstName: "First Name",
        lastName: "Last Name",
        email: "Email",
        phone: "Phone",
        dob: "Date of Birth",
        gender: "Gender",
        bio: "Bio",
        school: "School",
        grade: "Grade",
        academicGoals: "Academic Goals",
        languagePref: "Language Preference",
        notificationPref: "Notification Preference",
        studyTimes: "Preferred Study Times",
        avatar: "Profile Picture",
        updateAvatar: "Update Profile Picture",
        stream: "Subject Stream",
        learningStyles: "Learning Styles",
        games: "Games",
        playGames: "Play Games",
        forum: "Forum",
        askQuestion: "Ask a Question",
        viewForum: "View Forum",
        courses: "Courses",
        browseCourses: "Browse Courses",
        classes: "Classes",
        joinClass: "Join Class",
        changePasswordTitle: "Change Your Password",
        oldPassword: "Old Password",
        newPassword: "New Password",
        confirmPassword: "Confirm Password",
        saveChanges: "Save Changes",
        cancel: "Cancel",
        backToDashboard: "Back to Dashboard",
        edit: "Edit",
        save: "Save",
        close: "Close",
        selectStream: "Select Stream",
        selectLearningStyle: "Select Learning Style",
        personalInfo: "Personal Info",
        academicInfo: "Academic Info",
        preferences: "Preferences",
        // ...Forum Keys Start Here:
        forum: "Forum",
        askQuestion: "Ask a Question",
        submitQuestion: "Submit Question",
        cancel: "Cancel",
        reply: "Reply",
        answers: "Answers",
        noQuestionsFound: "No questions found",
        noAnswersYet: "No answers yet. Be the first!",
        loading: "Loading…",
        member: "Member",
    },
    zu: {
        profile: "Iphrofayela",
        subtitle: "Ake sikwazi ngawe",
        myProfile: "Iphrofayela Yami",
        sessions: "Izifundo",
        avgQuizScore: "Isilinganiso Semiphumela Yezivivinyo",
        dayStreak: "Izinsuku Ezilandelanayo",
        points: "Amaphuzu",
        saveProfile: "Londoloza Iphrofayela",
        changePassword: "Shintsha Iphasiwedi",
        deleteAccount: "Susa I-akhawunti",
        firstName: "Igama",
        lastName: "Isibongo",
        email: "I-imeyili",
        phone: "Ucingo",
        dob: "Usuku Lokuzalwa",
        gender: "Ubulili",
        bio: "I-Bio",
        school: "Isikole",
        grade: "Ibanga",
        academicGoals: "Izinhloso Zokufunda",
        languagePref: "Ulimi Oluthandwayo",
        notificationPref: "Izaziso Ozithandayo",
        studyTimes: "Izikhathi Zokufunda",
        avatar: "Isithombe Sefrofayela",
        updateAvatar: "Buyekeza Isithombe Sefrofayela",
        stream: "Umkhakha Wesifundo",
        learningStyles: "Izindlela Zokufunda",
        games: "Imidlalo",
        playGames: "Dlala Imidlalo",
        forum: "Iforamu",
        askQuestion: "Buza Umbuzo",
        viewForum: "Buka Iforamu",
        courses: "Izifundo",
        browseCourses: "Hlola Izifundo",
        classes: "Amakilasi",
        joinClass: "Joyina Ikilasi",
        changePasswordTitle: "Shintsha Iphasiwedi Yakho",
        oldPassword: "Iphasiwedi Endala",
        newPassword: "Iphasiwedi Entsha",
        confirmPassword: "Qinisekisa Iphasiwedi",
        saveChanges: "Londoloza Izinguquko",
        cancel: "Khansela",
        backToDashboard: "Buyela KuDashboard",
        edit: "Hlela",
        save: "Londoloza",
        close: "Vala",
        selectStream: "Khetha Umkhakha",
        selectLearningStyle: "Khetha Indlela Yokufunda",
        personalInfo: "Ulwazi Lomuntu",
        academicInfo: "Ulwazi Lokufunda",
        preferences: "Okuthandwayo",
        // Zulu forum start here
            forum: "Iforamu",
        askQuestion: "Buza Umbuzo",
        submitQuestion: "Thumela Umbuzo",
        cancel: "Khansela",
        reply: "Phendula",
        answers: "Izimpendulo",
        noQuestionsFound: "Azikho imibuzo etholakele",
        noAnswersYet: "Azikho izimpendulo okwamanje. Yiba wokuqala!",
        loading: "Ilayisha…",
        member: "Ilungu",

        
    }
    // Add more languages here
};

window.applyTranslations = function(lang) {
    if (document.querySelector('h1')) document.querySelector('h1').textContent = window.translations[lang].profile;
    if (document.querySelector('.subtitle')) document.querySelector('.subtitle').textContent = window.translations[lang].subtitle;
    if (document.querySelector('.section-title')) document.querySelector('.section-title').textContent = window.translations[lang].myProfile;
    if (document.querySelector('#completedSessions')) document.querySelector('#completedSessions').nextElementSibling.textContent = window.translations[lang].sessions;
    if (document.querySelector('#quizScore')) document.querySelector('#quizScore').nextElementSibling.textContent = window.translations[lang].avgQuizScore;
    if (document.querySelector('#streakDays')) document.querySelector('#streakDays').nextElementSibling.textContent = window.translations[lang].dayStreak;
    if (document.querySelector('#pointsEarned')) document.querySelector('#pointsEarned').nextElementSibling.textContent = window.translations[lang].points;
    if (document.getElementById('saveProfileBtn')) document.getElementById('saveProfileBtn').innerHTML = `<i class="fas fa-save"></i> ${window.translations[lang].saveProfile}`;
    if (document.querySelector('a.btn-secondary.btn-small')) document.querySelector('a.btn-secondary.btn-small').innerHTML = `<i class="fas fa-key"></i> ${window.translations[lang].changePassword}`;
    if (document.getElementById('deleteAccountBtn')) document.getElementById('deleteAccountBtn').innerHTML = `<i class="fas fa-user-slash"></i> ${window.translations[lang].deleteAccount}`;
    if (document.getElementById('firstName')) document.getElementById('firstName').previousElementSibling.textContent = window.translations[lang].firstName;
    if (document.getElementById('lastName')) document.getElementById('lastName').previousElementSibling.textContent = window.translations[lang].lastName;
    if (document.getElementById('email')) document.getElementById('email').previousElementSibling.textContent = window.translations[lang].email;
    if (document.getElementById('phone')) document.getElementById('phone').previousElementSibling.textContent = window.translations[lang].phone;
    if (document.getElementById('dob')) document.getElementById('dob').previousElementSibling.textContent = window.translations[lang].dob;
    if (document.getElementById('gender')) document.getElementById('gender').previousElementSibling.textContent = window.translations[lang].gender;
    if (document.getElementById('bio')) document.getElementById('bio').previousElementSibling.textContent = window.translations[lang].bio;
    if (document.getElementById('school')) document.getElementById('school').previousElementSibling.textContent = window.translations[lang].school;
    if (document.getElementById('grade')) document.getElementById('grade').previousElementSibling.textContent = window.translations[lang].grade;
    if (document.getElementById('academicGoals')) document.getElementById('academicGoals').previousElementSibling.textContent = window.translations[lang].academicGoals;
    if (document.getElementById('languagePref')) document.getElementById('languagePref').previousElementSibling.textContent = window.translations[lang].languagePref;
    if (document.getElementById('notificationPref')) document.getElementById('notificationPref').previousElementSibling.textContent = window.translations[lang].notificationPref;
    if (document.getElementById('studyTimes')) document.getElementById('studyTimes').previousElementSibling.textContent = window.translations[lang].studyTimes;
    if (document.querySelector('.profile-avatar')) document.querySelector('.profile-avatar').title = window.translations[lang].avatar;
    if (document.querySelector('.profile-avatar-edit')) document.querySelector('.profile-avatar-edit').title = window.translations[lang].updateAvatar;
    if (document.querySelector('.stream-title')) document.querySelector('.stream-title').textContent = window.translations[lang].stream;
    if (document.querySelector('.learning-styles-title')) document.querySelector('.learning-styles-title').textContent = window.translations[lang].learningStyles;
    if (document.getElementById('gamesSection')) document.getElementById('gamesSection').textContent = window.translations[lang].games;
    if (document.getElementById('playGamesBtn')) document.getElementById('playGamesBtn').textContent = window.translations[lang].playGames;
    if (document.getElementById('forumSection')) document.getElementById('forumSection').textContent = window.translations[lang].forum;
    if (document.getElementById('askQuestionBtn')) document.getElementById('askQuestionBtn').textContent = window.translations[lang].askQuestion;
    if (document.getElementById('viewForumBtn')) document.getElementById('viewForumBtn').textContent = window.translations[lang].viewForum;
    if (document.getElementById('coursesSection')) document.getElementById('coursesSection').textContent = window.translations[lang].courses;
    if (document.getElementById('browseCoursesBtn')) document.getElementById('browseCoursesBtn').textContent = window.translations[lang].browseCourses;
    if (document.getElementById('classesSection')) document.getElementById('classesSection').textContent = window.translations[lang].classes;
    if (document.getElementById('joinClassBtn')) document.getElementById('joinClassBtn').textContent = window.translations[lang].joinClass;
    if (document.getElementById('changePasswordTitle')) document.getElementById('changePasswordTitle').textContent = window.translations[lang].changePasswordTitle;
    if (document.getElementById('oldPassword')) document.getElementById('oldPassword').previousElementSibling.textContent = window.translations[lang].oldPassword;
    if (document.getElementById('newPassword')) document.getElementById('newPassword').previousElementSibling.textContent = window.translations[lang].newPassword;
    if (document.getElementById('confirmPassword')) document.getElementById('confirmPassword').previousElementSibling.textContent = window.translations[lang].confirmPassword;
    if (document.getElementById('saveChangesBtn')) document.getElementById('saveChangesBtn').textContent = window.translations[lang].saveChanges;
    if (document.getElementById('cancelBtn')) document.getElementById('cancelBtn').textContent = window.translations[lang].cancel;
    if (document.querySelector('.back-to-dashboard')) document.querySelector('.back-to-dashboard').textContent = window.translations[lang].backToDashboard;
    
     if (document.getElementById('personalinfoTab')) document.getElementById('personalinfoTab').textContent = window.translations[lang].personalInfo;
    if (document.getElementById('academicinfoTab')) document.getElementById('academicinfoTab').textContent = window.translations[lang].academicInfo;
    if (document.getElementById('preferencesTab')) document.getElementById('preferencesTab').textContent = window.translations[lang].preferences;
    // ...update more elements as needed
}

// Function to handle language toggle
window.setupLanguageToggle = function() {
    const languageToggleBtns = document.querySelectorAll('.language-toggle-btn');
    languageToggleBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            languageToggleBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const lang = this.dataset.lang;
            // Save language preference
            localStorage.setItem('preferredLanguage', lang);
            window.applyTranslations(lang);
        });
    });
};