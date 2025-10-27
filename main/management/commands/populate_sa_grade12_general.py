from django.core.management.base import BaseCommand
from main.models import Course, CourseResource
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate South African Grade 12 General subjects (NSC curriculum) with YouTube resources'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true')
        parser.add_argument(
            '--subjects',
            nargs='*',
            choices=['english', 'afrikaans', 'history', 'geography', 'business', 'economics', 'lol']
        )

    def handle(self, *args, **options):
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('❌ No admin user found. Create one first.'))
            return

        if options['clear']:
            Course.objects.filter(classification='General').delete()
            self.stdout.write(self.style.WARNING('🗑️ Cleared existing “General” courses'))

        # Metadata for courses
        sa_general_courses = {
            'english': {
                'title': 'English Home Language Grade 12 (NSC)',
                'summary': 'Advanced English literature, poetry, drama, and language skills',
                'description': (
                    'NSC English curriculum covering prescribed literature, poetry analysis, drama studies, '
                    'and advanced writing and comprehension skills.'
                ),
                'subject': 'English',
                'classification': 'General',
                'level': 'advanced',
                'resources': [
                    {
                        'title': 'Mindset Learn – English Literature / Poetry Live Show',
                        'description': 'Live show episodes on literature and poetry analysis',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/playlist?list=PL…',  # replace with actual playlist
                        'learning_style': 'visual',
                        'position': 1
                    },
                    {
                        'title': 'English Home Language – Essay Writing (Mindset)',
                        'description': 'Tips & strategies for NSC English essay writing',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/watch?v=…',  # placeholder
                        'learning_style': 'visual',
                        'position': 2
                    }
                ]
            },
            'afrikaans': {
                'title': 'Afrikaans Huistaal Graad 12 (NSC)',
                'summary': 'Gevorderde Afrikaanse letterkunde, poësie, drama en taalvaardighede',
                'description': (
                    'NSS Afrikaans kurrikulum wat voorgeskrewe letterkunde, poësie-analise, dramastudies, '
                    'en gevorderde taalvaardighede dek.'
                ),
                'subject': 'Afrikaans',
                'classification': 'General',
                'level': 'advanced',
                'resources': [
                    {
                        'title': 'Afrikaans Huistaal – Poësie Analise (Mindset)',
                        'description': 'Analise van gedigte volgens NSC kriteria',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/watch?v=…',  # placeholder
                        'learning_style': 'visual',
                        'position': 1
                    }
                ]
            },
            'history': {
                'title': 'History Grade 12 (NSC)',
                'summary': 'South African and world history — apartheid, independence, Cold War',
                'description': (
                    'NSC History covering South African history (apartheid era, liberation struggle), '
                    'African independence movements, Cold War dynamics, and global interconnections.'
                ),
                'subject': 'History',
                'classification': 'General',
                'level': 'intermediate',
                'resources': [
                    {
                        'title': 'History Grade 12 Live – Mindset Learn',
                        'description': 'Live show episodes on history topics for NSC',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/playlist?list=PL…',  # replace with actual playlist
                        'learning_style': 'visual',
                        'position': 1
                    },
                    {
                        'title': 'History Grade 11 / 12 – Context & Themes Review',
                        'description': 'Overview of major historical themes (useful as bridging content)',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/watch?v=6c2qeSC_CJg',  # sample video from “History Grade 11 : Revision” :contentReference[oaicite:0]{index=0}
                        'learning_style': 'visual',
                        'position': 2
                    }
                ]
            },
            'geography': {
                'title': 'Geography Grade 12 (NSC)',
                'summary': 'Physical & human geography – climate, urban development, sustainability',
                'description': (
                    'NSC Geography covering climate and weather systems, geomorphology, settlement dynamics, '
                    'and sustainable development.'
                ),
                'subject': 'Geography',
                'classification': 'General',
                'level': 'intermediate',
                'resources': [
                    {
                        'title': 'Geography Grade 12 – Geomorphology & Climatology (Live)',
                        'description': 'Mindset Live show on physical geography topics',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/watch?v=KUtWby1bPzE',  # sample video :contentReference[oaicite:1]{index=1}
                        'learning_style': 'visual',
                        'position': 1
                    }
                ]
            },
            'business': {
                'title': 'Business Studies Grade 12 (NSC)',
                'summary': 'Business management, entrepreneurship, corporate responsibility',
                'description': (
                    'NSC Business Studies covering business environments, business functions, entrepreneurship, '
                    'and contemporary business issues.'
                ),
                'subject': 'Business Studies',
                'classification': 'General',
                'level': 'intermediate',
                'resources': [
                    {
                        'title': 'Gr 12 Business Studies: Business Management (Live)',
                        'description': 'Mindset Live show on business management functions',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/watch?v=6nBe3EoeOA0',  # sample video :contentReference[oaicite:2]{index=2}
                        'learning_style': 'visual',
                        'position': 1
                    }
                ]
            },
            'economics': {
                'title': 'Economics Grade 12 (NSC)',
                'summary': 'Macroeconomics, microeconomics, and SA economic issues',
                'description': (
                    'NSC Economics covering economic systems, market dynamics, government intervention, '
                    'economic development, and South African case studies.'
                ),
                'subject': 'Economics',
                'classification': 'General',
                'level': 'intermediate',
                'resources': [
                    {
                        'title': 'Gr 12 Economics: Macro & Micro (Live)',
                        'description': 'Mindset Live show on macro- and microeconomics',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/watch?v=8Y01Wpm2KcA',  # sample video :contentReference[oaicite:3]{index=3}
                        'learning_style': 'visual',
                        'position': 1
                    },
                    {
                        'title': 'Gr 12 Economics: Exam Questions Live',
                        'description': 'Worked exam questions for Economics NSC',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/watch?v=c-LKNUdqyc4',  # sample video :contentReference[oaicite:4]{index=4}
                        'learning_style': 'visual',
                        'position': 2
                    }
                ]
            },
            'lol': {
                'title': 'Life Orientation Grade 12 (NSC)',
                'summary': 'Personal development, careers, citizenship, health education',
                'description': (
                    'NSC Life Orientation focusing on personal well-being, career planning, citizenship, '
                    'and life skills.'
                ),
                'subject': 'Life Orientation',
                'classification': 'General',
                'level': 'intro',
                'resources': [
                    {
                        'title': 'Life Orientation – Study / Learning Styles (Grade 8-12)',
                        'description': 'Video covering study skills, learning styles relevant for LO',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/watch?v=d67d8DkBU2c',  # sample video :contentReference[oaicite:5]{index=5}
                        'learning_style': 'visual',
                        'position': 1
                    }
                ]
            }
        }

        subjects_to_create = options['subjects'] or sa_general_courses.keys()
        created_count = 0

        for subject_key in subjects_to_create:
            data = sa_general_courses.get(subject_key)
            if not data:
                continue

            resources = data.pop('resources', [])
            course = Course.objects.create(
                **data,
                is_active=True,
                created_by=admin_user
            )

            for res in resources:
                CourseResource.objects.create(
                    course=course,
                    **res
                )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'✅ Created "{course.title}" with {len(resources)} resources'))

        self.stdout.write(self.style.SUCCESS(f'\n🎉 Successfully created {created_count} General courses!'))
