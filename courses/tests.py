from decimal import Decimal

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from accounts.models import UserProfile
from courses.map_utils import normalize_map_embed_url
from courses.models import Branch
from website.models import SiteSettings

PB_EMBED = (
    "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3989.5!2d34.7667!3d-0.6817"
    "!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2sOuru%20Power!5e0!3m2!1sen!2ske"
)


class MapInputNormalizationTests(SimpleTestCase):
    """Pure validation of what admins may paste into the map field."""

    def test_valid_embed_url_is_accepted(self):
        self.assertEqual(normalize_map_embed_url(PB_EMBED), PB_EMBED)
        simple = "https://www.google.com/maps?q=Ouru+Power+Kisii&output=embed"
        self.assertEqual(normalize_map_embed_url(f"  {simple}  "), simple)

    def test_empty_is_allowed_and_returns_empty(self):
        self.assertEqual(normalize_map_embed_url(""), "")
        self.assertEqual(normalize_map_embed_url("   "), "")
        self.assertEqual(normalize_map_embed_url(None), "")

    def test_pasted_iframe_is_reduced_to_src_and_amp_converted(self):
        snippet = (
            '<iframe src="https://www.google.com/maps/embed?pb=!1m18&amp;q=Ouru&amp;zoom=16" '
            'width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" '
            'referrerpolicy="no-referrer-when-downgrade" onload="alert(1)"></iframe>'
        )
        cleaned = normalize_map_embed_url(snippet)
        self.assertEqual(cleaned, "https://www.google.com/maps/embed?pb=!1m18&q=Ouru&zoom=16")
        self.assertNotIn("<", cleaned)
        self.assertNotIn("onload", cleaned)
        self.assertNotIn("&amp;", cleaned)

    def test_plain_url_with_amp_entities_is_converted(self):
        cleaned = normalize_map_embed_url("https://www.google.com/maps?q=Kisii&amp;z=16&amp;output=embed")
        self.assertEqual(cleaned, "https://www.google.com/maps?q=Kisii&z=16&output=embed")

    def test_non_google_urls_are_rejected(self):
        bad = [
            "https://evil.example.com/maps?q=Kisii",
            "https://www.openstreetmap.org/export/embed.html",
            "http://www.google.com/maps?q=Kisii",                      # not https
            "https://www.google.com.evil.com/maps?q=Kisii",            # look-alike host
            "https://www.google.com@evil.com/maps?q=Kisii",            # userinfo trick
            "https://www.google.com/mapsevil?q=Kisii",                 # path only starts with /maps
            "https://www.google.com/search?q=maps",
            "//www.google.com/maps?q=Kisii",
            "www.google.com/maps?q=Kisii",
            "ftp://www.google.com/maps",
            "https://www.google.com/maps?q=a b",                       # whitespace
            'https://www.google.com/maps?q="onload=alert(1)',          # quote injection
        ]
        for value in bad:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    normalize_map_embed_url(value)

    def test_javascript_url_is_rejected(self):
        for value in ("javascript:alert(1)", "JaVaScRiPt:alert(document.cookie)", "data:text/html;base64,PHNjcmlwdD4=",
                      '<iframe src="javascript:alert(1)"></iframe>'):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    normalize_map_embed_url(value)

    def test_injected_script_and_other_html_is_rejected(self):
        bad = [
            "<script>alert(1)</script>",
            '<script src="https://www.google.com/maps"></script>',
            '<iframe src="https://www.google.com/maps?q=a"></iframe><script>alert(1)</script>',
            '<iframe src="https://www.google.com/maps?q=a"></iframe> trailing text',
            '<div><iframe src="https://www.google.com/maps?q=a"></iframe></div>',
            '<img src=x onerror=alert(1)>',
            '<iframe></iframe>',
            '<iframe src="https://www.google.com/maps?q=a"></iframe><iframe src="https://www.google.com/maps?q=b"></iframe>',
        ]
        for value in bad:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    normalize_map_embed_url(value)


class BranchMapPropertyTests(TestCase):
    def test_priority_embed_then_coordinates_then_address(self):
        branch = Branch(name="B", code="B1", address="Ouru Power building, Kisii Town, Kisii County", town="Kisii",
                        map_embed_url=PB_EMBED, latitude=Decimal("-0.6817"), longitude=Decimal("34.7667"), map_zoom=15)
        self.assertEqual(branch.map_src, PB_EMBED)

        branch.map_embed_url = ""
        self.assertEqual(branch.map_src, "https://www.google.com/maps?q=-0.681700,34.766700&z=15&output=embed")

        branch.latitude = branch.longitude = None
        self.assertEqual(
            branch.map_src,
            "https://www.google.com/maps?q=Ouru+Power+building%2C+Kisii+Town%2C+Kisii+County&z=15&output=embed",
        )

    def test_directions_url(self):
        branch = Branch(name="B", code="B2", address="Ouru Power building, Kisii Town, Kisii County", town="Kisii")
        self.assertEqual(
            branch.directions_url,
            "https://www.google.com/maps/dir/?api=1&destination=Ouru+Power+building%2C+Kisii+Town%2C+Kisii+County",
        )
        branch.latitude, branch.longitude = Decimal("-0.6817"), Decimal("34.7667")
        self.assertEqual(
            branch.directions_url,
            "https://www.google.com/maps/dir/?api=1&destination=-0.681700%2C34.766700",
        )

    def test_default_zoom_is_16(self):
        self.assertEqual(Branch(name="B", code="B3").map_zoom, 16)

    def test_no_map_data_means_no_map(self):
        branch = Branch(name="B", code="B4", town="Kisii")
        self.assertEqual(branch.map_src, "")
        self.assertFalse(branch.has_map)
        self.assertEqual(branch.directions_url, "")

    def test_unsafe_stored_value_is_never_used(self):
        """Even if bad data reaches the DB (e.g. raw SQL), it is not rendered."""
        branch = Branch(name="B", code="B5", address="Kisii Town", map_embed_url="javascript:alert(1)")
        self.assertNotIn("javascript", branch.map_src)
        self.assertTrue(branch.map_src.startswith("https://www.google.com/maps?q=Kisii+Town"))
        branch.address = ""
        self.assertEqual(branch.map_src, "")

    def test_model_clean_normalizes_iframe_and_rejects_bad_value(self):
        branch = Branch(name="B", code="B6", map_embed_url='<iframe src="https://www.google.com/maps?q=a&amp;z=3"></iframe>')
        branch.clean()
        self.assertEqual(branch.map_embed_url, "https://www.google.com/maps?q=a&z=3")
        branch.map_embed_url = "https://evil.example.com/x"
        with self.assertRaises(ValidationError):
            branch.clean()

    def test_latitude_requires_longitude(self):
        branch = Branch(name="B", code="B7", latitude=Decimal("1.5"))
        with self.assertRaises(ValidationError):
            branch.clean()


def _make_user(username, role, staff=False):
    user = User.objects.create_user(username=username, email=f"{username}@example.com", password="Password123!")
    user.is_staff = staff
    user.save()
    user.profile.role = role
    user.profile.approval_status = UserProfile.APPROVAL_APPROVED
    user.profile.save()
    return user


class BranchMapManagementAndPublicTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        settings_obj = SiteSettings.load()
        settings_obj.school_name = "Belings Driving School"
        settings_obj.maintenance_mode = False
        settings_obj.save()

        self.super_admin = User.objects.create_superuser("mapsuper", "mapsuper@example.com", "Password123!")
        self.super_admin.profile.role = UserProfile.ROLE_SUPER_ADMIN
        self.super_admin.profile.approval_status = UserProfile.APPROVAL_APPROVED
        self.super_admin.profile.save()
        self.admin = _make_user("mapadmin", UserProfile.ROLE_ADMIN, staff=True)
        self.instructor = _make_user("mapinstructor", UserProfile.ROLE_INSTRUCTOR)
        self.student = _make_user("mapstudent", UserProfile.ROLE_STUDENT)
        self.receptionist = _make_user("maprecep", UserProfile.ROLE_RECEPTIONIST)

        self.branch = Branch.objects.create(
            name="Main Campus - Kisii", code="MAIN-KSI", address="Ouru Power building, Kisii Town, Kisii County",
            town="Kisii", phone="+254700000001", email="kisii@example.com",
            opening_hours="Mon - Fri: 8am - 5pm",
            map_embed_url="https://www.google.com/maps?q=Ouru+Power+Kisii&output=embed", is_active=True, order=1,
        )

    # ---------------- public pages ----------------

    def test_contact_page_shows_kisii_map_with_buttons_and_no_nairobi(self):
        resp = self.client.get(reverse('website:contact'))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn('<iframe src="https://www.google.com/maps?q=Ouru+Power+Kisii&amp;output=embed"', html)
        self.assertIn('loading="lazy"', html)
        self.assertIn('referrerpolicy="no-referrer-when-downgrade"', html)
        self.assertIn('title="Map showing the location of Main Campus - Kisii', html)
        self.assertIn('branch-map-frame', html)
        self.assertIn("Ouru Power building, Kisii Town, Kisii County", html)
        self.assertIn("+254700000001", html)
        self.assertIn("kisii@example.com", html)
        self.assertIn("Mon - Fri: 8am - 5pm", html)
        self.assertIn("Open in Google Maps", html)
        self.assertIn("Get directions", html)
        self.assertIn(
            'href="https://www.google.com/maps/dir/?api=1&amp;destination=Ouru+Power+building%2C+Kisii+Town%2C+Kisii+County" '
            'target="_blank" rel="noopener noreferrer"', html)
        self.assertIn(
            'href="https://www.google.com/maps/search/?api=1&amp;query=Ouru+Power+building%2C+Kisii+Town%2C+Kisii+County" '
            'target="_blank" rel="noopener noreferrer"', html)
        self.assertNotIn("Nairobi", html)
        self.assertNotIn("1.2833", html)

    def test_empty_map_hides_the_section_completely(self):
        Branch.objects.filter(pk=self.branch.pk).update(map_embed_url="", address="", latitude=None, longitude=None)
        resp = self.client.get(reverse('website:contact'))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertNotIn("<iframe", html)
        self.assertNotIn("branch-map-card", html)
        self.assertNotIn("branch-maps", html)
        self.assertNotIn("Find Us", html)
        self.assertNotIn("google.com/maps", html)
        self.assertNotIn("Open in Google Maps", html)

    def test_no_branches_means_no_map_and_no_default_map(self):
        Branch.objects.all().delete()
        html = self.client.get(reverse('website:contact')).content.decode()
        self.assertNotIn("<iframe", html)
        self.assertNotIn("google.com/maps", html)

    def test_branch_with_only_address_gets_address_based_map(self):
        Branch.objects.filter(pk=self.branch.pk).update(map_embed_url="")
        html = self.client.get(reverse('website:contact')).content.decode()
        self.assertIn("https://www.google.com/maps?q=Ouru+Power+building%2C+Kisii+Town%2C+Kisii+County&amp;z=16&amp;output=embed", html)

    def test_tampered_db_value_is_not_rendered(self):
        Branch.objects.filter(pk=self.branch.pk).update(map_embed_url='javascript:alert(1)"><script>alert(1)</script>')
        html = self.client.get(reverse('website:contact')).content.decode()
        self.assertNotIn("javascript:", html)
        self.assertNotIn("<script>alert(1)", html)

    def test_public_pages_have_no_site_wide_nairobi_map(self):
        self.assertFalse(hasattr(SiteSettings.load(), 'map_embed_url'))
        for name in ('website:home', 'website:contact', 'website:about'):
            with self.subTest(page=name):
                html = self.client.get(reverse(name)).content.decode()
                self.assertNotIn("2sNairobi", html)
                self.assertNotIn("Nairobi%2C%20Kenya", html)

    # ---------------- management ----------------

    def _edit_url(self):
        return reverse('manage:branch_edit', args=[self.branch.pk])

    def test_super_admin_can_edit_map_fields_and_whole_branch(self):
        self.client.force_login(self.super_admin)
        resp = self.client.get(self._edit_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Google Maps &gt; Share &gt; Embed a map &gt; copy the link")
        self.assertContains(resp, "UNVERIFIED")
        self.assertContains(resp, 'id="mapPreviewFrame"')

        resp = self.client.post(self._edit_url(), {
            'name': 'Main Campus - Kisii', 'code': 'MAIN-KSI', 'address': 'New Address, Kisii', 'town': 'Kisii',
            'phone': '+254700000001', 'email': 'kisii@example.com', 'opening_hours': 'Mon - Fri',
            'map_embed_url': '<iframe src="https://www.google.com/maps/embed?pb=!1m1&amp;x=2"></iframe>',
            'latitude': '-0.6817', 'longitude': '34.7667', 'map_zoom': '18', 'order': 1, 'is_active': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        self.branch.refresh_from_db()
        self.assertEqual(self.branch.map_embed_url, "https://www.google.com/maps/embed?pb=!1m1&x=2")
        self.assertEqual(self.branch.latitude, Decimal("-0.681700"))
        self.assertEqual(self.branch.map_zoom, 18)
        self.assertEqual(self.branch.address, "New Address, Kisii")

    def test_admin_can_edit_map_fields_only(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self._edit_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Google Maps &gt; Share &gt; Embed a map &gt; copy the link")
        self.assertNotContains(resp, 'name="name"')

        resp = self.client.post(self._edit_url(), {
            'map_embed_url': 'https://www.google.com/maps?q=Exact+Pin&output=embed',
            'latitude': '', 'longitude': '', 'map_zoom': '17',
            # tampering attempt: these must be ignored for an Admin
            'name': 'Hacked', 'code': 'HACK', 'address': 'Hacked address', 'is_active': '',
        })
        self.assertEqual(resp.status_code, 302)
        self.branch.refresh_from_db()
        self.assertEqual(self.branch.map_embed_url, "https://www.google.com/maps?q=Exact+Pin&output=embed")
        self.assertEqual(self.branch.map_zoom, 17)
        self.assertEqual(self.branch.name, "Main Campus - Kisii")
        self.assertEqual(self.branch.code, "MAIN-KSI")
        self.assertEqual(self.branch.address, "Ouru Power building, Kisii Town, Kisii County")
        self.assertTrue(self.branch.is_active)

    def test_admin_still_cannot_create_or_delete_branches(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('manage:branch_create')).status_code, 404)
        self.assertEqual(self.client.post(reverse('manage:branch_delete', args=[self.branch.pk])).status_code, 404)
        self.assertTrue(Branch.objects.filter(pk=self.branch.pk).exists())

    def test_invalid_map_input_is_rejected_with_clear_message_and_not_saved(self):
        original = self.branch.map_embed_url
        for role_user in (self.admin, self.super_admin):
            self.client.force_login(role_user)
            for bad in ("https://evil.example.com/maps", "javascript:alert(1)", "<script>alert(1)</script>",
                        '<iframe src="https://evil.example.com"></iframe>', "http://www.google.com/maps?q=a"):
                with self.subTest(user=role_user.username, value=bad):
                    data = {'map_embed_url': bad, 'latitude': '', 'longitude': '', 'map_zoom': '16'}
                    if role_user is self.super_admin:
                        data.update({'name': 'Main Campus - Kisii', 'code': 'MAIN-KSI', 'order': 1, 'is_active': 'on'})
                    resp = self.client.post(self._edit_url(), data)
                    self.assertEqual(resp.status_code, 200)
                    self.assertContains(resp, "https://www.google.com/maps")
                    self.assertTrue(resp.context['form'].errors.get('map_embed_url'))
                    self.branch.refresh_from_db()
                    self.assertEqual(self.branch.map_embed_url, original)

    def test_latitude_without_longitude_is_rejected(self):
        self.client.force_login(self.admin)
        resp = self.client.post(self._edit_url(), {'map_embed_url': '', 'latitude': '-0.68', 'longitude': '', 'map_zoom': '16'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Enter both latitude and longitude")

    def test_instructor_student_receptionist_and_anonymous_cannot_edit_maps(self):
        for label, user in (('anonymous', None), ('student', self.student), ('instructor', self.instructor),
                            ('receptionist', self.receptionist)):
            self.client.logout()
            if user:
                self.client.force_login(user)
            with self.subTest(role=label):
                self.assertEqual(self.client.get(self._edit_url()).status_code, 404)
                resp = self.client.post(self._edit_url(), {
                    'map_embed_url': 'https://www.google.com/maps?q=Hijack&output=embed', 'map_zoom': '16'})
                self.assertEqual(resp.status_code, 404)
                self.assertEqual(self.client.post(reverse('manage:branch_map_preview'), {'map_embed_url': ''}).status_code, 404)
                self.branch.refresh_from_db()
                self.assertNotIn("Hijack", self.branch.map_embed_url)

    def test_live_preview_endpoint_validates_like_saving(self):
        self.client.force_login(self.admin)
        url = reverse('manage:branch_map_preview')
        ok = self.client.post(url, {
            'map_embed_url': '<iframe src="https://www.google.com/maps?q=a&amp;output=embed"></iframe>',
            'map_zoom': '16'}).json()
        self.assertTrue(ok['ok'])
        self.assertEqual(ok['src'], "https://www.google.com/maps?q=a&output=embed")

        bad = self.client.post(url, {'map_embed_url': 'javascript:alert(1)'}).json()
        self.assertFalse(bad['ok'])
        self.assertIn("https://www.google.com/maps", bad['error'])

        from_address = self.client.post(url, {'map_embed_url': '', 'address': 'Kisii Town', 'town': 'Kisii'}).json()
        self.assertEqual(from_address['src'], "https://www.google.com/maps?q=Kisii+Town&z=16&output=embed")

        empty = self.client.post(url, {'map_embed_url': ''}).json()
        self.assertTrue(empty['ok'])
        self.assertEqual(empty['src'], "")
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_branches_list_shows_map_status_for_admin_and_super_admin(self):
        for user in (self.admin, self.super_admin):
            self.client.force_login(user)
            resp = self.client.get(reverse('manage:branches_list'))
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, "Map set")
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('manage:branches_list')), "Edit map")

