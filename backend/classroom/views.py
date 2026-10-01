from django.core.cache import cache
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsVerified

from .models import CODE_LENGTH, Group, Membership, new_code
from .stats import common_mistakes, student_row

JOIN_FAILURES_PER_HOUR = 10


class IsTeacher(BasePermission):
    message = "Бұл бөлім мұғалімдерге арналған."

    def has_permission(self, request, view):
        return IsVerified().has_permission(request, view) and request.user.is_teacher


class GroupSerializer(serializers.ModelSerializer):
    students = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ["id", "name", "code", "created_at", "students"]
        read_only_fields = ["code", "created_at"]

    def get_students(self, group):
        return group.memberships.count()


def _teacher_group(request, pk) -> Group:
    return get_object_or_404(Group, pk=pk, teacher=request.user)


class TeacherGroupsView(APIView):
    """GET /api/teacher/groups/ — the teacher's groups; POST {name} — a new group with a join code."""

    permission_classes = [IsTeacher]

    def get(self, request):
        return Response(GroupSerializer(Group.objects.filter(teacher=request.user), many=True).data)

    def post(self, request):
        serializer = GroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save(teacher=request.user)
        return Response(GroupSerializer(group).data, status=status.HTTP_201_CREATED)


class TeacherGroupView(APIView):
    """GET — the group with every learner's progress and the group's common mistakes; PATCH {name}; DELETE."""

    permission_classes = [IsTeacher]

    def get(self, request, pk):
        group = _teacher_group(request, pk)
        students = [m.student for m in group.memberships.select_related("student")]
        return Response(
            {
                **GroupSerializer(group).data,
                "rows": sorted(
                    (student_row(s) for s in students), key=lambda r: str(r["last_active"] or ""), reverse=True
                ),
                "mistakes": common_mistakes(students),
            }
        )

    def patch(self, request, pk):
        serializer = GroupSerializer(_teacher_group(request, pk), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(GroupSerializer(serializer.save()).data)

    def delete(self, request, pk):
        _teacher_group(request, pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeacherGroupCodeView(APIView):
    """POST — a new join code (the old one stops working, e.g. after it leaked outside the class)."""

    permission_classes = [IsTeacher]

    def post(self, request, pk):
        group = _teacher_group(request, pk)
        group.code = new_code()
        group.save(update_fields=["code"])
        return Response(GroupSerializer(group).data)


class TeacherStudentView(APIView):
    """DELETE — removes a learner from the group (their own progress is untouched)."""

    permission_classes = [IsTeacher]

    def delete(self, request, pk, student_id):
        Membership.objects.filter(group=_teacher_group(request, pk), student_id=student_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyGroupSerializer(serializers.ModelSerializer):
    teacher = serializers.CharField(source="teacher.name")

    class Meta:
        model = Group
        fields = ["id", "name", "teacher"]


class MyGroupsView(APIView):
    """GET /api/groups/ — the groups the learner is in."""

    def get(self, request):
        groups = Group.objects.filter(memberships__student=request.user).select_related("teacher")
        return Response(MyGroupSerializer(groups, many=True).data)


class JoinSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=20)


class JoinGroupView(APIView):
    """POST /api/groups/join/ {code} — joins a teacher's group."""

    def post(self, request):
        serializer = JoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"].strip().upper().replace(" ", "")
        key = f"group-join-fail:{request.user.pk}"
        if (cache.get(key) or 0) >= JOIN_FAILURES_PER_HOUR:
            return Response(
                {"detail": "Тым көп қате код. Бір сағаттан кейін қайталаңыз.", "code": "locked"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        group = Group.objects.filter(code=code).select_related("teacher").first() if len(code) == CODE_LENGTH else None
        if group is None:
            if not cache.add(key, 1, 3600):
                try:
                    cache.incr(key)
                except ValueError:  # expired between add and incr
                    cache.set(key, 1, 3600)
            return Response(
                {"detail": "Мұндай код жоқ. Мұғалімнен қайта сұраңыз.", "code": "invalid_code"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if group.teacher_id == request.user.id:
            return Response({"detail": "Бұл — өз тобыңыз.", "code": "invalid_code"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            Membership.objects.get_or_create(group=group, student=request.user)
        except IntegrityError:
            pass
        return Response(MyGroupSerializer(group).data, status=status.HTTP_201_CREATED)


class LeaveGroupView(APIView):
    """DELETE /api/groups/{id}/ — leaves the group; the teacher no longer sees this learner."""

    def delete(self, request, pk):
        Membership.objects.filter(group_id=pk, student=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
