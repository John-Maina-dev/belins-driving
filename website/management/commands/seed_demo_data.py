from django.core.management.base import BaseCommand
from website.models import SiteSettings, Testimonial, FAQ, GalleryImage
from courses.models import Course
from instructors.models import Instructor

class Command(BaseCommand):
    help = "Seeds initial Belings Driving School data including settings, courses, instructors, and testimonials."

    def handle(self, *args, **options):
        self.stdout.write("Seeding Belings Driving School data...")

        # 1. Site Settings
        settings = SiteSettings.load()
        settings.school_name = "Belings Driving School"
        settings.tagline = "Shaping Confident, Competent & Defensive Drivers Across Kenya"
        settings.phone = "+254 700 123 456"
        settings.phone_secondary = "+254 733 987 654"
        settings.email = "info@belingsdriving.co.ke"
        settings.address = "Belings Towers, 3rd Floor, Moi Avenue / Commercial Street, Nairobi, Kenya"
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

        # 2. Courses
        courses_data = [
            {
                "name": "Category B - Light Vehicle (Manual)",
                "license_category": "B",
                "category_display": "Category B (Manual)",
                "duration": "4 Weeks",
                "fee": 12500.00,
                "short_description": "Comprehensive manual saloon car training covering clutch control, town navigation, hill starts, and highway driving.",
                "full_description": "Our Category B Manual course is our most popular program. Trainees learn vehicle controls, gear synchronization, hill balance without rollback, emergency braking, roundabout rules on the Model Town Board, and city traffic maneuvers. Includes mock driving test and NTSA examination vehicle hire.",
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
                "full_description": "Designed for learners preferring modern automatic transmission vehicles. Focuses on safe steering control, parking, reversing, lane discipline, highway overtaking, and city traffic navigation. Complete NTSA test readiness guaranteed.",
                "practical_hours": 18,
                "theory_hours": 15,
                "icon_class": "bi-car-front",
                "is_featured": True,
                "order": 2,
            },
            {
                "name": "Category A - Motorcycle & Boda Boda",
                "license_category": "A",
                "category_display": "Category A (A1, A2, A3)",
                "duration": "2 to 3 Weeks",
                "fee": 8500.00,
                "short_description": "Professional rider training for personal motorcycles, courier riders, and commercial boda boda operators.",
                "full_description": "Learn motorcycle balance, clutch and gear coordination, defensive riding habits, helmet safety, pillion rider management, road sign mastery, and basic bike mechanics. Approved NTSA two-wheeler syllabus.",
                "practical_hours": 16,
                "theory_hours": 12,
                "icon_class": "bi-bicycle",
                "is_featured": True,
                "order": 3,
            },
            {
                "name": "Category C - Commercial Medium Trucks",
                "license_category": "C",
                "category_display": "Category C (Light/Medium Truck)",
                "duration": "4 Weeks",
                "fee": 15500.00,
                "short_description": "Commercial driver training for canters, lorries, and medium freight transport vehicles.",
                "full_description": "Equips drivers with commercial vehicle handling, air brake system awareness, load balancing, reversing with mirrors, blind spot management, and long-distance driving ethics.",
                "practical_hours": 22,
                "theory_hours": 18,
                "icon_class": "bi-truck",
                "is_featured": True,
                "order": 4,
            },
            {
                "name": "Category D - Public Service Vehicle (PSV)",
                "license_category": "D",
                "category_display": "Category D (Matatu & Bus)",
                "duration": "3 Weeks",
                "fee": 14000.00,
                "short_description": "Specialized certification for commercial passenger drivers, matatus, staff vans, and tour buses.",
                "full_description": "Designed for licensed drivers seeking PSV endorsement. Modules cover passenger customer care, speed governor compliance, anti-fatigue techniques, emergency evacuations, and first aid.",
                "practical_hours": 18,
                "theory_hours": 15,
                "icon_class": "bi-bus-front",
                "is_featured": False,
                "order": 5,
            },
            {
                "name": "Defensive Driving & Refresher Course",
                "license_category": "R",
                "category_display": "Refresher & Defensive",
                "duration": "1 to 2 Weeks",
                "fee": 9000.00,
                "short_description": "Tailored for licensed drivers needing a confidence boost, highway practice, or corporate fleet safety re-certification.",
                "full_description": "Customized practical sessions tackling specific challenges: parking in tight mall basements, night driving, wet weather skidding prevention, and overtaking judgment.",
                "practical_hours": 12,
                "theory_hours": 8,
                "icon_class": "bi-shield-check",
                "is_featured": True,
                "order": 6,
            },
        ]

        for cdata in courses_data:
            course, created = Course.objects.update_or_create(
                name=cdata["name"],
                defaults=cdata
            )
            status = "Created" if created else "Updated"
            self.stdout.write(f"  {status} course: {course.name}")

        # 3. Instructors
        instructors_data = [
            {
                "full_name": "Samuel Mwangi",
                "title": "Chief Driving Instructor",
                "license_categories": "Category A, B, C & PSV",
                "experience_years": 14,
                "bio": "Senior NTSA-certified trainer with over 14 years of instruction experience. Renowned for turning nervous beginners into calm, assertive, and technically sound drivers.",
                "is_featured": True,
                "order": 1,
            },
            {
                "full_name": "Grace Akinyi",
                "title": "Defensive Driving Specialist",
                "license_categories": "Category B (Manual & Automatic)",
                "experience_years": 9,
                "bio": "Specialist in highway safety, roundabout maneuvers, and spatial parking techniques. Passionate about empowering women drivers across Nairobi.",
                "is_featured": True,
                "order": 2,
            },
            {
                "full_name": "David Kiprono",
                "title": "Commercial & Fleet Lead",
                "license_categories": "Category C & D (Trucks & Buses)",
                "experience_years": 16,
                "bio": "Former long-haul logistics master trainer specializing in commercial vehicles, air brake systems, and eco-defensive fleet driving.",
                "is_featured": True,
                "order": 3,
            },
            {
                "full_name": "Patrick Mutiso",
                "title": "Category A Motorcycle Trainer",
                "license_categories": "Category A1, A2, A3",
                "experience_years": 8,
                "bio": "Certified two-wheeler instructor with extensive expertise in rider safety, counter-steering, wet surface braking, and traffic hazard prediction.",
                "is_featured": True,
                "order": 4,
            },
        ]

        for idata in instructors_data:
            inst, created = Instructor.objects.update_or_create(
                full_name=idata["full_name"],
                defaults=idata
            )
            self.stdout.write(f"  Instructor: {inst.full_name}")

        # 4. Testimonials
        testimonials_data = [
            {
                "name": "Mercy Wanjiku",
                "course_taken": "Category B (Light Vehicle) Graduate",
                "rating": 5,
                "quote": "I was terrified of highway driving and roundabouts. Belings instructors were remarkably patient and taught me defensive skills that gave me confidence. Passed my test first attempt!",
                "is_featured": True,
                "order": 1,
            },
            {
                "name": "Brian Ochieng",
                "course_taken": "Category C (Commercial Trucks)",
                "rating": 5,
                "quote": "Best driving school in Nairobi! The model town board classes were crystal clear, and the vehicle maintenance lectures were an unexpected bonus.",
                "is_featured": True,
                "order": 2,
            },
            {
                "name": "Kevin Mutua",
                "course_taken": "Category A (Motorcycle Riding)",
                "rating": 5,
                "quote": "Flexible installment payment plan allowed me to finish my course without financial stress. The staff helped me with all TIMS / NTSA test booking.",
                "is_featured": True,
                "order": 3,
            },
        ]

        for tdata in testimonials_data:
            testi, created = Testimonial.objects.update_or_create(
                name=tdata["name"],
                defaults=tdata
            )
            self.stdout.write(f"  Testimonial: {testi.name}")

        # 5. FAQs
        faqs_data = [
            {
                "question": "What are the requirements to enroll in Belings Driving School?",
                "answer": "To register, you need a copy of your Kenyan National ID or Passport (or Alien ID), 2 colored passport photos, minimum 18 years of age (21 for commercial), and an active eCitizen account. Our admissions office assists with all registration steps.",
                "category": "enrollment",
                "order": 1,
            },
            {
                "question": "Can I pay the course fee in installments?",
                "answer": "Yes! Belings Driving School offers a 3-part flexible installment schedule: 50% upon admission, 30% midway through practical lessons, and 20% prior to your NTSA examination booking.",
                "category": "fees",
                "order": 2,
            },
            {
                "question": "How long does a driving course take to complete?",
                "answer": "Standard courses run for 3 to 4 weeks depending on your availability. We provide morning, afternoon, evening, and weekend intensive batches to fit your personal schedule.",
                "category": "general",
                "order": 3,
            },
            {
                "question": "Does Belings Driving School assist with NTSA test booking and the Interim License?",
                "answer": "Yes, our team handles the test booking process directly on the NTSA portal, provides training vehicles on your exam day, and guides you through downloading your official Interim Driving License upon passing.",
                "category": "ntsa",
                "order": 4,
            },
        ]

        for fdata in faqs_data:
            faq, created = FAQ.objects.update_or_create(
                question=fdata["question"],
                defaults=fdata
            )
            self.stdout.write(f"  FAQ: {faq.question[:30]}...")

        self.stdout.write(self.style.SUCCESS("All demo data seeded successfully!"))
