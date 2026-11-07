from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.generic import TemplateView, ListView, DetailView, FormView, CreateView
from django.urls import reverse_lazy
from django.http import HttpResponse

from .models import SiteSettings, Testimonial, GalleryImage, FAQ, ContactMessage
from .forms import ContactForm, EnrollmentForm
from courses.models import Course
from instructors.models import Instructor
from students.models import Student

def home_view(request):
    """
    Homepage featuring Hero CTA, About snippet, Featured Courses,
    Why Choose Us, Stats counters, Testimonials, Instructors preview, and Banner CTA.
    """
    context = {
        'featured_courses': Course.objects.filter(is_active=True, is_featured=True)[:6],
        'all_courses': Course.objects.filter(is_active=True)[:8],
        'instructors': Instructor.objects.filter(is_active=True, is_featured=True)[:4],
        'testimonials': Testimonial.objects.filter(is_active=True, is_featured=True)[:6],
        'faqs': FAQ.objects.filter(is_active=True)[:5],
    }
    return render(request, 'website/home.html', context)


def about_view(request):
    """About Us page: School story, mission, vision, accreditation, and milestones."""
    context = {
        'instructors_count': Instructor.objects.filter(is_active=True).count(),
        'courses_count': Course.objects.filter(is_active=True).count(),
        'testimonials': Testimonial.objects.filter(is_active=True)[:3],
    }
    return render(request, 'website/about.html', context)


def courses_view(request):
    """Courses listing with category filters and details."""
    category = request.GET.get('category')
    qs = Course.objects.filter(is_active=True)
    if category:
        qs = qs.filter(license_category=category)

    context = {
        'courses': qs,
        'selected_category': category,
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
    instructors = Instructor.objects.filter(is_active=True).order_by('order', 'full_name')
    return render(request, 'website/instructors.html', {'instructors': instructors})


def gallery_view(request):
    """Gallery page with filterable categories and lightbox."""
    category = request.GET.get('category')
    images = GalleryImage.objects.filter(is_active=True)
    if category:
        images = images.filter(category=category)
    return render(request, 'website/gallery.html', {
        'images': images,
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
    """Contact page with form submission, email notification, and map."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()

            # Attempt email notification
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

    return render(request, 'website/contact.html', {'form': form})


def enroll_view(request):
    """Online student enrollment form."""
    course_slug = request.GET.get('course')
    initial = {}
    if course_slug:
        course = Course.objects.filter(slug=course_slug, is_active=True).first()
        if course:
            initial['course'] = course.id

    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            student = form.save()
            messages.success(
                request,
                f"Congratulations {student.first_name}! Your enrollment application for {student.course.name} has been received. Our admissions officer will contact you within 24 hours to finalize your schedule and onboarding."
            )
            return redirect('website:enroll_success')
    else:
        form = EnrollmentForm(initial=initial)

    return render(request, 'website/enroll.html', {'form': form})


def enroll_success_view(request):
    """Enrollment success confirmation page."""
    return render(request, 'website/enroll_success.html')


def robots_txt_view(request):
    """SEO robots.txt file."""
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
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

