from django.shortcuts import render
import json

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Student


def serialize_student(student):
    return {
        "id": str(student.pk),
        "name": student.name,
        "email": student.email,
        "course": student.course,
        "age": student.age,
        "created_at": student.created_at.isoformat() if student.created_at else None,
    }


@csrf_exempt
def student_list_create(request):
    if request.method == "GET":
        students = Student.objects.all().order_by("-created_at")
        return JsonResponse([serialize_student(student) for student in students], safe=False)

    if request.method == "POST":
        try:
            data = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        student = Student(
            name=data.get("name", ""),
            email=data.get("email", ""),
            course=data.get("course", ""),
            age=data.get("age"),
        )

        try:
            student.full_clean()
            student.save()
        except (ValidationError, TypeError, ValueError) as exc:
            if isinstance(exc, ValidationError):
                errors = exc.message_dict
            else:
                errors = {"error": str(exc)}
            return JsonResponse({"error": "Invalid student data.", "details": errors}, status=400)

        return JsonResponse(serialize_student(student), status=201)

    return JsonResponse({"error": "Method not allowed."}, status=405)


@csrf_exempt
def student_detail(request, pk):
    try:
        student = Student.objects.get(pk=pk)
    except (Student.DoesNotExist, ValidationError, ValueError):
        return JsonResponse({"error": "Student not found."}, status=404)

    if request.method == "GET":
        return JsonResponse(serialize_student(student))

    if request.method in ("PUT", "PATCH"):
        try:
            data = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        fields = ("name", "email", "course", "age")
        for field in fields:
            if request.method == "PUT" or field in data:
                setattr(student, field, data.get(field, getattr(student, field)))

        try:
            student.full_clean()
            student.save()
        except (ValidationError, TypeError, ValueError) as exc:
            if isinstance(exc, ValidationError):
                errors = exc.message_dict
            else:
                errors = {"error": str(exc)}
            return JsonResponse({"error": "Invalid student data.", "details": errors}, status=400)

        return JsonResponse(serialize_student(student))

    if request.method == "DELETE":
        student.delete()
        return JsonResponse({"deleted": True}, status=200)

    return JsonResponse({"error": "Method not allowed."}, status=405)