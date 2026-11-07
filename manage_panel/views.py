from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from decouple import config

from accounts.permissions import (
    management_required, super_admin_required,
    is_super_admin
)
from website.models import (
    SiteSettings, HeroSlide, WhyChooseUsItem, PageContent,
    NavigationItem, Testimonial, GalleryImage, FAQ, ContactMessage,
    AuditLog
)
from courses.models import Course
from instructors.models import Instructor
from students.models import Student
from accounts.models import UserProfile
from .forms import (
    BrandingForm, HomepageContentForm, HeroSlideForm, WhyChooseUsForm,
    PageContentForm, CourseForm, InstructorForm, GalleryImageForm,
    TestimonialForm, FAQForm, NavigationItemForm, ContactSettingsForm,
    SEOForm, SystemSettingsForm, MaintenanceModeForm, UserManagementForm
)

def log_audit(user, action, model_name="", object_id="", details="", request=None):
    """Utility to record an audit log entry."""
    ip = request.META.get('REMOTE_ADDR') if request else None
    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        details=details,
        ip_address=ip
    )


@management_required
def dashboard_view(request):
    """Management dashboard overview with quick operational metrics."""
    context = {
        'total_courses': Course.objects.count(),
        'total_students': Student.objects.count(),
        'pending_students': Student.objects.filter(status='pending').count(),
        'total_instructors': Instructor.objects.count(),
        'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
        'gallery_count': GalleryImage.objects.count(),
        'recent_messages': ContactMessage.objects.order_by('-created_at')[:5],
        'recent_students': Student.objects.order_by('-created_at')[:5],
        'recent_audits': AuditLog.objects.order_by('-timestamp')[:8] if is_super_admin(request.user) else [],
        'is_super_admin': is_super_admin(request.user),
    }
    return render(request, 'manage_panel/dashboard.html', context)


@management_required
def branding_view(request):
    """1. School Branding, Colors, Logo, and Typography Settings."""
    site_settings = SiteSettings.load()
    if request.method == 'POST':
        form = BrandingForm(request.POST, request.FILES, instance=site_settings)
        if form.is_valid():
            form.save()
            log_audit(request.user, "UPDATED_BRANDING", "SiteSettings", site_settings.pk, "Updated brand colors, logos, fonts, or school name", request)
            messages.success(request, "Branding settings saved successfully. Visual changes are now live across the public site.")
            return redirect('manage:branding')
    else:
        form = BrandingForm(instance=site_settings)

    return render(request, 'manage_panel/branding.html', {
        'form': form,
        'site_settings': site_settings,
    })


@management_required
def media_library_view(request):
    """2. Media Library and image asset overview."""
    site_settings = SiteSettings.load()
    gallery_images = GalleryImage.objects.all().order_by('-created_at')
    hero_slides = HeroSlide.objects.all()

    if request.method == 'POST':
        form = GalleryImageForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.save()
            log_audit(request.user, "UPLOADED_MEDIA", "GalleryImage", img.pk, f"Uploaded new image '{img.title}'", request)
            messages.success(request, f"Image '{img.title}' uploaded successfully.")
            return redirect('manage:media_library')
    else:
        form = GalleryImageForm()

    return render(request, 'manage_panel/media_library.html', {
        'site_settings': site_settings,
        'gallery_images': gallery_images,
        'hero_slides': hero_slides,
        'form': form,
    })


@management_required
def homepage_content_view(request):
    """3. Homepage Content: Hero headlines, section texts, stats, and CTA banner."""
    site_settings = SiteSettings.load()
    if request.method == 'POST':
        form = HomepageContentForm(request.POST, request.FILES, instance=site_settings)
        if form.is_valid():
            form.save()
            log_audit(request.user, "UPDATED_HOMEPAGE", "SiteSettings", site_settings.pk, "Updated homepage headings, hero content, or stats counters", request)
            messages.success(request, "Homepage content updated successfully.")
            return redirect('manage:homepage_content')
    else:
        form = HomepageContentForm(instance=site_settings)

    slides = HeroSlide.objects.all().order_by('order')
    why_items = WhyChooseUsItem.objects.all().order_by('order')

    return render(request, 'manage_panel/homepage_content.html', {
        'form': form,
        'slides': slides,
        'why_items': why_items,
        'site_settings': site_settings,
    })


# Hero Slides CRUD
@management_required
def slide_create_view(request):
    if request.method == 'POST':
        form = HeroSlideForm(request.POST, request.FILES)
        if form.is_valid():
            slide = form.save()
            log_audit(request.user, "CREATED_SLIDE", "HeroSlide", slide.pk, f"Created hero slide '{slide.title}'", request)
            messages.success(request, f"Hero slide '{slide.title}' created.")
            return redirect('manage:homepage_content')
    else:
        form = HeroSlideForm()
    return render(request, 'manage_panel/slide_form.html', {'form': form, 'title': 'Add Hero Slide'})


@management_required
def slide_edit_view(request, pk):
    slide = get_object_or_404(HeroSlide, pk=pk)
    if request.method == 'POST':
        form = HeroSlideForm(request.POST, request.FILES, instance=slide)
        if form.is_valid():
            form.save()
            log_audit(request.user, "EDITED_SLIDE", "HeroSlide", slide.pk, f"Updated hero slide '{slide.title}'", request)
            messages.success(request, f"Hero slide '{slide.title}' updated.")
            return redirect('manage:homepage_content')
    else:
        form = HeroSlideForm(instance=slide)
    return render(request, 'manage_panel/slide_form.html', {'form': form, 'slide': slide, 'title': 'Edit Hero Slide'})


@management_required
def slide_delete_view(request, pk):
    slide = get_object_or_404(HeroSlide, pk=pk)
    if request.method == 'POST':
        title = slide.title
        slide.delete()
        log_audit(request.user, "DELETED_SLIDE", "HeroSlide", pk, f"Deleted hero slide '{title}'", request)
        messages.success(request, f"Hero slide '{title}' deleted.")
        return redirect('manage:homepage_content')
    return render(request, 'manage_panel/confirm_delete.html', {'object': slide, 'cancel_url': 'manage:homepage_content'})


# Why Choose Us CRUD
@management_required
def why_choose_create_view(request):
    if request.method == 'POST':
        form = WhyChooseUsForm(request.POST)
        if form.is_valid():
            item = form.save()
            log_audit(request.user, "CREATED_WHY_CHOOSE", "WhyChooseUsItem", item.pk, f"Created reason '{item.title}'", request)
            messages.success(request, f"Item '{item.title}' created.")
            return redirect('manage:homepage_content')
    else:
        form = WhyChooseUsForm()
    return render(request, 'manage_panel/why_choose_form.html', {'form': form, 'title': 'Add Advantage Point'})


@management_required
def why_choose_edit_view(request, pk):
    item = get_object_or_404(WhyChooseUsItem, pk=pk)
    if request.method == 'POST':
        form = WhyChooseUsForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            log_audit(request.user, "EDITED_WHY_CHOOSE", "WhyChooseUsItem", item.pk, f"Updated reason '{item.title}'", request)
            messages.success(request, f"Item '{item.title}' updated.")
            return redirect('manage:homepage_content')
    else:
        form = WhyChooseUsForm(instance=item)
    return render(request, 'manage_panel/why_choose_form.html', {'form': form, 'title': 'Edit Advantage Point'})


@management_required
def why_choose_delete_view(request, pk):
    item = get_object_or_404(WhyChooseUsItem, pk=pk)
    if request.method == 'POST':
        title = item.title
        item.delete()
        log_audit(request.user, "DELETED_WHY_CHOOSE", "WhyChooseUsItem", pk, f"Deleted reason '{title}'", request)
        messages.success(request, f"Item '{title}' deleted.")
        return redirect('manage:homepage_content')
    return render(request, 'manage_panel/confirm_delete.html', {'object': item, 'cancel_url': 'manage:homepage_content'})


# 4. Pages Content (About, Terms, Privacy)
@management_required
def pages_list_view(request):
    default_pages = [
        ('about', 'About Us', 'Established with a commitment to road safety and driving excellence, Belings Driving School equips Kenyan drivers with defensive motoring skills, sound road ethics, and technical proficiency.'),
        ('terms', 'Terms and Conditions', 'Registration policies, attendance requirements, fee payment schedules, and conduct guidelines for students at Belings Driving School.'),
        ('privacy', 'Privacy Policy', 'How Belings Driving School collects, uses, and safeguards student personal data in accordance with the Kenya Data Protection Act 2019.'),
    ]
    for slug, title, content in default_pages:
        PageContent.objects.get_or_create(slug=slug, defaults={'title': title, 'content': content, 'is_published': True})

    pages = PageContent.objects.all().order_by('title')
    return render(request, 'manage_panel/pages_list.html', {'pages': pages})


@management_required
def page_edit_view(request, slug):
    page = get_object_or_404(PageContent, slug=slug)
    if request.method == 'POST':
        form = PageContentForm(request.POST, instance=page)
        if form.is_valid():
            form.save()
            log_audit(request.user, "EDITED_PAGE", "PageContent", page.pk, f"Updated page '{page.title}'", request)
            messages.success(request, f"Page '{page.title}' updated successfully.")
            return redirect('manage:pages_list')
    else:
        form = PageContentForm(instance=page)
    return render(request, 'manage_panel/page_form.html', {'form': form, 'page': page})


# 5. Courses & Fees
@management_required
def courses_list_view(request):
    courses = Course.objects.all().order_by('order', 'name')
    return render(request, 'manage_panel/courses_list.html', {'courses': courses})


@management_required
def course_create_view(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save()
            log_audit(request.user, "CREATED_COURSE", "Course", course.pk, f"Created course '{course.name}' with fee KES {course.fee}", request)
            messages.success(request, f"Course '{course.name}' created.")
            return redirect('manage:courses_list')
    else:
        form = CourseForm()
    return render(request, 'manage_panel/course_form.html', {'form': form, 'title': 'Add Driving Course'})


@management_required
def course_edit_view(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            log_audit(request.user, "EDITED_COURSE", "Course", course.pk, f"Updated course '{course.name}' - Fee KES {course.fee}", request)
            messages.success(request, f"Course '{course.name}' updated successfully.")
            return redirect('manage:courses_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'manage_panel/course_form.html', {'form': form, 'course': course, 'title': f'Edit {course.name}'})


@management_required
def course_delete_view(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        name = course.name
        course.delete()
        log_audit(request.user, "DELETED_COURSE", "Course", pk, f"Deleted course '{name}'", request)
        messages.success(request, f"Course '{name}' deleted.")
        return redirect('manage:courses_list')
    return render(request, 'manage_panel/confirm_delete.html', {'object': course, 'cancel_url': 'manage:courses_list'})


# 6. Instructors, Gallery, Testimonials, FAQs
@management_required
def instructors_list_view(request):
    instructors = Instructor.objects.all().order_by('order', 'full_name')
    return render(request, 'manage_panel/instructors_list.html', {'instructors': instructors})


@management_required
def instructor_create_view(request):
    if request.method == 'POST':
        form = InstructorForm(request.POST, request.FILES)
        if form.is_valid():
            inst = form.save()
            log_audit(request.user, "CREATED_INSTRUCTOR", "Instructor", inst.pk, f"Created instructor '{inst.full_name}'", request)
            messages.success(request, f"Instructor '{inst.full_name}' added.")
            return redirect('manage:instructors_list')
    else:
        form = InstructorForm()
    return render(request, 'manage_panel/instructor_form.html', {'form': form, 'title': 'Add Instructor'})


@management_required
def instructor_edit_view(request, pk):
    inst = get_object_or_404(Instructor, pk=pk)
    if request.method == 'POST':
        form = InstructorForm(request.POST, request.FILES, instance=inst)
        if form.is_valid():
            form.save()
            log_audit(request.user, "EDITED_INSTRUCTOR", "Instructor", inst.pk, f"Updated instructor '{inst.full_name}'", request)
            messages.success(request, f"Instructor '{inst.full_name}' updated.")
            return redirect('manage:instructors_list')
    else:
        form = InstructorForm(instance=inst)
    return render(request, 'manage_panel/instructor_form.html', {'form': form, 'instructor': inst, 'title': f'Edit {inst.full_name}'})


@management_required
def instructor_delete_view(request, pk):
    inst = get_object_or_404(Instructor, pk=pk)
    if request.method == 'POST':
        name = inst.full_name
        inst.delete()
        log_audit(request.user, "DELETED_INSTRUCTOR", "Instructor", pk, f"Deleted instructor '{name}'", request)
        messages.success(request, f"Instructor '{name}' deleted.")
        return redirect('manage:instructors_list')
    return render(request, 'manage_panel/confirm_delete.html', {'object': inst, 'cancel_url': 'manage:instructors_list'})


# Gallery CRUD
@management_required
def gallery_list_view(request):
    images = GalleryImage.objects.all().order_by('order', '-created_at')
    return render(request, 'manage_panel/gallery_list.html', {'images': images})


@management_required
def gallery_create_view(request):
    if request.method == 'POST':
        form = GalleryImageForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.save()
            log_audit(request.user, "CREATED_GALLERY_IMAGE", "GalleryImage", img.pk, f"Added gallery image '{img.title}'", request)
            messages.success(request, f"Image '{img.title}' added to gallery.")
            return redirect('manage:gallery_list')
    else:
        form = GalleryImageForm()
    return render(request, 'manage_panel/gallery_form.html', {'form': form, 'title': 'Add Gallery Image'})


@management_required
def gallery_edit_view(request, pk):
    img = get_object_or_404(GalleryImage, pk=pk)
    if request.method == 'POST':
        form = GalleryImageForm(request.POST, request.FILES, instance=img)
        if form.is_valid():
            form.save()
            log_audit(request.user, "EDITED_GALLERY_IMAGE", "GalleryImage", img.pk, f"Updated gallery image '{img.title}'", request)
            messages.success(request, f"Gallery image '{img.title}' updated.")
            return redirect('manage:gallery_list')
    else:
        form = GalleryImageForm(instance=img)
    return render(request, 'manage_panel/gallery_form.html', {'form': form, 'image': img, 'title': f'Edit {img.title}'})


@management_required
def gallery_delete_view(request, pk):
    img = get_object_or_404(GalleryImage, pk=pk)
    if request.method == 'POST':
        title = img.title
        img.delete()
        log_audit(request.user, "DELETED_GALLERY_IMAGE", "GalleryImage", pk, f"Deleted gallery image '{title}'", request)
        messages.success(request, f"Image '{title}' deleted from gallery.")
        return redirect('manage:gallery_list')
    return render(request, 'manage_panel/confirm_delete.html', {'object': img, 'cancel_url': 'manage:gallery_list'})


# Testimonials CRUD
@management_required
def testimonials_list_view(request):
    testimonials = Testimonial.objects.all().order_by('order', '-created_at')
    return render(request, 'manage_panel/testimonials_list.html', {'testimonials': testimonials})


@management_required
def testimonial_create_view(request):
    if request.method == 'POST':
        form = TestimonialForm(request.POST, request.FILES)
        if form.is_valid():
            testi = form.save()
            log_audit(request.user, "CREATED_TESTIMONIAL", "Testimonial", testi.pk, f"Added testimonial from '{testi.name}'", request)
            messages.success(request, f"Testimonial from '{testi.name}' added.")
            return redirect('manage:testimonials_list')
    else:
        form = TestimonialForm()
    return render(request, 'manage_panel/testimonial_form.html', {'form': form, 'title': 'Add Testimonial'})


@management_required
def testimonial_edit_view(request, pk):
    testi = get_object_or_404(Testimonial, pk=pk)
    if request.method == 'POST':
        form = TestimonialForm(request.POST, request.FILES, instance=testi)
        if form.is_valid():
            form.save()
            log_audit(request.user, "EDITED_TESTIMONIAL", "Testimonial", testi.pk, f"Updated testimonial from '{testi.name}'", request)
            messages.success(request, f"Testimonial from '{testi.name}' updated.")
            return redirect('manage:testimonials_list')
    else:
        form = TestimonialForm(instance=testi)
    return render(request, 'manage_panel/testimonial_form.html', {'form': form, 'testimonial': testi, 'title': f'Edit Testimonial from {testi.name}'})


@management_required
def testimonial_delete_view(request, pk):
    testi = get_object_or_404(Testimonial, pk=pk)
    if request.method == 'POST':
        name = testi.name
        testi.delete()
        log_audit(request.user, "DELETED_TESTIMONIAL", "Testimonial", pk, f"Deleted testimonial from '{name}'", request)
        messages.success(request, f"Testimonial from '{name}' deleted.")
        return redirect('manage:testimonials_list')
    return render(request, 'manage_panel/confirm_delete.html', {'object': testi, 'cancel_url': 'manage:testimonials_list'})


# FAQs CRUD
@management_required
def faqs_list_view(request):
    faqs = FAQ.objects.all().order_by('category', 'order')
    return render(request, 'manage_panel/faqs_list.html', {'faqs': faqs})


@management_required
def faq_create_view(request):
    if request.method == 'POST':
        form = FAQForm(request.POST)
        if form.is_valid():
            faq = form.save()
            log_audit(request.user, "CREATED_FAQ", "FAQ", faq.pk, f"Added FAQ '{faq.question[:30]}'", request)
            messages.success(request, "FAQ added successfully.")
            return redirect('manage:faqs_list')
    else:
        form = FAQForm()
    return render(request, 'manage_panel/faq_form.html', {'form': form, 'title': 'Add FAQ'})


@management_required
def faq_edit_view(request, pk):
    faq = get_object_or_404(FAQ, pk=pk)
    if request.method == 'POST':
        form = FAQForm(request.POST, instance=faq)
        if form.is_valid():
            form.save()
            log_audit(request.user, "EDITED_FAQ", "FAQ", faq.pk, f"Updated FAQ '{faq.question[:30]}'", request)
            messages.success(request, "FAQ updated successfully.")
            return redirect('manage:faqs_list')
    else:
        form = FAQForm(instance=faq)
    return render(request, 'manage_panel/faq_form.html', {'form': form, 'faq': faq, 'title': 'Edit FAQ'})


@management_required
def faq_delete_view(request, pk):
    faq = get_object_or_404(FAQ, pk=pk)
    if request.method == 'POST':
        q = faq.question
        faq.delete()
        log_audit(request.user, "DELETED_FAQ", "FAQ", pk, f"Deleted FAQ '{q[:30]}'", request)
        messages.success(request, "FAQ deleted.")
        return redirect('manage:faqs_list')
    return render(request, 'manage_panel/confirm_delete.html', {'object': faq, 'cancel_url': 'manage:faqs_list'})


# 7. Navigation & Menu Items
@management_required
def navigation_list_view(request):
    items = NavigationItem.objects.all().order_by('order')
    return render(request, 'manage_panel/navigation_list.html', {'items': items})


@management_required
def navigation_create_view(request):
    if request.method == 'POST':
        form = NavigationItemForm(request.POST)
        if form.is_valid():
            nav = form.save()
            log_audit(request.user, "CREATED_NAVIGATION", "NavigationItem", nav.pk, f"Added menu item '{nav.label}'", request)
            messages.success(request, f"Menu item '{nav.label}' added.")
            return redirect('manage:navigation_list')
    else:
        form = NavigationItemForm()
    return render(request, 'manage_panel/navigation_form.html', {'form': form, 'title': 'Add Navigation Item'})


@management_required
def navigation_edit_view(request, pk):
    nav = get_object_or_404(NavigationItem, pk=pk)
    if request.method == 'POST':
        form = NavigationItemForm(request.POST, instance=nav)
        if form.is_valid():
            form.save()
            log_audit(request.user, "EDITED_NAVIGATION", "NavigationItem", nav.pk, f"Updated menu item '{nav.label}'", request)
            messages.success(request, f"Menu item '{nav.label}' updated.")
            return redirect('manage:navigation_list')
    else:
        form = NavigationItemForm(instance=nav)
    return render(request, 'manage_panel/navigation_form.html', {'form': form, 'item': nav, 'title': f'Edit {nav.label}'})


@management_required
def navigation_delete_view(request, pk):
    nav = get_object_or_404(NavigationItem, pk=pk)
    if request.method == 'POST':
        lbl = nav.label
        nav.delete()
        log_audit(request.user, "DELETED_NAVIGATION", "NavigationItem", pk, f"Deleted menu item '{lbl}'", request)
        messages.success(request, f"Menu item '{lbl}' deleted.")
        return redirect('manage:navigation_list')
    return render(request, 'manage_panel/confirm_delete.html', {'object': nav, 'cancel_url': 'manage:navigation_list'})


# 8. Contact Settings & Messages Inbox
@management_required
def contact_settings_view(request):
    site_settings = SiteSettings.load()
    if request.method == 'POST':
        form = ContactSettingsForm(request.POST, instance=site_settings)
        if form.is_valid():
            form.save()
            log_audit(request.user, "UPDATED_CONTACT_SETTINGS", "SiteSettings", site_settings.pk, "Updated school contact info, address, map, or social links", request)
            messages.success(request, "Contact and footer settings updated.")
            return redirect('manage:contact_settings')
    else:
        form = ContactSettingsForm(instance=site_settings)

    return render(request, 'manage_panel/contact_settings.html', {'form': form, 'site_settings': site_settings})


@management_required
def messages_list_view(request):
    messages_qs = ContactMessage.objects.all().order_by('-created_at')
    return render(request, 'manage_panel/messages_list.html', {'contact_messages': messages_qs})


@management_required
def message_toggle_read_view(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    msg.is_read = not msg.is_read
    msg.save()
    status = "Read" if msg.is_read else "Unread"
    log_audit(request.user, "TOGGLED_MESSAGE_READ", "ContactMessage", pk, f"Marked message from {msg.name} as {status}", request)
    messages.info(request, f"Message marked as {status}.")
    return redirect('manage:messages_list')


@management_required
def message_delete_view(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    if request.method == 'POST':
        name = msg.name
        msg.delete()
        log_audit(request.user, "DELETED_MESSAGE", "ContactMessage", pk, f"Deleted inquiry from {name}", request)
        messages.success(request, f"Message from {name} deleted.")
        return redirect('manage:messages_list')
    return render(request, 'manage_panel/confirm_delete.html', {'object': msg, 'cancel_url': 'manage:messages_list'})


# 9. SEO Settings
@management_required
def seo_settings_view(request):
    site_settings = SiteSettings.load()
    if request.method == 'POST':
        form = SEOForm(request.POST, request.FILES, instance=site_settings)
        if form.is_valid():
            form.save()
            log_audit(request.user, "UPDATED_SEO", "SiteSettings", site_settings.pk, "Updated meta title, description, OG image, or indexing settings", request)
            messages.success(request, "SEO configuration updated successfully.")
            return redirect('manage:seo_settings')
    else:
        form = SEOForm(instance=site_settings)

    return render(request, 'manage_panel/seo_settings.html', {'form': form, 'site_settings': site_settings})


# 10. System Settings
@management_required
def system_settings_view(request):
    site_settings = SiteSettings.load()
    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, instance=site_settings)
        if form.is_valid():
            form.save()
            log_audit(request.user, "UPDATED_SYSTEM_SETTINGS", "SiteSettings", site_settings.pk, "Updated lesson duration, cancellation window, receipt details, or notification templates", request)
            messages.success(request, "Operational system settings updated.")
            return redirect('manage:system_settings')
    else:
        form = SystemSettingsForm(instance=site_settings)

    return render(request, 'manage_panel/system_settings.html', {'form': form, 'site_settings': site_settings})


# 11. Maintenance Mode
@management_required
def maintenance_mode_view(request):
    site_settings = SiteSettings.load()
    if request.method == 'POST':
        form = MaintenanceModeForm(request.POST, instance=site_settings)
        if form.is_valid():
            form.save()
            status = "ENABLED" if site_settings.maintenance_mode else "DISABLED"
            log_audit(request.user, f"MAINTENANCE_{status}", "SiteSettings", site_settings.pk, f"Maintenance mode {status}", request)
            messages.warning(request, f"Maintenance mode has been {status}.")
            return redirect('manage:maintenance_mode')
    else:
        form = MaintenanceModeForm(instance=site_settings)

    return render(request, 'manage_panel/maintenance_mode.html', {'form': form, 'site_settings': site_settings})


# 12. Audit Log (Super Admin Exclusive)
@super_admin_required
def audit_log_view(request):
    logs = AuditLog.objects.all().select_related('user').order_by('-timestamp')
    return render(request, 'manage_panel/audit_log.html', {'logs': logs})


# 13. Sensitive Credentials Screen (Super Admin Exclusive to edit, Admin sees masked)
@management_required
def credentials_view(request):
    is_super = is_super_admin(request.user)
    credentials_info = [
        {
            'name': 'M-Pesa Daraja Consumer Key',
            'env_var': 'MPESA_CONSUMER_KEY',
            'configured': bool(config('MPESA_CONSUMER_KEY', default='')),
            'value': config('MPESA_CONSUMER_KEY', default=''),
        },
        {
            'name': 'M-Pesa Daraja Consumer Secret',
            'env_var': 'MPESA_CONSUMER_SECRET',
            'configured': bool(config('MPESA_CONSUMER_SECRET', default='')),
            'value': config('MPESA_CONSUMER_SECRET', default=''),
        },
        {
            'name': 'M-Pesa Shortcode (Paybill/Till)',
            'env_var': 'MPESA_SHORTCODE',
            'configured': bool(config('MPESA_SHORTCODE', default='')),
            'value': config('MPESA_SHORTCODE', default=''),
        },
        {
            'name': 'M-Pesa Passkey',
            'env_var': 'MPESA_PASSKEY',
            'configured': bool(config('MPESA_PASSKEY', default='')),
            'value': config('MPESA_PASSKEY', default=''),
        },
        {
            'name': 'SMS Gateway API Key',
            'env_var': 'SMS_API_KEY',
            'configured': bool(config('SMS_API_KEY', default='')),
            'value': config('SMS_API_KEY', default=''),
        },
        {
            'name': 'SMS Username / Sender ID',
            'env_var': 'SMS_USERNAME',
            'configured': bool(config('SMS_USERNAME', default='')),
            'value': config('SMS_USERNAME', default=''),
        },
        {
            'name': 'Django SECRET_KEY',
            'env_var': 'SECRET_KEY',
            'configured': bool(config('SECRET_KEY', default='')),
            'value': config('SECRET_KEY', default=''),
        },
        {
            'name': 'Database URL',
            'env_var': 'DATABASE_URL',
            'configured': bool(config('DATABASE_URL', default='')),
            'value': config('DATABASE_URL', default=''),
        },
    ]

    return render(request, 'manage_panel/credentials.html', {
        'credentials': credentials_info,
        'is_super_admin': is_super,
    })


# 14. User Accounts Management (Super Admin Exclusive)
@super_admin_required
def users_list_view(request):
    users = User.objects.all().select_related('profile').order_by('-date_joined')
    return render(request, 'manage_panel/users_list.html', {'user_list': users})


@super_admin_required
def user_create_view(request):
    if request.method == 'POST':
        form = UserManagementForm(request.POST)
        if form.is_valid():
            u = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                u.set_password(password)
            else:
                u.set_password('ChangeMe123!')
            role = form.cleaned_data.get('role')
            if role == UserProfile.ROLE_SUPER_ADMIN:
                u.is_superuser = True
                u.is_staff = True
            elif role == UserProfile.ROLE_ADMIN:
                u.is_superuser = False
                u.is_staff = True
            else:
                u.is_superuser = False
                u.is_staff = False
            u.save()
            u.profile.role = role
            u.profile.save()

            log_audit(request.user, "CREATED_USER", "User", u.pk, f"Created account {u.username} with role {role}", request)
            messages.success(request, f"User '{u.username}' created successfully.")
            return redirect('manage:users_list')
    else:
        form = UserManagementForm(initial={'role': UserProfile.ROLE_ADMIN})

    return render(request, 'manage_panel/user_form.html', {'form': form, 'title': 'Create Staff / Admin Account'})


@super_admin_required
def user_edit_view(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserManagementForm(request.POST, instance=target_user)
        if form.is_valid():
            u = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                u.set_password(password)
            role = form.cleaned_data.get('role')
            if role == UserProfile.ROLE_SUPER_ADMIN:
                u.is_superuser = True
                u.is_staff = True
            elif role == UserProfile.ROLE_ADMIN:
                u.is_superuser = False
                u.is_staff = True
            else:
                u.is_superuser = False
                u.is_staff = False
            u.save()
            u.profile.role = role
            u.profile.save()

            log_audit(request.user, "EDITED_USER", "User", u.pk, f"Updated account {u.username} role to {role}", request)
            messages.success(request, f"Account '{u.username}' updated.")
            return redirect('manage:users_list')
    else:
        current_role = target_user.profile.role if hasattr(target_user, 'profile') else UserProfile.ROLE_STUDENT
        form = UserManagementForm(instance=target_user, initial={'role': current_role})

    return render(request, 'manage_panel/user_form.html', {'form': form, 'target_user': target_user, 'title': f'Edit Account: {target_user.username}'})


@super_admin_required
def user_delete_view(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        messages.error(request, "You cannot delete your own logged-in account.")
        return redirect('manage:users_list')

    if request.method == 'POST':
        uname = target_user.username
        target_user.delete()
        log_audit(request.user, "DELETED_USER", "User", pk, f"Deleted account {uname}", request)
        messages.success(request, f"Account '{uname}' deleted.")
        return redirect('manage:users_list')

    return render(request, 'manage_panel/confirm_delete.html', {'object': target_user, 'cancel_url': 'manage:users_list'})
