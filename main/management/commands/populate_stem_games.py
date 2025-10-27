from django.core.management.base import BaseCommand
from main.models import Game, GameQuestion
from main.models.user import CustomUser  # Use your custom user model
from django.contrib.auth import get_user_model

User = get_user_model()  # This automatically gets the correct user model

class Command(BaseCommand):
    help = 'Populate database with STEM-based quiz games'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing STEM games before adding new ones',
        )

    def handle(self, *args, **options):
        # Get admin user using the correct User model
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(
                self.style.ERROR('❌ No admin user found. Create one first with: python manage.py createsuperuser')
            )
            return

        # Clear existing games if requested
        if options['clear']:
            Game.objects.filter(category='stem').delete()
            self.stdout.write(self.style.WARNING('🗑️ Cleared existing STEM games'))

        # STEM Games data (matching your Game model exactly)
        games_data = [
            {
                'title': 'Advanced Algebra Quiz',
                'description': 'Test your knowledge of quadratic equations, polynomials, and algebraic functions',
                'category': 'stem',
                'difficulty': 'medium',
                'duration_minutes': 20,
                'max_points': 100,
                'questions': [
                    {
                        'order': 1,
                        'qtype': 'multiple-choice',
                        'question': 'What is the discriminant of the quadratic equation 2x² + 5x - 3 = 0?',
                        'options': ['49', '25', '1', '-23'],
                        'correct_answer': 0
                    },
                    {
                        'order': 2,
                        'qtype': 'calculation',
                        'question': 'Solve for x: 3x + 7 = 22',
                        'correct_answer': '5'
                    },
                    {
                        'order': 3,
                        'qtype': 'true-false',
                        'question': 'The graph of y = x² - 4x + 4 has its vertex at (2, 0)',
                        'correct_answer': True
                    },
                    {
                        'order': 4,
                        'qtype': 'fill-blank',
                        'question': 'The factored form of x² - 9 is (x + 3)(x - ___)',
                        'correct_answer': '3'
                    }
                ]
            },
            {
                'title': 'Physics: Motion and Forces',
                'description': 'Explore Newton\'s laws, kinematics, and dynamics',
                'category': 'stem',
                'difficulty': 'hard',
                'duration_minutes': 25,
                'max_points': 120,
                'questions': [
                    {
                        'order': 1,
                        'qtype': 'multiple-choice',
                        'question': 'What is Newton\'s second law of motion?',
                        'options': ['F = ma', 'F = mv', 'F = m/a', 'F = ma²'],
                        'correct_answer': 0
                    },
                    {
                        'order': 2,
                        'qtype': 'calculation',
                        'question': 'A car accelerates from 0 to 60 m/s in 10 seconds. What is its acceleration? (answer in m/s²)',
                        'correct_answer': '6'
                    },
                    {
                        'order': 3,
                        'qtype': 'matching',
                        'question': 'Match the physics quantities with their units:',
                        'left_items': ['Force', 'Energy', 'Power', 'Velocity'],
                        'right_items': ['Watts', 'Joules', 'Newtons', 'm/s'],
                        'correct_matches': [[0, 2], [1, 1], [2, 0], [3, 3]]
                    },
                    {
                        'order': 4,
                        'qtype': 'true-false',
                        'question': 'An object at rest will stay at rest unless acted upon by an external force (Newton\'s 1st Law)',
                        'correct_answer': True
                    }
                ]
            },
            {
                'title': 'Organic Chemistry Fundamentals',
                'description': 'Test your knowledge of organic compounds, reactions, and structures',
                'category': 'stem',
                'difficulty': 'medium',
                'duration_minutes': 30,
                'max_points': 150,
                'questions': [
                    {
                        'order': 1,
                        'qtype': 'multiple-choice',
                        'question': 'What is the molecular formula for methane?',
                        'options': ['CH₄', 'C₂H₆', 'C₃H₈', 'CH₂'],
                        'correct_answer': 0
                    },
                    {
                        'order': 2,
                        'qtype': 'fill-blank',
                        'question': 'The process of converting alkenes to alkanes is called ___________',
                        'correct_answer': 'hydrogenation'
                    },
                    {
                        'order': 3,
                        'qtype': 'true-false',
                        'question': 'Benzene has a ring structure with alternating single and double bonds',
                        'correct_answer': False
                    },
                    {
                        'order': 4,
                        'qtype': 'case-study',
                        'question': 'A student burns 2.0g of methane (CH₄) completely. How many moles of CO₂ are produced?',
                        'options': ['0.125 mol', '0.25 mol', '0.5 mol', '1.0 mol'],
                        'correct_answer': 0
                    }
                ]
            },
            {
                'title': 'Biology: Cell Structure & Function',
                'description': 'Test your knowledge of cell organelles and their functions',
                'category': 'stem',
                'difficulty': 'easy',
                'duration_minutes': 15,
                'max_points': 80,
                'questions': [
                    {
                        'order': 1,
                        'qtype': 'multiple-choice',
                        'question': 'Which organelle is known as the powerhouse of the cell?',
                        'options': ['Nucleus', 'Mitochondria', 'Ribosome', 'Golgi apparatus'],
                        'correct_answer': 1
                    },
                    {
                        'order': 2,
                        'qtype': 'true-false',
                        'question': 'Plant cells have cell walls, but animal cells do not',
                        'correct_answer': True
                    },
                    {
                        'order': 3,
                        'qtype': 'fill-blank',
                        'question': 'The _______ controls what enters and exits the cell',
                        'correct_answer': 'cell membrane'
                    },
                    {
                        'order': 4,
                        'qtype': 'matching',
                        'question': 'Match the organelle with its function:',
                        'left_items': ['Nucleus', 'Ribosomes', 'Vacuole', 'Chloroplast'],
                        'right_items': ['Photosynthesis', 'Storage', 'Protein synthesis', 'Controls cell'],
                        'correct_matches': [[0, 3], [1, 2], [2, 1], [3, 0]]
                    }
                ]
            },
            {
                'title': 'Engineering: Circuits & Electricity',
                'description': 'Explore electrical circuits, current, voltage, and resistance',
                'category': 'stem',
                'difficulty': 'hard',
                'duration_minutes': 35,
                'max_points': 200,
                'questions': [
                    {
                        'order': 1,
                        'qtype': 'multiple-choice',
                        'question': 'What is Ohm\'s Law?',
                        'options': ['V = IR', 'V = I/R', 'V = I + R', 'V = I - R'],
                        'correct_answer': 0
                    },
                    {
                        'order': 2,
                        'qtype': 'calculation',
                        'question': 'Calculate the current when voltage is 12V and resistance is 4Ω (answer in Amperes)',
                        'correct_answer': '3'
                    },
                    {
                        'order': 3,
                        'qtype': 'case-study',
                        'question': 'In a series circuit with 3 resistors (2Ω, 3Ω, 5Ω), what is the total resistance?',
                        'options': ['10Ω', '0.95Ω', '3.33Ω', '30Ω'],
                        'correct_answer': 0
                    },
                    {
                        'order': 4,
                        'qtype': 'true-false',
                        'question': 'In a parallel circuit, voltage is the same across all branches',
                        'correct_answer': True
                    }
                ]
            },
            {
                'title': 'Computer Science: Algorithms & Data Structures',
                'description': 'Basic algorithms, data structures, and computational thinking',
                'category': 'stem',
                'difficulty': 'medium',
                'duration_minutes': 25,
                'max_points': 120,
                'questions': [
                    {
                        'order': 1,
                        'qtype': 'multiple-choice',
                        'question': 'What is the time complexity of binary search?',
                        'options': ['O(n)', 'O(log n)', 'O(n²)', 'O(1)'],
                        'correct_answer': 1
                    },
                    {
                        'order': 2,
                        'qtype': 'matching',
                        'question': 'Match the data structure with its use case:',
                        'left_items': ['Stack', 'Queue', 'Array', 'Hash Table'],
                        'right_items': ['Random access', 'Key-value lookup', 'LIFO operations', 'FIFO operations'],
                        'correct_matches': [[0, 2], [1, 3], [2, 0], [3, 1]]
                    },
                    {
                        'order': 3,
                        'qtype': 'true-false',
                        'question': 'A recursive function must have a base case to avoid infinite recursion',
                        'correct_answer': True
                    },
                    {
                        'order': 4,
                        'qtype': 'fill-blank',
                        'question': 'The worst-case time complexity of quicksort is O(___)',
                        'correct_answer': 'n²'
                    }
                ]
            }
        ]

        # Create games and questions
        created_count = 0
        for game_data in games_data:
            # Extract questions data
            questions_data = game_data.pop('questions')
            
            # Create game
            game = Game.objects.create(
                **game_data,
                is_active=True,
                created_by=admin_user
            )

            # Create questions
            for q_data in questions_data:
                GameQuestion.objects.create(game=game, **q_data)

            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created "{game.title}" with {len(questions_data)} questions')
            )

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Successfully created {created_count} STEM quiz games!')
        )
        
        # Show summary
        self.stdout.write('\n📊 Summary:')
        for category in ['easy', 'medium', 'hard']:
            count = Game.objects.filter(category='stem', difficulty=category).count()
            if count > 0:
                self.stdout.write(f'   {category.title()}: {count} games')
        
        total_questions = sum(game.questions.count() for game in Game.objects.filter(category='stem'))
        self.stdout.write(f'   Total questions: {total_questions}')