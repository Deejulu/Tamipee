import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Seed default active SecurityQuestion rows for account recovery.'

    def handle(self, *args, **options):
        from accounts.models import SecurityQuestion

        # Keep questions easy to remember and non-sensitive.
        # These are used for account recovery / security question selection.
        questions = [
            'What was the name of your first school?',
            'What is the name of your favorite teacher?',
            'What is the city where you were born?',
            'What is the name of your favorite book?',
            'What is the name of your favorite movie?',
            'What is the name of the street you grew up on?',
            'What is the name of your first pet?',
            'What is the name of your best friend from childhood?',
            'What is the name of the town where you grew up?',
            'What is the name of your favorite hobby?',
        ]


        created = 0
        for q in questions:
            obj, is_created = SecurityQuestion.objects.get_or_create(
                question_text=q,
                defaults={
                    'is_active': True,
                    'order': questions.index(q),
                },
            )
            if is_created:
                created += 1
            else:
                # Ensure active if it exists
                if not obj.is_active:
                    obj.is_active = True
                    obj.save(update_fields=['is_active'])

        self.stdout.write(self.style.SUCCESS(
            f'Security questions seeded. Created {created} (existing were reused).'
        ))

