from main.models.game import Game, GameQuestion

print("Games in DB:")
for g in Game.objects.all():
    print(f"ID: {g.id}, Title: {g.title}, Slug: {g.slug}, Duration: {getattr(g, 'duration_minutes', None)}")
    questions = g.questions.all()
    print(f"  Questions: {questions.count()}")
    for q in questions:
        print(f"    Q{q.order}: {q.qtype} - {q.question}")

if not Game.objects.exists():
    print("No games found. Add some quizzes!")
