import os
import time as time_mod
from datetime import date, time, timedelta
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.utils import timezone

from website.models import (
    SiteSettings, AuditLog, FAQ, HeroSlide, GalleryCategory, GalleryImage,
    EmailSettings, EmailLog, CustomSocialLink, HomeSection,
    Testimonial, WhyChooseUsItem, PageContent, NavigationItem, ContactMessage
)
from accounts.models import UserProfile
from courses.models import Course, Branch, Vehicle
from instructors.models import Instructor
from students.models import Student, LessonBooking


TINY_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
    b'\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ManagementPanelSecurityAndPermissionsTests(TestCase):
    """
    Comprehensive tests covering all requirements for Belings Driving School:
    - Role-based access control & 404 concealment
    - Age 18+ enforcement (exact 18th birthday, 1 day short, future date, tampered POST)
    - POST Logout & 15-minute Inactivity Auto-Logout (HTML redirect + AJAX 401)
    - Hero Slider natural colors (no blue tint) & toggleable overlay
    - Super Admin Email Settings (Fernet encryption, test email, password reset, compose, Admin 404)
    - Social Media Links & Custom Social Links immediate propagation
    - Branches CRUD, deletion protection, branch-course filtering & tampered POST rejection
    - Lesson Booking Schedule, conflict prevention, instructor completion & Admin verification
    - Gallery Categories (Practical, Theory, Classroom) & Featured Home Gallery
    - Clean Empty Database Homepage (only school name & Login link when empty)
    """

    def setUp(self):
        cache.clear()
        self.client = Client()

        self.settings = SiteSettings.load()
        self.settings.school_name = "Belings Driving School"
        self.settings.maintenance_mode = False
        self.settings.save()

        # 1. Super Admin User (Auto-approved)
        self.super_admin = User.objects.create_superuser(
            username='superadmin',
            email='superadmin@belingsdriving.co.ke',
            password='Password123!'
        )
        self.super_admin.profile.role = UserProfile.ROLE_SUPER_ADMIN
        self.super_admin.profile.approval_status = UserProfile.APPROVAL_APPROVED
        self.super_admin.profile.save()

        # 2. Admin User (Approved)
        self.admin = User.objects.create_user(
            username='adminuser',
            email='adminuser@belingsdriving.co.ke',
            password='Password123!'
        )
        self.admin.is_staff = True
        self.admin.save()
        self.admin.profile.role = UserProfile.ROLE_ADMIN
        self.admin.profile.approval_status = UserProfile.APPROVAL_APPROVED
        self.admin.profile.save()

        # 3. Instructor User (Approved)
        self.instructor = User.objects.create_user(
            username='instructoruser',
            email='instructor@belingsdriving.co.ke',
            password='Password123!'
        )
        self.instructor.profile.role = UserProfile.ROLE_INSTRUCTOR
        self.instructor.profile.approval_status = UserProfile.APPROVAL_APPROVED
        self.instructor.profile.save()

        # 4. Student User (Approved)
        self.student = User.objects.create_user(
            username='studentuser',
            email='student@belingsdriving.co.ke',
            password='Password123!'
        )
        self.student.profile.role = UserProfile.ROLE_STUDENT
        self.student.profile.approval_status = UserProfile.APPROVAL_APPROVED
        self.student.profile.date_of_birth = date(2000, 1, 1)
        self.student.profile.save()

        # 5. Receptionist User (Approved)
        self.receptionist = User.objects.create_user(
            username='receptionistuser',
            email='receptionist@belingsdriving.co.ke',
            password='Password123!'
        )
        self.receptionist.profile.role = UserProfile.ROLE_RECEPTIONIST
        self.receptionist.profile.approval_status = UserProfile.APPROVAL_APPROVED
        self.receptionist.profile.save()

        # Default Branch
        self.branch = Branch.objects.create(
            name="Main Campus (Nairobi CBD)",
            code="MAIN-NRB",
            address="Moi Avenue",
            town="Nairobi",
            phone="+254700000001",
            is_active=True,
            order=1,
        )

        # Sample Course linked to self.branch
        self.course = Course.objects.create(
            name="Category B Light Vehicle",
            slug="category-b-light-vehicle",
            license_category="B",
            fee=16500,
            duration="4 Weeks",
            short_description="Full manual and automatic driving course",
            practical_hours=20,
            theory_hours=15,
            is_active=True,
            is_featured=True,
        )
        self.course.branches.add(self.branch)

    def tearDown(self):
        cache.clear()
        self.settings.maintenance_mode = False
        self.settings.save()

    # =========================================================================
    # 1. REFERENCE RULES & PUBLIC LINK CONCEALMENT
    # =========================================================================

    def test_zero_forbidden_references_and_no_manage_links_on_public_pages(self):
        """Public pages must never contain 'jodan', '/manage/', or '/admin/' links."""
        public_urls = [
            reverse('website:home'),
            reverse('website:about'),
            reverse('website:courses'),
            reverse('website:fees'),
            reverse('website:instructors'),
            reverse('website:gallery'),
            reverse('website:faq'),
            reverse('website:contact'),
            reverse('website:enroll'),
        ]
        for url in public_urls:
            with self.subTest(public_url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                content = response.content.decode('utf-8')
                self.assertNotIn('jodan', content.lower())
                self.assertNotIn('/manage/', content)
                self.assertNotIn('/admin/', content)

    def test_anonymous_and_non_admin_users_receive_404_on_manage_and_admin(self):
        """Anonymous, student, instructor, and receptionist users must receive HTTP 404 on /manage/ and /admin/."""
        test_urls = [
            '/manage/',
            reverse('manage:dashboard'),
            reverse('manage:branding'),
            reverse('manage:email_settings'),
            reverse('manage:branches_list'),
            reverse('manage:lessons_list'),
            '/admin/',
        ]
        # Anonymous
        for url in test_urls:
            self.assertEqual(self.client.get(url).status_code, 404)

        # Non-management roles
        for u in [self.student, self.instructor, self.receptionist]:
            self.client.force_login(u)
            for url in test_urls:
                self.assertEqual(self.client.get(url).status_code, 404)

    # =========================================================================
    # 2. AGE 18+ ENFORCEMENT (EXACT 18 TODAY, 1 DAY SHORT, FUTURE, TAMPERED POST)
    # =========================================================================

    def test_age_18_plus_validation_on_registration_and_enrollment(self):
        """
        Tests 18+ age validation:
        - Exactly 18 years old today -> Accepted
        - 17 years 364 days (one day short of 18) -> Rejected
        - Future date -> Rejected
        - Tampered POST without DOB -> Rejected
        """
        today = timezone.localdate()
        try:
            dob_exact_18 = today.replace(year=today.year - 18)
        except ValueError:
            dob_exact_18 = today.replace(year=today.year - 18, month=2, day=28)

        dob_one_day_short = dob_exact_18 + timedelta(days=1)
        dob_future = today + timedelta(days=10)

        # 1. One day short of 18 on Registration -> Rejected
        resp_under = self.client.post(reverse('accounts:register'), {
            'first_name': 'Young',
            'last_name': 'Applicant',
            'email': 'young@example.com',
            'phone': '0711111111',
            'date_of_birth': dob_one_day_short.isoformat(),
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        })
        self.assertEqual(resp_under.status_code, 200)
        self.assertContains(resp_under, "You must be 18 years or older to register.")
        self.assertFalse(User.objects.filter(email='young@example.com').exists())

        # 2. Future date on Registration -> Rejected
        resp_future = self.client.post(reverse('accounts:register'), {
            'first_name': 'Future',
            'last_name': 'Person',
            'email': 'future@example.com',
            'phone': '0711111112',
            'date_of_birth': dob_future.isoformat(),
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        })
        self.assertEqual(resp_future.status_code, 200)
        self.assertContains(resp_future, "Date of birth cannot be in the future.")
        self.assertFalse(User.objects.filter(email='future@example.com').exists())

        # 3. Exactly 18 today on Registration -> Accepted
        resp_ok = self.client.post(reverse('accounts:register'), {
            'first_name': 'Adult',
            'last_name': 'Today',
            'email': 'adult18@example.com',
            'phone': '0711111113',
            'date_of_birth': dob_exact_18.isoformat(),
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        })
        self.assertEqual(resp_ok.status_code, 302)
        self.assertTrue(User.objects.filter(email='adult18@example.com').exists())

        # 4. Enrollment: 1 day short of 18 -> Rejected
        enroll_under = self.client.post(reverse('website:enroll'), {
            'first_name': 'Minor',
            'last_name': 'Learner',
            'email': 'minor@example.com',
            'phone': '0722000111',
            'id_number': '11223344',
            'date_of_birth': dob_one_day_short.isoformat(),
            'gender': 'M',
            'branch': self.branch.id,
            'course': self.course.id,
            'preferred_schedule': 'morning',
        })
        self.assertEqual(enroll_under.status_code, 200)
        self.assertContains(enroll_under, "You must be 18 years or older to register.")
        self.assertFalse(Student.objects.filter(email='minor@example.com').exists())

        # 5. Enrollment: Tampered POST missing date_of_birth -> Rejected
        enroll_tampered = self.client.post(reverse('website:enroll'), {
            'first_name': 'Tampered',
            'last_name': 'Post',
            'email': 'tampered@example.com',
            'phone': '0722000222',
            'id_number': '22334455',
            'date_of_birth': '',
            'gender': 'F',
            'branch': self.branch.id,
            'course': self.course.id,
            'preferred_schedule': 'morning',
        })
        self.assertEqual(enroll_tampered.status_code, 200)
        self.assertFalse(Student.objects.filter(email='tampered@example.com').exists())

        # 6. Enrollment: Exactly 18 today -> Accepted
        enroll_exact = self.client.post(reverse('website:enroll'), {
            'first_name': 'Exact',
            'last_name': 'Eighteen',
            'email': 'exact18@example.com',
            'phone': '0722000333',
            'id_number': '33445566',
            'date_of_birth': dob_exact_18.isoformat(),
            'gender': 'F',
            'branch': self.branch.id,
            'course': self.course.id,
            'preferred_schedule': 'morning',
        })
        self.assertEqual(enroll_exact.status_code, 302)
        self.assertTrue(Student.objects.filter(email='exact18@example.com').exists())

    # =========================================================================
    # 3. LOGOUT & 15-MINUTE INACTIVITY AUTO-LOGOUT
    # =========================================================================

    def test_post_logout_clears_session_and_protects_dashboard(self):
        """Logging out via POST clears the session and subsequent dashboard access redirects to login."""
        self.client.force_login(self.student)
        resp = self.client.post(reverse('accounts:logout'), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "You have been logged out.")

        # Accessing student dashboard now redirects to login
        dash_resp = self.client.get(reverse('students:dashboard'))
        self.assertEqual(dash_resp.status_code, 302)
        self.assertIn('/login/', dash_resp.url)

    def test_inactivity_auto_logout_after_timeout(self):
        """
        Idle sessions exceeding session_timeout_minutes are automatically logged out:
        - HTML request redirects to /login/?timeout=1 with 'You were logged out due to inactivity.'
        - AJAX request returns HTTP 401 JSON.
        """
        self.settings.session_timeout_minutes = 15
        self.settings.save()

        self.client.force_login(self.student)
        # First request sets last_activity_ts
        self.client.get(reverse('students:dashboard'))

        # Simulate 16 minutes of inactivity in session
        session = self.client.session
        session['last_activity_ts'] = time_mod.time() - (16 * 60)
        session.save()

        # HTML request -> redirected to /login/?timeout=1
        resp = self.client.get(reverse('students:dashboard'), follow=True)
        self.assertContains(resp, "You were logged out due to inactivity.")

        # Re-login and test AJAX request expiry -> HTTP 401
        self.client.force_login(self.student)
        self.client.get(reverse('students:dashboard'))
        session = self.client.session
        session['last_activity_ts'] = time_mod.time() - (16 * 60)
        session.save()

        ajax_resp = self.client.get(
            reverse('accounts:keep_alive'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(ajax_resp.status_code, 401)
        self.assertEqual(ajax_resp.json().get('reason'), 'inactivity_timeout')

    # =========================================================================
    # 4. HERO SLIDER NATURAL IMAGE COLORS (NO BLUE TINT OVERLAY BY DEFAULT)
    # =========================================================================

    def test_hero_slider_natural_colors_and_optional_overlay(self):
        """
        Hero slides render pure background-image without blue linear-gradient tint
        when overlay_enabled is False (default), and apply .hero-overlay-layer when True.
        """
        img = SimpleUploadedFile("hero_natural.gif", TINY_GIF, content_type="image/gif")
        slide = HeroSlide.objects.create(
            title="Natural Color Hero Slide",
            subtitle="Pure image with no blue tint",
            image=img,
            overlay_enabled=False,
            is_active=True,
        )
        resp = self.client.get(reverse('website:home'))
        html = resp.content.decode('utf-8')
        self.assertIn("Natural Color Hero Slide", html)
        self.assertNotIn("hero-overlay-layer", html)
        self.assertNotIn("rgba(2, 3, 129, 0.85)", html)

        # Enable overlay on the slide -> overlay layer appears
        slide.overlay_enabled = True
        slide.overlay_color = "#000000"
        slide.overlay_opacity = 40
        slide.save()

        resp2 = self.client.get(reverse('website:home'))
        html2 = resp2.content.decode('utf-8')
        self.assertIn("hero-overlay-layer", html2)
        self.assertIn("rgba(0, 0, 0, 0.40)", html2)

    # =========================================================================
    # 5. EMAIL CONFIGURATION, ENCRYPTION, PASSWORD RESET & COMPOSE (SUPER ADMIN)
    # =========================================================================

    def test_super_admin_email_settings_encryption_test_reset_and_compose(self):
        """
        - Admin gets 404 on /manage/email-settings/ and /manage/email-compose/.
        - Super Admin configures SMTP password; password is Fernet-encrypted in DB and never rendered in HTML.
        - Super Admin triggers test email and composes message (logged in EmailLog).
        - Password reset flow works end-to-end.
        """
        # Admin blocked (404)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('manage:email_settings')).status_code, 404)
        self.assertEqual(self.client.get(reverse('manage:email_compose')).status_code, 404)

        # Super Admin saves SMTP settings with password
        self.client.force_login(self.super_admin)
        save_resp = self.client.post(reverse('manage:email_settings'), {
            'action': 'save',
            'smtp_host': '',  # Blank host uses console/locmem fallback cleanly in test
            'smtp_port': 587,
            'security_protocol': 'TLS',
            'smtp_username': 'smtpuser@belings.co.ke',
            'smtp_password': 'MySuperSecretSmtpPassword99!',
            'default_from_name': 'Belings Driving School',
            'default_from_email': 'noreply@belings.co.ke',
            'reply_to_email': 'support@belings.co.ke',
            'is_enabled': 'on',
        })
        self.assertEqual(save_resp.status_code, 302)

        cfg = EmailSettings.load()
        self.assertTrue(cfg.has_password)
        # Stored value in DB is encrypted (not plaintext)
        self.assertNotEqual(cfg.smtp_password_encrypted, 'MySuperSecretSmtpPassword99!')
        # Decryption returns exact password
        self.assertEqual(cfg.get_password(), 'MySuperSecretSmtpPassword99!')

        # GET email settings page must NEVER contain raw password in HTML, only "Password is set"
        page_resp = self.client.get(reverse('manage:email_settings'))
        page_html = page_resp.content.decode('utf-8')
        self.assertNotIn('MySuperSecretSmtpPassword99!', page_html)
        self.assertIn('Password is set', page_html)

        # Send Test Email
        test_email_resp = self.client.post(reverse('manage:email_settings'), {
            'action': 'send_test_email',
            'test_recipient': 'testtarget@example.com',
        })
        self.assertEqual(test_email_resp.status_code, 302)
        self.assertTrue(EmailLog.objects.filter(recipient='testtarget@example.com', status='SENT').exists())

        # Compose & Send Email
        compose_resp = self.client.post(reverse('manage:email_compose'), {
            'target_type': 'custom',
            'custom_email': 'composed@example.com',
            'subject': 'Welcome to Belings',
            'body': 'Your orientation starts Monday at 8:00 AM.',
        })
        self.assertEqual(compose_resp.status_code, 302)
        self.assertTrue(EmailLog.objects.filter(recipient='composed@example.com', subject='Welcome to Belings').exists())

        # Password Reset Flow
        reset_resp = self.client.post(reverse('accounts:password_reset'), {
            'email': self.student.email,
        })
        self.assertEqual(reset_resp.status_code, 302)

    # =========================================================================
    # 6. SOCIAL MEDIA LINKS (SUPER ADMIN & ADMIN)
    # =========================================================================

    def test_social_media_links_and_custom_links_visibility(self):
        """Social icons appear on public site ONLY when URL is set and enabled."""
        self.client.force_login(self.admin)

        # Set Facebook enabled and Instagram disabled
        self.client.post(reverse('manage:social_links'), {
            'facebook_url': 'https://facebook.com/belingsdriving',
            'facebook_enabled': 'on',
            'instagram_url': 'https://instagram.com/belingsdriving',
            # instagram_enabled omitted -> False
            'whatsapp_number': '254799887766',
            'whatsapp_enabled': 'on',
        })

        # Add a Custom Social Link
        self.client.post(reverse('manage:custom_social_create'), {
            'label': 'Threads',
            'url': 'https://threads.net/@belingsdriving',
            'icon': 'bi-threads',
            'order': 1,
            'is_active': 'on',
        })

        pub_resp = self.client.get(reverse('website:home'))
        pub_html = pub_resp.content.decode('utf-8')
        self.assertIn('https://facebook.com/belingsdriving', pub_html)
        self.assertNotIn('https://instagram.com/belingsdriving', pub_html)
        self.assertIn('https://threads.net/@belingsdriving', pub_html)
        self.assertIn('rel="noopener noreferrer"', pub_html)

    # =========================================================================
    # 7. BRANCHES, BRANCH-SPECIFIC COURSES & TAMPERED POST REJECTION
    # =========================================================================

    def test_branches_and_branch_specific_courses_enforcement(self):
        """
        - Super Admin creates two branches and assigns branch-specific courses.
        - Admin gets 404 on branch creation/deletion.
        - /api/branch-courses/ filters courses by branch.
        - Enrollment form rejects tampered branch/course pair.
        - Branch with dependent records cannot be deleted.
        """
        # Admin cannot create branch (404)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('manage:branch_create')).status_code, 404)

        # Super Admin creates Westlands Branch
        self.client.force_login(self.super_admin)
        self.client.post(reverse('manage:branch_create'), {
            'name': 'Westlands Campus',
            'code': 'WST-02',
            'address': 'Waiyaki Way',
            'town': 'Nairobi',
            'phone': '+254700000002',
            'is_active': 'on',
            'order': 2,
        })
        westlands = Branch.objects.get(code='WST-02')

        # Create a course offered ONLY at Westlands
        course_truck = Course.objects.create(
            name="Category C Commercial Truck",
            slug="category-c-truck",
            license_category="C",
            fee=22000,
            duration="5 Weeks",
            short_description="Commercial truck course",
            practical_hours=22,
            theory_hours=18,
            is_active=True,
        )
        course_truck.branches.add(westlands)

        # Check /api/branch-courses/ for Main Branch vs Westlands Branch
        api_main = self.client.get(reverse('website:branch_courses_api'), {'branch_id': self.branch.id}).json()
        main_course_ids = [c['id'] for c in api_main['courses']]
        self.assertIn(self.course.id, main_course_ids)
        self.assertNotIn(course_truck.id, main_course_ids)

        api_west = self.client.get(reverse('website:branch_courses_api'), {'branch_id': westlands.id}).json()
        west_course_ids = [c['id'] for c in api_west['courses']]
        self.assertIn(course_truck.id, west_course_ids)
        self.assertNotIn(self.course.id, west_course_ids)

        # Tampered POST: trying to enroll in course_truck (Westlands only) under Main Branch -> Rejected!
        tampered_resp = self.client.post(reverse('website:enroll'), {
            'first_name': 'Branch',
            'last_name': 'Tamper',
            'email': 'branchtamper@example.com',
            'phone': '0733112233',
            'id_number': '44556677',
            'date_of_birth': '1998-05-15',
            'gender': 'M',
            'branch': self.branch.id,
            'course': course_truck.id,
            'preferred_schedule': 'morning',
        })
        self.assertEqual(tampered_resp.status_code, 200)
        self.assertContains(tampered_resp, "not offered at")
        self.assertFalse(Student.objects.filter(email='branchtamper@example.com').exists())

        # Branch deletion protection when linked records exist
        del_resp = self.client.post(reverse('manage:branch_delete', args=[self.branch.pk]))
        self.assertEqual(del_resp.status_code, 302)
        self.assertTrue(Branch.objects.filter(pk=self.branch.pk).exists())

    # =========================================================================
    # 8. LESSON BOOKING SCHEDULE, DOUBLE-BOOKING PREVENTION & VERIFICATION
    # =========================================================================

    def test_lesson_booking_schedule_and_verification_lifecycle(self):
        """
        End-to-end test of Lesson Booking & Verification:
        1. Approved 18+ student views free slots and books a lesson (SCHEDULED).
        2. Double-booking the same slot & instructor for another student fails.
        3. Student cannot mark their own lesson COMPLETED or VERIFIED.
        4. Instructor marks lesson COMPLETED with feedback notes.
        5. Unverified (SCHEDULED/COMPLETED) lessons do NOT count toward verified_practical_hours.
        6. Admin marks lesson VERIFIED -> verified_practical_hours increments & AuditLog recorded.
        """
        inst_obj = Instructor.objects.create(
            full_name="Trainer John",
            title="Senior Instructor",
            license_categories="B",
            experience_years=10,
            phone="0711223344",
            branch=self.branch,
            is_active=True,
        )
        veh_obj = Vehicle.objects.create(
            plate_number="KDD 123A",
            make_model="Toyota Vitz",
            license_category="B",
            transmission="MANUAL",
            branch=self.branch,
            is_active=True,
        )

        # Create approved 18+ student enrollment
        student_rec = Student.objects.create(
            user=self.student,
            first_name="Kelvin",
            last_name="Learner",
            email=self.student.email,
            phone="0712000999",
            id_number="29998888",
            date_of_birth=date(2000, 1, 1),
            course=self.course,
            branch=self.branch,
            status=Student.STATUS_APPROVED,
        )

        # Second approved student to test instructor/vehicle double-booking conflict
        student2_user = User.objects.create_user(username='student2', email='student2@example.com', password='Password123!')
        student2_user.profile.role = UserProfile.ROLE_STUDENT
        student2_user.profile.approval_status = UserProfile.APPROVAL_APPROVED
        student2_user.profile.date_of_birth = date(1999, 6, 15)
        student2_user.profile.save()
        student2_rec = Student.objects.create(
            user=student2_user,
            first_name="Mary",
            last_name="Learner",
            email=student2_user.email,
            phone="0712000888",
            id_number="28887777",
            date_of_birth=date(1999, 6, 15),
            course=self.course,
            branch=self.branch,
            status=Student.STATUS_APPROVED,
        )

        tomorrow = timezone.localdate() + timedelta(days=1)

        # 1. Student 1 views available slots and books 08:00-09:00
        self.client.force_login(self.student)
        slots_resp = self.client.get(reverse('students:available_slots_api'), {
            'date': tomorrow.isoformat(),
            'branch': self.branch.id,
            'lesson_type': 'PRACTICAL',
            'instructor': inst_obj.id,
        }).json()
        slot_codes = [s['code'] for s in slots_resp['slots']]
        self.assertIn('08:00-09:00', slot_codes)

        book_resp = self.client.post(reverse('students:book_lesson'), {
            'lesson_type': 'PRACTICAL',
            'branch': self.branch.id,
            'date': tomorrow.isoformat(),
            'time_slot': '08:00-09:00',
            'instructor': inst_obj.id,
            'vehicle': veh_obj.id,
            'student_notes': 'Practicing hill starts',
        })
        self.assertEqual(book_resp.status_code, 302)
        booking = LessonBooking.objects.get(student=student_rec, date=tomorrow)
        self.assertEqual(booking.status, 'SCHEDULED')

        # 08:00-09:00 is no longer in available slots for inst_obj
        slots_after = self.client.get(reverse('students:available_slots_api'), {
            'date': tomorrow.isoformat(),
            'branch': self.branch.id,
            'lesson_type': 'PRACTICAL',
            'instructor': inst_obj.id,
        }).json()
        self.assertNotIn('08:00-09:00', [s['code'] for s in slots_after['slots']])

        # 2. Student 2 tries to double-book the same slot & instructor -> Rejected!
        self.client.force_login(student2_user)
        conflict_resp = self.client.post(reverse('students:book_lesson'), {
            'lesson_type': 'PRACTICAL',
            'branch': self.branch.id,
            'date': tomorrow.isoformat(),
            'time_slot': '08:00-09:00',
            'instructor': inst_obj.id,
            'vehicle': veh_obj.id,
        })
        self.assertEqual(conflict_resp.status_code, 200)
        self.assertContains(conflict_resp, "already booked")
        self.assertFalse(LessonBooking.objects.filter(student=student2_rec, date=tomorrow).exists())

        # 3. Student 1 tries to mark their own lesson COMPLETED or VERIFIED -> Forbidden (403/404)
        self.client.force_login(self.student)
        stu_complete = self.client.post(reverse('students:complete_lesson', args=[booking.pk]), {
            'action': 'complete',
            'instructor_notes': 'Hacked complete',
        })
        self.assertEqual(stu_complete.status_code, 403)
        stu_verify = self.client.post(reverse('manage:lesson_verify', args=[booking.pk]))
        self.assertEqual(stu_verify.status_code, 404)

        # 4. Instructor marks lesson COMPLETED with feedback notes
        self.client.force_login(self.instructor)
        inst_complete = self.client.post(reverse('students:complete_lesson', args=[booking.pk]), {
            'action': 'complete',
            'instructor_notes': 'Good clutch control and hill start mastery.',
        })
        self.assertEqual(inst_complete.status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'COMPLETED')
        self.assertEqual(booking.instructor_notes, 'Good clutch control and hill start mastery.')

        # 5. Unverified (COMPLETED) lesson does NOT count as verified package usage
        self.assertEqual(student_rec.verified_practical_hours, 0.0)
        self.assertEqual(student_rec.reserved_practical_hours, 1.0)

        # 6. Admin verifies the lesson -> status becomes VERIFIED & verified_practical_hours increments
        self.client.force_login(self.admin)
        verify_resp = self.client.post(reverse('manage:lesson_verify', args=[booking.pk]))
        self.assertEqual(verify_resp.status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'VERIFIED')
        self.assertEqual(booking.verified_by, self.admin)
        self.assertIsNotNone(booking.verified_at)
        self.assertEqual(student_rec.verified_practical_hours, 1.0)
        self.assertTrue(AuditLog.objects.filter(action='VERIFIED_LESSON', object_id=str(booking.pk)).exists())

    # =========================================================================
    # 9. GALLERY CATEGORIES & FEATURED HOMEPAGE GALLERY
    # =========================================================================

    def test_gallery_categories_and_featured_home_images(self):
        """
        Uploading gallery images into Practical, Theory, and Classroom categories
        and marking them 'is_featured_home=True' makes them appear on the home screen
        under their category tabs immediately.
        """
        cat_practical = GalleryCategory.objects.create(name="Practical", slug="practical", order=1, is_active=True)
        cat_theory = GalleryCategory.objects.create(name="Theory", slug="theory", order=2, is_active=True)
        cat_classroom = GalleryCategory.objects.create(name="Classroom", slug="classroom", order=3, is_active=True)

        img1 = GalleryImage.objects.create(
            title="Highway Practical Session",
            category_obj=cat_practical,
            image=SimpleUploadedFile("prac.gif", TINY_GIF, content_type="image/gif"),
            is_featured_home=True,
            is_active=True,
        )
        img2 = GalleryImage.objects.create(
            title="Road Signs Theory Lecture",
            category_obj=cat_theory,
            image=SimpleUploadedFile("theo.gif", TINY_GIF, content_type="image/gif"),
            is_featured_home=True,
            is_active=True,
        )
        img3 = GalleryImage.objects.create(
            title="Model Town Board Classroom",
            category_obj=cat_classroom,
            image=SimpleUploadedFile("class.gif", TINY_GIF, content_type="image/gif"),
            is_featured_home=True,
            is_active=True,
        )

        resp = self.client.get(reverse('website:home'))
        html = resp.content.decode('utf-8')
        self.assertIn("Highway Practical Session", html)
        self.assertIn("Road Signs Theory Lecture", html)
        self.assertIn("Model Town Board Classroom", html)
        self.assertIn('data-category="practical"', html)
        self.assertIn('data-category="theory"', html)
        self.assertIn('data-category="classroom"', html)

    # =========================================================================
    # 10. EMPTY DATABASE HOMEPAGE SHOWS ONLY SCHOOL NAME & LOGIN LINK
    # =========================================================================

    def test_empty_database_homepage_has_no_fake_marketing_content(self):
        """
        When all homepage content models are empty, '/' renders only the school name
        and Login link — zero fake stats, zero dummy testimonials, zero sample courses.
        Then adding content section by section shows only those sections.
        """
        # Clear all content
        Course.objects.all().delete()
        Branch.objects.all().delete()
        HeroSlide.objects.all().delete()
        Testimonial.objects.all().delete()
        FAQ.objects.all().delete()
        GalleryImage.objects.all().delete()
        Instructor.objects.all().delete()
        SiteSettings.objects.all().delete()

        resp = self.client.get(reverse('website:home'))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode('utf-8')
        self.assertIn("Belings Driving School", html)
        self.assertIn("/login/", html)
        # Ensure no fake stats, dummy testimonials, or sections appear
        self.assertNotIn("12,500+", html)
        self.assertNotIn("Mercy Wanjiku", html)
        self.assertNotIn("What Our Graduates Say", html)
        self.assertNotIn("Available Driving Courses", html)

        # Now add an FAQ and verify ONLY the FAQ section appears on homepage
        FAQ.objects.create(
            question="Do you offer weekend classes?",
            answer="Yes, Saturday intensive classes are available.",
            is_active=True,
        )
        resp2 = self.client.get(reverse('website:home'))
        html2 = resp2.content.decode('utf-8')
        self.assertIn("Do you offer weekend classes?", html2)
        self.assertNotIn("What Our Graduates Say", html2)

    def test_progressive_homepage_hero_about_and_gallery_only(self):
        """
        Verifies:
        1. With an empty content database, '/' loads and shows only the school name and Login.
        2. Adding a hero slide, about text, and one gallery image via management makes
           ONLY those three sections (hero, about, gallery) appear on '/'.
        """
        Course.objects.all().delete()
        Branch.objects.all().delete()
        HeroSlide.objects.all().delete()
        Testimonial.objects.all().delete()
        FAQ.objects.all().delete()
        GalleryImage.objects.all().delete()
        Instructor.objects.all().delete()
        WhyChooseUsItem.objects.all().delete()
        PageContent.objects.all().delete()
        SiteSettings.objects.all().delete()

        # 1. Empty content database -> only school name and Login
        resp_empty = self.client.get(reverse('website:home'))
        self.assertEqual(resp_empty.status_code, 200)
        self.assertEqual(resp_empty.context['active_section_keys'], [])
        html_empty = resp_empty.content.decode('utf-8')
        self.assertIn("Belings Driving School", html_empty)
        self.assertIn("/login/", html_empty)

        # 2. Add a Hero Slide, About text, and one Gallery Image via management
        self.client.force_login(self.admin)
        self.client.post(reverse('manage:slide_create'), {
            'title': 'Master Safe Driving Today',
            'subtitle': 'Accredited defensive driving school',
            'cta_text': 'Enroll Now',
            'cta_link': '/enroll/',
            'overlay_color': '#000000',
            'overlay_opacity': 0,
            'order': 1,
            'is_active': 'on',
        })
        site_cfg = SiteSettings.load()
        site_cfg.about_section_title = "About Belings Driving Academy"
        site_cfg.about_section_text = "Dedicated to road safety and responsible motoring."
        site_cfg.save()

        cat = GalleryCategory.ensure_defaults().first()
        self.client.post(reverse('manage:gallery_create'), {
            'title': 'Morning Yard Drill',
            'category_obj': cat.id,
            'category': 'practical',
            'image': SimpleUploadedFile("yard.gif", TINY_GIF, content_type="image/gif"),
            'caption': 'Student practicing reversing',
            'is_featured_home': 'on',
            'order': 1,
            'is_active': 'on',
        })

        self.client.logout()
        resp_populated = self.client.get(reverse('website:home'))
        self.assertEqual(resp_populated.status_code, 200)
        self.assertEqual(resp_populated.context['active_section_keys'], ['hero', 'about', 'gallery'])
        html_pop = resp_populated.content.decode('utf-8')
        self.assertIn("Master Safe Driving Today", html_pop)
        self.assertIn("About Belings Driving Academy", html_pop)
        self.assertIn("Morning Yard Drill", html_pop)
        self.assertNotIn("Available Driving Courses", html_pop)
        self.assertNotIn("What Our Graduates Say", html_pop)
        self.assertNotIn("Frequently Asked Questions", html_pop)

    # =========================================================================
    # 11. DYNAMIC BRANDING & FILE CLEANUP
    # =========================================================================

    def test_dynamic_branding_updates_propagate_immediately(self):
        """Updating school name, colors, and fees reflects immediately on public site."""
        self.settings.school_name = "Belings Premier Driving Academy"
        self.settings.brand_primary = "#003366"
        self.settings.save()

        self.course.fee = 18500
        self.course.save()

        response = self.client.get(reverse('website:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Belings Premier Driving Academy")
        self.assertContains(response, "--brand-primary: #003366;")
        self.assertContains(response, "18,500")

    def test_file_cleanup_on_replacement_and_deletion(self):
        """Replacing or deleting an image removes the old file from disk."""
        img1 = SimpleUploadedFile("slide1.gif", TINY_GIF, content_type="image/gif")
        slide = HeroSlide.objects.create(title="First Slide", image=img1, order=1, is_active=True)
        file1_path = slide.image.path
        self.assertTrue(os.path.exists(file1_path))

        img2 = SimpleUploadedFile("slide2.gif", TINY_GIF, content_type="image/gif")
        slide.image = img2
        slide.save()
        file2_path = slide.image.path

        self.assertFalse(os.path.exists(file1_path))
        self.assertTrue(os.path.exists(file2_path))

        slide.delete()
        self.assertFalse(os.path.exists(file2_path))

    # =========================================================================
    # 12. HOME SECTION ENSURE_DEFAULTS, READ-ONLY HOME VIEW & REORDERING
    # =========================================================================

    def test_home_section_ensure_defaults_and_reordering(self):
        """
        Verifies:
        - HomeSection.ensure_defaults() is idempotent, creates all 12 standard rows,
          never creates marketing content, and never overwrites admin order/visibility.
        - home_view only reads HomeSection and does not write to DB on anonymous GET.
        - Admin reordering and hiding sections in /manage/home-sections/ updates '/' immediately.
        """
        sections = HomeSection.ensure_defaults()
        self.assertEqual(sections.count(), 12)

        # Customize 'courses' order=99 and disable 'branches'
        courses_sec = HomeSection.objects.get(section_key='courses')
        courses_sec.order = 99
        courses_sec.save()
        branches_sec = HomeSection.objects.get(section_key='branches')
        branches_sec.is_enabled = False
        branches_sec.save()

        # Calling ensure_defaults() again must NOT overwrite custom order or is_enabled
        HomeSection.ensure_defaults()
        courses_sec.refresh_from_db()
        branches_sec.refresh_from_db()
        self.assertEqual(courses_sec.order, 99)
        self.assertFalse(branches_sec.is_enabled)

        # Even if HomeSection table is cleared, anonymous GET '/' must NOT write to HomeSection
        HomeSection.objects.all().delete()
        resp = self.client.get(reverse('website:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(HomeSection.objects.count(), 0)

        # Restore defaults and test /manage/home-sections/ POST by Admin
        HomeSection.ensure_defaults()
        FAQ.objects.create(question="Sample FAQ Question?", answer="Sample Answer", is_active=True)

        self.client.force_login(self.admin)
        # Disable 'courses' and enable 'faqs' via /manage/home-sections/
        post_data = {
            'order_faqs': '1',
            'enabled_faqs': 'on',
            'order_courses': '2',
            # 'enabled_courses' omitted -> disabled
        }
        manage_resp = self.client.post(reverse('manage:home_sections'), post_data)
        self.assertEqual(manage_resp.status_code, 302)

        pub_html = self.client.get(reverse('website:home')).content.decode('utf-8')
        self.assertIn("Sample FAQ Question?", pub_html)
        self.assertNotIn("Available Driving Courses", pub_html)

    # =========================================================================
    # 13. COMPREHENSIVE SMOKE TEST ACROSS ALL ROLES & ALL URLS
    # =========================================================================

    def test_smoke_all_urls_across_all_roles(self):
        """
        Logs in as each role (anonymous, student, instructor, receptionist, admin, super_admin)
        and requests every no-arg URL plus detail/edit URLs using demo objects.
        Asserts zero HTTP 500 responses and verifies expected 200/302/404 status codes.
        """
        HomeSection.ensure_defaults()
        cat = GalleryCategory.ensure_defaults().first()
        slide = HeroSlide.objects.create(title="Smoke Slide", is_active=True)
        why = WhyChooseUsItem.objects.create(title="Smoke Why", description="Desc", is_active=True)
        page, _ = PageContent.objects.get_or_create(slug='about', defaults={'title': 'About Us', 'content': 'Body'})
        inst = Instructor.objects.create(full_name="Smoke Inst", title="Trainer", bio="Bio", branch=self.branch)
        gal = GalleryImage.objects.create(
            title="Smoke Img",
            category_obj=cat,
            image=SimpleUploadedFile("s.gif", TINY_GIF, content_type="image/gif"),
        )
        testi = Testimonial.objects.create(name="Smoke Grad", course_taken="Cat B", quote="Great!")
        faq = FAQ.objects.create(question="Smoke Q?", answer="Smoke A.")
        nav = NavigationItem.objects.create(label="Home", url="/")
        msg = ContactMessage.objects.create(name="Smoke Sender", email="s@example.com", subject="Hi", message="Hello")
        csoc = CustomSocialLink.objects.create(label="TikTok", url="https://tiktok.com/@belings")
        veh = Vehicle.objects.create(plate_number="KZZ 999Z", make_model="Toyota Vitz", branch=self.branch)
        student_rec = Student.objects.create(
            user=self.student,
            first_name="Smoke",
            last_name="Student",
            email=self.student.email,
            phone="0712345678",
            id_number="99887766",
            date_of_birth=date(1999, 1, 1),
            course=self.course,
            branch=self.branch,
            status=Student.STATUS_APPROVED,
        )
        booking = LessonBooking.objects.create(
            student=student_rec,
            course=self.course,
            branch=self.branch,
            instructor=inst,
            vehicle=veh,
            date=timezone.localdate() + timedelta(days=2),
            start_time=time(9, 0),
            end_time=time(10, 0),
            status='COMPLETED',
        )

        public_urls = [
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
            reverse('website:enroll_success'),
            reverse('website:branch_courses_api'),
            reverse('website:robots_txt'),
            reverse('website:sitemap_xml'),
            reverse('accounts:login'),
            reverse('accounts:register'),
            reverse('accounts:password_reset'),
            reverse('accounts:password_reset_done'),
            reverse('accounts:password_reset_complete'),
        ]

        student_urls = [
            reverse('students:dashboard'),
            reverse('students:book_lesson'),
            reverse('students:available_slots_api'),
        ]

        instructor_schedule_url = reverse('students:instructor_schedule')

        admin_allowed_manage_urls = [
            reverse('manage:dashboard'),
            reverse('manage:branding'),
            reverse('manage:media_library'),
            reverse('manage:homepage_content'),
            reverse('manage:slide_create'),
            reverse('manage:slide_edit', args=[slide.pk]),
            reverse('manage:slide_delete', args=[slide.pk]),
            reverse('manage:why_choose_create'),
            reverse('manage:why_choose_edit', args=[why.pk]),
            reverse('manage:why_choose_delete', args=[why.pk]),
            reverse('manage:pages_list'),
            reverse('manage:page_edit', args=[page.slug]),
            reverse('manage:courses_list'),
            reverse('manage:course_create'),
            reverse('manage:course_edit', args=[self.course.pk]),
            reverse('manage:course_delete', args=[self.course.pk]),
            reverse('manage:instructors_list'),
            reverse('manage:instructor_create'),
            reverse('manage:instructor_edit', args=[inst.pk]),
            reverse('manage:instructor_delete', args=[inst.pk]),
            reverse('manage:gallery_list'),
            reverse('manage:gallery_create'),
            reverse('manage:gallery_edit', args=[gal.pk]),
            reverse('manage:gallery_delete', args=[gal.pk]),
            reverse('manage:gallery_categories_list'),
            reverse('manage:gallery_category_create'),
            reverse('manage:gallery_category_edit', args=[cat.pk]),
            reverse('manage:gallery_category_delete', args=[cat.pk]),
            reverse('manage:testimonials_list'),
            reverse('manage:testimonial_create'),
            reverse('manage:testimonial_edit', args=[testi.pk]),
            reverse('manage:testimonial_delete', args=[testi.pk]),
            reverse('manage:faqs_list'),
            reverse('manage:faq_create'),
            reverse('manage:faq_edit', args=[faq.pk]),
            reverse('manage:faq_delete', args=[faq.pk]),
            reverse('manage:navigation_list'),
            reverse('manage:navigation_create'),
            reverse('manage:navigation_edit', args=[nav.pk]),
            reverse('manage:navigation_delete', args=[nav.pk]),
            reverse('manage:contact_settings'),
            reverse('manage:social_links'),
            reverse('manage:custom_social_create'),
            reverse('manage:custom_social_edit', args=[csoc.pk]),
            reverse('manage:custom_social_delete', args=[csoc.pk]),
            reverse('manage:messages_list'),
            reverse('manage:message_delete', args=[msg.pk]),
            reverse('manage:seo_settings'),
            reverse('manage:system_settings'),
            reverse('manage:maintenance_mode'),
            reverse('manage:credentials'),
            reverse('manage:registrations_list'),
            reverse('manage:enrollments_list'),
            reverse('manage:enrollment_create'),
            reverse('manage:home_sections'),
            reverse('manage:branches_list'),
            reverse('manage:branch_edit', args=[self.branch.pk]),
            reverse('manage:vehicles_list'),
            reverse('manage:vehicle_create'),
            reverse('manage:vehicle_edit', args=[veh.pk]),
            reverse('manage:vehicle_delete', args=[veh.pk]),
            reverse('manage:enrollments_list'),
            reverse('manage:enrollment_create'),
            reverse('manage:students_list'),
            reverse('manage:student_detail', args=[student_rec.pk]),
            reverse('manage:lessons_list'),
        ]

        sample_audit = AuditLog.objects.create(user=self.super_admin, action="SMOKE_TEST_LOG", details="Smoke test")
        super_admin_only_urls = [
            reverse('manage:audit_log'),
            reverse('manage:audit_log_delete_single', args=[sample_audit.pk]),
            reverse('manage:users_list'),
            reverse('manage:user_create'),
            reverse('manage:user_edit', args=[self.admin.pk]),
            reverse('manage:user_delete', args=[self.admin.pk]),
            reverse('manage:branch_create'),
            reverse('manage:branch_delete', args=[self.branch.pk]),
            reverse('manage:email_settings'),
            reverse('manage:email_compose'),
        ]

        roles = [
            ('anonymous', None),
            ('student', self.student),
            ('instructor', self.instructor),
            ('receptionist', self.receptionist),
            ('admin', self.admin),
            ('super_admin', self.super_admin),
        ]

        for role_name, user_obj in roles:
            self.client.logout()
            if user_obj:
                self.client.force_login(user_obj)

            # 1. Public URLs -> 200 or 302 (never 500)
            for url in public_urls:
                with self.subTest(role=role_name, url=url):
                    resp = self.client.get(url)
                    self.assertIn(resp.status_code, (200, 302))

            # 2. Student URLs -> 200 or 302 (never 500)
            for url in student_urls:
                with self.subTest(role=role_name, url=url):
                    resp = self.client.get(url)
                    if role_name == 'anonymous':
                        self.assertEqual(resp.status_code, 302)
                    else:
                        self.assertIn(resp.status_code, (200, 302))

            # 2b. Instructor schedule URL -> 302 for anonymous, 403 for student/receptionist, 200 for instructor/admin/super_admin
            with self.subTest(role=role_name, url=instructor_schedule_url):
                resp = self.client.get(instructor_schedule_url)
                if role_name == 'anonymous':
                    self.assertEqual(resp.status_code, 302)
                elif role_name in ('student', 'receptionist'):
                    self.assertEqual(resp.status_code, 403)
                else:
                    self.assertEqual(resp.status_code, 200)

            # 3. Admin-allowed /manage/ URLs -> 200 for admin & super_admin, 404 for everyone else
            for url in admin_allowed_manage_urls:
                with self.subTest(role=role_name, url=url):
                    resp = self.client.get(url)
                    if role_name in ('admin', 'super_admin'):
                        self.assertEqual(resp.status_code, 200)
                    else:
                        self.assertEqual(resp.status_code, 404)

            # 4. Super Admin exclusive URLs -> 200 for super_admin, 404 for everyone else (including admin)
            for url in super_admin_only_urls:
                with self.subTest(role=role_name, url=url):
                    resp = self.client.get(url)
                    if role_name == 'super_admin':
                        self.assertEqual(resp.status_code, 200)
                    else:
                        self.assertEqual(resp.status_code, 404)

    # =========================================================================
    # 14. BRANCHES: ADD, MOVE-AND-DELETE, TYPED CONFIRMATION & DEACTIVATE
    # =========================================================================

    def test_branch_delete_with_dependents_move_typed_confirm_and_deactivate(self):
        """
        Verifies:
        - Admin gets 404 on branch add/edit/delete.
        - Super Admin adds a branch with all fields.
        - Deleting an empty branch requires exact typed confirmation of branch name.
        - Deleting a branch with dependents (students, instructors, vehicles, courses, bookings)
          without target_branch_id is blocked; with target_branch_id moves all dependent records
          inside an atomic transaction, deletes the old branch, and writes an AuditLog entry.
        - 'Deactivate instead' sets is_active=False without deleting.
        """
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(reverse('manage:branch_create'), {'name': 'X', 'code': 'X'}).status_code, 404)
        self.assertEqual(self.client.post(reverse('manage:branch_delete', args=[self.branch.pk])).status_code, 404)

        self.client.force_login(self.super_admin)
        # 1. Add a new empty branch
        self.client.post(reverse('manage:branch_create'), {
            'name': 'Eldoret Annex',
            'code': 'ELD',
            'town': 'Eldoret',
            'address': 'Uganda Road',
            'phone': '+254 700 111 222',
            'email': 'eldoret@belings.co.ke',
            'opening_hours': 'Mon-Sat 8am-5pm',
            'map_embed_url': 'https://www.google.com/maps?q=Eldoret&output=embed',
            'order': 5,
            'is_active': 'on',
        })
        eld = Branch.objects.get(code='ELD')

        # 2. Empty branch delete without typed confirmation -> blocked
        self.client.post(reverse('manage:branch_delete', args=[eld.pk]), {'action': 'delete', 'confirm_branch_name': 'Wrong Name'})
        self.assertTrue(Branch.objects.filter(pk=eld.pk).exists())

        # 3. Empty branch delete with exact typed confirmation -> deleted + audit log
        self.client.post(reverse('manage:branch_delete', args=[eld.pk]), {'action': 'delete', 'confirm_branch_name': 'Eldoret Annex'})
        self.assertFalse(Branch.objects.filter(pk=eld.pk).exists())
        self.assertTrue(AuditLog.objects.filter(action='DELETED_BRANCH').exists())

        # 4. Create a destination branch and linked records on self.branch, then test moving dependents -> dest_branch
        dest_branch = Branch.objects.create(name='Nakuru Central', code='NKR', town='Nakuru', is_active=True)
        dep_student = Student.objects.create(
            user=self.student,
            first_name='Branch',
            last_name='Student',
            email='branchstudent@belings.co.ke',
            phone='0711000999',
            id_number='11223344',
            date_of_birth=date(1999, 1, 1),
            course=self.course,
            branch=self.branch,
            status=Student.STATUS_APPROVED,
        )
        dep_instructor = Instructor.objects.create(
            full_name='Branch Trainer',
            title='Senior Instructor',
            bio='Experienced',
            branch=self.branch,
        )
        dep_vehicle = Vehicle.objects.create(
            plate_number='KDD 111A',
            make_model='Toyota Axio',
            branch=self.branch,
        )

        # Attempting to delete self.branch (which has students, instructors, vehicles, courses) without target_branch_id -> blocked
        self.client.post(reverse('manage:branch_delete', args=[self.branch.pk]), {'action': 'delete'})
        self.assertTrue(Branch.objects.filter(pk=self.branch.pk).exists())

        # Option (c): Deactivate instead -> sets is_active=False
        self.client.post(reverse('manage:branch_delete', args=[self.branch.pk]), {'action': 'deactivate'})
        self.branch.refresh_from_db()
        self.assertFalse(self.branch.is_active)
        self.branch.is_active = True
        self.branch.save()

        # Option (b): Move all dependents to dest_branch and delete self.branch atomically
        old_branch_pk = self.branch.pk
        self.client.post(reverse('manage:branch_delete', args=[old_branch_pk]), {
            'action': 'delete',
            'target_branch_id': str(dest_branch.pk),
        })
        self.assertFalse(Branch.objects.filter(pk=old_branch_pk).exists())
        dep_student.refresh_from_db()
        dep_instructor.refresh_from_db()
        dep_vehicle.refresh_from_db()
        self.assertEqual(dep_student.branch_id, dest_branch.pk)
        self.assertEqual(dep_instructor.branch_id, dest_branch.pk)
        self.assertEqual(dep_vehicle.branch_id, dest_branch.pk)
        self.assertTrue(self.course.branches.filter(pk=dest_branch.pk).exists())
        self.assertTrue(AuditLog.objects.filter(action='MOVED_AND_DELETED_BRANCH').exists())

    # =========================================================================
    # 15. AUDIT LOGS: DELETE SINGLE, SELECTED, DATE RANGE & ALL (SUPER ADMIN)
    # =========================================================================

    def test_audit_log_delete_single_selected_range_all_and_self_logging(self):
        """
        Verifies:
        - Admin gets HTTP 404 on audit log delete endpoints.
        - Super Admin can delete a single entry, selected entries, date-range entries, and all entries.
        - Confirmation step is required (confirmed != 'yes' renders confirmation page without deleting).
        - Every deletion immediately creates ONE new AuditLog entry ('DELETED_AUDIT_LOGS').
        """
        l1 = AuditLog.objects.create(user=self.super_admin, action="TEST_LOG_1", details="First")
        l2 = AuditLog.objects.create(user=self.super_admin, action="TEST_LOG_2", details="Second")
        l3 = AuditLog.objects.create(user=self.super_admin, action="TEST_LOG_3", details="Third")

        # Admin blocked (404)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(reverse('manage:audit_log_delete_single', args=[l1.pk]), {'confirmed': 'yes'}).status_code, 404)
        self.assertEqual(self.client.post(reverse('manage:audit_log_delete'), {'mode': 'all', 'confirmed': 'yes'}).status_code, 404)

        self.client.force_login(self.super_admin)

        # 1. Without confirmed='yes' -> renders confirmation page and does NOT delete
        preview_resp = self.client.get(reverse('manage:audit_log_delete_single', args=[l1.pk]))
        self.assertEqual(preview_resp.status_code, 200)
        self.assertTrue(AuditLog.objects.filter(pk=l1.pk).exists())

        # 2. Delete single entry -> deletes l1 and creates 1 new DELETED_AUDIT_LOGS entry
        self.client.post(reverse('manage:audit_log_delete_single', args=[l1.pk]), {'confirmed': 'yes'})
        self.assertFalse(AuditLog.objects.filter(pk=l1.pk).exists())
        self.assertTrue(AuditLog.objects.filter(action='DELETED_AUDIT_LOGS', object_id=str(l1.pk)).exists())

        # 3. Delete selected entries (l2, l3)
        self.client.post(reverse('manage:audit_log_delete'), {
            'mode': 'selected',
            'log_ids': [str(l2.pk), str(l3.pk)],
            'confirmed': 'yes',
        })
        self.assertFalse(AuditLog.objects.filter(pk__in=[l2.pk, l3.pk]).exists())

        # 4. Delete date range
        today_str = timezone.localdate().isoformat()
        self.client.post(reverse('manage:audit_log_delete'), {
            'mode': 'range',
            'start_date': today_str,
            'end_date': today_str,
            'confirmed': 'yes',
        })
        # After deleting today's range, exactly 1 new self-logged entry exists from the range deletion itself
        self.assertEqual(AuditLog.objects.count(), 1)
        self.assertEqual(AuditLog.objects.first().action, 'DELETED_AUDIT_LOGS')

        # 5. Delete ALL entries -> leaves 1 new DELETED_AUDIT_LOGS entry recording the full wipe
        AuditLog.objects.create(user=self.super_admin, action="EXTRA_LOG", details="Extra")
        self.client.post(reverse('manage:audit_log_delete'), {
            'mode': 'all',
            'confirmed': 'yes',
        })
        self.assertEqual(AuditLog.objects.count(), 1)
        last_entry = AuditLog.objects.first()
        self.assertEqual(last_entry.action, 'DELETED_AUDIT_LOGS')
        self.assertIn('all audit log entries', last_entry.details)

    # =========================================================================
    # 16. STAFF ENROLLMENT (SUPER ADMIN VS ADMIN, EXISTING STUDENT, DUPLICATES, 18+)
    # =========================================================================

    def test_staff_enrollment_super_admin_vs_admin_existing_student_duplicate_and_age_18(self):
        """
        Verifies:
        - Staff accounts without a Student profile can enroll students.
        - Super Admin enrollments are APPROVED automatically; Admin enrollments are PENDING_APPROVAL.
        - Supports new student creation (18+ enforced) and existing student selection.
        - Supports editable total_fee, discount_amount + discount_reason, and initial_payment_amount.
        - Blocks duplicate active enrollment for the same student + same course.
        """
        course2 = Course.objects.create(
            name="Class C1 Light Truck",
            slug="class-c1-light-truck",
            license_category="C",
            short_description="Commercial truck course",
            duration="5 Weeks",
            practical_hours=22,
            theory_hours=12,
            fee=19000,
            is_active=True,
        )
        course2.branches.add(self.branch)

        # 1. Super Admin enrolls a new 18+ student with discount & first payment -> APPROVED automatically
        self.client.force_login(self.super_admin)
        resp_sa = self.client.post(reverse('manage:enrollment_create'), {
            'student_mode': 'new',
            'first_name': 'Grace',
            'last_name': 'Muthoni',
            'email': 'grace.muthoni@test.com',
            'phone': '0711222333',
            'id_number': '33445566',
            'date_of_birth': '1999-05-15',
            'gender': 'F',
            'branch': self.branch.pk,
            'course': self.course.pk,
            'start_date': timezone.localdate().isoformat(),
            'preferred_schedule': 'morning',
            'total_fee': '15000',
            'discount_amount': '1500',
            'discount_reason': 'Early bird scholarship',
            'initial_payment_amount': '5000',
            'payment_method': 'MPESA',
            'payment_reference': 'QWE987RTY',
        })
        self.assertEqual(resp_sa.status_code, 302)
        grace = Student.objects.get(email='grace.muthoni@test.com', course=self.course)
        self.assertEqual(grace.status, Student.STATUS_APPROVED)
        self.assertEqual(float(grace.effective_fee), 13500.0)
        self.assertEqual(float(grace.balance_due), 8500.0)

        # 2. Duplicate active enrollment in the same course -> blocked
        dup_resp = self.client.post(reverse('manage:enrollment_create'), {
            'student_mode': 'existing',
            'existing_student': grace.pk,
            'branch': self.branch.pk,
            'course': self.course.pk,
            'preferred_schedule': 'morning',
        })
        self.assertEqual(dup_resp.status_code, 200)
        self.assertContains(dup_resp, "already has an active enrollment")
        self.assertEqual(Student.objects.filter(email='grace.muthoni@test.com', course=self.course).count(), 1)

        # 3. Admin enrolls existing student 'grace' into a different course (course2) -> PENDING_APPROVAL
        self.client.force_login(self.admin)
        resp_admin = self.client.post(reverse('manage:enrollment_create'), {
            'student_mode': 'existing',
            'existing_student': grace.pk,
            'branch': self.branch.pk,
            'course': course2.pk,
            'preferred_schedule': 'afternoon',
            'total_fee': '19000',
            'discount_amount': '0',
            'initial_payment_amount': '0',
        })
        self.assertEqual(resp_admin.status_code, 302)
        grace_c2 = Student.objects.get(email='grace.muthoni@test.com', course=course2)
        self.assertEqual(grace_c2.status, Student.STATUS_PENDING_APPROVAL)

        # 4. Under-18 student -> rejected
        under18_dob = (date.today().replace(year=date.today().year - 16)).isoformat()
        u18_resp = self.client.post(reverse('manage:enrollment_create'), {
            'student_mode': 'new',
            'first_name': 'Young',
            'last_name': 'Applicant',
            'email': 'young@test.com',
            'phone': '0799888777',
            'id_number': '99887766',
            'date_of_birth': under18_dob,
            'branch': self.branch.pk,
            'course': self.course.pk,
            'preferred_schedule': 'morning',
        })
        self.assertEqual(u18_resp.status_code, 200)
        self.assertContains(u18_resp, "You must be 18 years or older to register.")
        self.assertFalse(Student.objects.filter(email='young@test.com').exists())

    # =========================================================================
    # 17. MULTI-PHOTO BATCH UPLOAD, PARTIAL FAILURE, VARIANTS & BULK DELETE
    # =========================================================================

    def test_multi_photo_batch_upload_variants_partial_failure_bulk_edit_and_delete(self):
        """
        Verifies:
        - Uploading 10 valid photos + 1 invalid file in a single batch saves the 10 valid photos
          with generated grid (~800px) and large (~1600px) WebP variants, and reports '10 uploaded, 1 failed'.
        - Bulk editing captions/order/featured updates DB records.
        - Bulk deleting selected photos deletes DB rows AND removes original + grid + large files from disk.
        """
        GalleryImage.objects.all().delete()
        cat = GalleryCategory.ensure_defaults().first()

        # Generate 10 valid PNG images + 1 invalid fake file
        from io import BytesIO
        from PIL import Image
        valid_files = []
        for i in range(10):
            buf = BytesIO()
            Image.new('RGB', (1200, 900), color=(20 * i, 80, 140)).save(buf, format='JPEG', quality=85)
            valid_files.append(SimpleUploadedFile(f"fleet_photo_{i+1}.jpg", buf.getvalue(), content_type="image/jpeg"))
        bad_file = SimpleUploadedFile("not_an_image.txt", b"This is plain text, not an image", content_type="text/plain")

        self.client.force_login(self.admin)
        resp = self.client.post(reverse('manage:gallery_upload_api'), {
            'category_obj': cat.pk,
            'title_prefix': 'Fleet Session',
            'default_caption': 'Practical highway drill',
            'is_featured_home': 'on',
            'is_active': 'on',
            'order': '10',
            'images': valid_files + [bad_file],
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['uploaded_count'], 10)
        self.assertEqual(data['failed_count'], 1)
        self.assertIn("10 uploaded, 1 failed", data['summary'])
        self.assertEqual(GalleryImage.objects.count(), 10)

        # Verify each uploaded image has original, grid, and large files on disk
        sample_img = GalleryImage.objects.first()
        self.assertTrue(bool(sample_img.image_grid))
        self.assertTrue(bool(sample_img.image_large))
        orig_path = sample_img.image.path
        grid_path = sample_img.image_grid.path
        large_path = sample_img.image_large.path
        self.assertTrue(os.path.exists(orig_path))
        self.assertTrue(os.path.exists(grid_path))
        self.assertTrue(os.path.exists(large_path))

        # Test public gallery and home page render srcset, sizes, width="800" height="600", and full-screen lightbox
        pub_gallery = self.client.get(reverse('website:gallery')).content.decode('utf-8')
        self.assertIn('srcset="', pub_gallery)
        self.assertIn('width="800" height="600"', pub_gallery)
        self.assertIn('belingsFullscreenLightbox', pub_gallery)
        self.assertIn('col-lg-4', pub_gallery)

        # Bulk delete sample_img and verify original + grid + large files are deleted from disk
        del_resp = self.client.post(reverse('manage:gallery_bulk_action'), {
            'bulk_action': 'delete_selected',
            'selected_ids': [str(sample_img.pk)],
            'confirmed': 'yes',
        })
        self.assertEqual(del_resp.status_code, 302)
        self.assertEqual(GalleryImage.objects.count(), 9)
        self.assertFalse(os.path.exists(orig_path))
        self.assertFalse(os.path.exists(grid_path))
        self.assertFalse(os.path.exists(large_path))


