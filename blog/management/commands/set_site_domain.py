"""Point the django.contrib.sites record at the public domain.

Activation and password-reset emails build their links from it. The domain is
the first entry of ALLOWED_HOSTS.
"""
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Set the Site domain to the first ALLOWED_HOSTS entry."

    def handle(self, *args, **options):
        hosts = [h for h in settings.ALLOWED_HOSTS if h not in ("*", "localhost", "127.0.0.1")]
        if not hosts:
            self.stdout.write("No public host in ALLOWED_HOSTS; Site left unchanged.")
            return
        Site.objects.update_or_create(
            id=settings.SITE_ID, defaults={"domain": hosts[0], "name": "Advanced Blog System"}
        )
        self.stdout.write(f"Site domain set to {hosts[0]}")
