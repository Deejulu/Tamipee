"""
Update security questions with stronger, harder-to-guess options.
Run with: python manage.py shell < update_security_questions.py
"""

from accounts.models import SecurityQuestion

# Better security questions (harder to guess from social media)
IMPROVED_QUESTIONS = [
    # Personal but not easily findable
    "What was the name of the street you lived on in third grade?",
    "What was your childhood phone number (last 4 digits)?",
    "What was the name of your first employer?",
    "What is the middle name of your oldest sibling?",
    "What was the name of your first school teacher?",
    
    # Memorable but obscure
    "What was the make and model of your first vehicle?",
    "What was the name of your childhood best friend's pet?",
    "What was your favorite subject in high school?",
    "What was the name of the city where your parents met?",
    "What was your favorite childhood toy or game?",
    
    # Unique to user
    "What was the title of your favorite childhood book?",
    "What was the first concert or live event you attended?",
    "What was your dream job as a child?",
    "What was the name of your first farm animal (if applicable)?",
    "What is the name of a place you visited that made you feel peaceful?",
    
    # Harder to find online
    "What was the first dish you learned to cook?",
    "What was the nickname of your grandfather or grandmother?",
    "What was the name of the hospital where you were born?",
    "What was your favorite childhood hiding spot?",
    "What was the first film you saw in a cinema?",
]

# Deactivate old weak questions
print("Deactivating old questions...")
SecurityQuestion.objects.all().update(is_active=False)

# Add new improved questions
print("Adding improved security questions...")
for i, question_text in enumerate(IMPROVED_QUESTIONS, 1):
    obj, created = SecurityQuestion.objects.update_or_create(
        question_text=question_text,
        defaults={'is_active': True, 'order': i}
    )
    if created:
        print(f"  ✓ Created: {question_text}")
    else:
        print(f"  ↻ Updated: {question_text}")

print(f"\n✅ Total active questions: {SecurityQuestion.objects.filter(is_active=True).count()}")
print("⚠️  Note: Existing users keep their old questions. Only new registrations use these.")
