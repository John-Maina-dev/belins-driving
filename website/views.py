from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q

from .models import (
    SiteSettings, Testimonial, GalleryImage, GalleryCategory, FAQ, ContactMessage,
    HeroSlide, WhyChooseUsItem, PageContent, HomeSection
)
from .forms import ContactForm, EnrollmentForm
from courses.models import Course, Branch
from instructors.models import Instructor
from students.models import Student


def home_view(request):
    """
    Homepage rendering ONLY sections that are enabled in HomeSection AND
    have admin-created content. Zero hardcoded/demo fallback content.
    Pure READ operation: does not write to the database on anonymous page loads.
    """
    site_cfg = SiteSettings.objects.first() or SiteSettings(pk=1)
    sections_qs = list(HomeSection.objects.all().order_by('order', 'id'))
    if sections_qs:
        enabled_sections = [s.section_key for s in sections_qs if s.is_enabled]
    else:
        enabled_sections = [key for key, _, _ in HomeSection.DEFAULT_SECTIONS]

    slides = list(HeroSlide.objects.filter(is_active=True).order_by('order'))
    why_items = list(WhyChooseUsItem.objects.filter(is_active=True).order_by('order'))

    featured_courses = list(Course.objects.filter(is_active=True, is_featured=True).order_by('order')[:6])
    if not featured_courses:
        featured_courses = list(Course.objects.filter(is_active=True).order_by('order')[:6])

    all_courses = list(Course.objects.filter(is_active=True).order_by('order'))
    instructors = list(Instructor.objects.filter(is_active=True, is_featured=True).order_by('order')[:4])
    if not instructors:
        instructors = list(Instructor.objects.filter(is_active=True).order_by('order')[:4])

    testimonials = list(Testimonial.objects.filter(is_active=True, is_featured=True).order_by('order')[:6])
    if not testimonials:
        testimonials = list(Testimonial.objects.filter(is_active=True).order_by('order')[:6])

    faqs = list(FAQ.objects.filter(is_active=True).order_by('order')[:6])
    branches = list(Branch.objects.filter(is_active=True).order_by('order', 'name'))
    about_page = PageContent.objects.filter(slug='about', is_published=True).first()

    gallery_limit = max(1, int(getattr(site_cfg, 'home_gallery_count', 8) or 8))
    if getattr(site_cfg, 'home_gallery_featured_first', True):
        home_gallery_images = list(
            GalleryImage.objects.filter(is_active=True, is_featured_home=True)
            .select_related('category_obj')
            .order_by('order', '-created_at')[:gallery_limit]
        )
    else:
        home_gallery_images = list(
            GalleryImage.objects.filter(is_active=True)
            .select_related('category_obj')
            .order_by('-created_at', 'order')[:gallery_limit]
        )
    gallery_categories = list(GalleryCategory.objects.filter(is_active=True).order_by('order', 'name'))

    has_hero = bool(slides or site_cfg.hero_title or site_cfg.hero_subtitle or site_cfg.hero_image)
    has_stats = bool(
        site_cfg.stat_students or site_cfg.stat_pass_rate
        or site_cfg.stat_experience_years or site_cfg.stat_certified_instructors
    )
    has_about = bool(
        site_cfg.about_section_title or site_cfg.about_section_text
        or (about_page and about_page.content)
    )
    has_courses = bool(featured_courses)
    has_branches = bool(branches)
    has_gallery = bool(home_gallery_images)
    has_why = bool(why_items)
    has_testimonials = bool(testimonials)
    has_instructors = bool(instructors)
    has_faqs = bool(faqs)
    has_cta = bool(site_cfg.cta_banner_title or site_cfg.cta_banner_desc)
    has_contact = bool(site_cfg.phone or site_cfg.email or site_cfg.address or site_cfg.opening_hours)

    content_availability = {
        'hero': has_hero,
        'stats': has_stats,
        'about': has_about,
        'courses': has_courses,
        'branches': has_branches,
        'gallery': has_gallery,
        'why_choose_us': has_why,
        'why_us': has_why,
        'testimonials': has_testimonials,
        'instructors': has_instructors,
        'faqs': has_faqs,
        'cta': has_cta,
        'contact': has_contact,
    }

    active_section_keys = [
        ('why_choose_us' if key == 'why_us' else key)
        for key in enabled_sections
        if content_availability.get(key, False)
    ]

    context = {
        'active_section_keys': active_section_keys,
        'slides': slides,
        'why_items': why_items,
        'featured_courses': featured_courses,
        'all_courses': all_courses,
        'instructors': instructors,
        'testimonials': testimonials,
        'faqs': faqs,
        'branches': branches,
        'about_page': about_page,
        'home_gallery_images': home_gallery_images,
        'gallery_categories': gallery_categories,
    }
    return render(request, 'website/home.html', context)


def about_view(request):
    """About Us page: School story, mission, vision, accreditation, and milestones."""
    about_page = PageContent.objects.filter(slug='about', is_published=True).first()
    context = {
        'about_page': about_page,
        'instructors_count': Instructor.objects.filter(is_active=True).count(),
        'courses_count': Course.objects.filter(is_active=True).count(),
        'testimonials': Testimonial.objects.filter(is_active=True)[:3],
    }
    return render(request, 'website/about.html', context)


def courses_view(request):
    """Courses listing with category and branch filters."""
    category = request.GET.get('category')
    branch_id = request.GET.get('branch')
    qs = Course.objects.filter(is_active=True).prefetch_related('branches')
    if category:
        qs = qs.filter(license_category=category)
    if branch_id and branch_id.isdigit():
        qs = qs.filter(branches__id=int(branch_id))

    context = {
        'courses': qs,
        'selected_category': category,
        'selected_branch': int(branch_id) if (branch_id and branch_id.isdigit()) else None,
        'categories': Course.CATEGORY_CHOICES,
    }
    return render(request, 'website/courses.html', context)


def course_detail_view(request, slug):
    """Course detail page."""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    related = Course.objects.filter(is_active=True).exclude(id=course.id)[:3]
    return render(request, 'website/course_detail.html', {
        'course': course,
        'related_courses': related,
    })


def fees_view(request):
    """Fees structure table dynamically loaded from courses in database."""
    courses = Course.objects.filter(is_active=True).order_by('order', 'license_category', 'fee')
    return render(request, 'website/fees.html', {'courses': courses})


def instructors_view(request):
    """Instructors showcase page."""
    instructors = Instructor.objects.filter(is_active=True).select_related('branch').order_by('order', 'full_name')
    return render(request, 'website/instructors.html', {'instructors': instructors})


def gallery_view(request):
    """Gallery page with filterable categories and lightbox."""
    category = request.GET.get('category')
    images = GalleryImage.objects.filter(is_active=True).select_related('category_obj')
    gallery_categories = GalleryCategory.objects.filter(is_active=True).order_by('order', 'name')
    if category:
        images = images.filter(Q(category_obj__slug=category) | Q(category=category))
    return render(request, 'website/gallery.html', {
        'images': images,
        'gallery_categories': gallery_categories,
        'categories': GalleryImage.CATEGORY_CHOICES,
        'selected_category': category,
    })


def faq_view(request):
    """FAQ page categorized."""
    faqs = FAQ.objects.filter(is_active=True).order_by('order')
    return render(request, 'website/faq.html', {
        'faqs': faqs,
        'categories': FAQ.CATEGORY_CHOICES,
    })


def contact_view(request):
    """Contact page with form submission, email notification, branches list, and map."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()

            try:
                subject = f"New Contact Message: {contact.subject} (from {contact.name})"
                body = (
                    f"Name: {contact.name}\n"
                    f"Email: {contact.email}\n"
                    f"Phone: {contact.phone}\n\n"
                    f"Message:\n{contact.message}\n"
                )
                recipient = getattr(settings, 'CONTACT_NOTIFICATION_EMAIL', 'admin@belingsdriving.co.ke')
                send_mail(
                    subject,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient],
                    fail_silently=True,
                )
            except Exception:
                pass

            messages.success(
                request,
                "Thank you for contacting Belings Driving School! Our team will get back to you shortly."
            )
            return redirect('website:contact')
    else:
        form = ContactForm()

    branches = list(Branch.objects.filter(is_active=True).order_by('order', 'name'))
    map_branches = [b for b in branches if b.has_map]
    return render(request, 'website/contact.html', {'form': form, 'branches': branches, 'map_branches': map_branches})


def enroll_view(request):
    """Online student enrollment form with 18+ DOB check and branch-course validation."""
    course_slug = request.GET.get('course')
    branch_id = request.GET.get('branch')
    initial = {}
    if course_slug:
        course = Course.objects.filter(slug=course_slug, is_active=True).first()
        if course:
            initial['course'] = course.id
    if branch_id and branch_id.isdigit():
        branch = Branch.objects.filter(pk=int(branch_id), is_active=True).first()
        if branch:
            initial['branch'] = branch.id

    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            email = student.email.strip()
            user = User.objects.filter(email__iexact=email).first()
            if not user:
                base_username = email.split('@')[0]
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=student.first_name,
                    last_name=student.last_name,
                )
                user.set_unusable_password()
                user.save()
                profile = user.profile
                profile.role = 'STUDENT'
                profile.approval_status = 'PENDING'
                profile.phone = student.phone
                profile.date_of_birth = student.date_of_birth
                profile.save()
            student.user = user
            student.status = 'PENDING_APPROVAL'
            if student.branch:
                student.preferred_branch = student.branch.name
            student.save()

            messages.success(
                request,
                "Your registration was received. You can log in once the school approves your account."
            )
            return redirect('website:enroll_success')
    else:
        form = EnrollmentForm(initial=initial)

    return render(request, 'website/enroll.html', {'form': form})


def branch_courses_api_view(request):
    """JSON endpoint returning active courses offered at a given branch."""
    branch_id = request.GET.get('branch_id')
    qs = Course.objects.filter(is_active=True).order_by('order', 'name')
    if branch_id and branch_id.isdigit():
        branch_courses = qs.filter(branches__id=int(branch_id))
        # If courses have branch assignments, return those assigned to this branch;
        # also include courses that have no specific branch restrictions if none matched
        qs = branch_courses
    data = [
        {
            'id': c.id,
            'name': c.name,
            'slug': c.slug,
            'fee': float(c.fee),
            'category': c.get_license_category_display(),
        }
        for c in qs.distinct()
    ]
    return JsonResponse({'courses': data})


def enroll_success_view(request):
    """Enrollment success confirmation page."""
    return render(request, 'website/enroll_success.html')


def robots_txt_view(request):
    """SEO robots.txt file."""
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def sitemap_xml_view(request):
    """SEO sitemap.xml."""
    courses = Course.objects.filter(is_active=True)
    base_url = request.build_absolute_uri('/')[:-1]
    static_urls = [
        '',
        '/about/',
        '/courses/',
        '/fees/',
        '/instructors/',
        '/gallery/',
        '/faq/',
        '/contact/',
        '/enroll/',
    ]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for path in static_urls:
        xml.append(f'  <url><loc>{base_url}{path}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    for c in courses:
        xml.append(f'  <url><loc>{base_url}/courses/{c.slug}/</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>')
    xml.append('</urlset>')
    return HttpResponse("\n".join(xml), content_type="application/xml")
