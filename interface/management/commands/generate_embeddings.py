import time
from django.core.management.base import BaseCommand
from django.db import transaction
from interface.models import QuizQuestion, TheoryQuestion, MCQQuestion, QuestionEmbedding
from interface.embeddings import store_question_embedding
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate embeddings for all existing questions in the database'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=50, 
                          help='Number of questions to process in a batch before sleeping (to avoid API rate limits)')
        parser.add_argument('--sleep-time', type=float, default=10.0,
                          help='Sleep time in seconds between batches')
        parser.add_argument('--types', type=str, default='all',
                          help='Question types to process (comma-separated): coding,theory,mcq,all')
        parser.add_argument('--force', action='store_true',
                          help='Force regeneration of embeddings for questions that already have them')

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        sleep_time = options['sleep_time']
        question_types = options['types'].split(',')
        force = options['force']
        
        # Add message about OpenAI API version
        self.stdout.write(self.style.SUCCESS("Using OpenAI API v1.0+ format for embedding generation"))
        
        if 'all' in question_types:
            question_types = ['coding', 'theory', 'mcq']
        
        total_processed = 0
        total_skipped = 0
        total_errors = 0
        
        self.stdout.write(self.style.SUCCESS(f"Starting to generate embeddings for question types: {', '.join(question_types)}"))
        
        # Process QuizQuestion (coding questions)
        if 'coding' in question_types:
            self.stdout.write("Processing coding questions...")
            
            # Get questions that don't have embeddings yet (or all if force=True)
            if force:
                questions = QuizQuestion.objects.all()
            else:
                existing_embeddings = QuestionEmbedding.objects.filter(question_type='coding').values_list('question_id', flat=True)
                questions = QuizQuestion.objects.exclude(id__in=existing_embeddings)
            
            total_questions = questions.count()
            self.stdout.write(f"Found {total_questions} coding questions to process")
            
            processed = 0
            batch_count = 0
            
            with tqdm(total=total_questions, desc="Coding questions") as pbar:
                for question in questions:
                    try:
                        with transaction.atomic():
                            store_question_embedding(question.id, 'coding', question.question_text)
                            processed += 1
                            batch_count += 1
                            total_processed += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error generating embedding for coding question {question.id}: {str(e)}"))
                        total_errors += 1
                    
                    pbar.update(1)
                    
                    # Sleep after each batch to avoid API rate limits
                    if batch_count >= batch_size:
                        self.stdout.write(f"Processed {batch_count} questions, sleeping for {sleep_time} seconds...")
                        time.sleep(sleep_time)
                        batch_count = 0
            
            self.stdout.write(self.style.SUCCESS(f"Processed {processed} coding questions"))
        
        # Process TheoryQuestion
        if 'theory' in question_types:
            self.stdout.write("Processing theory questions...")
            
            # Get questions that don't have embeddings yet (or all if force=True)
            if force:
                questions = TheoryQuestion.objects.all()
            else:
                existing_embeddings = QuestionEmbedding.objects.filter(question_type='theory').values_list('question_id', flat=True)
                questions = TheoryQuestion.objects.exclude(id__in=existing_embeddings)
            
            total_questions = questions.count()
            self.stdout.write(f"Found {total_questions} theory questions to process")
            
            processed = 0
            batch_count = 0
            
            with tqdm(total=total_questions, desc="Theory questions") as pbar:
                for question in questions:
                    try:
                        with transaction.atomic():
                            store_question_embedding(question.id, 'theory', question.question_text)
                            processed += 1
                            batch_count += 1
                            total_processed += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error generating embedding for theory question {question.id}: {str(e)}"))
                        total_errors += 1
                    
                    pbar.update(1)
                    
                    # Sleep after each batch to avoid API rate limits
                    if batch_count >= batch_size:
                        self.stdout.write(f"Processed {batch_count} questions, sleeping for {sleep_time} seconds...")
                        time.sleep(sleep_time)
                        batch_count = 0
            
            self.stdout.write(self.style.SUCCESS(f"Processed {processed} theory questions"))
        
        # Process MCQQuestion
        if 'mcq' in question_types:
            self.stdout.write("Processing MCQ questions...")
            
            # Get questions that don't have embeddings yet (or all if force=True)
            if force:
                questions = MCQQuestion.objects.all()
            else:
                existing_embeddings = QuestionEmbedding.objects.filter(question_type='mcq').values_list('question_id', flat=True)
                questions = MCQQuestion.objects.exclude(id__in=existing_embeddings)
            
            total_questions = questions.count()
            self.stdout.write(f"Found {total_questions} MCQ questions to process")
            
            processed = 0
            batch_count = 0
            
            with tqdm(total=total_questions, desc="MCQ questions") as pbar:
                for question in questions:
                    try:
                        with transaction.atomic():
                            store_question_embedding(question.id, 'mcq', question.question_text)
                            processed += 1
                            batch_count += 1
                            total_processed += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error generating embedding for MCQ question {question.id}: {str(e)}"))
                        total_errors += 1
                    
                    pbar.update(1)
                    
                    # Sleep after each batch to avoid API rate limits
                    if batch_count >= batch_size:
                        self.stdout.write(f"Processed {batch_count} questions, sleeping for {sleep_time} seconds...")
                        time.sleep(sleep_time)
                        batch_count = 0
            
            self.stdout.write(self.style.SUCCESS(f"Processed {processed} MCQ questions"))
        
        # Print summary
        self.stdout.write(self.style.SUCCESS(f"Embedding generation complete:"))
        self.stdout.write(f"  Total processed: {total_processed}")
        self.stdout.write(f"  Total errors: {total_errors}")
        
        if total_errors > 0:
            self.stdout.write(self.style.WARNING("Some embeddings could not be generated. See logs for details.")) 