from main.models.game import Game

print("Games in DB:")
for g in Game.objects.all():
    print(f"ID: {g.id}, Title: {g.title}, is_active: {getattr(g, 'is_active', None)}")

if not Game.objects.exists():
    print("No games found. Add some quizzes!")