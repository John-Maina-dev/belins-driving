from django.views.generic import ListView, DetailView
from .models import Course

class CourseListView(ListView):
    model = Course
    template_name = 'website/courses.html'
    context_object_name = 'courses'

    def get_queryset(self):
        return Course.objects.filter(is_active=True).order_by('order', 'name')

class CourseDetailView(DetailView):
    model = Course
    template_name = 'website/course_detail.html'
    context_object_name = 'course'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Course.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_courses'] = Course.objects.filter(
            is_active=True
        ).exclude(id=self.object.id).order_by('order')[:3]
        return context
