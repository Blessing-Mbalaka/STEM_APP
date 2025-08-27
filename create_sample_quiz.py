from main.models.game import Game, GameQuestion

# Create a sample game (quiz)
game = Game.objects.create(
    title="Calculus Fundamentals Quiz",
    slug="calculus-fundamentals",
    duration_minutes=15,
    points=10
)

# Add sample questions
GameQuestion.objects.create(
    game=game,
    order=1,
    qtype="multiple-choice",
    question="What is the derivative of f(x) = 3x² + 2x - 5?",
    options=["6x + 2", "3x + 2", "6x² + 2", "3x² + 2x"],
    correct_answer=0
)
GameQuestion.objects.create(
    game=game,
    order=2,
    qtype="true-false",
    question="The integral of a function represents the area under its curve.",
    correct_answer=True
)
GameQuestion.objects.create(
    game=game,
    order=3,
    qtype="fill-blank",
    question="The limit as x approaches 0 of (sin x)/x is __________.",
    correct_answer="1"
)
# Add more questions as needed...

print("Sample quiz and questions created!")
