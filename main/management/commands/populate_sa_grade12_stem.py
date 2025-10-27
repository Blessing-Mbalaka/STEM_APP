from django.core.management.base import BaseCommand
from main.models import Course, CourseResource, Game
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate South African Grade 12 STEM subjects (NSC curriculum)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing Grade 12 STEM courses',
        )
        parser.add_argument(
            '--subjects',
            nargs='*',
            help='Specific subjects to create (default: all)',
            choices=['mathematics', 'physical_sciences', 'life_sciences', 'it', 'engineering', 'accounting']
        )

    def handle(self, *args, **options):
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('❌ No admin user found.'))
            return

        if options['clear']:
            Course.objects.filter(classification='STEM', subject__in=[
                'Mathematics', 'Physical Sciences', 'Life Sciences', 
                'Information Technology', 'Engineering Graphics & Design', 'Accounting'
            ]).delete()
            self.stdout.write(self.style.WARNING('🗑️ Cleared Grade 12 STEM courses'))

        # South African Grade 12 STEM Courses (NSC Curriculum)
        sa_stem_courses = {
            'mathematics': {
                'title': 'Mathematics Grade 12 (NSC)',
                'summary': 'South African Grade 12 Mathematics covering calculus, trigonometry, and analytical geometry',
                'description': 'Comprehensive NSC Mathematics curriculum including differential calculus, trigonometry, analytical geometry, statistics, and probability. Prepares students for university mathematics.',
                'subject': 'Mathematics',
                'classification': 'STEM',
                'level': 'advanced',
                'resources': [
                    {
                        'title': 'Calculus Introduction - Derivatives',
                        'description': 'NSC Grade 12 calculus concepts and applications',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/watch?v=calculus_sa',
                        'learning_style': 'visual',
                        'position': 1
                    },
                    {
                        'title': 'Trigonometry Compound Angles',
                        'description': 'Advanced trigonometric identities and proofs',
                        'resource_type': 'document',
                        'learning_style': 'readwrite',
                        'position': 2
                    },
                    {
                        'title': 'Analytical Geometry Practice',
                        'description': 'Circle geometry and coordinate geometry problems',
                        'resource_type': 'link',
                        'url': 'https://www.mindset.africa/learn/grade-12-mathematics',
                        'learning_style': 'visual',
                        'position': 3
                    },
                    {
                        'title': 'NSC Mathematics Mock Exam',
                        'description': 'Practice exam following DBE format',
                        'resource_type': 'quiz',
                        'learning_style': 'readwrite',
                        'position': 4
                    }
                ]
            },
            'physical_sciences': {
                'title': 'Physical Sciences Grade 12 (NSC)',
                'summary': 'Physics and Chemistry combined - mechanics, waves, organic chemistry, and electrochemistry',
                'description': 'NSC Physical Sciences covering Physics (mechanics, waves, electricity) and Chemistry (organic chemistry, chemical equilibrium, electrochemistry). Essential for engineering and science careers.',
                'subject': 'Physical Sciences',
                'classification': 'STEM',
                'level': 'advanced',
                'resources': [
                    {
                        'title': 'Newton\'s Laws & Momentum',
                        'description': 'Grade 12 Physics mechanics concepts',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/watch?v=physics_mechanics',
                        'learning_style': 'visual',
                        'position': 1
                    },
                    {
                        'title': 'Organic Chemistry Reactions',
                        'description': 'Addition, substitution, and elimination reactions',
                        'resource_type': 'document',
                        'learning_style': 'readwrite',
                        'position': 2
                    },
                    {
                        'title': 'Waves and Sound Simulation',
                        'description': 'Interactive wave properties demonstration',
                        'resource_type': 'link',
                        'url': 'https://phet.colorado.edu/en/simulation/wave-on-a-string',
                        'learning_style': 'visual',
                        'position': 3
                    },
                    {
                        'title': 'Physical Sciences Quiz',
                        'description': 'Combined Physics and Chemistry assessment',
                        'resource_type': 'quiz',
                        'learning_style': 'visual',
                        'position': 4,
                        'game_link': 'Physics: Motion and Forces'
                    }
                ]
            },
            'life_sciences': {
                'title': 'Life Sciences Grade 12 (NSC)',
                'summary': 'Biology covering genetics, evolution, human physiology, and ecology',
                'description': 'NSC Life Sciences curriculum including molecular genetics, evolution, human reproductive system, nervous system, and environmental studies. Foundation for medical and biological sciences.',
                'subject': 'Life Sciences',
                'classification': 'STEM',
                'level': 'intermediate',
                'resources': [
                    {
                        'title': 'DNA & RNA Structure',
                        'description': 'Molecular basis of genetics and protein synthesis',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/watch?v=dna_structure',
                        'learning_style': 'visual',
                        'position': 1
                    },
                    {
                        'title': 'Human Reproductive System',
                        'description': 'Anatomy and physiology of reproduction',
                        'resource_type': 'document',
                        'learning_style': 'readwrite',
                        'position': 2
                    },
                    {
                        'title': 'Evolution Evidence',
                        'description': 'Fossil records and natural selection examples',
                        'resource_type': 'link',
                        'url': 'https://www.biointeractive.org/',
                        'learning_style': 'visual',
                        'position': 3
                    },
                    {
                        'title': 'Life Sciences Assessment',
                        'description': 'Genetics and evolution quiz',
                        'resource_type': 'quiz',
                        'learning_style': 'readwrite',
                        'position': 4,
                        'game_link': 'Biology: Cell Structure & Function'
                    }
                ]
            },
            'it': {
                'title': 'Information Technology Grade 12 (NSC)',
                'summary': 'Programming, databases, networking, and digital solutions',
                'description': 'NSC IT curriculum covering programming concepts, database design, networking fundamentals, and digital solutions. Includes practical programming projects and system analysis.',
                'subject': 'Information Technology',
                'classification': 'STEM',
                'level': 'intermediate',
                'resources': [
                    {
                        'title': 'Delphi Programming Basics',
                        'description': 'Introduction to Delphi programming language',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/watch?v=delphi_basics',
                        'learning_style': 'visual',
                        'position': 1
                    },
                    {
                        'title': 'Database Design Principles',
                        'description': 'ERD and normalization concepts',
                        'resource_type': 'document',
                        'learning_style': 'readwrite',
                        'position': 2
                    },
                    {
                        'title': 'Networking Fundamentals',
                        'description': 'TCP/IP, protocols, and network topologies',
                        'resource_type': 'link',
                        'url': 'https://www.cisco.com/c/en/us/solutions/small-business/resource-center/networking/networking-basics.html',
                        'learning_style': 'readwrite',
                        'position': 3
                    },
                    {
                        'title': 'IT Programming Quiz',
                        'description': 'Test programming and database concepts',
                        'resource_type': 'quiz',
                        'learning_style': 'readwrite',
                        'position': 4,
                        'game_link': 'Computer Science: Algorithms & Data Structures'
                    }
                ]
            },
            'engineering': {
                'title': 'Engineering Graphics & Design Grade 12 (NSC)',
                'summary': 'Technical drawing, CAD, and engineering design principles',
                'description': 'NSC EGD covering orthographic projection, isometric drawing, CAD software, civil and mechanical engineering drawings. Develops spatial visualization and technical communication skills.',
                'subject': 'Engineering Graphics & Design',
                'classification': 'STEM',
                'level': 'intermediate',
                'resources': [
                    {
                        'title': 'Orthographic Projection Tutorial',
                        'description': 'First and third angle projection methods',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/watch?v=orthographic_projection',
                        'learning_style': 'visual',
                        'position': 1
                    },
                    {
                        'title': 'Isometric Drawing Guide',
                        'description': 'Step-by-step isometric construction',
                        'resource_type': 'document',
                        'learning_style': 'visual',
                        'position': 2
                    },
                    {
                        'title': 'CAD Software Practice',
                        'description': 'Free CAD tools for technical drawing',
                        'resource_type': 'link',
                        'url': 'https://www.freecadweb.org/',
                        'learning_style': 'visual',
                        'position': 3
                    },
                    {
                        'title': 'Engineering Design Quiz',
                        'description': 'Technical drawing and design principles',
                        'resource_type': 'quiz',
                        'learning_style': 'visual',
                        'position': 4,
                        'game_link': 'Engineering: Circuits & Electricity'
                    }
                ]
            },
            'accounting': {
                'title': 'Accounting Grade 12 (NSC)',
                'summary': 'Financial accounting, management accounting, and auditing principles',
                'description': 'NSC Accounting covering financial statements, cost accounting, budgeting, internal control, and ethics. Prepares students for commerce and business studies.',
                'subject': 'Accounting',
                'classification': 'STEM',  # Can be debated, but involves mathematical analysis
                'level': 'intermediate',
                'resources': [
                    {
                        'title': 'Financial Statements Analysis',
                        'description': 'Income statement and balance sheet preparation',
                        'resource_type': 'youtube',
                        'url': 'https://www.youtube.com/watch?v=accounting_basics',
                        'learning_style': 'readwrite',
                        'position': 1
                    },
                    {
                        'title': 'Cost Accounting Methods',
                        'description': 'Standard costing and variance analysis',
                        'resource_type': 'document',
                        'learning_style': 'readwrite',
                        'position': 2
                    },
                    {
                        'title': 'Budgeting Templates',
                        'description': 'Practical budgeting exercises and templates',
                        'resource_type': 'link',
                        'url': 'https://www.accountingtools.com/',
                        'learning_style': 'readwrite',
                        'position': 3
                    },
                    {
                        'title': 'Accounting Principles Quiz',
                        'description': 'Test financial and management accounting',
                        'resource_type': 'quiz',
                        'learning_style': 'readwrite',
                        'position': 4
                    }
                ]
            }
        }

        # Filter subjects if specified
        subjects_to_create = options['subjects'] or sa_stem_courses.keys()
        
        created_count = 0
        for subject_key in subjects_to_create:
            if subject_key not in sa_stem_courses:
                self.stdout.write(self.style.ERROR(f'❌ Unknown subject: {subject_key}'))
                continue
                
            course_data = sa_stem_courses[subject_key].copy()
            resources_data = course_data.pop('resources', [])
            
            # Create course
            course = Course.objects.create(
                **course_data,
                is_active=True,
                created_by=admin_user
            )

            # Create resources
            for resource_data in resources_data:
                game_title = resource_data.pop('game_link', None)
                game = None
                if game_title:
                    try:
                        game = Game.objects.get(title=game_title)
                    except Game.DoesNotExist:
                        pass

                CourseResource.objects.create(
                    course=course,
                    game=game,
                    **resource_data
                )

            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created "{course.title}" with {len(resources_data)} resources')
            )

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Successfully created {created_count} SA Grade 12 STEM courses!')
        )