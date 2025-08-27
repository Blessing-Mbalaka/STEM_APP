# Run this in Django shell: python manage.py shell
from main.models.course import Course, CourseResource

# Demo subjects and resources (matches your JS)
demo_data = {
    'Mathematics': {
        'subject': 'Math',
        'visual': [
            {'title': 'Introduction to Calculus', 'duration': '12:45 min'},
            {'title': 'Algebra Fundamentals', 'duration': '18:30 min'},
            {'title': 'Geometry in Real World', 'duration': '15:20 min'},
            {'title': 'Statistics Made Easy', 'duration': '22:10 min'},
        ],
        'auditory': [
            {'title': 'Calculus Concepts Explained', 'duration': '24:15 min'},
            {'title': 'Algebraic Formulas', 'duration': '18:45 min'},
            {'title': 'Geometry Podcast', 'duration': '32:10 min'},
            {'title': 'Probability Basics', 'duration': '15:30 min'},
        ],
        'readwrite': [
            {'title': 'Advanced Calculus', 'author': 'By Dr. Math Expert', 'pages': '320 pages'},
            {'title': 'Algebra Study Guide', 'author': 'By Professor Algebra', 'pages': '210 pages'},
            {'title': 'Geometry Textbook', 'author': 'By The Geometry Team', 'pages': '450 pages'},
            {'title': 'Statistics Handbook', 'author': 'By Stats Masters', 'pages': '180 pages'},
        ],
    },
    'Science': {
        'subject': 'Science',
        'visual': [
            {'title': 'Physics of Motion', 'duration': '14:25 min'},
            {'title': 'Chemistry Reactions', 'duration': '16:40 min'},
            {'title': 'Biology Basics', 'duration': '19:15 min'},
            {'title': 'Scientific Method', 'duration': '11:50 min'},
        ],
        'auditory': [
            {'title': 'Physics Concepts', 'duration': '28:30 min'},
            {'title': 'Chemistry Explained', 'duration': '22:15 min'},
            {'title': 'Biology Podcast', 'duration': '35:20 min'},
            {'title': 'Science Discoveries', 'duration': '18:45 min'},
        ],
        'readwrite': [
            {'title': 'Physics Textbook', 'author': 'By Science Writers', 'pages': '380 pages'},
            {'title': 'Chemistry Guide', 'author': 'By Chem Experts', 'pages': '290 pages'},
            {'title': 'Biology Handbook', 'author': 'By Bio Team', 'pages': '420 pages'},
            {'title': 'Science Encyclopedia', 'author': 'By Various Authors', 'pages': '510 pages'},
        ],
    },
    'English': {
        'subject': 'English',
        'visual': [
            {'title': 'Grammar Rules', 'duration': '10:35 min'},
            {'title': 'Writing Techniques', 'duration': '15:20 min'},
            {'title': 'Literature Analysis', 'duration': '18:45 min'},
            {'title': 'Poetry Explained', 'duration': '12:10 min'},
        ],
        'auditory': [
            {'title': 'Grammar Podcast', 'duration': '25:40 min'},
            {'title': 'Writing Tips Audio', 'duration': '19:15 min'},
            {'title': 'Literature Discussion', 'duration': '42:30 min'},
            {'title': 'Poetry Readings', 'duration': '31:20 min'},
        ],
        'readwrite': [
            {'title': 'Grammar Handbook', 'author': 'By Language Experts', 'pages': '240 pages'},
            {'title': 'Writing Guide', 'author': 'By Famous Authors', 'pages': '320 pages'},
            {'title': 'Literature Anthology', 'author': 'By Literary Society', 'pages': '480 pages'},
            {'title': 'Poetry Collection', 'author': 'By Various Poets', 'pages': '210 pages'},
        ],
    },
    'History': {
        'subject': 'History',
        'visual': [
            {'title': 'Ancient Civilizations', 'duration': '16:25 min'},
            {'title': 'World Wars Explained', 'duration': '22:40 min'},
            {'title': 'Government Systems', 'duration': '14:15 min'},
            {'title': 'Geography Basics', 'duration': '13:50 min'},
        ],
        'auditory': [
            {'title': 'History Podcast', 'duration': '38:20 min'},
            {'title': 'Civics Audio Lesson', 'duration': '24:45 min'},
            {'title': 'Geography Facts', 'duration': '29:10 min'},
            {'title': 'Historical Events', 'duration': '33:25 min'},
        ],
        'readwrite': [
            {'title': 'World History', 'author': 'By Historians', 'pages': '450 pages'},
            {'title': 'Civics Textbook', 'author': 'By Government Experts', 'pages': '310 pages'},
            {'title': 'Geography Guide', 'author': 'By Travel Writers', 'pages': '280 pages'},
            {'title': 'Historical Documents', 'author': 'By Various Authors', 'pages': '390 pages'},
        ],
    },
}

for course_name, info in demo_data.items():
    course, created = Course.objects.get_or_create(
        title=course_name,
        defaults={
            'subject': info['subject'],
            'is_active': True,
            'level': 'intro',
        }
    )
    for v in info['visual']:
        CourseResource.objects.get_or_create(
            course=course,
            title=v['title'],
            resource_type='video',
            learning_style='visual',
            description='',
            url='',
        )
    for a in info['auditory']:
        CourseResource.objects.get_or_create(
            course=course,
            title=a['title'],
            resource_type='audio',
            learning_style='auditory',
            description='',
            url='',
        )
    for r in info['readwrite']:
        CourseResource.objects.get_or_create(
            course=course,
            title=r['title'],
            resource_type='document',
            learning_style='readwrite',
            description=r.get('author', ''),
            url='',
        )
print('Demo courses and resources created!')
