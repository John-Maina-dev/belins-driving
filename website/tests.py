from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from courses.models import Course
from instructors.models import Instructor
from students.models import Student
from website.models import SiteSettings, Testimonial, FAQ, GalleryImage, ContactMessage
from website.forms import ContactForm, EnrollmentForm

class PublicWebsiteTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

        # Seed site settings with maintenance mode disabled
        self.settings = SiteSettings.load()
        self.settings.school_name = "Belings Driving School"
        self.settings.maintenance_mode = False
        self.settings.save()

        # Seed a test course
        self.course = Course.objects.create(
            name="Category B Light Vehicle (Manual)",
            license_category="B",
            duration="4 Weeks",
            fee=12500.00,
            short_description="Learn to drive manual transmission saloon cars with complete road test prep.",
            practical_hours=20,
            theory_hours=15,
            is_active=True,
            is_featured=True,
            order=1
        )

        # Seed a test instructor
        self.instructor = Instructor.objects.create(
            full_name="Peter Kamau",
            title="Senior Chief Instructor",
            license_categories="Category A, B & C",
            experience_years=10,
            bio="Certified NTSA instructor specializing in defensive road techniques.",
            is_active=True,
            is_featured=True
        )

        # Seed an FAQ
        self.faq = FAQ.objects.create(
            question="What documents are needed to enroll?",
            answer="Copy of ID and 2 passport photos.",
            is_active=True
        )

    def test_all_public_pages_status_code(self):
        """Test that all public marketing pages load successfully (HTTP 200)."""
        urls = [
            reverse('website:home'),
            reverse('website:about'),
            reverse('website:courses'),
            reverse('website:course_detail', kwargs={'slug': self.course.slug}),
            reverse('website:fees'),
            reverse('website:instructors'),
            reverse('website:gallery'),
            reverse('website:faq'),
            reverse('website:contact'),
            reverse('website:enroll'),
            reverse('website:robots_txt'),
            reverse('website:sitemap_xml'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_home_page_contains_branding(self):
        """Test that homepage contains Belings Driving School branding and key sections."""
        response = self.client.get(reverse('website:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Belings Driving School")
        self.assertContains(response, self.course.name)
        self.assertContains(response, self.instructor.full_name)
        self.assertContains(response, "Enroll Now")

    def test_contact_form_valid_submission(self):
        """Test that valid contact form submission creates ContactMessage record."""
        payload = {
            'name': 'John Kamau',
            'email': 'john.kamau@example.com',
            'phone': '0712345678',
            'subject': 'Inquiry about Category B Weekend Batch',
            'message': 'Hello, do you have space for Saturday classes next month?',
        }
        form = ContactForm(data=payload)
        self.assertTrue(form.is_valid())

        # Test POST view
        response = self.client.post(reverse('website:contact'), data=payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ContactMessage.objects.filter(email='john.kamau@example.com').exists())
        message = ContactMessage.objects.get(email='john.kamau@example.com')
        self.assertEqual(message.name, 'John Kamau')
        self.assertEqual(message.is_resolved, False)

    def test_contact_form_invalid_submission(self):
        """Test that missing required fields does not save a record."""
        payload = {
            'name': '',
            'email': 'invalid-email',
            'subject': '',
            'message': '',
        }
        form = ContactForm(data=payload)
        self.assertFalse(form.is_valid())

        response = self.client.post(reverse('website:contact'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_enrollment_form_creates_pending_student(self):
        """Test that enrollment form creates a pending Student record for staff to approve in admin."""
        payload = {
            'first_name': 'Wanjiku',
            'last_name': 'Mwangi',
            'email': 'wanjiku@example.com',
            'phone': '0722123456',
            'id_number': '31245678',
            'date_of_birth': '2001-05-15',
            'gender': 'F',
            'course': self.course.id,
            'preferred_schedule': 'morning',
            'preferred_branch': 'Main Campus Nairobi',
            'notes': 'Beginner with no prior driving experience.',
        }
        form = EnrollmentForm(data=payload)
        self.assertTrue(form.is_valid(), form.errors)

        # Submit via HTTP POST
        response = self.client.post(reverse('website:enroll'), data=payload)
        self.assertRedirects(response, reverse('website:enroll_success'))

        # Check student saved with pending status
        self.assertTrue(Student.objects.filter(id_number='31245678').exists())
        student = Student.objects.get(id_number='31245678')
        self.assertEqual(student.first_name, 'Wanjiku')
        self.assertEqual(student.last_name, 'Mwangi')
        self.assertEqual(student.status, 'pending')
        self.assertEqual(student.course, self.course)

    def test_course_detail_page(self):
        """Test that course detail page displays course specifics and fee in KES."""
        response = self.client.get(reverse('website:course_detail', kwargs={'slug': self.course.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.course.name)
        self.assertContains(response, "12,500")
        self.assertContains(response, "Practical Lessons")

    def test_fees_page_displays_database_rates(self):
        """Test fees page dynamically loads courses and fees from database."""
        response = self.client.get(reverse('website:fees'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.course.name)
        self.assertContains(response, "12,500")

    def test_site_settings_singleton(self):
        """Test that SiteSettings acts as a singleton."""
        s1 = SiteSettings.load()
        s2 = SiteSettings.load()
        self.assertEqual(s1.pk, s2.pk)
        self.assertEqual(SiteSettings.objects.count(), 1)

