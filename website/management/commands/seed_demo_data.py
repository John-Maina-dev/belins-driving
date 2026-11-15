from django.core.management.base import BaseCommand
from website.models import SiteSettings, Testimonial, FAQ, GalleryImage
from courses.models import Course, Branch
from courses.map_utils import (
    DEFAULT_MAIN_BRANCH_ADDRESS, DEFAULT_MAIN_BRANCH_TOWN, DEFAULT_MAIN_BRANCH_EMBED,
)from instructors.models import Instructor


class Command(BaseCommand):
    help = "Seeds initial Belings Driving School data only when --with-demo is explicitly passed."

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-demo',
            action='store_true',
            help='Explicitly seed demo marketing content, sample courses, instructors, testimonials, and FAQs.',
        )

    def handle(self, *args, **options):
        if not options.get('with_demo'):
            self.stdout.write(
                self.style.WARNING(
                    "Skipping demo seed: fresh setups start clean. Pass --with-demo to seed demo marketing data."
                )
            )
            return

        self.stdout.write("Seeding Belings Driving School demo data (--with-demo)...")

        # 1. Site Settings
        settings = SiteSettings.load()
        settings.school_name = "Belings Driving School"
        settings.tagline = "Shaping Confident, Competent & Defensive Drivers Across Kenya"
        settings.phone = "+254 700 123 456"
        settings.phone_secondary = "+254 733 987 654"
        settings.email = "info@belingsdriving.co.ke"
        settings.address = DEFAULT_MAIN_BRANCH_ADDRESS
        settings.whatsapp_number = "254700123456"
        settings.opening_hours = "Monday - Friday: 7:00 AM - 6:30 PM | Saturday: 8:00 AM - 4:00 PM | Sunday: Closed"
        settings.hero_title = "Drive with Confidence. Pass Your Test on First Attempt."
        settings.hero_subtitle = "NTSA-accredited driving institution offering category A, B, and C curriculum with modern dual-pedal vehicles, certified professional instructors, and personalized schedules."
        settings.ntsa_accreditation_note = "Fully Accredited by the National Transport and Safety Authority (NTSA) - BDS/NTSA/2024/098"
        settings.stat_students = "12,500+"
        settings.stat_pass_rate = "98.5%"
        settings.stat_experience_years = "12+"
        settings.stat_certified_instructors = "24+"
        settings.save()
        self.stdout.write(self.style.SUCCESS("[OK] SiteSettings configured."))

        main_branch, _ = Branch.objects.get_or_create(
            code="MAIN-KSI",
            defaults={
                "name": "Main Campus (Kisii Town)",
                "address": DEFAULT_MAIN_BRANCH_ADDRESS,
                "town": DEFAULT_MAIN_BRANCH_TOWN,
                # UNVERIFIED: staff must confirm the pin is on the right building and replace it.
                "map_embed_url": DEFAULT_MAIN_BRANCH_EMBED,
                "phone": "+254 700 123 456",
                "email": "info@belingsdriving.co.ke",
                "opening_hours": "Mon-Sat: 7:00 AM - 6:30 PM",
                "is_active": True,
                "order": 1,
            }
        )

        # 2. Courses
        courses_data = [
            {
                "name": "Category B - Light Vehicle (Manual)",
                "license_category": "B",
                "category_display": "Category B (Manual)",
                "duration": "4 Weeks",
                "fee": 12500.00,
                "short_description": "Comprehensive manual saloon car training covering clutch control, town navigation, hill starts, and highway driving.",
                "full_description": "Our Category B Manual course is our most popular program. Trainees learn vehicle controls, gear synchronization, hill balance without rollback, emergency braking, roundabout rules on the Model Town Board, and city traffic maneuvers.",
                "practical_hours": 20,
                "theory_hours": 15,
                "icon_class": "bi-car-front-fill",
                "is_featured": True,
                "order": 1,
            },
            {
                "name": "Category B - Light Vehicle (Automatic)",
                "license_category": "B",
                "category_display": "Category B (Automatic)",
                "duration": "3 Weeks",
                "fee": 13500.00,
                "short_description": "Learn modern automatic transmission driving with full defensive techniques and traffic hazard anticipation.",
                "full_description": "Designed for learners preferring modern automatic transmission vehicles. Focuses on safe steering control, parking, reversing, lane discipline, highway overtaking, and city traffic navigation.",
                "practical_hours": 18,
                "theory_hours": 15,
                "icon_class": "bi-car-front",
                "is_featured": True,
                "order": 2,
            },
        ]

        for cdata in courses_data:
            course, created = Course.objects.update_or_create(
                name=cdata["name"],
                defaults=cdata
            )
            course.branches.add(main_branch)
            status = "Created" if created else "Updated"
            self.stdout.write(f"  {status} course: {course.name}")

        # 3. Instructors
        instructors_data = [
            {
                "full_name": "Samuel Mwangi",
                "title": "Chief Driving Instructor",
                "license_categories": "Category A, B, C & PSV",
                "experience_years": 14,
                "bio": "Senior NTSA-certified trainer with over 14 years of instruction experience.",
                "is_featured": True,
                "branch": main_branch,
                "order": 1,
            },
        ]

        for idata in instructors_data:
            inst, _ = Instructor.objects.update_or_create(
                full_name=idata["full_name"],
                defaults=idata
            )
            self.stdout.write(f"  Instructor: {inst.full_name}")

        self.stdout.write(self.style.SUCCESS("All demo data seeded successfully!"))
