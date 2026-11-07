from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
from website.models import SiteSettings, AuditLog
from accounts.models import UserProfile
from courses.models import Course

class ManagementPanelSecurityAndPermissionsTests(TestCase):
    """
    Comprehensive tests enforcing role-based access control and security
    for Belings Driving School's management panel (/manage/).
    """
    def setUp(self):
        cache.clear()
        self.client = Client()

        # Site Settings - ensure clean state and maintenance mode OFF
        self.settings = SiteSettings.load()
        self.settings.school_name = "Belings Driving School"
        self.settings.maintenance_mode = False
        self.settings.save()

        # 1. Super Admin User
        self.super_admin = User.objects.create_superuser(
            username='superadmin',
            email='superadmin@belingsdriving.co.ke',
            password='Password123!'
        )
        self.super_admin.profile.role = UserProfile.ROLE_SUPER_ADMIN
        self.super_admin.profile.save()

        # 2. Admin User
        self.admin = User.objects.create_user(
            username='adminuser',
            email='adminuser@belingsdriving.co.ke',
            password='Password123!'
        )
        self.admin.is_staff = True
        self.admin.save()
        self.admin.profile.role = UserProfile.ROLE_ADMIN
        self.admin.profile.save()

        # 3. Instructor User
        self.instructor = User.objects.create_user(
            username='instructoruser',
            email='instructor@belingsdriving.co.ke',
            password='Password123!'
        )
        self.instructor.profile.role = UserProfile.ROLE_INSTRUCTOR
        self.instructor.profile.save()

        # 4. Student User
        self.student = User.objects.create_user(
            username='studentuser',
            email='student@belingsdriving.co.ke',
            password='Password123!'
        )
        self.student.profile.role = UserProfile.ROLE_STUDENT
        self.student.profile.save()

        # 5. Receptionist User
        self.receptionist = User.objects.create_user(
            username='receptionistuser',
            email='receptionist@belingsdriving.co.ke',
            password='Password123!'
        )
        self.receptionist.profile.role = UserProfile.ROLE_RECEPTIONIST
        self.receptionist.profile.save()

    def tearDown(self):
        cache.clear()
        self.settings.maintenance_mode = False
        self.settings.save()

    def test_anonymous_user_redirected_to_login(self):
        """Anonymous users must be redirected to login on any /manage/ URL."""
        test_urls = [
            reverse('manage:dashboard'),
            reverse('manage:branding'),
            reverse('manage:media_library'),
            reverse('manage:homepage_content'),
            reverse('manage:pages_list'),
            reverse('manage:courses_list'),
            reverse('manage:instructors_list'),
            reverse('manage:audit_log'),
            reverse('manage:users_list'),
        ]
        for url in test_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn('/login/', response.url)

    def test_student_and_instructor_and_receptionist_forbidden(self):
        """
        Instructors, students, and receptionists have ZERO access to the site
        management panel. The server must return 403 Forbidden.
        """
        restricted_users = [self.student, self.instructor, self.receptionist]
        test_urls = [
            reverse('manage:dashboard'),
            reverse('manage:branding'),
            reverse('manage:media_library'),
            reverse('manage:homepage_content'),
            reverse('manage:pages_list'),
            reverse('manage:courses_list'),
            reverse('manage:audit_log'),
            reverse('manage:users_list'),
        ]

        for u in restricted_users:
            self.client.force_login(u)
            for url in test_urls:
                with self.subTest(user=u.username, role=u.profile.role, url=url):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 403)

    def test_admin_has_access_to_management_but_not_super_admin_views(self):
        """
        Role ADMIN can manage website content, operational settings, courses,
        and view masked credentials, but is strictly blocked (403) from:
        - Audit Log (manage:audit_log)
        - User Account Administration (manage:users_list)
        """
        self.client.force_login(self.admin)

        # Permitted URLs (HTTP 200)
        allowed_urls = [
            reverse('manage:dashboard'),
            reverse('manage:branding'),
            reverse('manage:media_library'),
            reverse('manage:homepage_content'),
            reverse('manage:pages_list'),
            reverse('manage:courses_list'),
            reverse('manage:instructors_list'),
            reverse('manage:gallery_list'),
            reverse('manage:testimonials_list'),
            reverse('manage:faqs_list'),
            reverse('manage:navigation_list'),
            reverse('manage:contact_settings'),
            reverse('manage:messages_list'),
            reverse('manage:seo_settings'),
            reverse('manage:system_settings'),
            reverse('manage:maintenance_mode'),
            reverse('manage:credentials'),
        ]
        for url in allowed_urls:
            with self.subTest(allowed_url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

        # Blocked URLs (HTTP 403)
        blocked_urls = [
            reverse('manage:audit_log'),
            reverse('manage:users_list'),
            reverse('manage:user_create'),
        ]
        for url in blocked_urls:
            with self.subTest(blocked_url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

    def test_super_admin_has_full_access_to_all_views(self):
        """Role SUPER_ADMIN has full access to all 14 screens including audit log and user management."""
        self.client.force_login(self.super_admin)

        all_urls = [
            reverse('manage:dashboard'),
            reverse('manage:branding'),
            reverse('manage:media_library'),
            reverse('manage:homepage_content'),
            reverse('manage:pages_list'),
            reverse('manage:courses_list'),
            reverse('manage:instructors_list'),
            reverse('manage:gallery_list'),
            reverse('manage:testimonials_list'),
            reverse('manage:faqs_list'),
            reverse('manage:navigation_list'),
            reverse('manage:contact_settings'),
            reverse('manage:messages_list'),
            reverse('manage:seo_settings'),
            reverse('manage:system_settings'),
            reverse('manage:maintenance_mode'),
            reverse('manage:audit_log'),
            reverse('manage:credentials'),
            reverse('manage:users_list'),
        ]
        for url in all_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_admin_sees_masked_credentials(self):
        """Admin views sensitive credentials with masked characters."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('manage:credentials'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Masked")
        self.assertContains(response, "●●●●●●●●●●")

    def test_audit_log_records_changes(self):
        """Saving changes through the management panel creates an AuditLog record."""
        self.client.force_login(self.admin)
        post_data = {
            'school_name': 'Belings Elite Driving School',
            'tagline': 'Professional Driver Training',
            'brand_primary': '#020381',
            'brand_secondary': '#e9a825',
            'brand_accent': '#25D366',
            'font_heading': "'Roboto Slab', serif",
            'font_body': "'Inter', sans-serif",
        }
        response = self.client.post(reverse('manage:branding'), post_data)
        self.assertEqual(response.status_code, 302)

        # Verify audit log recorded
        self.assertTrue(AuditLog.objects.filter(action='UPDATED_BRANDING').exists())
        log = AuditLog.objects.filter(action='UPDATED_BRANDING').first()
        self.assertEqual(log.user, self.admin)
        self.assertEqual(log.model_name, 'SiteSettings')

    def test_dynamic_brand_colors_in_public_html(self):
        """Changing brand colors reflects dynamically in the public site <style> root block."""
        self.settings.brand_primary = '#112233'
        self.settings.brand_secondary = '#445566'
        self.settings.brand_accent = '#778899'
        self.settings.save()

        response = self.client.get(reverse('website:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '--brand-primary: #112233;')
        self.assertContains(response, '--brand-secondary: #445566;')
        self.assertContains(response, '--brand-accent: #778899;')

    def test_maintenance_mode_enforcement(self):
        """
        When maintenance_mode is enabled:
        - Anonymous visitor gets 503 Service Unavailable.
        - Admin user can still view the site and management panel.
        """
        self.settings.maintenance_mode = True
        self.settings.maintenance_message = "Routine engine tuning in progress."
        self.settings.save()

        try:
            # Anonymous public request -> HTTP 503
            anon_response = self.client.get(reverse('website:home'))
            self.assertEqual(anon_response.status_code, 503)
            self.assertContains(anon_response, "Routine engine tuning in progress.", status_code=503)

            # Authenticated Admin request -> HTTP 200
            self.client.force_login(self.admin)
            admin_response = self.client.get(reverse('website:home'))
            self.assertEqual(admin_response.status_code, 200)
        finally:
            # Always restore maintenance mode to False
            self.settings.maintenance_mode = False
            self.settings.save()
            cache.clear()
