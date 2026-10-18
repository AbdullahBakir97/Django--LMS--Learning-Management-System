from io import BytesIO

from celery import shared_task
from django.core.files.base import ContentFile


@shared_task
def render_certificate_pdf(certificate_id: int) -> None:
    """A one-page certificate. reportlab is pure Python, so no system libraries are needed."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas

    from .models import Certificate

    certificate = Certificate.objects.select_related(
        "enrollment__student", "enrollment__course__instructor"
    ).get(pk=certificate_id)
    enrollment = certificate.enrollment
    student = enrollment.student
    name = f"{student.first_name} {student.last_name}".strip() or student.username
    instructor = enrollment.course.instructor
    instructor_name = instructor.get_full_name() or instructor.username

    buffer = BytesIO()
    page = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    page.setFont("Helvetica", 14)
    page.drawCentredString(width / 2, height - 120, "CERTIFICATE OF COMPLETION")
    page.setFont("Helvetica-Bold", 30)
    page.drawCentredString(width / 2, height / 2 + 40, name)
    page.setFont("Helvetica", 16)
    page.drawCentredString(width / 2, height / 2, "has completed")
    page.setFont("Helvetica-Bold", 20)
    page.drawCentredString(width / 2, height / 2 - 40, enrollment.course.title)
    page.setFont("Helvetica", 11)
    page.drawCentredString(
        width / 2,
        110,
        f"Instructor: {instructor_name}",
    )
    page.drawCentredString(width / 2, 90, f"Completed {enrollment.completed_at:%d %B %Y}")
    page.drawCentredString(width / 2, 60, f"Verification code {certificate.code}")
    page.showPage()
    page.save()

    certificate.pdf.save(f"{certificate.code}.pdf", ContentFile(buffer.getvalue()), save=True)
