from main.models.game import Game, GameQuestion

# Create several sample quizzes
quizzes = [
    {
        "title": "Calculus Fundamentals Quiz",
        "slug": "calculus-fundamentals",
        "duration_minutes": 15,
        "points": 10,
        "questions": [
            {
                "order": 1,
                "qtype": "multiple-choice",
                "question": "What is the derivative of f(x) = 3x² + 2x - 5?",
                "options": ["6x + 2", "3x + 2", "6x² + 2", "3x² + 2x"],
                "correct_answer": 0
            },
            {
                "order": 2,
                "qtype": "true-false",
                "question": "The integral of a function represents the area under its curve.",
                "correct_answer": True
            },
            {
                "order": 3,
                "qtype": "fill-blank",
                "question": "The limit as x approaches 0 of (sin x)/x is __________.",
                "correct_answer": "1"
            }
        ]
    },
    {
        "title": "Newtonian Physics Quiz",
        "slug": "newtonian-physics",
        "duration_minutes": 15,
        "points": 10,
        "questions": [
            {
                "order": 1,
                "qtype": "multiple-choice",
                "question": "Which of Newton's Laws states that F = ma?",
                "options": ["First Law", "Second Law", "Third Law", "Law of Gravitation"],
                "correct_answer": 1
            },
            {
                "order": 2,
                "qtype": "true-false",
                "question": "In the absence of air resistance, all objects fall with the same acceleration.",
                "correct_answer": True
            },
            {
                "order": 3,
                "qtype": "fill-blank",
                "question": "The SI unit of force is the __________.",
                "correct_answer": "newton"
            }
        ]
    }
]

for quiz in quizzes:
    game = Game.objects.create(
        title=quiz["title"],
        slug=quiz["slug"],
        duration_minutes=quiz["duration_minutes"],
        points=quiz["points"],
        category=quiz.get("category", "STEM"),
        difficulty=quiz.get("difficulty", "Medium"),
        is_active=True
    )
    for q in quiz["questions"]:
        GameQuestion.objects.create(
            game=game,
            order=q["order"],
            qtype=q["qtype"],
            question=q["question"],
            options=q.get("options"),
            correct_answer=q["correct_answer"]
        )
print("Sample quizzes and questions created!")
