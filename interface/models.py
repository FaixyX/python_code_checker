from django.db import models
from authemail.models import EmailUserManager, EmailAbstractUser
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField
from pgvector.django import VectorField

class MyUser(EmailAbstractUser):
	# Custom fields example
	#date_of_birth = models.DateField('Date of birth', null=True, blank=True)

	# Required
	objects = EmailUserManager()

class ProgrammingLanguage(models.Model):
	name = models.CharField(max_length=100, unique=True)

	def __str__(self):
		return self.name

class ExpertiseLevel(models.Model):
	level = models.CharField(max_length=100, unique=True)

	def __str__(self):
		return self.level

class QuizQuestion(models.Model):
	question_text = models.TextField()
	programming_language = models.ForeignKey(ProgrammingLanguage, on_delete=models.CASCADE)
	expertise_level = models.ForeignKey(ExpertiseLevel, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.programming_language} - {self.expertise_level}"

class UserSubmission(models.Model):
	user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
	question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
	code = models.TextField()
	submitted_at = models.DateTimeField(auto_now_add=True)
	is_correct = models.BooleanField(default=False)
	time_taken = models.FloatField(default=0.0, help_text="Time taken to solve the question in seconds")

	def formatted_time_taken(self):
		hours, remainder = divmod(self.time_taken, 3600)
		minutes, seconds = divmod(remainder, 60)
		return f"{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"

class TestCase(models.Model):
	question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
	input_data = models.TextField()
	expected_output = models.TextField()

class UserProgress(models.Model):
	user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
	correct_answers = models.IntegerField(default=0)
	total_attempts = models.IntegerField(default=0)
	accuracy = models.FloatField(default=0.0)
	average_time_per_question = models.FloatField(default=0.0)

	def __str__(self):
		return f"{self.correct_answers}/{self.total_attempts} correct, Accuracy: {self.accuracy}%, Speed: {self.average_time_per_question}s/question"

class MCQQuestion(models.Model):
	question_text = models.TextField()
	option_a = models.CharField(max_length=255)
	option_b = models.CharField(max_length=255)
	option_c = models.CharField(max_length=255)
	option_d = models.CharField(max_length=255)
	correct_option = models.CharField(max_length=1)
	programming_language = models.ForeignKey(ProgrammingLanguage, on_delete=models.CASCADE)
	expertise_level = models.ForeignKey(ExpertiseLevel, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"MCQ: {self.question_text[:50]}..."

class TheoryQuestion(models.Model):
	question_text = models.TextField()
	programming_language = models.ForeignKey(ProgrammingLanguage, on_delete=models.CASCADE)
	expertise_level = models.ForeignKey(ExpertiseLevel, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Theory: {self.question_text[:50]}..."

class Quiz(models.Model):
	user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
	programming_language = models.ForeignKey(ProgrammingLanguage, on_delete=models.CASCADE)
	expertise_level = models.ForeignKey(ExpertiseLevel, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)
	completed_at = models.DateTimeField(null=True, blank=True)
	score = models.IntegerField(default=0)
	total_questions = models.IntegerField(default=10)
	
	def __str__(self):
		return f"Quiz for {self.user.email} - {self.programming_language.name} ({self.expertise_level.level})"
	
	def calculate_score(self):
		correct_answers = self.quizquestionresponse_set.filter(is_correct=True).count()
		total = self.quizquestionresponse_set.count()
		if total > 0:
			self.score = correct_answers
			self.total_questions = total
			self.save()
		return self.score
		
	def get_score_percentage(self):
		"""Return the score as a percentage"""
		if self.total_questions == 0:
			return 0
		return (self.score * 100) // self.total_questions
		
	def get_progress(self):
		"""Return the progress as a percentage"""
		if self.total_questions == 0:
			return 0
		answered = self.quizquestionresponse_set.count()
		return (answered * 100) // self.total_questions
		
	def get_remaining_questions(self):
		"""Return the number of remaining questions"""
		answered = self.quizquestionresponse_set.count()
		return max(0, self.total_questions - answered)

class QuizQuestionResponse(models.Model):
	QUESTION_TYPE_CHOICES = (
		('coding', 'Coding Question'),
		('theory', 'Theory Question'),
		('mcq', 'Multiple Choice Question'),
	)
	
	quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
	question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES)
	question_id = models.IntegerField()  # ID of the question in its respective table
	user_response = models.TextField()  # User's answer or code
	is_correct = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	
	# Scoring fields for ML-style evaluation
	score = models.FloatField(default=0.0, null=True, blank=True, help_text="Numeric score (0-100)")
	semantic_similarity = models.FloatField(null=True, blank=True, help_text="Semantic similarity for theory questions (0-1)")
	code_similarity = models.FloatField(null=True, blank=True, help_text="Code similarity for coding questions (0-1)")
	test_pass_rate = models.FloatField(null=True, blank=True, help_text="Test case pass rate for coding questions (0-1)")
	code_quality_score = models.FloatField(null=True, blank=True, help_text="Code quality score (0-1)")
	
	def __str__(self):
		return f"Response for Quiz #{self.quiz.id} - {self.question_type} Question #{self.question_id}"

class QuestionEmbedding(models.Model):
	"""Model to store vector embeddings for questions to detect semantic duplicates."""
	QUESTION_TYPE_CHOICES = (
		('coding', 'Coding Question'),
		('theory', 'Theory Question'),
		('mcq', 'Multiple Choice Question'),
	)
	
	question_id = models.IntegerField()
	question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES)
	embedding = VectorField(dimensions=1536, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		unique_together = ('question_id', 'question_type')
		indexes = [
			models.Index(fields=['question_type']),
		]
		db_table = 'question_embeddings'
	
	def __str__(self):
		return f"{self.question_type} Embedding for Question #{self.question_id}"


# <<< NEW ASSIGNMENT MODELS >>>

class Assignment(models.Model):
	"""Represents a specific assignment instance given to a user."""
	user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
	programming_language = models.ForeignKey(ProgrammingLanguage, on_delete=models.CASCADE)
	expertise_level = models.ForeignKey(ExpertiseLevel, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)
	completed_at = models.DateTimeField(null=True, blank=True)
	score = models.IntegerField(default=0, help_text="Number of correct answers")
	total_questions = models.IntegerField(default=10, help_text="Should always be 10 (8 coding + 2 theory)")

	def __str__(self):
		status = "Completed" if self.completed_at else "In Progress"
		return f"Assignment for {self.user.email} - {self.programming_language.name} ({self.expertise_level.level}) - Status: {status}"

	def calculate_score(self):
		"""Calculates and updates the score based on responses."""
		correct_answers = self.assignmentresponse_set.filter(is_correct=True).count()
		self.score = correct_answers
		# Ensure total_questions reflects actual responses if needed, though it should be fixed at 10
		# self.total_questions = self.assignmentresponse_set.count() 
		self.save()
		return self.score

class AssignmentResponse(models.Model):
	"""Stores a user's response to a single question within an assignment."""
	QUESTION_TYPE_CHOICES = (
		('coding', 'Coding Question'),
		('theory', 'Theory Question'),
	)
	
	assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
	question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES)
	question_id = models.IntegerField()  # ID of the question in its respective table (QuizQuestion or TheoryQuestion)
	user_response = models.TextField(blank=True)  # User's answer or code
	is_correct = models.BooleanField(default=False)
	feedback = models.TextField(blank=True, default='') # <-- New field for LLM feedback
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('assignment', 'question_type', 'question_id') # Prevent duplicate responses for the same question in one assignment
		ordering = ['created_at']

	def __str__(self):
		return f"Response for Assignment #{self.assignment.id} - {self.question_type} Question #{self.question_id}"

# <<< END NEW ASSIGNMENT MODELS >>>