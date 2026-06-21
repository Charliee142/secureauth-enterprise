from django.db import migrations

ROLES = ["Guest", "User", "Moderator", "Administrator"]

PERMISSIONS = [
    "view_own_profile",
    "edit_own_profile",
    "change_own_password",
    "view_user_list",
    "flag_user_activity",
    "view_security_dashboard",
    "manage_users",
    "manage_roles",
    "view_audit_logs",
    "export_audit_logs",
    "manage_system_settings",
]

ROLE_PERMISSIONS = {
    "Guest": [],
    "User": ["view_own_profile", "edit_own_profile", "change_own_password"],
    "Moderator": [
        "view_own_profile", "edit_own_profile", "change_own_password",
        "view_user_list", "flag_user_activity",
    ],
    "Administrator": PERMISSIONS,
}


def seed_rbac(apps, schema_editor):
    Role = apps.get_model("rbac", "Role")
    Permission = apps.get_model("rbac", "Permission")
    RolePermission = apps.get_model("rbac", "RolePermission")

    role_objs = {}
    for name in ROLES:
        role_objs[name], _ = Role.objects.get_or_create(name=name)

    perm_objs = {}
    for codename in PERMISSIONS:
        perm_objs[codename], _ = Permission.objects.get_or_create(codename=codename)

    for role_name, codenames in ROLE_PERMISSIONS.items():
        for codename in codenames:
            RolePermission.objects.get_or_create(
                role=role_objs[role_name], permission=perm_objs[codename]
            )


def unseed_rbac(apps, schema_editor):
    Role = apps.get_model("rbac", "Role")
    Permission = apps.get_model("rbac", "Permission")
    Role.objects.filter(name__in=ROLES).delete()
    Permission.objects.filter(codename__in=PERMISSIONS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_rbac, unseed_rbac),
    ]
