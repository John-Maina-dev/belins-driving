from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from decouple import config
import uuid

from accounts.permissions import (
    management_required, super_admin_required,
    is_super_admin
)
from website.models import (
    SiteSettings, HeroSlide, WhyChooseUsItem, PageContent,
    NavigationItem, Testimonial, GalleryImage, GalleryCategory, FAQ, ContactMessage,
    AuditLog, EmailSettings, EmailLog, CustomSocialLink, HomeSection
)
from website.image_utils import generate_image_variants
from courses.models import Course, Branch, Vehicle
from instructors.models import Instructor
from students.models import Student, LessonBooking
from accounts.models import UserProfile
from .forms import (
    BrandingForm, HomepageContentForm, HeroSlideForm, WhyChooseUsForm,
    PageContentForm, CourseForm, InstructorForm, GalleryImageForm, GalleryBatchUploadForm,
    GalleryCategoryForm, TestimonialForm, FAQForm, NavigationItemForm, ContactSettingsForm,
    SocialLinksForm, CustomSocialLinkForm, BranchForm, BranchMapForm, VehicleForm, EmailSettingsForm,
    SEOForm, SystemSettingsForm, MaintenanceModeForm, UserManagementForm, StaffEnrollmentForm
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
        created_instances, failed_files, summary_text = _process_gallery_batch_upload(request)
        if created_instances and not failed_files:
            messages.success(request, f"{summary_text}. Uploaded and generated responsive variants.")
            return redirect('manage:media_library')
        elif created_instances and failed_files:
            messages.warning(request, summary_text)
            return redirect('manage:media_library')
        else:
            messages.error(request, summary_text)
            form = GalleryImageForm(request.POST)
    else:
        form = GalleryImageForm()

    return render(request, 'manage_panel/media_library.html', {
        'site_settings': site_settings,
        'gallery_images': gallery_images,
        'hero_slides': hero_slides,
        'form': form,
        'batch_form': GalleryBatchUploadForm(),
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


# Gallery CRUD & Fast Batch Upload
def _process_gallery_batch_upload(request):
    """
    Processes one or many uploaded gallery images.
    Each file is validated and converted into clean/grid/large variants independently
    so one invalid or oversized file never cancels the rest of the batch.
    Database rows are inserted with bulk_create() and cache is cleared once.
    """
    uploaded_files = request.FILES.getlist('images') or request.FILES.getlist('image')
    if not uploaded_files:
        return [], [{'filename': 'None', 'reason': 'No image files were selected.'}], "0 uploaded, 1 failed: No image files were selected."

    category_id = request.POST.get('category_obj', '').strip()
    cat_obj = GalleryCategory.objects.filter(pk=int(category_id)).first() if category_id.isdigit() else None
    category_slug = cat_obj.slug if cat_obj else (request.POST.get('category', '').strip() or 'general')
    title_prefix = (request.POST.get('title_prefix') or request.POST.get('title') or '').strip()
    default_caption = (request.POST.get('default_caption') or request.POST.get('caption') or '').strip()
    alt_text_input = (request.POST.get('alt_text') or '').strip()
    is_featured_home = request.POST.get('is_featured_home') in ('on', 'true', 'True', '1')
    if 'is_active' in request.POST:
        is_active = request.POST.get('is_active') in ('on', 'true', 'True', '1')
    elif 'is_published' in request.POST:
        is_active = request.POST.get('is_published') in ('on', 'true', 'True', '1')
    else:
        is_active = True
    order_raw = str(request.POST.get('order', '0')).strip()
    base_order = int(order_raw) if order_raw.lstrip('-').isdigit() else 0

    created_instances = []
    failed_files = []

    for idx, f in enumerate(uploaded_files):
        fname = getattr(f, 'name', f'Photo #{idx + 1}')
        try:
            variants = generate_image_variants(f)
            if len(uploaded_files) == 1 and title_prefix:
                img_title = title_prefix
            elif title_prefix:
                img_title = f"{title_prefix} ({idx + 1})"
            else:
                img_title = variants['original_stem']

            img_obj = GalleryImage(
                title=img_title[:150],
                category=category_slug,
                category_obj=cat_obj,
                caption=default_caption[:255],
                alt_text=(alt_text_input or img_title)[:200],
                is_featured_home=is_featured_home,
                is_active=is_active,
                order=base_order + idx,
            )
            img_obj.image.save(variants['clean_file'].name, variants['clean_file'], save=False)
            img_obj.image_grid.save(variants['grid_file'].name, variants['grid_file'], save=False)
            img_obj.image_large.save(variants['large_file'].name, variants['large_file'], save=False)
            created_instances.append(img_obj)
        except ValidationError as exc:
            reason = exc.messages[0] if hasattr(exc, 'messages') and exc.messages else str(exc)
            failed_files.append({'filename': fname, 'reason': reason})
        except Exception as exc:
            failed_files.append({'filename': fname, 'reason': str(exc)})

    if created_instances:
        GalleryImage.objects.bulk_create(created_instances)
        cache.delete('site_settings_singleton')
        log_audit(
            request.user,
            "UPLOADED_GALLERY_BATCH",
            "GalleryImage",
            "",
            f"Uploaded {len(created_instances)} gallery photo(s); {len(failed_files)} failed",
            request,
        )

    summary_text = f"{len(created_instances)} uploaded, {len(failed_files)} failed"
    if failed_files:
        reasons_str = "; ".join(f"{item['filename']}: {item['reason']}" for item in failed_files)
        summary_text = f"{summary_text} ({reasons_str})"

    return created_instances, failed_files, summary_text


@management_required
def gallery_list_view(request):
    categories = GalleryCategory.ensure_defaults()
    category_filter = request.GET.get('category', '').strip()
    images = GalleryImage.objects.select_related('category_obj').order_by('order', '-created_at')
    if category_filter and category_filter.isdigit():
        images = images.filter(category_obj_id=int(category_filter))
    return render(request, 'manage_panel/gallery_list.html', {
        'images': images,
        'categories': categories,
        'category_filter': int(category_filter) if category_filter.isdigit() else None,
        'batch_form': GalleryBatchUploadForm(),
    })


@management_required
def gallery_create_view(request):
    categories = GalleryCategory.ensure_defaults()
    if request.method == 'POST':
        created_instances, failed_files, summary_text = _process_gallery_batch_upload(request)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'ok': len(created_instances) > 0,
                'uploaded_count': len(created_instances),
                'failed_count': len(failed_files),
                'failed': failed_files,
                'summary': summary_text,
            }, status=200 if (created_instances or failed_files) else 400)

        if created_instances and not failed_files:
            messages.success(request, f"{summary_text}. All photos optimized with grid & full-screen variants.")
            return redirect('manage:gallery_list')
        elif created_instances and failed_files:
            messages.warning(request, summary_text)
            return redirect('manage:gallery_list')
        else:
            messages.error(request, summary_text)
            form = GalleryImageForm(request.POST)
            batch_form = GalleryBatchUploadForm(request.POST)
            return render(request, 'manage_panel/gallery_form.html', {
                'form': form,
                'batch_form': batch_form,
                'categories': categories,
                'failed_files': failed_files,
                'summary_text': summary_text,
                'title': 'Upload Gallery Photos',
            })
    else:
        form = GalleryImageForm()
        batch_form = GalleryBatchUploadForm()
    return render(request, 'manage_panel/gallery_form.html', {
        'form': form,
        'batch_form': batch_form,
        'categories': categories,
        'title': 'Upload Gallery Photos',
    })


@management_required
def gallery_upload_api_view(request):
    """JSON endpoint for parallel multi-file uploader with per-file progress and retry."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
    created_instances, failed_files, summary_text = _process_gallery_batch_upload(request)
    created_data = [
        {
            'title': obj.title,
            'grid_url': obj.grid_url,
            'large_url': obj.large_url,
        }
        for obj in created_instances
    ]
    return JsonResponse({
        'ok': len(created_instances) > 0,
        'uploaded_count': len(created_instances),
        'failed_count': len(failed_files),
        'uploaded': created_data,
        'failed': failed_files,
        'summary': summary_text,
    })


@management_required
def gallery_bulk_action_view(request):
    """
    Handles bulk metadata editing (caption, title, alt text, category, order, featured, published)
    and bulk deletion of selected gallery images (with confirmation and full variant cleanup).
    """
    if request.method != 'POST':
        return redirect('manage:gallery_list')

    bulk_action = request.POST.get('bulk_action', 'save_edits')

    if bulk_action == 'delete_selected':
        selected_ids = [int(i) for i in request.POST.getlist('selected_ids') if str(i).isdigit()]
        if not selected_ids:
            messages.warning(request, "No gallery images were selected for deletion.")
            return redirect('manage:gallery_list')

        target_qs = GalleryImage.objects.filter(pk__in=selected_ids).order_by('order', '-created_at')
        count = target_qs.count()
        if count == 0:
            messages.warning(request, "Selected gallery images were not found.")
            return redirect('manage:gallery_list')

        if request.POST.get('confirmed') != 'yes':
            return render(request, 'manage_panel/gallery_bulk_confirm_delete.html', {
                'images_to_delete': target_qs,
                'selected_ids': selected_ids,
                'count': count,
            })

        # Delete each image so post_delete signal removes original + grid + large files from disk
        for img in list(target_qs):
            img.delete()
        cache.delete('site_settings_singleton')
        log_audit(
            request.user,
            "BULK_DELETED_GALLERY_IMAGES",
            "GalleryImage",
            "",
            f"Bulk deleted {count} gallery photo(s) and their generated variants from disk",
            request,
        )
        messages.success(request, f"Deleted {count} gallery photo(s) and removed their files from disk.")
        return redirect('manage:gallery_list')

    elif bulk_action == 'save_edits':
        image_ids = [int(i) for i in request.POST.getlist('image_ids') if str(i).isdigit()]
        images_by_id = {img.pk: img for img in GalleryImage.objects.filter(pk__in=image_ids)}
        categories_by_id = {c.pk: c for c in GalleryCategory.objects.all()}
        updated_count = 0

        for pk in image_ids:
            img = images_by_id.get(pk)
            if not img:
                continue
            title_val = request.POST.get(f'title_{pk}', img.title).strip() or img.title
            caption_val = request.POST.get(f'caption_{pk}', img.caption).strip()
            alt_val = request.POST.get(f'alt_text_{pk}', img.alt_text).strip()
            cat_id_raw = request.POST.get(f'category_obj_{pk}', '').strip()
            cat_obj = categories_by_id.get(int(cat_id_raw)) if cat_id_raw.isdigit() else None
            order_raw = str(request.POST.get(f'order_{pk}', img.order)).strip()
            order_val = int(order_raw) if order_raw.lstrip('-').isdigit() else img.order
            featured_val = f'featured_{pk}' in request.POST
            published_val = (f'published_{pk}' in request.POST) or (f'active_{pk}' in request.POST)

            img.title = title_val[:150]
            img.caption = caption_val[:255]
            img.alt_text = alt_val[:200]
            img.category_obj = cat_obj
            if cat_obj:
                img.category = cat_obj.slug
            img.order = order_val
            img.is_featured_home = featured_val
            img.is_active = published_val
            img.save()
            updated_count += 1

        cache.delete('site_settings_singleton')
        log_audit(
            request.user,
            "BULK_EDITED_GALLERY_IMAGES",
            "GalleryImage",
            "",
            f"Bulk updated metadata/order/featured flags for {updated_count} gallery photo(s)",
            request,
        )
        messages.success(request, f"Saved changes for {updated_count} gallery photo(s).")
        return redirect('manage:gallery_list')

    return redirect('manage:gallery_list')


@management_required
def gallery_edit_view(request, pk):
    img = get_object_or_404(GalleryImage, pk=pk)
    if request.method == 'POST':
        form = GalleryImageForm(request.POST, request.FILES, instance=img)
        if form.is_valid():
            form.save()
            cache.delete('site_settings_singleton')
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
        cache.delete('site_settings_singleton')
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


# 12. Audit Log & Audit Log Deletion (Super Admin Exclusive)
@super_admin_required
def audit_log_view(request):
    logs = AuditLog.objects.all().select_related('user').order_by('-timestamp')
    return render(request, 'manage_panel/audit_log.html', {
        'logs': logs,
        'total_logs_count': logs.count(),
    })


@super_admin_required
def audit_log_delete_single_view(request, pk):
    """Super Admin deletes a single audit log entry after confirmation, then writes a new audit entry."""
    entry = get_object_or_404(AuditLog, pk=pk)
    if request.method == 'POST' and request.POST.get('confirmed') == 'yes':
        with transaction.atomic():
            entry_ts = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            entry_action = entry.action
            entry.delete()
            now_str = timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')
            log_audit(
                request.user,
                "DELETED_AUDIT_LOGS",
                "AuditLog",
                str(pk),
                f"Super Admin '{request.user.username}' deleted 1 audit log entry (ID #{pk}, action='{entry_action}', timestamp={entry_ts}) at {now_str}.",
                request,
            )
        messages.success(request, f"Deleted 1 audit log entry (#{pk}) and logged the deletion event.")
        return redirect('manage:audit_log')

    return render(request, 'manage_panel/audit_log_confirm_delete.html', {
        'mode': 'single',
        'single_id': pk,
        'count': 1,
        'range_desc': f"Single entry #{pk} ({entry.action} on {entry.timestamp:%Y-%m-%d %H:%M})",
        'preview_logs': [entry],
    })


@super_admin_required
def audit_log_delete_view(request):
    """
    Super Admin deletes audit log entries by:
    - 'single': single entry by ID
    - 'selected': selected checkboxes (log_ids)
    - 'range': date range (start_date .. end_date)
    - 'all': all audit log entries
    Requires a confirmation step showing the count, and immediately writes
    ONE new AuditLog entry recording who deleted how many entries, the date range, and when.
    """
    data = request.POST if request.method == 'POST' else request.GET
    mode = (data.get('mode') or 'selected').strip()
    single_id = (data.get('single_id') or '').strip()
    selected_ids = [int(i) for i in data.getlist('log_ids') if str(i).isdigit()]
    start_date = (data.get('start_date') or '').strip()
    end_date = (data.get('end_date') or '').strip()

    if mode == 'single' and single_id.isdigit():
        target_qs = AuditLog.objects.filter(pk=int(single_id))
        range_desc = f"single entry #{single_id}"
    elif mode == 'selected':
        target_qs = AuditLog.objects.filter(pk__in=selected_ids)
        range_desc = f"{len(selected_ids)} selected entries"
    elif mode == 'range':
        if not start_date and not end_date:
            messages.error(request, "Please specify a start date or end date for date-range deletion.")
            return redirect('manage:audit_log')
        target_qs = AuditLog.objects.all()
        if start_date:
            target_qs = target_qs.filter(timestamp__date__gte=start_date)
        if end_date:
            target_qs = target_qs.filter(timestamp__date__lte=end_date)
        range_desc = f"date range {start_date or 'beginning'} to {end_date or 'present'}"
    elif mode == 'all':
        target_qs = AuditLog.objects.all()
        range_desc = "all audit log entries"
    else:
        target_qs = AuditLog.objects.none()
        range_desc = "invalid selection"

    count = target_qs.count()
    if count == 0:
        messages.warning(request, "No matching audit log entries found to delete.")
        return redirect('manage:audit_log')

    if request.method == 'POST' and request.POST.get('confirmed') == 'yes':
        with transaction.atomic():
            first_ts = target_qs.order_by('timestamp').values_list('timestamp', flat=True).first()
            last_ts = target_qs.order_by('-timestamp').values_list('timestamp', flat=True).first()
            ts_span = f"{first_ts:%Y-%m-%d %H:%M} to {last_ts:%Y-%m-%d %H:%M}" if (first_ts and last_ts) else range_desc
            target_qs.delete()
            now_str = timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')
            log_audit(
                request.user,
                "DELETED_AUDIT_LOGS",
                "AuditLog",
                mode,
                f"Super Admin '{request.user.username}' deleted {count} audit log entries ({range_desc}; span: {ts_span}) at {now_str}.",
                request,
            )
        messages.success(request, f"Deleted {count} audit log entries and recorded the deletion in the audit log.")
        return redirect('manage:audit_log')

    return render(request, 'manage_panel/audit_log_confirm_delete.html', {
        'mode': mode,
        'single_id': single_id,
        'selected_ids': selected_ids,
        'start_date': start_date,
        'end_date': end_date,
        'count': count,
        'range_desc': range_desc,
        'preview_logs': target_qs.select_related('user').order_by('-timestamp')[:25],
    })


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
            role = form.cleaned_data.get('role')
            if target_user == request.user and role != UserProfile.ROLE_SUPER_ADMIN:
                messages.error(request, "You cannot demote your own currently logged-in Super Admin account.")
                return redirect('manage:users_list')
            if target_user == request.user and not form.cleaned_data.get('is_active', True):
                messages.error(request, "You cannot deactivate your own currently logged-in account.")
                return redirect('manage:users_list')
            u = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                u.set_password(password)
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


# =========================================================================
# 15. Pending Registrations & User Approvals (Super Admin Only for Actions)
# =========================================================================

@management_required
def registrations_list_view(request):
    """
    Displays pending, approved, and rejected user registrations.
    Super Admin can approve/reject; Admin can view in read-only mode.
    """
    status_filter = request.GET.get('status', 'PENDING')
    qs = UserProfile.objects.select_related('user').order_by('-created_at')
    if status_filter in ['PENDING', 'APPROVED', 'REJECTED']:
        qs = qs.filter(approval_status=status_filter)

    context = {
        'profiles': qs,
        'status_filter': status_filter,
        'is_super_admin': is_super_admin(request.user),
        'pending_count': UserProfile.objects.filter(approval_status='PENDING').count(),
        'approved_count': UserProfile.objects.filter(approval_status='APPROVED').count(),
        'rejected_count': UserProfile.objects.filter(approval_status='REJECTED').count(),
    }
    return render(request, 'manage_panel/registrations_list.html', context)


@super_admin_required
def registration_approve_view(request, pk):
    """Approve a user registration, write audit log, and send notification."""
    profile = get_object_or_404(UserProfile, pk=pk)
    if request.method == 'POST':
        profile.approval_status = UserProfile.APPROVAL_APPROVED
        profile.approved_by = request.user
        profile.approved_at = timezone.now()
        profile.rejection_reason = ""
        profile.save()

        # Audit log
        log_audit(
            request.user, "APPROVED_USER_REGISTRATION", "UserProfile", profile.pk,
            f"Approved account for {profile.user.username} ({profile.user.email})", request
        )

        # Email notification
        site_settings = SiteSettings.load()
        subject = f"Account Approved - {site_settings.school_name}"
        message = (
            f"Dear {profile.user.first_name or profile.user.username},\n\n"
            f"Your registration at {site_settings.school_name} has been approved.\n"
            f"You can now log in using your registered credentials at:\n"
            f"http://{request.get_host()}/login/\n\n"
            f"Thank you,\n{site_settings.school_name} Administration"
        )
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [profile.user.email], fail_silently=True)
        except Exception:
            pass

        messages.success(request, f"User '{profile.user.username}' has been successfully approved.")
    return redirect('manage:registrations_list')


@super_admin_required
def registration_reject_view(request, pk):
    """Reject a user registration with a reason, write audit log, and send notification."""
    profile = get_object_or_404(UserProfile, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', '').strip() or "Registration requirements could not be verified."
        profile.approval_status = UserProfile.APPROVAL_REJECTED
        profile.approved_by = request.user
        profile.approved_at = timezone.now()
        profile.rejection_reason = reason
        profile.save()

        # Audit log
        log_audit(
            request.user, "REJECTED_USER_REGISTRATION", "UserProfile", profile.pk,
            f"Rejected account for {profile.user.username}. Reason: {reason}", request
        )

        # Email notification
        site_settings = SiteSettings.load()
        subject = f"Registration Status - {site_settings.school_name}"
        message = (
            f"Dear {profile.user.first_name or profile.user.username},\n\n"
            f"Thank you for your interest in {site_settings.school_name}.\n"
            f"Your account registration was not approved for the following reason:\n"
            f"{reason}\n\n"
            f"If you believe this is in error, please contact the school administration.\n\n"
            f"Sincerely,\n{site_settings.school_name} Admissions Desk"
        )
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [profile.user.email], fail_silently=True)
        except Exception:
            pass

        messages.warning(request, f"User '{profile.user.username}' was marked as REJECTED.")
    return redirect('manage:registrations_list')


@super_admin_required
def registration_bulk_approve_view(request):
    """Bulk approve all pending user registrations."""
    if request.method == 'POST':
        pending_profiles = UserProfile.objects.filter(approval_status=UserProfile.APPROVAL_PENDING)
        count = pending_profiles.count()
        now = timezone.now()
        for p in pending_profiles:
            p.approval_status = UserProfile.APPROVAL_APPROVED
            p.approved_by = request.user
            p.approved_at = now
            p.rejection_reason = ""
            p.save()

        log_audit(
            request.user, "BULK_APPROVED_REGISTRATIONS", "UserProfile", "",
            f"Bulk approved {count} pending user registrations", request
        )
        messages.success(request, f"Successfully approved {count} pending user accounts.")
    return redirect('manage:registrations_list')


# =========================================================================
# 16. Student Enrollment Approvals (Super Admin Only for Actions)
# =========================================================================

@management_required
def enrollments_approval_list_view(request):
    """
    List student course enrollments for approval and management.
    Super Admin can approve/reject; Admin has read-only access.
    """
    status_filter = request.GET.get('status', 'PENDING')
    qs = Student.objects.select_related('course', 'user', 'approved_by').order_by('-created_at')

    if status_filter == 'PENDING':
        qs = qs.filter(status__in=['pending', 'PENDING_APPROVAL'])
    elif status_filter == 'APPROVED':
        qs = qs.filter(status__in=['approved', 'APPROVED', 'enrolled'])
    elif status_filter == 'REJECTED':
        qs = qs.filter(status__in=['rejected', 'REJECTED'])

    context = {
        'enrollments': qs,
        'status_filter': status_filter,
        'is_super_admin': is_super_admin(request.user),
        'pending_count': Student.objects.filter(status__in=['pending', 'PENDING_APPROVAL']).count(),
        'approved_count': Student.objects.filter(status__in=['approved', 'APPROVED', 'enrolled']).count(),
        'rejected_count': Student.objects.filter(status__in=['rejected', 'REJECTED']).count(),
    }
    return render(request, 'manage_panel/enrollments_list.html', context)


@super_admin_required
def enrollment_approve_view(request, pk):
    """Approve a student enrollment, unlocking course content, payments, and lesson bookings."""
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.status = Student.STATUS_APPROVED
        student.approved_by = request.user
        student.approved_at = timezone.now()
        student.rejection_reason = ""
        student.save()

        # If user account is still pending, approve user account too
        if student.user and hasattr(student.user, 'profile'):
            if student.user.profile.approval_status != UserProfile.APPROVAL_APPROVED:
                student.user.profile.approval_status = UserProfile.APPROVAL_APPROVED
                student.user.profile.approved_by = request.user
                student.user.profile.approved_at = timezone.now()
                student.user.profile.save()

        log_audit(
            request.user, "APPROVED_ENROLLMENT", "Student", student.pk,
            f"Approved enrollment for {student.full_name} in {student.course.name}", request
        )

        site_settings = SiteSettings.load()
        subject = f"Course Enrollment Approved - {site_settings.school_name}"
        message = (
            f"Dear {student.first_name},\n\n"
            f"Your enrollment application for {student.course.name} has been approved!\n"
            f"You can now log in to your student dashboard to book driving lessons, review the course curriculum, and complete fee payments:\n"
            f"http://{request.get_host()}/dashboard/\n\n"
            f"We look forward to training you.\n\n"
            f"Sincerely,\n{site_settings.school_name}"
        )
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [student.email], fail_silently=True)
        except Exception:
            pass

        messages.success(request, f"Enrollment for '{student.full_name}' has been approved.")
    return redirect('manage:enrollments_list')


@super_admin_required
def enrollment_reject_view(request, pk):
    """Reject a student enrollment with a specified reason."""
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', '').strip() or "Schedule conflict or eligibility criteria not satisfied."
        student.status = Student.STATUS_REJECTED
        student.approved_by = request.user
        student.approved_at = timezone.now()
        student.rejection_reason = reason
        student.save()

        log_audit(
            request.user, "REJECTED_ENROLLMENT", "Student", student.pk,
            f"Rejected enrollment for {student.full_name} in {student.course.name}. Reason: {reason}", request
        )

        site_settings = SiteSettings.load()
        subject = f"Enrollment Application Update - {site_settings.school_name}"
        message = (
            f"Dear {student.first_name},\n\n"
            f"Your enrollment application for {student.course.name} could not be approved at this time.\n"
            f"Reason provided: {reason}\n\n"
            f"Please contact the admissions desk if you have questions.\n\n"
            f"Sincerely,\n{site_settings.school_name}"
        )
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [student.email], fail_silently=True)
        except Exception:
            pass

        messages.warning(request, f"Enrollment for '{student.full_name}' was marked as REJECTED.")
    return redirect('manage:enrollments_list')


@management_required
def students_list_view(request):
    """List of all student profiles/enrollments with search and quick link to Student Detail & Enroll in Course."""
    q = (request.GET.get('q') or '').strip()
    students = Student.objects.select_related('course', 'branch', 'user', 'approved_by').order_by('-created_at')
    if q:
        students = students.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
            | Q(phone__icontains=q)
            | Q(id_number__icontains=q)
        )
    return render(request, 'manage_panel/students_list.html', {
        'students': students,
        'search_query': q,
        'is_super_admin': is_super_admin(request.user),
    })


@management_required
def student_detail_view(request, pk):
    """
    Student Detail Page:
    Displays student profile, age, all course enrollments for this student,
    fee/discount/payment breakdown, lesson bookings, and an "Enroll in a course" button.
    """
    student = get_object_or_404(Student.objects.select_related('course', 'branch', 'user', 'approved_by'), pk=pk)
    all_enrollments = Student.objects.filter(
        Q(email__iexact=student.email) | Q(id_number__iexact=student.id_number)
    ).select_related('course', 'branch', 'approved_by').order_by('-created_at')
    bookings = LessonBooking.objects.filter(student__in=all_enrollments).select_related('course', 'branch', 'instructor', 'vehicle').order_by('-date', 'start_time')

    return render(request, 'manage_panel/student_detail.html', {
        'student': student,
        'all_enrollments': all_enrollments,
        'bookings': bookings,
        'is_super_admin': is_super_admin(request.user),
    })


@management_required
def enrollment_create_view(request):
    """
    Staff Student Enrollment (Super Admin & Admin):
    - Pick an existing student (searchable) OR create a new 18+ student on the spot.
    - Select branch, course (filtered by branch), start date, total fee (defaults to course fee, editable),
      optional discount with reason, and optional initial payment.
    - Staff accounts do NOT need a Student profile.
    - Super Admin enrollments are APPROVED automatically.
    - Admin enrollments are set to PENDING_APPROVAL for Super Admin review.
    - Blocks duplicate active enrollments (same student + same course + still active).
    """
    is_super = is_super_admin(request.user)
    preselected_student = None
    student_id_param = (request.GET.get('student_id') or '').strip()
    if student_id_param.isdigit():
        preselected_student = Student.objects.filter(pk=int(student_id_param)).first()

    if request.method == 'POST':
        form = StaffEnrollmentForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            mode = cd.get('student_mode') or 'new'
            existing_st = cd.get('existing_student')
            course = cd['course']
            branch = cd['branch']
            total_fee = cd.get('total_fee')
            if total_fee is None:
                total_fee = course.fee

            student = Student(
                first_name=cd['first_name'],
                last_name=cd['last_name'],
                email=cd['email'],
                phone=cd['phone'],
                id_number=cd['id_number'],
                date_of_birth=cd['date_of_birth'],
                gender=cd.get('gender') or '',
                course=course,
                branch=branch,
                preferred_branch=branch.name,
                start_date=cd.get('start_date') or timezone.localdate(),
                preferred_schedule=cd.get('preferred_schedule') or 'morning',
                total_fee=total_fee,
                discount_amount=cd.get('discount_amount') or 0,
                discount_reason=cd.get('discount_reason') or '',
                initial_payment_amount=cd.get('initial_payment_amount') or 0,
                payment_method=cd.get('payment_method') or '',
                payment_reference=cd.get('payment_reference') or '',
                notes=cd.get('notes') or '',
            )
            if mode == 'existing' and existing_st and existing_st.user_id:
                student.user = existing_st.user
            else:
                matched_user = User.objects.filter(email__iexact=cd['email']).first()
                if matched_user and not is_super_admin(matched_user) and not matched_user.is_staff:
                    student.user = matched_user

            if is_super:
                student.status = Student.STATUS_APPROVED
                student.approved_by = request.user
                student.approved_at = timezone.now()
            else:
                student.status = Student.STATUS_PENDING_APPROVAL

            student.save()

            log_audit(
                request.user,
                "MANUAL_ENROLLMENT_CREATED",
                "Student",
                student.pk,
                (
                    f"Staff ({request.user.username}) enrolled {student.full_name} in '{course.name}' "
                    f"at '{branch.name}' (Fee: KES {student.total_fee}, Discount: KES {student.discount_amount}, "
                    f"Initial Paid: KES {student.initial_payment_amount}, Status: {student.status})"
                ),
                request,
            )
            msg = f"Student '{student.full_name}' enrolled in '{course.name}' successfully." + (
                " (Auto-approved by Super Admin)" if is_super else " (Pending Super Admin approval)"
            )
            messages.success(request, msg)
            return redirect('manage:student_detail', pk=student.pk)
    else:
        initial = {'student_mode': 'new', 'start_date': timezone.localdate().isoformat()}
        if preselected_student:
            initial.update({
                'student_mode': 'existing',
                'existing_student': preselected_student.pk,
                'branch': preselected_student.branch_id,
            })
        form = StaffEnrollmentForm(initial=initial)

    # Provide branch->course and course->fee JSON map for instant client-side filtering & fee default
    courses_qs = Course.objects.filter(is_active=True).prefetch_related('branches').order_by('order', 'name')
    courses_meta = [
        {
            'id': c.pk,
            'name': c.name,
            'code': c.code,
            'fee': str(c.fee),
            'branch_ids': [b.pk for b in c.branches.all()],
        }
        for c in courses_qs
    ]

    return render(request, 'manage_panel/enrollment_form.html', {
        'form': form,
        'title': 'Enroll a Student',
        'is_super_admin': is_super,
        'preselected_student': preselected_student,
        'courses_meta': courses_meta,
    })


# =========================================================================
# 17. Homepage Sections Toggle & Order (Super Admin & Admin)
# =========================================================================

@management_required
def home_sections_view(request):
    """Toggle each homepage section on/off and set display order."""
    sections = HomeSection.ensure_defaults()
    if request.method == 'POST':
        for sec in sections:
            enabled_key = f"enabled_{sec.section_key}"
            order_key = f"order_{sec.section_key}"
            sec.is_enabled = enabled_key in request.POST
            order_val = request.POST.get(order_key)
            if order_val and str(order_val).lstrip('-').isdigit():
                sec.order = int(order_val)
            sec.save()
        log_audit(request.user, "UPDATED_HOME_SECTIONS", "HomeSection", "", "Updated homepage section visibility and display order", request)
        messages.success(request, "Homepage sections visibility and order updated.")
        return redirect('manage:home_sections')

    return render(request, 'manage_panel/home_sections.html', {'sections': HomeSection.objects.all().order_by('order', 'id')})


# =========================================================================
# 18. School Branches (Super Admin CRUD; Admin View-Only)
# =========================================================================

@management_required
def branches_list_view(request):
    branches = Branch.objects.all().order_by('order', 'name')
    return render(request, 'manage_panel/branches_list.html', {
        'branches': branches,
        'is_super_admin': is_super_admin(request.user),
    })


@super_admin_required
def branch_create_view(request):
    if request.method == 'POST':
        form = BranchForm(request.POST, request.FILES)
        if form.is_valid():
            branch = form.save()
            log_audit(request.user, "CREATED_BRANCH", "Branch", branch.pk, f"Created branch '{branch.name}' ({branch.code})", request)
            messages.success(request, f"Branch '{branch.name}' created.")
            return redirect('manage:branches_list')
    else:
        form = BranchForm()
    return render(request, 'manage_panel/branch_form.html', {'form': form, 'title': 'Add School Branch'})


@management_required
def branch_edit_view(request, pk):
    """Super Admin edits the whole branch; Admin may edit the map fields only."""
    branch = get_object_or_404(Branch, pk=pk)
    super_admin = is_super_admin(request.user)
    form_class = BranchForm if super_admin else BranchMapForm
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=branch)
        if form.is_valid():
            form.save()
            action = "EDITED_BRANCH" if super_admin else "EDITED_BRANCH_MAP"
            log_audit(request.user, action, "Branch", branch.pk, f"Updated branch '{branch.name}'" + ("" if super_admin else " (map only)"), request)
            messages.success(request, f"Branch '{branch.name}' updated." if super_admin else f"Map for '{branch.name}' updated.")
            return redirect('manage:branches_list')
    else:
        form = form_class(instance=branch)
    return render(request, 'manage_panel/branch_form.html', {
        'form': form,
        'branch': branch,
        'map_only': not super_admin,
        'title': f'Edit Branch: {branch.name}' if super_admin else f'Edit Map: {branch.name}',
    })


@management_required
def branch_map_preview_view(request):
    """Live preview for the branch form: validates exactly like saving, returns the iframe src as JSON."""
    from decimal import Decimal, InvalidOperation
    from courses.map_utils import normalize_map_embed_url

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required.'}, status=405)

    post = request.POST
    try:
        embed = normalize_map_embed_url(post.get('map_embed_url', ''))
    except ValidationError as exc:
        return JsonResponse({'ok': False, 'error': exc.messages[0]})

    def _decimal(name, low, high):
        raw = (post.get(name) or '').strip()
        if not raw:
            return None
        try:
            value = Decimal(raw)
        except InvalidOperation:
            raise ValidationError(f"{name.title()} must be a number.")
        if not (Decimal(low) <= value <= Decimal(high)):
            raise ValidationError(f"{name.title()} must be between {low} and {high}.")
        return value

    try:
        latitude = _decimal('latitude', '-90', '90')
        longitude = _decimal('longitude', '-180', '180')
    except ValidationError as exc:
        return JsonResponse({'ok': False, 'error': exc.messages[0]})
    if (latitude is None) != (longitude is None):
        return JsonResponse({'ok': False, 'error': "Enter both latitude and longitude, or leave both empty."})

    try:
        zoom = int(post.get('map_zoom') or 16)
    except ValueError:
        zoom = 16
    zoom = min(max(zoom, 1), 21)

    probe = Branch(
        address=(post.get('address') or '')[:255],
        town=(post.get('town') or '')[:100],
        map_embed_url=embed,
        latitude=latitude,
        longitude=longitude,
        map_zoom=zoom,
    )
    return JsonResponse({
        'ok': True,
        'src': probe.map_src,
        'directions_url': probe.directions_url,
        'maps_open_url': probe.maps_open_url,
    })


@super_admin_required
def branch_toggle_view(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == 'POST':
        branch.is_active = not branch.is_active
        branch.save()
        state = "activated" if branch.is_active else "deactivated"
        log_audit(request.user, "TOGGLED_BRANCH", "Branch", branch.pk, f"Branch '{branch.name}' {state}", request)
        messages.success(request, f"Branch '{branch.name}' {state}.")
    return redirect('manage:branches_list')


@super_admin_required
def branch_delete_view(request, pk):
    """
    Super Admin Branch Deletion with Dependent Protection:
    - Shows dependent counts (students/enrollments, instructors, vehicles, courses, bookings).
    - (a) If 0 dependents: requires typed confirmation of the exact branch name (`confirm_branch_name`).
    - (b) If dependents exist: requires choosing another branch (`target_branch_id`) to MOVE all
      dependent records to inside a single transaction.atomic(), then deletes the branch and writes an AuditLog entry.
    - (c) Offers "Deactivate instead" (`action == 'deactivate'`).
    """
    branch = get_object_or_404(Branch, pk=pk)
    students_count = branch.students.count()
    instructors_count = branch.instructors.count()
    vehicles_count = branch.vehicles.count()
    courses_count = branch.courses.count()
    bookings_count = branch.bookings.count()
    enrollments_count = students_count
    total_dependents = students_count + instructors_count + vehicles_count + courses_count + bookings_count
    has_dependents = total_dependents > 0
    other_branches = Branch.objects.exclude(pk=branch.pk).order_by('order', 'name')

    if request.method == 'POST':
        action = (request.POST.get('action') or 'delete').strip()

        # Option (c): Deactivate instead
        if action == 'deactivate':
            branch.is_active = False
            branch.save()
            log_audit(
                request.user,
                "DEACTIVATED_BRANCH",
                "Branch",
                branch.pk,
                f"Deactivated branch '{branch.name}' ({branch.code}) instead of deleting",
                request,
            )
            messages.success(request, f"Branch '{branch.name}' has been deactivated.")
            return redirect('manage:branches_list')

        # Option (b): Dependents exist -> require moving to target_branch_id inside transaction.atomic()
        if has_dependents:
            target_branch_id = (request.POST.get('target_branch_id') or '').strip()
            target_branch = (
                Branch.objects.exclude(pk=branch.pk).filter(pk=int(target_branch_id)).first()
                if target_branch_id.isdigit()
                else None
            )
            if not target_branch:
                messages.error(
                    request,
                    f"Cannot delete branch '{branch.name}' without selecting a target branch to move its {total_dependents} dependent record(s) to.",
                )
                return redirect('manage:branch_delete', pk=branch.pk)

            with transaction.atomic():
                moved_students = branch.students.update(branch=target_branch, preferred_branch=target_branch.name)
                moved_instructors = branch.instructors.update(branch=target_branch)
                moved_vehicles = branch.vehicles.update(branch=target_branch)
                moved_bookings = branch.bookings.update(branch=target_branch)
                linked_courses = list(branch.courses.all())
                for c in linked_courses:
                    c.branches.add(target_branch)
                    c.branches.remove(branch)
                moved_courses = len(linked_courses)

                old_name = branch.name
                old_code = branch.code
                branch.delete()

                log_audit(
                    request.user,
                    "MOVED_AND_DELETED_BRANCH",
                    "Branch",
                    pk,
                    (
                        f"Moved dependents from '{old_name}' ({old_code}) to '{target_branch.name}' "
                        f"(students/enrollments={moved_students}, instructors={moved_instructors}, "
                        f"vehicles={moved_vehicles}, courses={moved_courses}, bookings={moved_bookings}) "
                        f"and deleted branch '{old_name}'."
                    ),
                    request,
                )
            messages.success(
                request,
                f"Moved all dependent records to '{target_branch.name}' and deleted branch '{old_name}'.",
            )
            return redirect('manage:branches_list')

        # Option (a): 0 dependents -> require typed confirmation of the branch name
        confirm_name = (request.POST.get('confirm_branch_name') or '').strip()
        if confirm_name != branch.name:
            messages.error(
                request,
                f"Please type the exact branch name '{branch.name}' to confirm deletion.",
            )
            return render(request, 'manage_panel/branch_confirm_delete.html', {
                'branch': branch,
                'has_dependents': False,
                'total_dependents': 0,
                'students_count': 0,
                'enrollments_count': 0,
                'instructors_count': 0,
                'vehicles_count': 0,
                'courses_count': 0,
                'bookings_count': 0,
                'other_branches': other_branches,
            })

        with transaction.atomic():
            name = branch.name
            code = branch.code
            branch.delete()
            log_audit(request.user, "DELETED_BRANCH", "Branch", pk, f"Deleted empty branch '{name}' ({code})", request)
        messages.success(request, f"Branch '{name}' deleted.")
        return redirect('manage:branches_list')

    return render(request, 'manage_panel/branch_confirm_delete.html', {
        'branch': branch,
        'has_dependents': has_dependents,
        'total_dependents': total_dependents,
        'students_count': students_count,
        'enrollments_count': enrollments_count,
        'instructors_count': instructors_count,
        'vehicles_count': vehicles_count,
        'courses_count': courses_count,
        'bookings_count': bookings_count,
        'other_branches': other_branches,
    })


# =========================================================================
# 19. Training Vehicles Fleet (Super Admin & Admin)
# =========================================================================

@management_required
def vehicles_list_view(request):
    vehicles = Vehicle.objects.select_related('branch').all()
    return render(request, 'manage_panel/vehicles_list.html', {'vehicles': vehicles})


@management_required
def vehicle_create_view(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            v = form.save()
            log_audit(request.user, "CREATED_VEHICLE", "Vehicle", v.pk, f"Added vehicle {v.plate_number}", request)
            messages.success(request, f"Vehicle '{v.plate_number}' added.")
            return redirect('manage:vehicles_list')
    else:
        form = VehicleForm()
    return render(request, 'manage_panel/vehicle_form.html', {'form': form, 'title': 'Add Training Vehicle'})


@management_required
def vehicle_edit_view(request, pk):
    v = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=v)
        if form.is_valid():
            form.save()
            log_audit(request.user, "EDITED_VEHICLE", "Vehicle", v.pk, f"Updated vehicle {v.plate_number}", request)
            messages.success(request, f"Vehicle '{v.plate_number}' updated.")
            return redirect('manage:vehicles_list')
    else:
        form = VehicleForm(instance=v)
    return render(request, 'manage_panel/vehicle_form.html', {'form': form, 'vehicle': v, 'title': f'Edit Vehicle: {v.plate_number}'})


@management_required
def vehicle_delete_view(request, pk):
    v = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        plate = v.plate_number
        v.delete()
        log_audit(request.user, "DELETED_VEHICLE", "Vehicle", pk, f"Deleted vehicle {plate}", request)
        messages.success(request, f"Vehicle '{plate}' deleted.")
        return redirect('manage:vehicles_list')
    return render(request, 'manage_panel/confirm_delete.html', {'object': v, 'cancel_url': 'manage:vehicles_list'})


# =========================================================================
# 20. Gallery Categories CRUD (Super Admin & Admin)
# =========================================================================

@management_required
def gallery_categories_list_view(request):
    categories = GalleryCategory.ensure_defaults()
    return render(request, 'manage_panel/gallery_categories_list.html', {'categories': categories})


@management_required
def gallery_category_create_view(request):
    if request.method == 'POST':
        form = GalleryCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            log_audit(request.user, "CREATED_GALLERY_CATEGORY", "GalleryCategory", cat.pk, f"Created gallery category '{cat.name}'", request)
            messages.success(request, f"Gallery category '{cat.name}' created.")
            return redirect('manage:gallery_categories_list')
    else:
        form = GalleryCategoryForm()
    return render(request, 'manage_panel/gallery_category_form.html', {'form': form, 'title': 'Add Gallery Category'})


@management_required
def gallery_category_edit_view(request, pk):
    cat = get_object_or_404(GalleryCategory, pk=pk)
    if request.method == 'POST':
        form = GalleryCategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            log_audit(request.user, "EDITED_GALLERY_CATEGORY", "GalleryCategory", cat.pk, f"Updated gallery category '{cat.name}'", request)
            messages.success(request, f"Gallery category '{cat.name}' updated.")
            return redirect('manage:gallery_categories_list')
    else:
        form = GalleryCategoryForm(instance=cat)
    return render(request, 'manage_panel/gallery_category_form.html', {'form': form, 'category': cat, 'title': f'Edit Category: {cat.name}'})


@management_required
def gallery_category_delete_view(request, pk):
    cat = get_object_or_404(GalleryCategory, pk=pk)
    if request.method == 'POST':
        name = cat.name
        cat.delete()
        log_audit(request.user, "DELETED_GALLERY_CATEGORY", "GalleryCategory", pk, f"Deleted gallery category '{name}'", request)
        messages.success(request, f"Gallery category '{name}' deleted.")
        return redirect('manage:gallery_categories_list')
    return render(request, 'manage_panel/confirm_delete.html', {'object': cat, 'cancel_url': 'manage:gallery_categories_list'})


# =========================================================================
# 21. Social Media Links (Super Admin & Admin)
# =========================================================================

@management_required
def social_links_view(request):
    site_settings = SiteSettings.load()
    custom_links = CustomSocialLink.objects.all().order_by('order', 'label')
    if request.method == 'POST':
        form = SocialLinksForm(request.POST, instance=site_settings)
        if form.is_valid():
            form.save()
            log_audit(request.user, "UPDATED_SOCIAL_LINKS", "SiteSettings", site_settings.pk, "Updated social media URLs and visibility toggles", request)
            messages.success(request, "Social media links updated and live on the public site.")
            return redirect('manage:social_links')
    else:
        form = SocialLinksForm(instance=site_settings)

    return render(request, 'manage_panel/social_links.html', {
        'form': form,
        'custom_links': custom_links,
        'site_settings': site_settings,
    })


@management_required
def custom_social_create_view(request):
    if request.method == 'POST':
        form = CustomSocialLinkForm(request.POST)
        if form.is_valid():
            link = form.save()
            log_audit(request.user, "CREATED_CUSTOM_SOCIAL", "CustomSocialLink", link.pk, f"Created social link '{link.label}'", request)
            messages.success(request, f"Custom social link '{link.label}' added.")
            return redirect('manage:social_links')
    else:
        form = CustomSocialLinkForm()
    return render(request, 'manage_panel/custom_social_form.html', {'form': form, 'title': 'Add Custom Social Link'})


@management_required
def custom_social_edit_view(request, pk):
    link = get_object_or_404(CustomSocialLink, pk=pk)
    if request.method == 'POST':
        form = CustomSocialLinkForm(request.POST, instance=link)
        if form.is_valid():
            form.save()
            log_audit(request.user, "EDITED_CUSTOM_SOCIAL", "CustomSocialLink", link.pk, f"Updated social link '{link.label}'", request)
            messages.success(request, f"Custom social link '{link.label}' updated.")
            return redirect('manage:social_links')
    else:
        form = CustomSocialLinkForm(instance=link)
    return render(request, 'manage_panel/custom_social_form.html', {'form': form, 'link': link, 'title': f'Edit Social Link: {link.label}'})


@management_required
def custom_social_delete_view(request, pk):
    link = get_object_or_404(CustomSocialLink, pk=pk)
    if request.method == 'POST':
        label = link.label
        link.delete()
        log_audit(request.user, "DELETED_CUSTOM_SOCIAL", "CustomSocialLink", pk, f"Deleted social link '{label}'", request)
        messages.success(request, f"Custom social link '{label}' deleted.")
        return redirect('manage:social_links')
    return render(request, 'manage_panel/confirm_delete.html', {'object': link, 'cancel_url': 'manage:social_links'})


# =========================================================================
# 22. Lesson Verification Queue & Schedule (Super Admin & Admin)
# =========================================================================

@management_required
def lessons_list_view(request):
    """
    Admin & Super Admin Lesson Verification & Schedule screen.
    Filter by status, branch, instructor, student, course, and date.
    """
    status_filter = request.GET.get('status', 'COMPLETED')
    branch_id = request.GET.get('branch')
    instructor_id = request.GET.get('instructor')
    course_id = request.GET.get('course')
    date_filter = request.GET.get('date')

    qs = LessonBooking.objects.select_related('student', 'course', 'branch', 'instructor', 'vehicle', 'verified_by').order_by('-date', 'start_time')
    if status_filter and status_filter != 'ALL':
        qs = qs.filter(status=status_filter)
    if branch_id and branch_id.isdigit():
        qs = qs.filter(branch_id=int(branch_id))
    if instructor_id and instructor_id.isdigit():
        qs = qs.filter(instructor_id=int(instructor_id))
    if course_id and course_id.isdigit():
        qs = qs.filter(course_id=int(course_id))
    if date_filter:
        qs = qs.filter(date=date_filter)

    context = {
        'bookings': qs,
        'status_filter': status_filter,
        'branches': Branch.objects.all(),
        'instructors': Instructor.objects.all(),
        'courses': Course.objects.all(),
        'selected_branch': int(branch_id) if (branch_id and branch_id.isdigit()) else None,
        'selected_instructor': int(instructor_id) if (instructor_id and instructor_id.isdigit()) else None,
        'selected_course': int(course_id) if (course_id and course_id.isdigit()) else None,
        'date_filter': date_filter or '',
        'completed_count': LessonBooking.objects.filter(status='COMPLETED').count(),
        'scheduled_count': LessonBooking.objects.filter(status='SCHEDULED').count(),
        'verified_count': LessonBooking.objects.filter(status='VERIFIED').count(),
    }
    return render(request, 'manage_panel/lessons_list.html', context)


@management_required
def lesson_verify_view(request, pk):
    """Admin or Super Admin verifies a completed lesson."""
    booking = get_object_or_404(LessonBooking, pk=pk)
    if request.method == 'POST':
        booking.status = 'VERIFIED'
        booking.verified_by = request.user
        booking.verified_at = timezone.now()
        booking.rejection_reason = ''
        booking.save()

        log_audit(
            request.user, "VERIFIED_LESSON", "LessonBooking", booking.pk,
            f"Verified {booking.get_lesson_type_display()} for {booking.student.full_name} on {booking.date}", request
        )
        try:
            send_mail(
                f"Lesson Verified - Belings Driving School",
                f"Dear {booking.student.first_name},\n\nYour {booking.get_lesson_type_display()} on {booking.date} has been verified by administration and credited to your course progress.",
                settings.DEFAULT_FROM_EMAIL,
                [booking.student.email],
                fail_silently=True,
            )
        except Exception:
            pass
        messages.success(request, f"Lesson for {booking.student.full_name} on {booking.date} verified.")
    return redirect('manage:lessons_list')


@management_required
def lesson_reject_view(request, pk):
    """Admin or Super Admin rejects/disputes a lesson with a reason."""
    booking = get_object_or_404(LessonBooking, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', '').strip() or "Attendance or lesson duration could not be verified."
        booking.status = 'REJECTED'
        booking.verified_by = request.user
        booking.verified_at = timezone.now()
        booking.rejection_reason = reason
        booking.save()

        log_audit(
            request.user, "REJECTED_LESSON", "LessonBooking", booking.pk,
            f"Rejected lesson for {booking.student.full_name} on {booking.date}. Reason: {reason}", request
        )
        messages.warning(request, f"Lesson for {booking.student.full_name} marked as Disputed/Rejected.")
    return redirect('manage:lessons_list')


@management_required
def lesson_bulk_verify_view(request):
    """Bulk verify selected or all COMPLETED lessons."""
    if request.method == 'POST':
        ids = request.POST.getlist('booking_ids')
        qs = LessonBooking.objects.filter(status='COMPLETED')
        if ids:
            qs = qs.filter(pk__in=ids)
        count = qs.count()
        now = timezone.now()
        for b in qs:
            b.status = 'VERIFIED'
            b.verified_by = request.user
            b.verified_at = now
            b.rejection_reason = ''
            b.save()
        log_audit(request.user, "BULK_VERIFIED_LESSONS", "LessonBooking", "", f"Bulk verified {count} completed lessons", request)
        messages.success(request, f"Verified {count} lessons.")
    return redirect('manage:lessons_list')


# =========================================================================
# 23. Email Configuration & Compose (Super Admin Exclusive)
# =========================================================================

@super_admin_required
def email_settings_view(request):
    """
    Super Admin Exclusive: Configure SMTP settings with Fernet-encrypted password,
    and send a live test email.
    """
    email_cfg = EmailSettings.load()
    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        if action == 'send_test_email':
            test_recipient = request.POST.get('test_recipient', '').strip() or request.user.email
            if not test_recipient:
                messages.error(request, "Please enter a recipient email address for the test email.")
            else:
                subject = "Test Email - Belings Driving School SMTP Configuration"
                body = (
                    f"Hello,\n\nThis is a test email triggered by {request.user.username} from the Belings Driving School Management Panel.\n"
                    f"SMTP Host: {email_cfg.smtp_host or 'Console Fallback'}\n"
                    f"Port: {email_cfg.smtp_port}\n"
                    f"Security: {email_cfg.security_protocol}\n"
                )
                from_addr = f"{email_cfg.default_from_name} <{email_cfg.default_from_email}>" if email_cfg.default_from_name else email_cfg.default_from_email
                try:
                    send_mail(subject, body, from_addr, [test_recipient], fail_silently=False)
                    EmailLog.objects.create(
                        sender=request.user,
                        recipient=test_recipient,
                        subject=subject,
                        body=body,
                        status='SENT',
                    )
                    log_audit(request.user, "SENT_TEST_EMAIL", "EmailSettings", email_cfg.pk, f"Sent test email to {test_recipient}", request)
                    messages.success(request, f"Test email sent successfully to {test_recipient}.")
                except Exception as exc:
                    EmailLog.objects.create(
                        sender=request.user,
                        recipient=test_recipient,
                        subject=subject,
                        body=body,
                        status='FAILED',
                        error_message=str(exc),
                    )
                    messages.error(request, f"SMTP Test Failed: {exc}")
            return redirect('manage:email_settings')
        else:
            form = EmailSettingsForm(request.POST, instance=email_cfg)
            if form.is_valid():
                form.save()
                log_audit(request.user, "UPDATED_EMAIL_SETTINGS", "EmailSettings", email_cfg.pk, "Updated SMTP configuration", request)
                messages.success(request, "Email configuration saved and encrypted.")
                return redirect('manage:email_settings')
    else:
        form = EmailSettingsForm(instance=email_cfg)

    return render(request, 'manage_panel/email_settings.html', {
        'form': form,
        'email_cfg': email_cfg,
    })


@super_admin_required
def email_compose_view(request):
    """
    Super Admin Exclusive: Compose and send email to a student, instructor,
    group, or custom address with rate limiting and EmailLog recording.
    """
    students = Student.objects.all().order_by('first_name', 'last_name')
    instructors = Instructor.objects.all().order_by('full_name')
    recent_logs = EmailLog.objects.select_related('sender').order_by('-created_at')[:25]

    if request.method == 'POST':
        target_type = request.POST.get('target_type', 'custom')
        custom_email = request.POST.get('custom_email', '').strip()
        student_id = request.POST.get('student_id')
        instructor_id = request.POST.get('instructor_id')
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()

        # Rate limit check: max 30 emails sent in the last 10 minutes
        ten_mins_ago = timezone.now() - timezone.timedelta(minutes=10)
        recent_count = EmailLog.objects.filter(sender=request.user, created_at__gte=ten_mins_ago).count()
        if recent_count >= 30:
            messages.error(request, "Rate limit reached: Maximum 30 emails per 10 minutes.")
            return redirect('manage:email_compose')

        recipients = []
        if target_type == 'student' and student_id and student_id.isdigit():
            st = Student.objects.filter(pk=int(student_id)).first()
            if st and st.email:
                recipients.append(st.email)
        elif target_type == 'instructor' and instructor_id and instructor_id.isdigit():
            inst = Instructor.objects.filter(pk=int(instructor_id)).first()
            if inst and inst.email:
                recipients.append(inst.email)
        elif target_type == 'all_students':
            recipients = [s.email for s in students if s.email]
        elif target_type == 'all_instructors':
            recipients = [i.email for i in instructors if i.email]
        elif custom_email:
            recipients = [e.strip() for e in custom_email.split(',') if e.strip()]

        if not recipients:
            messages.error(request, "Please select or enter at least one valid recipient email address.")
        elif not subject or not body:
            messages.error(request, "Subject and message body are required.")
        else:
            email_cfg = EmailSettings.load()
            from_addr = f"{email_cfg.default_from_name} <{email_cfg.default_from_email}>" if email_cfg.default_from_name else email_cfg.default_from_email
            sent_ok = 0
            for rcpt in recipients:
                try:
                    send_mail(subject, body, from_addr, [rcpt], fail_silently=False)
                    EmailLog.objects.create(
                        sender=request.user,
                        recipient=rcpt,
                        subject=subject,
                        body=body,
                        status='SENT',
                    )
                    sent_ok += 1
                except Exception as exc:
                    EmailLog.objects.create(
                        sender=request.user,
                        recipient=rcpt,
                        subject=subject,
                        body=body,
                        status='FAILED',
                        error_message=str(exc),
                    )
            log_audit(request.user, "SENT_COMPOSED_EMAIL", "EmailLog", "", f"Sent '{subject}' to {sent_ok}/{len(recipients)} recipients", request)
            if sent_ok == len(recipients):
                messages.success(request, f"Email sent to {sent_ok} recipient(s).")
            else:
                messages.warning(request, f"Sent {sent_ok} of {len(recipients)} emails. Check the log below for errors.")
            return redirect('manage:email_compose')

    return render(request, 'manage_panel/email_compose.html', {
        'students': students,
        'instructors': instructors,
        'recent_logs': recent_logs,
    })

