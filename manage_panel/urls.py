from django.urls import path
from . import views

app_name = 'manage'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),

    # 1. Branding
    path('branding/', views.branding_view, name='branding'),

    # 2. Media Library
    path('media/', views.media_library_view, name='media_library'),

    # 3. Homepage Content, Slider & Sections
    path('homepage/', views.homepage_content_view, name='homepage_content'),
    path('home-sections/', views.home_sections_view, name='home_sections'),
    path('slides/add/', views.slide_create_view, name='slide_create'),
    path('slides/<int:pk>/edit/', views.slide_edit_view, name='slide_edit'),
    path('slides/<int:pk>/delete/', views.slide_delete_view, name='slide_delete'),
    path('why-choose/add/', views.why_choose_create_view, name='why_choose_create'),
    path('why-choose/<int:pk>/edit/', views.why_choose_edit_view, name='why_choose_edit'),
    path('why-choose/<int:pk>/delete/', views.why_choose_delete_view, name='why_choose_delete'),

    # 4. Pages (About, Terms, Privacy)
    path('pages/', views.pages_list_view, name='pages_list'),
    path('pages/<str:slug>/edit/', views.page_edit_view, name='page_edit'),

    # 5. Courses & Fees
    path('courses/', views.courses_list_view, name='courses_list'),
    path('courses/add/', views.course_create_view, name='course_create'),
    path('courses/<int:pk>/edit/', views.course_edit_view, name='course_edit'),
    path('courses/<int:pk>/delete/', views.course_delete_view, name='course_delete'),

    # 6. Branches, Vehicles, Instructors, Gallery, Categories, Testimonials, FAQs
    path('branches/', views.branches_list_view, name='branches_list'),
    path('branches/add/', views.branch_create_view, name='branch_create'),
    path('branches/map-preview/', views.branch_map_preview_view, name='branch_map_preview'),
    path('branches/<int:pk>/edit/', views.branch_edit_view, name='branch_edit'),
    path('branches/<int:pk>/toggle/', views.branch_toggle_view, name='branch_toggle'),
    path('branches/<int:pk>/delete/', views.branch_delete_view, name='branch_delete'),

    path('vehicles/', views.vehicles_list_view, name='vehicles_list'),
    path('vehicles/add/', views.vehicle_create_view, name='vehicle_create'),
    path('vehicles/<int:pk>/edit/', views.vehicle_edit_view, name='vehicle_edit'),
    path('vehicles/<int:pk>/delete/', views.vehicle_delete_view, name='vehicle_delete'),

    path('instructors/', views.instructors_list_view, name='instructors_list'),
    path('instructors/add/', views.instructor_create_view, name='instructor_create'),
    path('instructors/<int:pk>/edit/', views.instructor_edit_view, name='instructor_edit'),
    path('instructors/<int:pk>/delete/', views.instructor_delete_view, name='instructor_delete'),

    path('gallery/', views.gallery_list_view, name='gallery_list'),
    path('gallery/add/', views.gallery_create_view, name='gallery_create'),
    path('gallery/upload-api/', views.gallery_upload_api_view, name='gallery_upload_api'),
    path('gallery/bulk-action/', views.gallery_bulk_action_view, name='gallery_bulk_action'),
    path('gallery/<int:pk>/edit/', views.gallery_edit_view, name='gallery_edit'),
    path('gallery/<int:pk>/delete/', views.gallery_delete_view, name='gallery_delete'),

    path('gallery/categories/', views.gallery_categories_list_view, name='gallery_categories_list'),
    path('gallery/categories/add/', views.gallery_category_create_view, name='gallery_category_create'),
    path('gallery/categories/<int:pk>/edit/', views.gallery_category_edit_view, name='gallery_category_edit'),
    path('gallery/categories/<int:pk>/delete/', views.gallery_category_delete_view, name='gallery_category_delete'),

    path('testimonials/', views.testimonials_list_view, name='testimonials_list'),
    path('testimonials/add/', views.testimonial_create_view, name='testimonial_create'),
    path('testimonials/<int:pk>/edit/', views.testimonial_edit_view, name='testimonial_edit'),
    path('testimonials/<int:pk>/delete/', views.testimonial_delete_view, name='testimonial_delete'),

    path('faqs/', views.faqs_list_view, name='faqs_list'),
    path('faqs/add/', views.faq_create_view, name='faq_create'),
    path('faqs/<int:pk>/edit/', views.faq_edit_view, name='faq_edit'),
    path('faqs/<int:pk>/delete/', views.faq_delete_view, name='faq_delete'),

    # 7. Navigation
    path('navigation/', views.navigation_list_view, name='navigation_list'),
    path('navigation/add/', views.navigation_create_view, name='navigation_create'),
    path('navigation/<int:pk>/edit/', views.navigation_edit_view, name='navigation_edit'),
    path('navigation/<int:pk>/delete/', views.navigation_delete_view, name='navigation_delete'),

    # 8. Contact Settings, Social Links & Messages
    path('contact-settings/', views.contact_settings_view, name='contact_settings'),
    path('social-links/', views.social_links_view, name='social_links'),
    path('social-links/custom/add/', views.custom_social_create_view, name='custom_social_create'),
    path('social-links/custom/<int:pk>/edit/', views.custom_social_edit_view, name='custom_social_edit'),
    path('social-links/custom/<int:pk>/delete/', views.custom_social_delete_view, name='custom_social_delete'),
    path('messages/', views.messages_list_view, name='messages_list'),
    path('messages/<int:pk>/toggle-read/', views.message_toggle_read_view, name='message_toggle_read'),
    path('messages/<int:pk>/delete/', views.message_delete_view, name='message_delete'),

    # 9. SEO
    path('seo/', views.seo_settings_view, name='seo_settings'),

    # 10. System Settings
    path('system-settings/', views.system_settings_view, name='system_settings'),

    # 11. Maintenance Mode
    path('maintenance/', views.maintenance_mode_view, name='maintenance_mode'),

    # 12. Audit Log (Super Admin)
    path('audit/', views.audit_log_view, name='audit_log'),
    path('audit/delete/', views.audit_log_delete_view, name='audit_log_delete'),
    path('audit/<int:pk>/delete/', views.audit_log_delete_single_view, name='audit_log_delete_single'),

    # 13. Sensitive Credentials Status
    path('credentials/', views.credentials_view, name='credentials'),

    # 14. User Accounts (Super Admin)
    path('users/', views.users_list_view, name='users_list'),
    path('users/add/', views.user_create_view, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit_view, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete_view, name='user_delete'),

    # 15. Pending Registrations & Approvals (Super Admin)
    path('registrations/', views.registrations_list_view, name='registrations_list'),
    path('registrations/<int:pk>/approve/', views.registration_approve_view, name='registration_approve'),
    path('registrations/<int:pk>/reject/', views.registration_reject_view, name='registration_reject'),
    path('registrations/bulk-approve/', views.registration_bulk_approve_view, name='registration_bulk_approve'),

    # 16. Student Enrollment Approvals & Student Profiles (Super Admin & Admin)
    path('students/', views.students_list_view, name='students_list'),
    path('students/<int:pk>/', views.student_detail_view, name='student_detail'),
    path('enrollments/', views.enrollments_approval_list_view, name='enrollments_list'),
    path('enrollments/add/', views.enrollment_create_view, name='enrollment_create'),
    path('enrollments/create/', views.enrollment_create_view, name='enrollment_create_alt'),
    path('enrollments/<int:pk>/approve/', views.enrollment_approve_view, name='enrollment_approve'),
    path('enrollments/<int:pk>/reject/', views.enrollment_reject_view, name='enrollment_reject'),

    # 17. Lesson Verification & Schedule (Super Admin & Admin)
    path('lessons/', views.lessons_list_view, name='lessons_list'),
    path('lessons/<int:pk>/verify/', views.lesson_verify_view, name='lesson_verify'),
    path('lessons/<int:pk>/reject/', views.lesson_reject_view, name='lesson_reject'),
    path('lessons/bulk-verify/', views.lesson_bulk_verify_view, name='lesson_bulk_verify'),

    # 18. Email Configuration & Compose (Super Admin Exclusive)
    path('email-settings/', views.email_settings_view, name='email_settings'),
    path('email-compose/', views.email_compose_view, name='email_compose'),
]
