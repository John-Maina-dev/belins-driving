from django.urls import path
from . import views

app_name = 'website'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('courses/', views.courses_view, name='courses'),
    path('courses/<slug:slug>/', views.course_detail_view, name='course_detail'),
    path('fees/', views.fees_view, name='fees'),
    path('instructors/', views.instructors_view, name='instructors'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('faq/', views.faq_view, name='faq'),
    path('contact/', views.contact_view, name='contact'),
    path('enroll/', views.enroll_view, name='enroll'),
    path('enroll/success/', views.enroll_success_view, name='enroll_success'),
    path('api/branch-courses/', views.branch_courses_api_view, name='branch_courses_api'),
    path('robots.txt', views.robots_txt_view, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml_view, name='sitemap_xml'),
]
