import random
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from interface.models import ProgrammingLanguage, ExpertiseLevel, QuizQuestion, TheoryQuestion, MCQQuestion, MyUser
from interface.views import generate_quiz_question as generate_coding_question_api
from interface.views import generate_theory_question
from interface.views import generate_mcq_question
from django.test import RequestFactory
import json


class Command(BaseCommand):
    help = 'Generate new questions for coding, theory, and MCQs using OpenAI API'

    def add_arguments(self, parser):
        parser.add_argument('--coding', type=int, default=0, help='Number of coding questions to generate')
        parser.add_argument('--theory', type=int, default=0, help='Number of theory questions to generate')
        parser.add_argument('--mcq', type=int, default=0, help='Number of MCQ questions to generate')
        parser.add_argument('--all', type=int, help='Generate equal number of all question types')
        parser.add_argument('--language', type=str, help='Specific language ID or "all" for all languages')
        parser.add_argument('--level', type=str, help='Specific level ID or "all" for all levels')
        parser.add_argument('--openai-key', type=str, help='OpenAI API key to use (optional, uses settings.OPENAI_API_KEY if not provided)')

    def handle(self, *args, **options):
        # Process arguments
        coding_count = options['coding']
        theory_count = options['theory']
        mcq_count = options['mcq']
        
        if options['all'] is not None:
            coding_count = theory_count = mcq_count = options['all']
            
        if coding_count == 0 and theory_count == 0 and mcq_count == 0:
            self.stdout.write(self.style.WARNING('No question counts provided. Use --coding, --theory, --mcq, or --all'))
            return
            
        # Process language and level filters
        languages = []
        levels = []
        
        if options['language'] == 'all' or not options['language']:
            languages = list(ProgrammingLanguage.objects.all())
        else:
            try:
                language_id = int(options['language'])
                language = ProgrammingLanguage.objects.get(id=language_id)
                languages = [language]
            except (ValueError, ProgrammingLanguage.DoesNotExist):
                raise CommandError(f"Language with ID {options['language']} does not exist")
                
        if options['level'] == 'all' or not options['level']:
            levels = list(ExpertiseLevel.objects.all())
        else:
            try:
                level_id = int(options['level'])
                level = ExpertiseLevel.objects.get(id=level_id)
                levels = [level]
            except (ValueError, ExpertiseLevel.DoesNotExist):
                raise CommandError(f"Level with ID {options['level']} does not exist")
                
        # Set OpenAI API key
        original_key = os.environ.get('OPENAI_API_KEY')
        if options['openai_key']:
            os.environ['OPENAI_API_KEY'] = options['openai_key']
        elif not settings.OPENAI_API_KEY and not original_key:
            raise CommandError("No OpenAI API key provided and none found in settings")
            
        try:
            # Get admin user for the request (or create one if not exists)
            admin_user, created = MyUser.objects.get_or_create(
                email='admin@example.com',
                defaults={'is_staff': True, 'is_superuser': True}
            )
            
            if created:
                admin_user.set_password('adminpassword')
                admin_user.is_verified = True
                admin_user.save()
            
            # Create request factory for API calls
            factory = RequestFactory()
            
            # Generate questions
            self._generate_questions(coding_count, theory_count, mcq_count, languages, levels, admin_user, factory)
            
        finally:
            # Restore original API key
            if options['openai_key']:
                if original_key:
                    os.environ['OPENAI_API_KEY'] = original_key
                else:
                    del os.environ['OPENAI_API_KEY']
                    
    def _generate_questions(self, coding_count, theory_count, mcq_count, languages, levels, user, factory):
        """Generate the requested number of questions"""
        total_generated = 0
        
        for language in languages:
            for level in levels:
                self.stdout.write(f"Generating questions for {language.name} - {level.level}...")
                
                # Generate coding questions
                for i in range(coding_count):
                    try:
                        with transaction.atomic():
                            self.stdout.write(f"  Generating coding question {i+1}/{coding_count}...")
                            self._generate_coding_question(language.id, level.id, user, factory)
                            total_generated += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error generating coding question: {str(e)}"))
                
                # Generate theory questions
                for i in range(theory_count):
                    try:
                        with transaction.atomic():
                            self.stdout.write(f"  Generating theory question {i+1}/{theory_count}...")
                            self._generate_theory_question(language.id, level.id, user, factory)
                            total_generated += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error generating theory question: {str(e)}"))
                
                # Generate MCQ questions
                for i in range(mcq_count):
                    try:
                        with transaction.atomic():
                            self.stdout.write(f"  Generating MCQ {i+1}/{mcq_count}...")
                            self._generate_mcq_question(language.id, level.id, user, factory)
                            total_generated += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error generating MCQ: {str(e)}"))
                        
        self.stdout.write(self.style.SUCCESS(f"Successfully generated {total_generated} questions"))
        
    def _generate_coding_question(self, language_id, level_id, user, factory):
        """Generate a single coding question using the API endpoint"""
        request = factory.post('/generate-quiz-question/', 
                              data=json.dumps({'language_id': language_id, 'level_id': level_id}),
                              content_type='application/json')
        request.user = user
        
        # Use a function that directly calls the view function (doesn't use DRF)
        response = generate_coding_question_api(request)
        
        # Check if the response was successful
        if response.status_code != 201:
            error_message = response.data.get('error', 'Unknown error') if hasattr(response, 'data') else "Unknown error"
            raise CommandError(f"Failed to generate coding question: {error_message}")
            
        # Return the response data
        self.stdout.write(f"  Successfully generated coding question.")
        return response.data if hasattr(response, 'data') else {}
        
    def _generate_theory_question(self, language_id, level_id, user, factory):
        """Generate a single theory question using the API endpoint"""
        request = factory.post('/generate-theory-question/', 
                              data=json.dumps({'language_id': language_id, 'level_id': level_id}),
                              content_type='application/json')
        request.user = user
        
        # Use a function that directly calls the view function (doesn't use DRF)
        response = generate_theory_question(request)
        
        # Check if the response was successful
        if response.status_code != 201:
            error_message = response.data.get('error', 'Unknown error') if hasattr(response, 'data') else "Unknown error"
            raise CommandError(f"Failed to generate theory question: {error_message}")
            
        # Return the response data
        self.stdout.write(f"  Successfully generated theory question.")
        return response.data if hasattr(response, 'data') else {}
        
    def _generate_mcq_question(self, language_id, level_id, user, factory):
        """Generate a single MCQ question using the API endpoint"""
        request = factory.post('/generate-mcq-question/', 
                              data=json.dumps({'language_id': language_id, 'level_id': level_id}),
                              content_type='application/json')
        request.user = user
        
        # Use a function that directly calls the view function (doesn't use DRF)
        response = generate_mcq_question(request)
        
        # Check if the response was successful
        if response.status_code != 201:
            error_message = response.data.get('error', 'Unknown error') if hasattr(response, 'data') else "Unknown error"
            raise CommandError(f"Failed to generate MCQ question: {error_message}")
            
        # Return the response data
        self.stdout.write(f"  Successfully generated MCQ question.")
        return response.data if hasattr(response, 'data') else {} 