from django.core.management.base import BaseCommand

from apps.users.bootstrap_dev_users import DEV_USERS, ensure_dev_users


class Command(BaseCommand):
    help = "Temporary: ensure local demo users exist (DEBUG only)."

    def handle(self, *args: object, **options: object) -> None:
        created = ensure_dev_users()
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created: {', '.join(created)}. Password: Devpass123!"
                )
            )
        else:
            self.stdout.write("No new users created (already exist, or seeding disabled).")
            self.stdout.write(
                "Demo accounts: "
                + ", ".join(u["username"] for u in DEV_USERS)
                + " / Devpass123!"
            )
