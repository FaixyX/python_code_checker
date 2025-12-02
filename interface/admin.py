from django.contrib import admin
from django.contrib.auth import get_user_model
from authemail.admin import EmailUserAdmin
from .models import (
	ProgrammingLanguage, ExpertiseLevel, QuizQuestion, UserSubmission, 
	TestCase, UserProgress, MCQQuestion, TheoryQuestion, Quiz, QuizQuestionResponse, QuestionEmbedding,
	Assignment, AssignmentResponse 
)

class MyUserAdmin(EmailUserAdmin):
	fieldsets = (
		(None, {'fields': ('email', 'password')}),
		('Personal Info', {'fields': ('first_name', 'last_name')}),
		('Permissions', {'fields': ('is_active', 'is_staff', 
									   'is_superuser', 'is_verified', 
									   'groups', 'user_permissions')}),
		('Important dates', {'fields': ('last_login', 'date_joined')}),
		#('Custom info', {'fields': ('date_of_birth',)}),
	)
	list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_verified')
	list_filter = ('is_active', 'is_staff', 'is_superuser', 'is_verified')
	search_fields = ('email', 'first_name', 'last_name')
	ordering = ('-date_joined',)

class ProgrammingLanguageAdmin(admin.ModelAdmin):
	list_display = ('name',)
	search_fields = ('name',)
 
class QuestionEmbeddingAdmin(admin.ModelAdmin):
	list_display = ('question_id', 'question_type', 'created_at')
	search_fields = ('question_id', 'question_type')
	ordering = ('-created_at',)
	date_hierarchy = 'created_at'

class ExpertiseLevelAdmin(admin.ModelAdmin):
	list_display = ('level',)
	search_fields = ('level',)

class QuizQuestionAdmin(admin.ModelAdmin):
	list_display = ('id', 'question_text_truncated', 'programming_language', 'expertise_level', 'created_at')
	list_filter = ('programming_language', 'expertise_level', 'created_at')
	search_fields = ('question_text',)
	ordering = ('-created_at',)
	date_hierarchy = 'created_at'
	
	def question_text_truncated(self, obj):
		return obj.question_text[:100] + '...' if len(obj.question_text) > 100 else obj.question_text
	question_text_truncated.short_description = 'Question'

class MCQQuestionAdmin(admin.ModelAdmin):
	list_display = ('id', 'question_text_truncated', 'programming_language', 'expertise_level', 'correct_option', 'created_at')
	list_filter = ('programming_language', 'expertise_level', 'correct_option', 'created_at')
	search_fields = ('question_text', 'option_a', 'option_b', 'option_c', 'option_d')
	ordering = ('-created_at',)
	date_hierarchy = 'created_at'
	
	def question_text_truncated(self, obj):
		return obj.question_text[:100] + '...' if len(obj.question_text) > 100 else obj.question_text
	question_text_truncated.short_description = 'Question'

class TheoryQuestionAdmin(admin.ModelAdmin):
	list_display = ('id', 'question_text_truncated', 'programming_language', 'expertise_level', 'created_at')
	list_filter = ('programming_language', 'expertise_level', 'created_at')
	search_fields = ('question_text',)
	ordering = ('-created_at',)
	date_hierarchy = 'created_at'
	
	def question_text_truncated(self, obj):
		return obj.question_text[:100] + '...' if len(obj.question_text) > 100 else obj.question_text
	question_text_truncated.short_description = 'Question'

class TestCaseInline(admin.TabularInline):
	model = TestCase
	extra = 1

class QuizQuestionWithTestCasesAdmin(admin.ModelAdmin):
	inlines = [TestCaseInline]
	list_display = ('id', 'question_text_truncated', 'programming_language', 'expertise_level', 'created_at', 'test_case_count')
	list_filter = ('programming_language', 'expertise_level', 'created_at')
	search_fields = ('question_text',)
	ordering = ('-created_at',)
	
	def question_text_truncated(self, obj):
		return obj.question_text[:100] + '...' if len(obj.question_text) > 100 else obj.question_text
	question_text_truncated.short_description = 'Question'
	
	def test_case_count(self, obj):
		return obj.testcase_set.count()
	test_case_count.short_description = 'Test Cases'

class UserSubmissionAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'question', 'is_correct', 'formatted_time_taken', 'submitted_at')
	list_filter = ('is_correct', 'submitted_at', 'question__programming_language', 'question__expertise_level')
	search_fields = ('user__email', 'code')
	ordering = ('-submitted_at',)
	date_hierarchy = 'submitted_at'
	readonly_fields = ('submitted_at',)

class TestCaseAdmin(admin.ModelAdmin):
	list_display = ('id', 'question', 'input_data', 'expected_output')
	list_filter = ('question__programming_language', 'question__expertise_level')
	search_fields = ('input_data', 'expected_output', 'question__question_text')

class UserProgressAdmin(admin.ModelAdmin):
	list_display = ('user', 'correct_answers', 'total_attempts', 'accuracy', 'average_time_per_question')
	list_filter = ('user__is_active',)
	search_fields = ('user__email',)
	ordering = ('-correct_answers',)

class QuizAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'programming_language', 'expertise_level', 'score', 'total_questions', 'get_score_percentage', 'created_at', 'completed_at')
	list_filter = ('programming_language', 'expertise_level', 'created_at', 'completed_at')
	search_fields = ('user__email',)
	readonly_fields = ('created_at', 'completed_at')
	date_hierarchy = 'created_at'
	ordering = ('-created_at',)

class QuizQuestionResponseAdmin(admin.ModelAdmin):
	list_display = ('id', 'quiz', 'question_type', 'question_id', 'is_correct', 'created_at')
	list_filter = ('is_correct', 'question_type', 'quiz__programming_language', 'quiz__expertise_level')
	search_fields = ('user_response', 'quiz__user__email')
	ordering = ('-created_at',)
	date_hierarchy = 'created_at'

class AssignmentAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'programming_language', 'expertise_level', 'score', 'total_questions', 'created_at', 'completed_at')
	list_filter = ('programming_language', 'expertise_level', 'created_at', 'completed_at')
	search_fields = ('user__email', 'id')
	readonly_fields = ('created_at', 'completed_at', 'score', 'total_questions')
	date_hierarchy = 'created_at'
	ordering = ('-created_at',)

class AssignmentResponseAdmin(admin.ModelAdmin):
	list_display = ('id', 'assignment', 'question_type', 'question_id', 'is_correct', 'created_at')
	list_filter = ('is_correct', 'question_type', 'assignment__programming_language', 'assignment__expertise_level')
	search_fields = ('user_response', 'assignment__user__email', 'assignment__id')
	readonly_fields = ('created_at',)
	date_hierarchy = 'created_at'
	ordering = ('-created_at',)

admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), MyUserAdmin)
admin.site.register(ProgrammingLanguage, ProgrammingLanguageAdmin)
admin.site.register(ExpertiseLevel, ExpertiseLevelAdmin)
admin.site.register(QuizQuestion, QuizQuestionWithTestCasesAdmin)
admin.site.register(UserSubmission, UserSubmissionAdmin)
admin.site.register(TestCase, TestCaseAdmin)
admin.site.register(UserProgress, UserProgressAdmin)
admin.site.register(MCQQuestion, MCQQuestionAdmin)
admin.site.register(TheoryQuestion, TheoryQuestionAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(QuizQuestionResponse, QuizQuestionResponseAdmin)
admin.site.register(QuestionEmbedding, QuestionEmbeddingAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(AssignmentResponse, AssignmentResponseAdmin)
