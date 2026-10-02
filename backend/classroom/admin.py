from django.contrib import admin

from .models import Group, Membership


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    raw_id_fields = ["student"]


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ["name", "teacher", "code", "created_at"]
    search_fields = ["name", "teacher__email", "code"]
    inlines = [MembershipInline]
