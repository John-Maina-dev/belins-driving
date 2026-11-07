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

    # 3. Homepage Content & Slider
    path('homepage/', views.homepage_content_view, name='homepage_content'),
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

    # 6. Instructors, Gallery, Testimonials, FAQs
    path('instructors/', views.instructors_list_view, name='instructors_list'),
    path('instructors/add/', views.instructor_create_view, name='instructor_create'),
    path('instructors/<int:pk>/edit/', views.instructor_edit_view, name='instructor_edit'),
    path('instructors/<int:pk>/delete/', views.instructor_delete_view, name='instructor_delete'),

    path('gallery/', views.gallery_list_view, name='gallery_list'),
    path('gallery/add/', views.gallery_create_view, name='gallery_create'),
    path('gallery/<int:pk>/edit/', views.gallery_edit_view, name='gallery_edit'),
    path('gallery/<int:pk>/delete/', views.gallery_delete_view, name='gallery_delete'),

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

    # 8. Contact Settings & Messages
    path('contact-settings/', views.contact_settings_view, name='contact_settings'),
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

    # 13. Sensitive Credentials Status
    path('credentials/', views.credentials_view, name='credentials'),

    # 14. User Accounts (Super Admin)
    path('users/', views.users_list_view, name='users_list'),
    path('users/add/', views.user_create_view, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit_view, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete_view, name='user_delete'),
]

