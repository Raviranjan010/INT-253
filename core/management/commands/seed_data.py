import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import CustomUser
from courses.models import Category, Course, Module, Lesson, Enrollment, LessonProgress, CourseReview
from live_classes.models import LiveSession, LiveClassDoubt
from quizzes.models import Quiz, Question, Choice, QuizAttempt
from community.models import DiscussionThread, DiscussionReply
from certificates.models import Certificate
from core.models import Announcement

class Command(BaseCommand):
    help = 'Seeds realistic demonstration data for Live School (INT-253)'

    def handle(self, *args, **options):
        self.stdout.write("Starting Live School database seeding...")

        # 1. Users
        admin_user, _ = CustomUser.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@liveschool.org',
                'first_name': 'Project',
                'last_name': 'Administrator',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'demographic_group': 'general',
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()

        teacher_user, _ = CustomUser.objects.get_or_create(
            username='teacher_demo',
            defaults={
                'email': 'ananya@liveschool.org',
                'first_name': 'Dr. Ananya',
                'last_name': 'Sharma',
                'role': 'instructor',
                'is_instructor_approved': True,
                'is_staff': True,
                'demographic_group': 'female_stem',
                'country': 'India',
                'bio': 'Passionate Computer Science educator and open education advocate with 10+ years teaching Python, Algorithms, and Web Systems.',
                'xp_points': 1450,
            }
        )
        teacher_user.is_instructor_approved = True
        teacher_user.set_password('teacher123')
        teacher_user.save()

        student_user, _ = CustomUser.objects.get_or_create(
            username='student_demo',
            defaults={
                'email': 'student@liveschool.org',
                'first_name': 'Ravi',
                'last_name': 'Kumar',
                'role': 'student',
                'demographic_group': 'rural',
                'country': 'India',
                'bio': 'First-generation STEM learner pursuing software engineering through free online education.',
                'xp_points': 580,
                'streak_count': 5,
            }
        )
        student_user.set_password('student123')
        student_user.save()

        # 2. Categories
        categories_data = [
            ('Computer Science & Coding', 'cs-coding', 'bi-code-slash', 'Fundamental programming, algorithms, and practical software engineering.'),
            ('Web & Cloud Development', 'web-cloud', 'bi-globe', 'Full-stack development with Python, Django, modern frontend, and cloud.'),
            ('Mathematics & Statistics', 'maths-stats', 'bi-calculator', 'Calculus, algebra, discrete math, and probability for technology and research.'),
            ('Data Science & AI', 'data-ai', 'bi-cpu', 'Machine learning, neural networks, data analysis, and predictive modeling.'),
            ('Languages & Communication', 'languages', 'bi-chat-heart', 'English fluency, public speaking, and professional correspondence for global opportunities.'),
            ('Vocational & Career Skills', 'career-skills', 'bi-briefcase', 'Resume crafting, technical interviews, and digital freelancing literacy.'),
        ]

        category_objs = {}
        for name, slug, icon, desc in categories_data:
            cat, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'icon': icon, 'description': desc}
            )
            category_objs[slug] = cat

        # 3. Courses
        # Course 1: Python for Everyone
        c1, _ = Course.objects.get_or_create(
            slug='python-for-everyone-zero-to-hero',
            defaults={
                'title': 'Python for Everyone: From Zero to Hero',
                'category': category_objs['cs-coding'],
                'instructor': teacher_user,
                'level': 'beginner',
                'language': 'English',
                'estimated_hours': 12,
                'short_description': 'Master the world’s most versatile programming language with step-by-step interactive lessons and free practical exercises.',
                'description': (
                    'Welcome to Python for Everyone! Whether you are a high schooler, a rural student exploring programming for the first time, '
                    'or a professional transitioning into technology, this free world-class course will build your coding foundation from the ground up.\n\n'
                    'You will learn variables, data structures, conditional control flow, functions, object-oriented concepts, and error handling. '
                    'Includes video lectures, rich notes, and interactive quizzes.'
                ),
            }
        )

        # Modules for Course 1
        m1, _ = Module.objects.get_or_create(course=c1, order=1, defaults={'title': 'Introduction to Python & Setup'})
        m2, _ = Module.objects.get_or_create(course=c1, order=2, defaults={'title': 'Control Flow, Loops & Functions'})
        m3, _ = Module.objects.get_or_create(course=c1, order=3, defaults={'title': 'Object-Oriented Programming (OOP)'})

        # Lessons for Course 1
        Lesson.objects.get_or_create(
            module=m1, order=1,
            defaults={
                'title': 'Welcome to Programming with Python',
                'video_url': 'https://www.youtube.com/watch?v=eWRfhZUzrAc',
                'duration_minutes': 15,
                'content': (
                    'Python is a high-level, interpreted programming language known for its readability and elegance.\n\n'
                    '### Key Characteristics:\n'
                    '- **Readable Syntax:** Uses clean indentation instead of curly braces.\n'
                    '- **Batteries Included:** Massive standard library for math, files, networking, and data processing.\n'
                    '- **Universal Applications:** Powers web development, AI, automation, and scientific research.\n\n'
                    '```python\n# Your very first Python line\nprint("Hello, World-Class Free Education!")\n```'
                )
            }
        )

        Lesson.objects.get_or_create(
            module=m1, order=2,
            defaults={
                'title': 'Variables, Data Types & Operators',
                'video_url': 'https://www.youtube.com/watch?v=kqtD5dpn9C8',
                'duration_minutes': 20,
                'content': (
                    'Variables act as labeled containers for storing data values.\n\n'
                    '### Primitive Types in Python:\n'
                    '- `int`: Whole numbers (e.g., `age = 21`)\n'
                    '- `float`: Decimal numbers (e.g., `pi = 3.14159`)\n'
                    '- `str`: Text wrapped in single or double quotes (e.g., `name = "Ravi"`)\n'
                    '- `bool`: Boolean truth values (`True` or `False`)\n\n'
                    '```python\nx = 10\ny = 5\nprint(f"Sum: {x + y}")\n```'
                )
            }
        )

        Lesson.objects.get_or_create(
            module=m2, order=1,
            defaults={
                'title': 'Conditionals: If, Elif, Else',
                'video_url': 'https://www.youtube.com/watch?v=DZwmZ8Usvnk',
                'duration_minutes': 18,
                'content': (
                    'Conditional statements evaluate Boolean expressions to direct program flow.\n\n'
                    '```python\nscore = 85\nif score >= 90:\n    print("Grade: A")\nelif score >= 75:\n    print("Grade: B")\nelse:\n    print("Grade: C")\n```'
                )
            }
        )

        Lesson.objects.get_or_create(
            module=m3, order=1,
            defaults={
                'title': 'Classes, Objects & Methods in Python',
                'video_url': 'https://www.youtube.com/watch?v=JeznW_7DlB0',
                'duration_minutes': 25,
                'content': (
                    'Object-Oriented Programming (OOP) allows developers to model real-world concepts as classes and instances.\n\n'
                    '```python\nclass Student:\n    def __init__(self, name, demographic):\n        self.name = name\n        self.demographic = demographic\n\n    def introduce(self):\n        return f"Hi, I am {self.name} learning through Live School!"\n\ns = Student("Ravi", "Rural Student")\nprint(s.introduce())\n```'
                )
            }
        )

        # Course 2: Full-Stack Web Development with Django & Python
        c2, _ = Course.objects.get_or_create(
            slug='fullstack-django-web-development',
            defaults={
                'title': 'Full-Stack Web Development with Django',
                'category': category_objs['web-cloud'],
                'instructor': teacher_user,
                'level': 'intermediate',
                'language': 'English',
                'estimated_hours': 16,
                'short_description': 'Build secure, scalable, and database-backed web platforms using Python and Django.',
                'description': (
                    'Learn how to create real-world web applications just like Live School using the Django web framework. '
                    'Covers Model-View-Template (MVT) architecture, ORM database querying, authentication, security, and deployment.'
                ),
            }
        )

        m2_1, _ = Module.objects.get_or_create(course=c2, order=1, defaults={'title': 'Django MVT Architecture & Setup'})
        Lesson.objects.get_or_create(
            module=m2_1, order=1,
            defaults={
                'title': 'Understanding Models, Views, and Templates',
                'video_url': 'https://www.youtube.com/watch?v=F5mRW0jo-U4',
                'duration_minutes': 22,
                'content': (
                    'Django follows the Model-View-Template pattern:\n'
                    '1. **Models:** Define the database schema via Python classes.\n'
                    '2. **Views:** Process requests and return responses.\n'
                    '3. **Templates:** Present HTML dynamically to the user.\n'
                )
            }
        )

        # Course 3: Mathematics for Machine Learning & Data Science
        c3, _ = Course.objects.get_or_create(
            slug='calculus-linear-algebra-machine-learning',
            defaults={
                'title': 'Calculus & Linear Algebra for Modern Computing',
                'category': category_objs['maths-stats'],
                'instructor': teacher_user,
                'level': 'all',
                'language': 'English',
                'estimated_hours': 14,
                'short_description': 'Demystifying the essential mathematics behind modern computer graphics, algorithms, and artificial intelligence.',
                'description': 'Master vectors, matrices, dot products, gradients, and partial derivatives with intuitive visual analogies and free computational examples.',
            }
        )

        m3_1, _ = Module.objects.get_or_create(course=c3, order=1, defaults={'title': 'Vectors & Matrix Operations'})
        Lesson.objects.get_or_create(
            module=m3_1, order=1,
            defaults={
                'title': 'Geometric Intuition of Vectors',
                'video_url': 'https://www.youtube.com/watch?v=fNk_zzaMoSs',
                'duration_minutes': 15,
                'content': 'Vectors represent direction and magnitude. In computing, vectors represent feature dimensions in multidimensional coordinate systems.'
            }
        )

        # Course 4: English Fluency & Professional Communication
        c4, _ = Course.objects.get_or_create(
            slug='english-fluency-and-communication',
            defaults={
                'title': 'English Fluency & Global Communication',
                'category': category_objs['languages'],
                'instructor': teacher_user,
                'level': 'beginner',
                'language': 'English',
                'estimated_hours': 10,
                'short_description': 'Build speaking confidence, vocabulary, and professional writing skills for global internships and interviews.',
                'description': 'Tailored specifically for non-native English speakers and rural learners looking to expand their global professional horizon.',
            }
        )

        m4_1, _ = Module.objects.get_or_create(course=c4, order=1, defaults={'title': 'Confident Technical Speaking'})
        Lesson.objects.get_or_create(
            module=m4_1, order=1,
            defaults={
                'title': 'Structuring Clear Explanations for Interviews',
                'video_url': 'https://www.youtube.com/watch?v=F0744nL4yK8',
                'duration_minutes': 18,
                'content': 'How to articulate your thoughts clearly during technical interviews using the STAR method (Situation, Task, Action, Result).'
            }
        )

        # Course 5: Applied Data Science & AI Foundations
        c5, _ = Course.objects.get_or_create(
            slug='applied-data-science-ai-foundations',
            defaults={
                'title': 'Applied Data Science & AI Foundations',
                'category': category_objs['data-ai'],
                'instructor': teacher_user,
                'level': 'intermediate',
                'language': 'English',
                'estimated_hours': 18,
                'short_description': 'Transform raw data into actionable intelligence with Python, Pandas, statistical modeling, and neural networks.',
                'description': 'Comprehensive hands-on training in data cleaning, exploratory analysis, machine learning algorithms, and ethical AI deployment for students worldwide.',
            }
        )

        m5_1, _ = Module.objects.get_or_create(course=c5, order=1, defaults={'title': 'Exploratory Data Analysis with Pandas'})
        Lesson.objects.get_or_create(
            module=m5_1, order=1,
            defaults={
                'title': 'Data Wrangling, Filtering, and Aggregation',
                'video_url': 'https://www.youtube.com/watch?v=vmEHCJofslg',
                'duration_minutes': 25,
                'content': 'Master dataframes, series manipulation, missing value handling, and statistical summarization for real-world datasets.'
            }
        )

        # Course 6: Technical Portfolio, Git & Career Acceleration
        c6, _ = Course.objects.get_or_create(
            slug='technical-portfolio-git-career-acceleration',
            defaults={
                'title': 'Technical Portfolio, Git & Career Acceleration',
                'category': category_objs['career-skills'],
                'instructor': teacher_user,
                'level': 'all',
                'language': 'English',
                'estimated_hours': 8,
                'short_description': 'Craft an impactful developer resume, master Git/GitHub collaboration, and prepare for tech industry interviews.',
                'description': 'Practical, no-fluff guide designed to help first-generation college students and career switchers land high-paying remote and local engineering roles.',
            }
        )

        m6_1, _ = Module.objects.get_or_create(course=c6, order=1, defaults={'title': 'Version Control Mastery with Git'})
        Lesson.objects.get_or_create(
            module=m6_1, order=1,
            defaults={
                'title': 'Branching, Pull Requests, and Open Source Etiquette',
                'video_url': 'https://www.youtube.com/watch?v=RGOj5yH7evk',
                'duration_minutes': 20,
                'content': 'Step-by-step collaborative Git workflows: creating branches, staging changes, writing atomic commit messages, and opening pull requests.'
            }
        )

        # 4. Quizzes
        quiz1, _ = Quiz.objects.get_or_create(
            course=c1,
            title='Python Fundamentals Assessment',
            defaults={
                'description': 'Verify your grasp of Python variables, datatypes, control flow, and basic syntax.',
                'pass_percentage': 70,
                'time_limit_minutes': 10,
            }
        )

        q1, _ = Question.objects.get_or_create(
            quiz=quiz1, order=1,
            defaults={
                'text': 'Which of the following data types is immutable in Python?',
                'explanation': 'Tuples and strings in Python cannot be altered in-place after creation, making them immutable.'
            }
        )
        Choice.objects.get_or_create(question=q1, text='List', defaults={'is_correct': False})
        Choice.objects.get_or_create(question=q1, text='Tuple', defaults={'is_correct': True})
        Choice.objects.get_or_create(question=q1, text='Dictionary', defaults={'is_correct': False})
        Choice.objects.get_or_create(question=q1, text='Set', defaults={'is_correct': False})

        q2, _ = Question.objects.get_or_create(
            quiz=quiz1, order=2,
            defaults={
                'text': 'How do you create a function in Python?',
                'explanation': 'In Python, the def keyword is used to declare and define functions.'
            }
        )
        Choice.objects.get_or_create(question=q2, text='function myFunc():', defaults={'is_correct': False})
        Choice.objects.get_or_create(question=q2, text='def my_func():', defaults={'is_correct': True})
        Choice.objects.get_or_create(question=q2, text='create my_func():', defaults={'is_correct': False})
        Choice.objects.get_or_create(question=q2, text='fn my_func():', defaults={'is_correct': False})

        q3, _ = Question.objects.get_or_create(
            quiz=quiz1, order=3,
            defaults={
                'text': 'What will be the output of print(10 // 3) in Python?',
                'explanation': 'The // operator performs floor division, truncating the fractional part and returning 3.'
            }
        )
        Choice.objects.get_or_create(question=q3, text='3.333', defaults={'is_correct': False})
        Choice.objects.get_or_create(question=q3, text='3', defaults={'is_correct': True})
        Choice.objects.get_or_create(question=q3, text='3.0', defaults={'is_correct': False})
        Choice.objects.get_or_create(question=q3, text='1', defaults={'is_correct': False})

        # 5. Live Classes
        now = timezone.now()
        live1, _ = LiveSession.objects.get_or_create(
            title='Live Doubt Clearing: Python OOP from Scratch',
            defaults={
                'course': c1,
                'instructor': teacher_user,
                'description': 'Interactive live session covering Python classes, inheritance, dunder methods, and answering student doubts live on WebRTC video.',
                'scheduled_start': now + datetime.timedelta(hours=2),
                'duration_minutes': 60,
                'status': 'scheduled',
                'target_demographics': 'All Students & Remote Learners',
            }
        )

        live2, _ = LiveSession.objects.get_or_create(
            title='Interactive WebRTC Workshop: Building Full-Stack Apps',
            defaults={
                'course': c2,
                'instructor': teacher_user,
                'description': 'Hands-on live coding workshop building database models and wiring dynamic views.',
                'scheduled_start': now + datetime.timedelta(days=2),
                'duration_minutes': 90,
                'status': 'scheduled',
                'target_demographics': 'College & Working Adults',
            }
        )

        LiveClassDoubt.objects.get_or_create(
            session=live1,
            student=student_user,
            defaults={
                'question': 'Can we inherit from multiple parent classes in Python, and what is MRO?',
                'is_answered': True,
                'answer': 'Yes, Python supports multiple inheritance! MRO (Method Resolution Order) defines the sequence in which classes are searched using the C3 linearization algorithm.'
            }
        )

        # 6. Student Enrollment & Progress for Demo Student
        enrollment, _ = Enrollment.objects.get_or_create(
            student=student_user,
            course=c1,
            defaults={'progress_percentage': 100, 'is_completed': True, 'completed_at': now}
        )

        for lesson in Lesson.objects.filter(module__course=c1):
            LessonProgress.objects.get_or_create(
                enrollment=enrollment,
                lesson=lesson,
                defaults={'is_completed': True, 'completed_at': now}
            )

        # Sample Course Review
        CourseReview.objects.get_or_create(
            course=c1,
            student=student_user,
            defaults={
                'rating': 5,
                'review_text': 'This completely free course helped me understand programming concepts that my local college never explained properly. The interactive exercises and live classes are a game-changer for rural learners!'
            }
        )

        # 7. Verified Certificate for Demo Student
        Certificate.objects.get_or_create(
            student=student_user,
            course=c1,
            defaults={
                'certificate_id': 'LS-2026-DEMO8942',
                'grade': 'Distinction Honors (100% Mastery)',
                'issued_at': now - datetime.timedelta(days=1),
            }
        )

        # 8. Community Threads & Replies
        thread1, _ = DiscussionThread.objects.get_or_create(
            title='What is the difference between a list and a tuple in Python?',
            defaults={
                'author': student_user,
                'course': c1,
                'content': 'I am learning Python data structures. When should I choose a tuple over a list, and what are the performance advantages?',
                'tags': 'python, list, tuple, performance',
                'is_resolved': True,
                'views_count': 142,
            }
        )

        reply1, _ = DiscussionReply.objects.get_or_create(
            thread=thread1,
            author=teacher_user,
            defaults={
                'content': (
                    'Great question! The core differences are:\n'
                    '1. **Mutability:** Lists are mutable (can add, remove, modify elements); tuples are immutable.\n'
                    '2. **Memory & Speed:** Tuples require less memory overhead and iterate slightly faster.\n'
                    '3. **Dictionary Keys:** Because tuples are immutable and hashable, they can be used as dictionary keys or in sets, whereas lists cannot!'
                ),
                'is_solution': True,
            }
        )
        reply1.upvotes.add(student_user)

        # 9. Announcement
        Announcement.objects.get_or_create(
            title='Free Live Class This Saturday!',
            defaults={
                'content': 'Join Dr. Ananya Sharma for a live interactive masterclass on WebRTC & Python OOP.',
                'badge': 'Live Webinar',
                'link_url': '/live/',
                'is_active': True,
            }
        )

        self.stdout.write(self.style.SUCCESS("✓ Live School data seeded successfully!"))
        self.stdout.write(self.style.SUCCESS("  Demo accounts ready:"))
        self.stdout.write("  - Administrator: admin / admin123")
        self.stdout.write("  - Instructor: teacher_demo / teacher123")
        self.stdout.write("  - Student: student_demo / student123")

