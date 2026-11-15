from datetime import datetime, date, time, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, Http404
from django.utils import timezone

from .models import Student, LessonBooking
from .validators import calculate_age
from courses.models import Branch, Vehicle
from instructors.models import Instructor
from website.models import SiteSettings


STANDARD_SLOTS = [
    (time(8, 0), time(9, 0), "08:00-09:00", "8:00 AM - 9:00 AM"),
    (time(9, 0), time(10, 0), "09:00-10:00", "9:00 AM - 10:00 AM"),
    (time(10, 0), time(11, 0), "10:00-11:00", "10:00 AM - 11:00 AM"),
    (time(11, 0), time(12, 0), "11:00-12:00", "11:00 AM - 12:00 PM"),
    (time(13, 0), time(14, 0), "13:00-14:00", "1:00 PM - 2:00 PM"),
    (time(14, 0), time(15, 0), "14:00-15:00", "2:00 PM - 3:00 PM"),
    (time(15, 0), time(16, 0), "15:00-16:00", "3:00 PM - 4:00 PM"),
    (time(16, 0), time(17, 0), "16:00-17:00", "4:00 PM - 5:00 PM"),
    (time(17, 0), time(18, 0), "17:00-18:00", "5:00 PM - 6:00 PM"),
]


def _overlaps(start1, end1, start2, end2):
    return start1 < end2 and end1 > start2


def get_available_slots(target_date, branch=None, lesson_type='PRACTICAL', instructor=None, vehicle=None, student=None):
    """
    Compute genuinely free time slots on target_date considering student,
    instructor, and vehicle availability.
    """
    active_bookings = list(
        LessonBooking.objects.filter(
            date=target_date,
            status__in=['SCHEDULED', 'COMPLETED', 'VERIFIED']
        )
    )

    branch_instructors = list(Instructor.objects.filter(is_active=True, branch=branch)) if branch else []
    if not branch_instructors:
        branch_instructors = list(Instructor.objects.filter(is_active=True))

    branch_vehicles = list(Vehicle.objects.filter(is_active=True, branch=branch)) if branch else []
    if not branch_vehicles:
        branch_vehicles = list(Vehicle.objects.filter(is_active=True))

    free_slots = []
    for s_time, e_time, code, label in STANDARD_SLOTS:
        # 1. Student conflict check
        if student:
            if any(b.student_id == student.id and _overlaps(s_time, e_time, b.start_time, b.end_time) for b in active_bookings):
                continue

        # 2. Instructor conflict check
        if instructor:
            if any(b.instructor_id == instructor.id and _overlaps(s_time, e_time, b.start_time, b.end_time) for b in active_bookings):
                continue
        elif branch_instructors:
            busy_inst_ids = {
                b.instructor_id for b in active_bookings
                if b.instructor_id and _overlaps(s_time, e_time, b.start_time, b.end_time)
            }
            if all(inst.id in busy_inst_ids for inst in branch_instructors):
                continue

        # 3. Vehicle conflict check (for practical lessons)
        if lesson_type == 'PRACTICAL':
            if vehicle:
                if any(b.vehicle_id == vehicle.id and _overlaps(s_time, e_time, b.start_time, b.end_time) for b in active_bookings):
                    continue
            elif branch_vehicles:
                busy_veh_ids = {
                    b.vehicle_id for b in active_bookings
                    if b.vehicle_id and _overlaps(s_time, e_time, b.start_time, b.end_time)
                }
                if all(v.id in busy_veh_ids for v in branch_vehicles):
                    continue

        free_slots.append({'code': code, 'label': label, 'start': s_time.strftime('%H:%M'), 'end': e_time.strftime('%H:%M')})

    return free_slots


def _get_student_for_user(user):
    enrollment = Student.objects.filter(user=user).select_related('course', 'branch').order_by('-created_at').first()
    if not enrollment and user.email:
        enrollment = Student.objects.filter(email__iexact=user.email).select_related('course', 'branch').order_by('-created_at').first()
    return enrollment


@login_required(login_url='accounts:login')
def dashboard_view(request):
    """
    Student learning dashboard displaying upcoming bookings, past lessons with
    verification status, verified vs reserved hours, and quick actions.
    """
    enrollment = _get_student_for_user(request.user)
    is_approved = bool(
        enrollment
        and enrollment.is_approved
        and hasattr(request.user, 'profile')
        and request.user.profile.approval_status == 'APPROVED'
    )
    is_pending = bool(enrollment and enrollment.is_pending)

    upcoming_bookings = []
    past_bookings = []
    if enrollment:
        today = timezone.localdate()
        all_bookings = enrollment.bookings.select_related('branch', 'instructor', 'vehicle', 'verified_by').order_by('date', 'start_time')
        for b in all_bookings:
            if b.status == 'SCHEDULED' and b.date >= today:
                upcoming_bookings.append(b)
            else:
                past_bookings.append(b)

    context = {
        'enrollment': enrollment,
        'is_approved': is_approved,
        'is_pending': is_pending,
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
    }
    return render(request, 'students/dashboard.html', context)


@login_required(login_url='accounts:login')
def book_lesson_view(request):
    """
    Full lesson booking schedule view for approved 18+ students.
    Enforces account approval, enrollment approval, 18+ age, package limits,
    max lessons per day, and atomic double-booking prevention.
    """
    enrollment = _get_student_for_user(request.user)
    user_approved = hasattr(request.user, 'profile') and request.user.profile.approval_status == 'APPROVED'
    if not enrollment or not enrollment.is_approved or not user_approved:
        messages.error(request, "Awaiting approval: You cannot book driving lessons until your account and enrollment are approved.")
        return redirect('students:dashboard')

    today = timezone.localdate()
    if not enrollment.date_of_birth or calculate_age(enrollment.date_of_birth, today) < 18:
        messages.error(request, "You must be 18 years or older to book driving lessons.")
        return redirect('students:dashboard')

    branches = Branch.objects.filter(is_active=True).order_by('order', 'name')
    selected_branch = enrollment.branch or branches.first()
    branch_id_param = request.GET.get('branch') or request.POST.get('branch')
    if branch_id_param and str(branch_id_param).isdigit():
        b_obj = branches.filter(pk=int(branch_id_param)).first()
        if b_obj:
            selected_branch = b_obj

    date_param = request.GET.get('date') or request.POST.get('date')
    target_date = today + timedelta(days=1)
    if date_param:
        try:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            pass

    instructors = Instructor.objects.filter(is_active=True).order_by('order', 'full_name')
    if selected_branch and instructors.filter(branch=selected_branch).exists():
        instructors = instructors.filter(branch=selected_branch)

    vehicles = Vehicle.objects.filter(is_active=True)
    if selected_branch and vehicles.filter(branch=selected_branch).exists():
        vehicles = vehicles.filter(branch=selected_branch)

    if request.method == 'POST':
        lesson_type = request.POST.get('lesson_type', 'PRACTICAL')
        if lesson_type not in ('PRACTICAL', 'THEORY'):
            lesson_type = 'PRACTICAL'

        slot_code = request.POST.get('time_slot', '').strip()
        start_str = request.POST.get('start_time', '').strip()
        end_str = request.POST.get('end_time', '').strip()

        start_t = None
        end_t = None
        if slot_code and '-' in slot_code:
            parts = slot_code.split('-', 1)
            try:
                start_t = datetime.strptime(parts[0].strip(), '%H:%M').time()
                end_t = datetime.strptime(parts[1].strip(), '%H:%M').time()
            except ValueError:
                pass
        elif start_str and end_str:
            try:
                start_t = datetime.strptime(start_str, '%H:%M').time()
                end_t = datetime.strptime(end_str, '%H:%M').time()
            except ValueError:
                pass

        if not start_t or not end_t or start_t >= end_t:
            messages.error(request, "Please select a valid lesson time slot.")
        elif target_date < today:
            messages.error(request, "Lesson date cannot be in the past.")
        elif not selected_branch:
            messages.error(request, "Please select a training branch.")
        else:
            instructor_id = request.POST.get('instructor')
            vehicle_id = request.POST.get('vehicle')
            student_notes = request.POST.get('student_notes', '').strip()

            chosen_instructor = Instructor.objects.filter(pk=instructor_id, is_active=True).first() if (instructor_id and str(instructor_id).isdigit()) else None
            chosen_vehicle = Vehicle.objects.filter(pk=vehicle_id, is_active=True).first() if (vehicle_id and str(vehicle_id).isdigit()) else None

            site_cfg = SiteSettings.load()
            max_per_day = max(1, int(getattr(site_cfg, 'max_lessons_per_day', 2) or 2))

            dummy_d = datetime(2000, 1, 1)
            slot_hours = max(1.0, (datetime.combine(dummy_d, end_t) - datetime.combine(dummy_d, start_t)).total_seconds() / 3600.0)

            try:
                with transaction.atomic():
                    locked_student = Student.objects.select_for_update().get(pk=enrollment.pk)
                    day_bookings = list(
                        LessonBooking.objects.select_for_update().filter(
                            date=target_date,
                            status__in=['SCHEDULED', 'COMPLETED', 'VERIFIED']
                        )
                    )

                    # 1. Check max lessons per day for student
                    student_day_bookings = [b for b in day_bookings if b.student_id == locked_student.id]
                    if len(student_day_bookings) >= max_per_day:
                        raise ValueError(f"You can book at most {max_per_day} lessons per day.")

                    # 2. Check package hours limit
                    if lesson_type == 'PRACTICAL':
                        if locked_student.reserved_practical_hours + slot_hours > float(locked_student.course.practical_hours):
                            raise ValueError("Booking exceeds your course package practical hours limit.")
                    else:
                        if locked_student.reserved_theory_hours + slot_hours > float(locked_student.course.theory_hours):
                            raise ValueError("Booking exceeds your course package theory hours limit.")

                    # 3. Check student overlap
                    for b in student_day_bookings:
                        if _overlaps(start_t, end_t, b.start_time, b.end_time):
                            raise ValueError("You already have a lesson booked during this time slot.")

                    # 4. Instructor conflict / auto-assign
                    if chosen_instructor:
                        for b in day_bookings:
                            if b.instructor_id == chosen_instructor.id and _overlaps(start_t, end_t, b.start_time, b.end_time):
                                raise ValueError("Selected instructor is already booked for this time slot.")
                    else:
                        busy_inst_ids = {
                            b.instructor_id for b in day_bookings
                            if b.instructor_id and _overlaps(start_t, end_t, b.start_time, b.end_time)
                        }
                        candidate_instructors = list(instructors)
                        free_instructors = [i for i in candidate_instructors if i.id not in busy_inst_ids]
                        if candidate_instructors and not free_instructors:
                            raise ValueError("No instructors are available for this time slot.")
                        chosen_instructor = free_instructors[0] if free_instructors else None

                    # 5. Vehicle conflict / auto-assign (for practical lessons)
                    if lesson_type == 'PRACTICAL':
                        if chosen_vehicle:
                            for b in day_bookings:
                                if b.vehicle_id == chosen_vehicle.id and _overlaps(start_t, end_t, b.start_time, b.end_time):
                                    raise ValueError("Selected training vehicle is already booked for this time slot.")
                        else:
                            busy_veh_ids = {
                                b.vehicle_id for b in day_bookings
                                if b.vehicle_id and _overlaps(start_t, end_t, b.start_time, b.end_time)
                            }
                            candidate_vehicles = list(vehicles)
                            free_vehicles = [v for v in candidate_vehicles if v.id not in busy_veh_ids]
                            if candidate_vehicles and not free_vehicles:
                                raise ValueError("No training vehicles are available for this time slot.")
                            chosen_vehicle = free_vehicles[0] if free_vehicles else None
                    else:
                        chosen_vehicle = None

                    booking = LessonBooking.objects.create(
                        student=locked_student,
                        course=locked_student.course,
                        branch=selected_branch,
                        instructor=chosen_instructor,
                        vehicle=chosen_vehicle,
                        lesson_type=lesson_type,
                        date=target_date,
                        start_time=start_t,
                        end_time=end_t,
                        status='SCHEDULED',
                        student_notes=student_notes,
                    )
                messages.success(
                    request,
                    f"Lesson booked for {booking.date} ({booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')})."
                )
                return redirect('students:dashboard')
            except ValueError as err:
                messages.error(request, str(err))

    available_slots = get_available_slots(
        target_date=target_date,
        branch=selected_branch,
        lesson_type='PRACTICAL',
        student=enrollment,
    )

    context = {
        'enrollment': enrollment,
        'branches': branches,
        'selected_branch': selected_branch,
        'target_date': target_date,
        'min_date': today,
        'instructors': instructors,
        'vehicles': vehicles,
        'available_slots': available_slots,
    }
    return render(request, 'students/book_lesson.html', context)


@login_required(login_url='accounts:login')
def available_slots_api_view(request):
    """JSON endpoint returning genuinely free time slots for the given filters."""
    enrollment = _get_student_for_user(request.user)
    date_str = request.GET.get('date')
    branch_id = request.GET.get('branch')
    lesson_type = request.GET.get('lesson_type', 'PRACTICAL')
    instructor_id = request.GET.get('instructor')
    vehicle_id = request.GET.get('vehicle')

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.localdate() + timedelta(days=1)
    except ValueError:
        target_date = timezone.localdate() + timedelta(days=1)

    branch = Branch.objects.filter(pk=branch_id).first() if (branch_id and str(branch_id).isdigit()) else (enrollment.branch if enrollment else None)
    instructor = Instructor.objects.filter(pk=instructor_id).first() if (instructor_id and str(instructor_id).isdigit()) else None
    vehicle = Vehicle.objects.filter(pk=vehicle_id).first() if (vehicle_id and str(vehicle_id).isdigit()) else None

    slots = get_available_slots(
        target_date=target_date,
        branch=branch,
        lesson_type=lesson_type,
        instructor=instructor,
        vehicle=vehicle,
        student=enrollment,
    )
    return JsonResponse({'slots': slots})


@login_required(login_url='accounts:login')
@require_POST
def cancel_lesson_view(request, pk):
    """Cancel a SCHEDULED lesson if within the allowed cancellation window."""
    booking = get_object_or_404(LessonBooking, pk=pk)
    enrollment = _get_student_for_user(request.user)
    is_admin = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_management_authorized)

    if not is_admin and (not enrollment or booking.student_id != enrollment.id):
        raise PermissionDenied("You cannot cancel another student's lesson.")

    if booking.status != 'SCHEDULED':
        messages.error(request, "Only scheduled lessons can be cancelled.")
        return redirect('students:dashboard')

    if not is_admin:
        site_cfg = SiteSettings.load()
        window_hours = int(getattr(site_cfg, 'cancellation_window_hours', 24) or 24)
        lesson_dt = timezone.make_aware(datetime.combine(booking.date, booking.start_time))
        if lesson_dt - timezone.now() < timedelta(hours=window_hours):
            messages.error(request, f"Lessons must be cancelled at least {window_hours} hours in advance.")
            return redirect('students:dashboard')

    booking.status = 'CANCELLED'
    booking.save()
    messages.success(request, "Your lesson booking has been cancelled.")
    return redirect('students:dashboard')


@login_required(login_url='accounts:login')
@require_POST
def complete_lesson_view(request, pk):
    """
    Instructor (or Admin/Super Admin) marks a SCHEDULED lesson as COMPLETED or NO_SHOW
    with feedback notes. Students are strictly forbidden from calling this endpoint.
    """
    is_instructor = hasattr(request.user, 'profile') and request.user.profile.role == 'INSTRUCTOR'
    is_admin = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_management_authorized)

    if not (is_instructor or is_admin):
        raise PermissionDenied("Students are not permitted to mark lessons completed.")

    booking = get_object_or_404(LessonBooking, pk=pk)
    action = request.POST.get('action', 'complete')
    notes = request.POST.get('instructor_notes', '').strip()

    if booking.status not in ('SCHEDULED', 'COMPLETED'):
        messages.error(request, f"Cannot mark a {booking.get_status_display()} lesson as completed.")
    else:
        if action == 'no_show':
            booking.status = 'NO_SHOW'
            booking.instructor_notes = notes or "Student did not attend."
            booking.save()
            messages.warning(request, f"Lesson for {booking.student.full_name} marked as No-Show.")
        else:
            booking.status = 'COMPLETED'
            booking.instructor_notes = notes
            booking.save()
            messages.success(request, f"Lesson for {booking.student.full_name} marked as Completed (awaiting admin verification).")

    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    if is_admin:
        return redirect('manage:lessons_list')
    return redirect('students:instructor_schedule')


@login_required(login_url='accounts:login')
def instructor_schedule_view(request):
    """Instructor dashboard to view assigned lessons and mark them COMPLETED or NO_SHOW."""
    is_instructor = hasattr(request.user, 'profile') and request.user.profile.role == 'INSTRUCTOR'
    is_admin = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_management_authorized)
    if not (is_instructor or is_admin):
        raise PermissionDenied("Only instructors and administrators can view the instructor schedule.")

    bookings = LessonBooking.objects.select_related('student', 'course', 'branch', 'instructor', 'vehicle').order_by('-date', 'start_time')
    return render(request, 'students/instructor_schedule.html', {'bookings': bookings})


@login_required(login_url='accounts:login')
def payment_view(request):
    """Attempting to pay fees before approval is blocked."""
    enrollment = _get_student_for_user(request.user)
    if not enrollment or not enrollment.is_approved:
        messages.error(request, "Awaiting approval: Fee payments are locked until your enrollment is officially approved.")
        return redirect('students:dashboard')
    messages.info(request, "M-Pesa payment gateway will open shortly.")
    return redirect('students:dashboard')


@login_required(login_url='accounts:login')
def course_content_view(request):
    """Attempting to view learning materials before approval is blocked."""
    enrollment = _get_student_for_user(request.user)
    if not enrollment or not enrollment.is_approved:
        messages.error(request, "Awaiting approval: Course materials and syllabus are locked until your enrollment is approved.")
        return redirect('students:dashboard')
    return render(request, 'students/course_content.html', {'enrollment': enrollment})
