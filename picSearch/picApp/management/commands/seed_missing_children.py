import os
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from picApp.models import MissingChild

class Command(BaseCommand):
    help = 'Seed the database with 10 sample MissingChild entries using existing images in media/missing_children'

    def handle(self, *args, **options):
        media_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../media/missing_children'))
        if not os.path.isdir(media_dir):
            self.stdout.write(self.style.ERROR(f"Media directory not found: {media_dir}"))
            return
        # Get first 10 image files
        image_files = [f for f in os.listdir(media_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))][:10]
        if not image_files:
            self.stdout.write(self.style.ERROR('No image files found to seed.'))
            return
        genders = ['M', 'F']
        for idx, img_name in enumerate(image_files, start=1):
            name = f"Sample Child {idx}"
            age = random.randint(1, 15)
            gender = random.choice(genders)
            # Random date_missing within last 5 years
            date_missing = date.today() - timedelta(days=random.randint(30, 5 * 365))
            # Simple placeholder data
            place_of_birth = 'Cityville'
            last_seen = (date_missing + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
            guardian_name = f"Guardian {idx}"
            guardian_contact = f"+12345678{idx:02d}"
            # Create MissingChild instance
            child = MissingChild(
                name=name,
                age=age,
                gender=gender,
                image=os.path.join('missing_children', img_name),  # stored relative to MEDIA_ROOT
                date_missing=date_missing,
                place_of_birth=place_of_birth,
                last_seen=last_seen,
                guardian_name=guardian_name,
                guardian_contact=guardian_contact,
            )
            child.save()
            self.stdout.write(self.style.SUCCESS(f"Created {name} with image {img_name}"))
        self.stdout.write(self.style.SUCCESS('Seeding complete.'))
