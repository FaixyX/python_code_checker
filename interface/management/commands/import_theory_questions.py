import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from interface.models import ProgrammingLanguage, ExpertiseLevel, TheoryQuestion
from interface.embeddings import store_question_embedding


class Command(BaseCommand):
    help = 'Import theory questions from a JSON file with support for multiple expertise levels'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to JSON file containing theory questions')
        parser.add_argument('--language', type=str, default='Python', help='Programming language name (default: Python)')
        parser.add_argument('--level', type=str, default=None, help='Default expertise level if not specified in JSON (optional)')
        parser.add_argument('--skip-embeddings', action='store_true', help='Skip generating embeddings for imported questions')

    def handle(self, *args, **options):
        file_path = options['file_path']
        language_name = options['language']
        default_level_name = options['level']
        skip_embeddings = options['skip_embeddings']

        # Get or create language
        try:
            language = ProgrammingLanguage.objects.get(name=language_name)
        except ProgrammingLanguage.DoesNotExist:
            language = ProgrammingLanguage.objects.create(name=language_name)
            self.stdout.write(self.style.SUCCESS(f'Created language: {language_name}'))

        # Read and parse JSON file
        import os
        if not os.path.exists(file_path):
            raise CommandError(f'File not found: {file_path}')
        
        # Try to read the file with different encodings
        file_content = None
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    file_content = f.read()
                    if file_content.strip():
                        break
            except UnicodeDecodeError:
                continue
        
        if not file_content or not file_content.strip():
            raise CommandError(f'File appears to be empty or could not be read: {file_path}')
        
        try:
            questions_data = json.loads(file_content)
        except json.JSONDecodeError as e:
            preview = file_content[:200] if len(file_content) > 200 else file_content
            raise CommandError(f'Invalid JSON file: {e}\nFile preview: {repr(preview)}')

        # Validate format
        if not isinstance(questions_data, list):
            raise CommandError('JSON file must contain an array of questions')

        # Import questions
        imported_by_level = {}
        skipped_count = 0

        with transaction.atomic():
            for idx, question_data in enumerate(questions_data, 1):
                try:
                    # Extract question fields
                    question_text = question_data.get('question') or question_data.get('question_text')
                    
                    # Get level from JSON or use default
                    level_name = question_data.get('level', default_level_name)
                    
                    if not question_text:
                        self.stdout.write(self.style.WARNING(f'Question {idx}: Missing question text, skipping'))
                        skipped_count += 1
                        continue
                    
                    if not level_name:
                        self.stdout.write(self.style.WARNING(f'Question {idx}: No level specified and no default level provided, skipping'))
                        skipped_count += 1
                        continue

                    # Normalize level name (handle case variations)
                    level_name = level_name.strip()
                    # Map common variations
                    level_mapping = {
                        'beginner': 'Easy',
                        'intermediate': 'Medium',
                        'advanced': 'Hard',
                        'easy': 'Easy',
                        'medium': 'Medium',
                        'hard': 'Hard'
                    }
                    level_name = level_mapping.get(level_name.lower(), level_name)

                    # Get or create expertise level
                    try:
                        level = ExpertiseLevel.objects.get(level=level_name)
                    except ExpertiseLevel.DoesNotExist:
                        level = ExpertiseLevel.objects.create(level=level_name)
                        self.stdout.write(self.style.SUCCESS(f'Created level: {level_name}'))

                    # Create the theory question
                    question = TheoryQuestion.objects.create(
                        question_text=question_text,
                        programming_language=language,
                        expertise_level=level
                    )

                    # Store embedding (optional)
                    if not skip_embeddings:
                        try:
                            store_question_embedding(question.id, 'theory', question_text)
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f'Question {idx}: Failed to create embedding: {e}'))

                    # Track imports by level
                    imported_by_level[level_name] = imported_by_level.get(level_name, 0) + 1
                    
                    if sum(imported_by_level.values()) % 10 == 0:
                        self.stdout.write(f'  ✓ Imported {sum(imported_by_level.values())}/{len(questions_data)} questions...')

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Question {idx}: Error importing - {e}'))
                    skipped_count += 1

        # Print summary
        total_imported = sum(imported_by_level.values())
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Successfully imported {total_imported} theory questions. Skipped {skipped_count} questions.'
        ))
        self.stdout.write(f'   Language: {language_name}')
        for level_name, count in imported_by_level.items():
            self.stdout.write(f'   - {level_name}: {count} questions')

