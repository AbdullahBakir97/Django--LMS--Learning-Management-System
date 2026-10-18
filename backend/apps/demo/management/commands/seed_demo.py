"""Fill an empty database with a small, believable community to explore.

    python manage.py seed_demo           # once; does nothing if the demo exists
    python manage.py seed_demo --reset   # remove the demo users (and what they own) first

Every account uses the password from DEMO_PASSWORD, or a random one printed at the end.
Never run this in production.
"""

import os
import secrets
from datetime import timedelta

from allauth.account.models import EmailAddress
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.careers import services as careers
from apps.careers.models import Company
from apps.community import services as community
from apps.engagement import registry
from apps.engagement import services as engagement
from apps.learning import services as learning
from apps.learning.models import Choice, Course, Lesson, Question, Quiz
from apps.messaging import services as messaging
from apps.network import services as network
from apps.profiles.models import PortfolioItem
from apps.profiles.services import add_skill

DOMAIN = "demo.lms"

PEOPLE = [
    (
        "karim",
        "Karim",
        "Nassar",
        "instructor",
        "Instructor, Django and APIs",
        "Amman",
        ["Django", "PostgreSQL", "Python"],
    ),
    (
        "amina",
        "Amina",
        "Haddad",
        "instructor",
        "Data engineer and SQL teacher",
        "Irbid",
        ["PostgreSQL", "SQL", "Python"],
    ),
    (
        "lina",
        "Lina",
        "Haddad",
        "learner",
        "Backend developer, learning PostgreSQL",
        "Amman",
        ["Django", "Python", "SQL"],
    ),
    ("omar", "Omar", "Saleh", "learner", "Data analyst at Nahla", "Zarqa", ["SQL", "Python"]),
    ("sara", "Sara", "Mansour", "learner", "Frontend engineer", "Dubai", ["Vue", "TypeScript"]),
    (
        "yusuf",
        "Yusuf",
        "Demir",
        "learner",
        "Student, computer science",
        "Istanbul",
        ["Python", "Vue"],
    ),
    ("rana", "Rana", "Odeh", "learner", "Talent partner at Nahla Labs", "Amman", []),
]

# A one-page PDF: enough for the résumé checks.
PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]"
    b"/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)


class Command(BaseCommand):
    help = "Create demo users, courses, groups, events, jobs and conversations."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete the demo first.")

    def handle(self, *args, reset=False, **options):
        if not settings.DEBUG and not getattr(settings, "ALLOW_DEMO_SEED", False):
            raise CommandError("Refusing to seed: DEBUG is off. Set ALLOW_DEMO_SEED to override.")
        demo = User.objects.filter(email__endswith=f"@{DOMAIN}")
        if reset:
            Company.objects.filter(members__user__in=demo).delete()
            for user in demo:
                user.owned_groups.all().delete()
                Course.objects.filter(instructor=user).delete()
            demo.delete()
        elif demo.exists():
            self.stdout.write("The demo already exists. Use --reset to rebuild it.")
            return
        # Never a password in the code: take it from the environment or make one up.
        self.password = os.environ.get("DEMO_PASSWORD") or secrets.token_urlsafe(9)
        with transaction.atomic():
            self.seed()
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo ready. Sign in as any of {', '.join(p[0] for p in PEOPLE)} "
                f"with <name>@{DOMAIN} and the password {self.password}"
            )
        )

    def seed(self):
        u = {}
        for username, first, last, role, headline, location, skills in PEOPLE:
            user = User.objects.create_user(
                username=username,
                email=f"{username}@{DOMAIN}",
                password=self.password,
                first_name=first,
                last_name=last,
                role=role,
            )
            EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
            user.profile.headline, user.profile.location = headline, location
            user.profile.save()
            for skill in skills:
                add_skill(user.profile, skill, "intermediate")
            u[username] = user

        # Network
        for a, b in [
            ("lina", "karim"),
            ("lina", "amina"),
            ("lina", "omar"),
            ("sara", "karim"),
            ("omar", "amina"),
            ("yusuf", "lina"),
        ]:
            network.accept(u[b], network.request_connection(u[a], u[b]))
        network.request_connection(u["sara"], u["lina"])
        for a, b in [("yusuf", "karim"), ("sara", "amina"), ("omar", "karim")]:
            network.follow(u[a], u[b])

        # Credentials
        lina = u["lina"].profile
        PortfolioItem.objects.create(
            profile=lina,
            title="Course catalogue API",
            url="https://example.org/catalogue",
            description="A versioned REST API with search, pagination and contract tests.",
        )
        PortfolioItem.objects.create(
            profile=lina,
            title="Talk: constraints over code",
            description="Why rules belong in the database, given at a local Python meetup.",
        )
        karim_says = network.write_recommendation(
            u["karim"],
            u["lina"],
            "Taught Lina in APIs with Django REST Framework",
            "Lina asked the questions everyone else was thinking and then wrote the tests to "
            "prove the answers. Her final project was the best in the cohort.",
        )
        network.set_recommendation_status(u["lina"], karim_says, "published")
        network.write_recommendation(
            u["amina"],
            u["lina"],
            "Worked with Lina on a data migration",
            "Careful, calm under pressure and generous with reviews. "
            "I would happily work with Lina again.",
        )

        # Learning
        api = self.course(
            u["karim"],
            "APIs with Django REST Framework",
            "Build a real API with permissions, pagination and tests.",
            "intermediate",
            [
                (
                    "Why REST, and what Django adds",
                    "An API is a contract. Django gives you the ORM, "
                    "migrations and an admin; DRF adds serializers, views and permissions.",
                    True,
                ),
                (
                    "Models, migrations and constraints",
                    "Put rules in the database: **unique**, "
                    "**check** and **foreign key** constraints catch what code forgets.",
                    False,
                ),
                (
                    "Serializers that validate",
                    "A serializer turns untrusted input into data a service "
                    "can rely on. Field rules live here; business rules live in services.",
                    False,
                ),
                (
                    "Permissions and object ownership",
                    "Scope every queryset to the signed-in user. A row "
                    "that is never fetched cannot leak.",
                    False,
                ),
            ],
            quiz_on=2,
        )
        sql = self.course(
            u["amina"],
            "PostgreSQL for application developers",
            "Indexes, constraints and query plans you will actually use.",
            "intermediate",
            [
                (
                    "Reading a query plan",
                    "`EXPLAIN ANALYZE` shows what the database did, not what you "
                    "hoped it would do.",
                    True,
                ),
                (
                    "Indexes that pay for themselves",
                    "An index speeds reads and slows writes. Index what you filter and sort on.",
                    False,
                ),
                (
                    "Constraints as documentation",
                    "A constraint is a rule the database enforces for every client, forever.",
                    False,
                ),
            ],
        )
        self.course(
            u["karim"],
            "Testing Django properly",
            "Factories, fixtures and API tests.",
            "advanced",
            [("The test pyramid, adjusted", "Test the API surface first.", True)],
        )
        enrollment = learning.enroll(u["lina"], api)
        learning.complete_lesson(u["lina"], api.lessons.get(order=1))
        learning.enroll(u["omar"], sql)
        learning.enroll(u["yusuf"], api)
        del enrollment

        # Discussion on a lesson
        lesson_target, lesson = registry.resolve("lesson", api.lessons.get(order=1).pk, u["lina"])
        question = engagement.add_comment(
            u["lina"],
            lesson_target,
            lesson,
            "Where would you check that an end date comes after a start date?",
        )
        engagement.add_comment(
            u["karim"],
            lesson_target,
            lesson,
            "In the serializer's validate(): it only needs the two fields, so it is a field rule.",
            question,
        )
        engagement.react(u["omar"], "comment", question.pk, "insightful")

        # Community
        django_amman = community.create_group(
            u["karim"],
            name="Django Amman",
            privacy="public",
            description="Monthly meetups, and a place to ask about Django, DRF and deploying.",
        )
        circle = community.create_group(
            u["amina"],
            name="SQL study circle",
            privacy="private",
            description="One chapter a week, and we review each other's queries.",
        )
        for name in ("lina", "omar", "sara", "yusuf"):
            community.join(u[name], django_amman)
        community.join(u["lina"], circle)
        community.approve(u["amina"], circle, u["lina"].id)
        community.join(u["omar"], circle)  # left pending for Amina to review

        posts = [
            community.create_post(
                u["lina"],
                "Finished the permissions lesson. Scoping every queryset "
                "to the signed-in user finally clicked: a row that is never fetched "
                "cannot leak.",
            ),
            community.create_post(
                u["karim"],
                "Slides from last night's meetup are in the group. "
                "Thanks to everyone who stayed for questions!",
                django_amman,
            ),
            community.create_post(
                u["amina"],
                "This week: chapter 4, indexes. Bring one slow query from your own work.",
                circle,
            ),
            community.create_post(
                u["sara"], "Looking for a study buddy for the Vue course. Evenings, Dubai time."
            ),
        ]
        post_target, first = registry.resolve("post", posts[0].pk, u["karim"])
        engagement.add_comment(
            u["karim"], post_target, first, "Exactly. Scope first, then permissions."
        )
        for name, kind in (("karim", "celebrate"), ("amina", "insightful"), ("omar", "like")):
            engagement.react(u[name], "post", posts[0].pk, kind)

        soon = timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=4)
        meetup = community.create_event(
            u["karim"],
            django_amman,
            title="Django Amman: monthly meetup",
            description="Two short talks, then questions and tea.",
            starts_at=soon.replace(hour=18),
            ends_at=soon.replace(hour=20),
            location="Amman, King Hussein Business Park",
            capacity=60,
        )
        community.create_event(
            u["amina"],
            circle,
            title="Query plan office hours",
            starts_at=soon + timedelta(days=2),
            ends_at=soon + timedelta(days=2, hours=1),
            online_url="https://meet.example.com/sql-circle",
        )
        for name in ("lina", "omar", "yusuf"):
            community.rsvp(u[name], meetup, "going")

        # Careers
        nahla = careers.create_company(
            u["rana"],
            name="Nahla Labs",
            industry="Health software",
            location="Amman",
            size="11-50",
            website="https://nahla.example",
            description="Software for small clinics: scheduling, records and billing.",
        )
        careers.add_member(u["rana"], nahla, u["karim"], "recruiter")
        qamar = careers.create_company(
            u["amina"],
            name="Qamar Health",
            industry="Health data",
            location="Remote",
            size="51-200",
        )
        backend = careers.create_job(
            u["rana"],
            nahla,
            skills=["Django", "PostgreSQL", "Celery"],
            title="Backend engineer (Django)",
            description="## The role\n\nOwn our scheduling and billing services.\n\n- Django and "
            "PostgreSQL\n- Tests first\n- Code review every day",
            location="Amman",
            workplace="hybrid",
            level="mid",
            salary_min=1200,
            salary_max=1800,
            currency="JOD",
        )
        careers.publish_job(u["rana"], backend)
        analyst = careers.create_job(
            u["amina"],
            qamar,
            skills=["SQL", "Python"],
            title="Junior data analyst",
            description="Turn clinic data into weekly reports.",
            workplace="remote",
            level="entry",
            salary_min=900,
            currency="USD",
        )
        careers.publish_job(u["amina"], analyst)
        careers.publish_job(
            u["rana"],
            careers.create_job(
                u["rana"],
                nahla,
                skills=["Python"],
                title="Engineering intern, summer",
                description="Ten weeks on a real team.",
                employment_type="internship",
                level="entry",
            ),
        )
        careers.apply(
            u["lina"],
            backend,
            ContentFile(PDF, name="lina.pdf"),
            "I build Django services and just finished the APIs course here.",
        )
        careers.apply(u["omar"], analyst, ContentFile(PDF, name="omar.pdf"))

        # Messaging
        chat = messaging.start(u["lina"], [u["amina"]])
        for sender, body in [
            ("lina", "Did you see the new chapter on indexes?"),
            ("amina", "Yes! Bring a slow query on Thursday and we will read its plan together."),
            ("lina", "Deal. I have one from the clinic project."),
        ]:
            messaging.send(u[sender], chat, body)
        group = messaging.start(u["karim"], [u["lina"], u["sara"]], "Meetup volunteers")
        messaging.send(u["karim"], group, "Who can help with chairs at 5:30?")

    @staticmethod
    def course(instructor, title, summary, level, lessons, quiz_on=None) -> Course:
        course = Course.objects.create(
            instructor=instructor,
            title=title,
            summary=summary,
            level=level,
            description=f"{summary}\n\nEach lesson is short and ends with something to try.",
        )
        for order, (name, content, preview) in enumerate(lessons, start=1):
            lesson = Lesson.objects.create(
                course=course, title=name, order=order, content=content, is_free_preview=preview
            )
            if order == quiz_on:
                quiz = Quiz.objects.create(
                    lesson=lesson, title="Check your understanding", pass_score=50
                )
                q = Question.objects.create(
                    quiz=quiz, order=1, text="Where does a rule that needs the acting user belong?"
                )
                Choice.objects.create(question=q, text="In a service function", is_correct=True)
                Choice.objects.create(question=q, text="In the serializer", is_correct=False)
        return learning.publish_course(instructor, course)
