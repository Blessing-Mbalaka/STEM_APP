from django.core.management.base import BaseCommand
from main.models import Course, CourseResource, Game
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with STEM courses and resources (Mindset Physics content)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing STEM courses before adding new ones',
        )

    def handle(self, *args, **options):
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('❌ No admin user found. Create one first.'))
            return

        if options['clear']:
            Course.objects.filter(classification='STEM', subject='Physics').delete()
            self.stdout.write(self.style.WARNING('🗑️ Cleared existing STEM Physics courses'))

        # Use a single “Physics: Mechanics & Electrodynamics” course (you could break it into units if you prefer)
        course_data = {
            'title': 'Physics (Physical Sciences) – Grade 12 (Mindset Learn)',
            'summary': 'Structured Mindset Learn / LearnXtra video series covering mechanics, energy, waves, fields, electricity, etc.',
            'description': (
                'This course organizes Mindset Learn / LearnXtra / Learn Xtra video content aligned with Grade 12 Physical Sciences. '
                'Topics include motion, forces, energy, momentum, waves, electricity and magnetism, and related exam practice.'
            ),
            'subject': 'Physics',
            'classification': 'STEM',
            'level': 'advanced',
            'is_active': True,
            # below we’ll fill resources
        }

        resources_data = [
            {
                'title': 'Learn Xtra Live – Motion (Whole Show)',
                'description': 'Live broadcast on mechanics / motion (Learn Xtra / Mindset) – overview',
                'resource_type': 'youtube',
                'url': 'https://www.youtube.com/playlist?list=PLOaNAKtW5HLQKYasZKPZSuXssMfM5pspL',  # Motion etc playlist
                'learning_style': 'visual',
                'position': 1
            },
            {
                'title': 'Vertical Projectile Motion (Mindset / LearnXtra)',
                'description': 'Video on vertical projectile motion (displacement, velocity, acceleration graphs)',
                'resource_type': 'youtube',
                'url': 'https://www.youtube.com/watch?v=fQ1qK5pkOws',
                'learning_style': 'visual',
                'position': 2
            },
            {
                'title': 'Work, Energy & Power (Grade 11 & 12)',
                'description': 'Covers work, energy, power relationships, conservative vs nonconservative forces',
                'resource_type': 'youtube',
                'url': 'https://www.youtube.com/watch?v=N9_aOJKdjq0',
                'learning_style': 'visual',
                'position': 3
            },
            {
                'title': 'Work done by Non-Conservative Forces – Practice',
                'description': 'Worked example for work done by nonconservative forces',
                'resource_type': 'youtube',
                'url': 'https://www.youtube.com/watch?v=5mhEvh5kG90',
                'learning_style': 'visual',
                'position': 4
            },
            {
                'title': 'Momentum & Impulse (Mindset / LearnXtra)',
                'description': 'Impulse, momentum conservation, collisions',
                'resource_type': 'youtube',
                'url': 'https://www.youtube.com/watch?v=GrjMbTN_DVU',
                'learning_style': 'visual',
                'position': 5
            },
            {
                'title': 'Gr 12 Physics: Term 1 Revision (Mindset)',
                'description': 'Revision of mechanics & kinematics topics – exam style questions',
                'resource_type': 'youtube',
                'url': 'https://www.youtube.com/watch?v=T2DWu6uIL3o',
                'learning_style': 'visual',
                'position': 6
            },
            {
                'title': 'Electronics / Basics (New curriculum physics Unit 5)',
                'description': 'Introduction to electronics / circuits (currents, voltages) – for Grade 12 physics',
                'resource_type': 'youtube',
                'url': 'https://www.youtube.com/watch?v=Mu00LxeuH64',
                'learning_style': 'visual',
                'position': 7
            },
            {
                'title': 'Meter Bridge / Current Electricity',
                'description': 'Construction & working of meter bridge and principles of current electricity',
                'resource_type': 'youtube',
                'url': 'https://www.youtube.com/watch?v=GFsvaCnLtzA',
                'learning_style': 'visual',
                'position': 8
            },
            {
                'title': 'Physics Exam Questions – Mindset / LearnXtra (Mechanics Section)',
                'description': 'Worked exam questions on mechanics & motion',
                'resource_type': 'youtube',
                'url': 'https://www.youtube.com/watch?v=tEV7O8ojZ6Y',
                'learning_style': 'visual',
                'position': 9
            },
            {
                'title': 'Physics: Mechanics & Motion Quiz',
                'description': 'Quiz / assessment on kinematics, forces, energy, momentum',
                'resource_type': 'quiz',
                'learning_style': 'readwrite',
                'position': 10,
                'game_link': 'Physics: Mechanics & Motion Quiz'
            }
        ]

        # Create course
        course = Course.objects.create(
            **course_data,
            created_by=admin_user
        )

        # Add resources
        for res in resources_data:
            game_link = res.pop('game_link', None)
            game = None
            if game_link:
                try:
                    game = Game.objects.get(title=game_link)
                except Game.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'⚠️ Game "{game_link}" not found for resource "{res.get("title")}"'))
            CourseResource.objects.create(
                course=course,
                game=game,
                **res
            )

        self.stdout.write(self.style.SUCCESS(f'✅ Created course "{course.title}" with {len(resources_data)} resources.'))
