import requests
from urllib.parse import urlencode
from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from .models import MyUser, ProgrammingLanguage, ExpertiseLevel, QuizQuestion, TestCase, UserProgress, UserSubmission, MCQQuestion, TheoryQuestion, Quiz, QuizQuestionResponse, Assignment, AssignmentResponse
from .serializers import CustomUserSignupSerializer, UserProfileUpdateSerializer, UserProfileRetrieveSerializer, ProgrammingLanguageSerializer, ExpertiseLevelSerializer, QuizQuestionSerializer, TheoryQuestionSerializer, AssignmentSerializer, AssignmentResponseSerializer, ChangePasswordSerializer
from rest_framework.decorators import api_view, permission_classes
import openai
import subprocess
from django.db.models import Avg, F, Q, Sum, Count
import json
from django.utils import timezone
import re
import random
from django.core.management import call_command
from django.http import HttpRequest
from django.core.handlers.wsgi import WSGIRequest
from rest_framework.request import Request
from rest_framework.parsers import JSONParser
import tempfile
import os
from .embeddings import is_question_duplicate, store_question_embedding
from .generation_utils import generate_coding_question, generate_theory_question as generate_theory_question_util, generate_mcq_question as generate_mcq_question_util
from .evaluation.evaluators import evaluate_theory_answer, evaluate_code_answer
from .utils import run_code, normalize_output, get_file_extension, get_execution_command
import logging

logger = logging.getLogger(__name__)

class CustomSignupView(APIView):
    permission_classes = [] # Allow any user (guest) to access this endpoint

    def post(self, request, *args, **kwargs):
        serializer = CustomUserSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Return user data (excluding password) upon successful creation
            return Response({
                "message": "User registered successfully.",
                "user_id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_verified": user.is_verified,
                "is_active": user.is_active
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GoogleLoginView(APIView):
    def get(self, request):

        auth_url = (
            f'https://accounts.google.com/o/oauth2/auth?'
            f'client_id={settings.GOOGLE_OAUTH2_CLIENT_ID}&'
            f'redirect_uri={settings.GOOGLE_OAUTH2_REDIRECT_URI}&'
            f'response_type=code&'
            f'scope=openid%20email%20profile&'
            f'prompt=select_account'
        )

        return Response({'auth_url': auth_url}, status=status.HTTP_200_OK)
    
class GoogleCallbackView(APIView):
    def get(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({'detail': 'Missing code parameter'}, status=status.HTTP_400_BAD_REQUEST)

        token_url = 'https://accounts.google.com/o/oauth2/token'
        token_data = {
            'code': code,
            'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_OAUTH2_REDIRECT_URI,
            'grant_type': 'authorization_code',
        }

        response = requests.post(token_url, data=token_data)
        token_info = response.json()

        if 'access_token' in token_info:
            user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
            headers = {'Authorization': f'Bearer {token_info["access_token"]}'}
            user_info_response = requests.get(user_info_url, headers=headers)
            user_info = user_info_response.json()
            email = user_info.get('email')
            first_name = user_info.get('given_name')
            last_name = user_info.get('family_name')
            if email:
                user, created = MyUser.objects.get_or_create(email=email)
                if created:
                    user.is_verified = True
                    if first_name:
                        user.first_name = first_name
                    if last_name:
                        user.last_name = last_name

                    user.save()

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            query_parameters = {
                'access_token': access_token,
                'refresh_token': str(refresh),
            }
            auth_url = settings.FRONTEND_REDIRECT_URL

            redirect_url = f'{auth_url}?{urlencode(query_parameters)}'

            return HttpResponseRedirect(redirect_url)
        return Response({'detail': 'Authentication failed'}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileUpdateView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserProfileRetrieveSerializer
        else:
            return UserProfileUpdateSerializer

    def get_object(self):
        return self.request.user

class ChangePasswordView(APIView):
    permission_classes = [] # Allow any user to access this endpoint

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            new_password = serializer.validated_data['new_password']

            try:
                user = MyUser.objects.get(email__iexact=email) # Case-insensitive email match
            except MyUser.DoesNotExist:
                return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

            user.set_password(new_password)
            user.save()
            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Programming Language CRUD APIs
class ProgrammingLanguageListCreateView(ListCreateAPIView):
    queryset = ProgrammingLanguage.objects.all()
    serializer_class = ProgrammingLanguageSerializer
    
    def get_permissions(self):
        # Remove authorization requirement for POST requests
        return []  # Allow all users to access this view
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = {
            'message': 'Programming language created successfully',
            'data': response.data
        }
        return response


class ProgrammingLanguageDetailView(RetrieveUpdateDestroyAPIView):
    queryset = ProgrammingLanguage.objects.all()
    serializer_class = ProgrammingLanguageSerializer
    
    def get_permissions(self):
        # Remove authorization requirement for PUT, PATCH, DELETE requests
        return []  # Allow all users to access this view
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = {
            'message': 'Programming language updated successfully',
            'data': response.data
        }
        return response
    
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return Response({
            'message': 'Programming language deleted successfully'
        }, status=status.HTTP_200_OK)


# Expertise Level CRUD APIs
class ExpertiseLevelListCreateView(ListCreateAPIView):
    queryset = ExpertiseLevel.objects.all()
    serializer_class = ExpertiseLevelSerializer
    
    def get_permissions(self):
        # Remove authorization requirement for POST requests
        return []  # Allow all users to access this view
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = {
            'message': 'Expertise level created successfully',
            'data': response.data
        }
        return response


class ExpertiseLevelDetailView(RetrieveUpdateDestroyAPIView):
    queryset = ExpertiseLevel.objects.all()
    serializer_class = ExpertiseLevelSerializer
    
    def get_permissions(self):
        # Remove authorization requirement for PUT, PATCH, DELETE requests
        return []  # Allow all users to access this view
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = {
            'message': 'Expertise level updated successfully',
            'data': response.data
        }
        return response
    
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return Response({
            'message': 'Expertise level deleted successfully'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
def generate_quiz_question(request):
    print("Received request to generate quiz question")
    language_id = request.data.get('language_id')
    level_id = request.data.get('level_id')
    print(f"Language ID: {language_id}, Level ID: {level_id}")
    
    # Validate input parameters
    if not language_id:
        print("Language ID not provided")
        return Response({'error': 'Programming language ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not level_id:
        print("Level ID not provided")
        return Response({'error': 'Expertise level ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        language = ProgrammingLanguage.objects.get(id=language_id)
        level = ExpertiseLevel.objects.get(id=level_id)
        print(f"Found language: {language.name}, level: {level.level}")
    except ProgrammingLanguage.DoesNotExist:
        print("Programming language not found")
        return Response({'error': 'Programming language not found'}, status=status.HTTP_404_NOT_FOUND)
    except ExpertiseLevel.DoesNotExist:
        print("Expertise level not found")
        return Response({'error': 'Expertise level not found'}, status=status.HTTP_404_NOT_FOUND)

    # Use the utility function to generate a coding question with duplicate detection
    success, result, status_code = generate_coding_question(language, level)
    
    if success:
        # If generation was successful, result is a QuizQuestion object
        question = result
        return Response({
            'question_id': question.id,
            'question': question.question_text
        }, status=status_code)
    else:
        # If generation failed, result is a Response object
        return result

def validate_syntax_and_execute(code, language, question_text):
    # Use OpenAI API to check for syntax errors and execute code
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    if not api_key:
        print("OpenAI API key not found")
        return False, "OpenAI API key not found"

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    prompt = f"Check the following {language} code for syntax errors and execute it to verify its correctness. The code is for the question: {question_text}. If there are syntax errors, return them. If the code executes correctly, return 'No syntax errors and code executed successfully'.\n\n{code}"

    data = {
        'model': 'gpt-4',
        'messages': [
            {'role': 'system', 'content': 'You are a syntax checking and code execution assistant.'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0,
        'max_tokens': 1500,
    }

    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        result = response.json()
        execution_result = result['choices'][0]['message']['content'].strip()
        if "No syntax errors and code executed successfully" in execution_result:
            return True, ""
        else:
            return False, execution_result
    else:
        print(f"OpenAI API Error: {response.status_code}, {response.text}")
        return False, "Failed to check syntax and execute code"


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer(request):
    user = request.user
    question_id = request.data.get('question_id')
    code = request.data.get('code')
    language = request.data.get('language')
    start_time = request.data.get('start_time')
    
    # Validate required fields
    if not question_id:
        return Response({'error': 'Question ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
    if not code:
        return Response({'error': 'Code submission is required'}, status=status.HTTP_400_BAD_REQUEST)
        
    if not language:
        return Response({'error': 'Programming language is required'}, status=status.HTTP_400_BAD_REQUEST)
        
    if not start_time:
        return Response({'error': 'Start time is required'}, status=status.HTTP_400_BAD_REQUEST)

    print(f"User {user.id} submitted code for question {question_id}")

    try:
        question = QuizQuestion.objects.get(id=question_id)
        level = question.expertise_level.level
    except QuizQuestion.DoesNotExist:
        return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)

    # Calculate time taken
    end_time = timezone.now()
    print(f"End time: {end_time}")
    
    # Handle timezone-aware datetime string
    try:
        # Parse the datetime string
        start_time_dt = timezone.datetime.fromisoformat(start_time)
        
        # Check if it's already timezone-aware
        if timezone.is_aware(start_time_dt):
            start_time = start_time_dt
        else:
            start_time = timezone.make_aware(start_time_dt)
    except Exception as e:
        print(f"Error parsing start_time: {e}")
        # Default to 5 minutes ago if we can't parse the time
        start_time = timezone.now() - timezone.timedelta(minutes=5)
    
    print(f"Start time: {start_time}")
    time_taken = (end_time - start_time).total_seconds()
    print(f"Time taken: {time_taken}")



    # Define headers for LLM Verification
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    if not api_key:
        return Response({'error': 'OpenAI API key not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Extract just the problem statement for cleaner prompt
    problem_statement = question.question_text
    # Try to extract just the question part if possible
    question_match = re.search(r'Question:\s*(.+?)(?=Sample Input:|$)', problem_statement, re.DOTALL)
    if question_match:
        problem_statement = question_match.group(1).strip()

    # Enhanced LLM Verification prompt
    prompt = (
        f"You are an AI code checker responsible for evaluating the correctness of submitted code. Your task is to analyze the provided code snippet, determine if it correctly implements a solution to the given problem, and provide helpful feedback. Respond only with the JSON response.\n"
        f"### Problem Description:\n{problem_statement}\n\n"
        f"### Submitted Code ({language}):\n```\n{code}\n```\n\n"
        f"### Instructions:\n"
        f"1. Determine if the code correctly solves the problem.\n"
        f"4. Include brief, constructive feedback about the solution.\n\n"
        f"Respond with a JSON object in the following format:\n"
        f"```json\n"
        f"{{\n"
        f'  "correct": true/false,\n'
        f'  "feedback": "Brief explanation of the evaluation result",\n'
        f'  "failed_test_cases": [] // List of failed test cases if any\n'
        f"}}\n"
        f"```"
    )
    
    data = {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'system', 'content': 'You are a code verification assistant that provides accurate and helpful feedback.'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0,
        'max_tokens': 1500,
    }
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data
        )
            
        if response.status_code == 200:
            result = response.json()
            verification_result = result['choices'][0]['message']['content'].strip()
                
            # Try to parse the JSON from the response
            try:
                # Clean the response in case it contains markdown formatting
                clean_result = re.sub(r'```json|```', '', verification_result).strip()
                verification_json = json.loads(clean_result)
                
                is_correct = verification_json.get('correct', False)
                feedback = verification_json.get('feedback', '')
                failed_test_cases = verification_json.get('failed_test_cases', [])
                
            except json.JSONDecodeError:
                print(f"Failed to parse JSON from GPT response: {verification_result}")
                # If we can't parse the JSON, extract information using regex
                is_correct = 'true' in verification_result.lower() and '"correct": true' in verification_result.lower()
                feedback_match = re.search(r'"feedback":\s*"([^"]+)"', verification_result)
                feedback = feedback_match.group(1) if feedback_match else "Feedback not available"
                failed_test_cases = verification_json.get('failed_test_cases', [])
        else:
            print(f"OpenAI API Error: {response.status_code}, {response.text}")
            return Response({
                'error': 'Failed to verify code',
                'details': response.text
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
    except Exception as e:
        print(f"Error during code verification: {e}")
        import traceback
        traceback.print_exc()
        
        # Fall back to test case results if API fails
        is_correct = all_passed
        feedback = "System encountered an error during verification. Evaluation based on test cases only."
        failed_test_cases = failed_cases

    # Format feedback
    formatted_feedback = "✅ Correct Answer: " if is_correct else "❌ Incorrect Answer: "
    formatted_feedback += feedback

    # Update user progress
    user_progress, created = UserProgress.objects.get_or_create(user=user)
    user_progress.total_attempts += 1
    if is_correct:
        user_progress.correct_answers += 1
    
    # Update accuracy
    if user_progress.total_attempts > 0:
        user_progress.accuracy = (user_progress.correct_answers / user_progress.total_attempts) * 100
    
    # Update average time
    if user_progress.average_time_per_question == 0:
        user_progress.average_time_per_question = time_taken
    else:
        user_progress.average_time_per_question = (user_progress.average_time_per_question + time_taken) / 2
    
    user_progress.save()

    # Save submission
    submission = UserSubmission.objects.create(
        user=user, 
        question=question, 
        code=code, 
        is_correct=is_correct, 
        time_taken=time_taken
    )

    return Response({
        'submission_id': submission.id,
        'is_correct': is_correct,
        'feedback': formatted_feedback,
        'time_taken': time_taken,
        'failed_test_cases': failed_test_cases,
    }, status=status.HTTP_200_OK)

# Enhanced Leaderboard view
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leaderboard(request):
    """
    Get the top performers based on average Quiz scores and average Assignment scores.
    Supports time period filtering (all, month, week).
    """
    # Removed leaderboard_type parameter
    time_period = request.query_params.get('period', 'all')  # Options: all, month, week
    limit = int(request.query_params.get('limit', 10)) # Allow specifying result limit, default 10
    
    # --- Time filtering --- 
    time_filter = Q()
    now = timezone.now()
    if time_period == 'month':
        start_date = now - timezone.timedelta(days=30)
        time_filter = Q(completed_at__gte=start_date)
    elif time_period == 'week':
        start_date = now - timezone.timedelta(days=7)
        time_filter = Q(completed_at__gte=start_date)
    # 'all' time period uses no time filter

    # --- Calculate Quiz Leaderboard --- 
    quiz_leaderboard_data = []
    try:
        completed_quizzes = Quiz.objects.filter(
            completed_at__isnull=False
        ).filter(time_filter).values(
            'user' # Group by user
        ).annotate(
            avg_score=Avg('score'),
            quiz_count=Count('id')
        ).order_by('-avg_score') # Order by average score descending
        
        # Get user details for the top N users
        top_quiz_users_data = completed_quizzes[:limit]
        top_quiz_user_ids = [data['user'] for data in top_quiz_users_data]
        
        # Fetch user objects in bulk
        user_map = {user.id: user for user in MyUser.objects.filter(id__in=top_quiz_user_ids)}
        
        # Build the quiz leaderboard list
        for data in top_quiz_users_data:
            user = user_map.get(data['user'])
            if user:
                quiz_leaderboard_data.append({
                    'user_id': user.id,
                    'user_email': user.email,
                    'average_quiz_score': round(data['avg_score'], 2),
                    'quiz_count': data['quiz_count']
                })
    except Exception as e:
        logger.error(f"Error calculating quiz leaderboard: {e}")
        # Optionally return an error indicator or empty list

    # --- Calculate Assignment Leaderboard --- 
    assignment_leaderboard_data = []
    try:
        completed_assignments = Assignment.objects.filter(
            completed_at__isnull=False
        ).filter(time_filter).values(
            'user' # Group by user
        ).annotate(
            avg_score=Avg('score'), # Average score per assignment
            assignment_count=Count('id') 
        ).order_by('-avg_score') # Order by average score descending

        # Get user details for the top N users
        top_assignment_users_data = completed_assignments[:limit]
        top_assignment_user_ids = [data['user'] for data in top_assignment_users_data]

        # Fetch user objects - reuse user_map if possible, or fetch new ones
        # Avoid refetching if lists overlap significantly - simple approach for now:
        needed_user_ids = set(top_assignment_user_ids) - set(user_map.keys())
        if needed_user_ids:
             additional_users = {user.id: user for user in MyUser.objects.filter(id__in=needed_user_ids)}
             user_map.update(additional_users)

        # Build the assignment leaderboard list
        for data in top_assignment_users_data:
            user = user_map.get(data['user'])
            if user:
                assignment_leaderboard_data.append({
                    'user_id': user.id,
                    'user_email': user.email,
                    'average_assignment_score': round(data['avg_score'], 2),
                    'assignment_count': data['assignment_count']
                })
    except Exception as e:
        logger.error(f"Error calculating assignment leaderboard: {e}")
        # Optionally return an error indicator or empty list

    # --- Return combined response --- 
    return Response({
        'time_period': time_period,
        'limit': limit,
        'quiz_leaderboard': quiz_leaderboard_data,
        'assignment_leaderboard': assignment_leaderboard_data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_submissions(request, user_id=None):
    """
    View to see other users' submissions and performance data.
    If user_id is provided, returns data for that specific user.
    Otherwise, returns data for the requesting user.
    """
    # Check if the requested user_id exists
    target_user_id = user_id if user_id else request.user.id
    
    try:
        target_user = MyUser.objects.get(id=target_user_id)
    except MyUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get user's quizzes
    quizzes = Quiz.objects.filter(user=target_user).order_by('-created_at')
    
    # Get user progress data
    try:
        user_progress = UserProgress.objects.get(user=target_user)
        accuracy = 0
        if user_progress.total_attempts > 0:
            accuracy = round((user_progress.correct_answers / user_progress.total_attempts) * 100, 2)
            
        progress_data = {
            'accuracy': accuracy,
            'correct_answers': user_progress.correct_answers,
            'total_attempts': user_progress.total_attempts,
            'average_time': user_progress.average_time_per_question
        }
    except UserProgress.DoesNotExist:
        progress_data = {
            'accuracy': 0,
            'correct_answers': 0,
            'total_attempts': 0,
            'average_time': 0
        }
    
    # Get quiz data
    quiz_data = []
    for quiz in quizzes:
        if quiz.completed_at:  # Only include completed quizzes
            # Get responses for this quiz
            correct_count = QuizQuestionResponse.objects.filter(quiz=quiz, is_correct=True).count()
            total_count = QuizQuestionResponse.objects.filter(quiz=quiz).count()
            
            # Calculate duration if possible
            duration_seconds = 0
            if total_count > 0:
                first_response = QuizQuestionResponse.objects.filter(quiz=quiz).order_by('created_at').first()
                last_response = QuizQuestionResponse.objects.filter(quiz=quiz).order_by('-created_at').first()
                if first_response and last_response:
                    duration_seconds = (last_response.created_at - first_response.created_at).total_seconds()
            
            quiz_data.append({
                'quiz_id': quiz.id,
                'language': quiz.programming_language.name,
                'level': quiz.expertise_level.level,
                'score': quiz.score,
                'created_at': quiz.created_at,
                'completed_at': quiz.completed_at,
                'correct_answers': correct_count,
                'total_questions': total_count,
                'duration_seconds': duration_seconds
            })
    
    # Get recent correct submissions
    recent_submissions = UserSubmission.objects.filter(
        user=target_user,
        is_correct=True
    ).order_by('-submitted_at')[:5]
    
    submission_data = []
    for submission in recent_submissions:
        submission_data.append({
            'question_text': submission.question.question_text,
            'language': submission.question.programming_language.name,
            'level': submission.question.expertise_level.level,
            'time_taken': submission.time_taken,
            'created_at': submission.submitted_at
        })
    
    # Get language proficiency - calculate percentage of correct answers by language
    language_proficiency = {}
    
    # First get all programming languages
    languages = ProgrammingLanguage.objects.all()
    
    for language in languages:
        # Get all submissions for this language
        language_submissions = UserSubmission.objects.filter(
            user=target_user,
            question__programming_language=language
        )
        
        total_for_language = language_submissions.count()
        correct_for_language = language_submissions.filter(is_correct=True).count()
        
        if total_for_language > 0:
            proficiency = round((correct_for_language / total_for_language) * 100, 2)
            language_proficiency[language.name] = {
                'total': total_for_language,
                'correct': correct_for_language,
                'proficiency': proficiency
            }
    
    return Response({
        'user_id': target_user.id,
        'user_email': target_user.email,
        'progress': progress_data,
        'quizzes': quiz_data,
        'recent_submissions': submission_data,
        'language_proficiency': language_proficiency
    }, status=status.HTTP_200_OK)

# Add global leaderboard for quiz performance
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_leaderboard(request):
    """
    Get the best performers by quiz scores
    """
    language_id = request.query_params.get('language_id')
    level_id = request.query_params.get('level_id')
    
    # Base filter
    quiz_filter = Q(completed_at__isnull=False)
    
    # Add optional filters
    if language_id:
        try:
            language = ProgrammingLanguage.objects.get(id=language_id)
            quiz_filter &= Q(programming_language=language)
        except ProgrammingLanguage.DoesNotExist:
            pass
    
    if level_id:
        try:
            level = ExpertiseLevel.objects.get(id=level_id)
            quiz_filter &= Q(expertise_level=level)
        except ExpertiseLevel.DoesNotExist:
            pass
    
    # Get completed quizzes with filters
    quizzes = Quiz.objects.filter(quiz_filter).order_by('-score')[:25]
    
    # Format the response
    leaderboard_data = []
    for quiz in quizzes:
        correct_answers = QuizQuestionResponse.objects.filter(quiz=quiz, is_correct=True).count()
        total_questions = QuizQuestionResponse.objects.filter(quiz=quiz).count()
        
        # Calculate completion time
        duration_seconds = 0
        if total_questions > 0:
            first_response = QuizQuestionResponse.objects.filter(quiz=quiz).order_by('created_at').first()
            last_response = QuizQuestionResponse.objects.filter(quiz=quiz).order_by('-created_at').first()
            if first_response and last_response:
                duration_seconds = (last_response.created_at - first_response.created_at).total_seconds()
        
        leaderboard_data.append({
            'quiz_id': quiz.id,
            'user_id': quiz.user.id,
            'user_email': quiz.user.email,
            'language': quiz.programming_language.name,
            'level': quiz.expertise_level.level,
            'score': quiz.score,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'completion_time': duration_seconds,
            'completed_at': quiz.completed_at
        })
    
    return Response({
        'leaderboard': leaderboard_data
    }, status=status.HTTP_200_OK)

# User comparison view
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def compare_user_progress(request, friend_id=None):
    user_progress = UserProgress.objects.get(user=request.user)
    friend_progress = UserProgress.objects.get(user__id=friend_id) if friend_id else None

    comparison_data = {
        'user': {
            'accuracy': user_progress.accuracy,
            'speed': user_progress.average_time_per_question
        },
        'friend': {
            'accuracy': friend_progress.accuracy,
            'speed': friend_progress.average_time_per_question
        } if friend_progress else None
    }

    return Response({'comparison': comparison_data}, status=status.HTTP_200_OK)

@api_view(['POST'])
def generate_mcq_question(request):
    language_id = request.data.get('language_id')
    level_id = request.data.get('level_id')

    try:
        language = ProgrammingLanguage.objects.get(id=language_id)
        level = ExpertiseLevel.objects.get(id=level_id)
    except ProgrammingLanguage.DoesNotExist:
        return Response({'error': 'Programming language not found'}, status=status.HTTP_404_NOT_FOUND)
    except ExpertiseLevel.DoesNotExist:
        return Response({'error': 'Expertise level not found'}, status=status.HTTP_404_NOT_FOUND)

    # Use the utility function to generate an MCQ with duplicate detection
    success, result, status_code = generate_mcq_question_util(language, level)
    
    if success:
        # If generation was successful, result is an MCQQuestion object
        question = result
        return Response({
            'id': question.id,
            'question': question.question_text,
            'options': {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d
            },
            'correct_option': question.correct_option
        }, status=status_code)
    else:
        # If generation failed, result is a Response object
        return result

@api_view(['POST'])
def generate_theory_question(request):
    language_id = request.data.get('language_id')
    level_id = request.data.get('level_id')

    try:
        language = ProgrammingLanguage.objects.get(id=language_id)
        level = ExpertiseLevel.objects.get(id=level_id)
    except ProgrammingLanguage.DoesNotExist:
        return Response({'error': 'Programming language not found'}, status=status.HTTP_404_NOT_FOUND)
    except ExpertiseLevel.DoesNotExist:
        return Response({'error': 'Expertise level not found'}, status=status.HTTP_404_NOT_FOUND)

    # Use the utility function to generate a theory question with duplicate detection
    success, result, status_code = generate_theory_question_util(language, level)
    
    if success:
        # If generation was successful, result is a TheoryQuestion object
        question = result
        return Response({
            'id': question.id,
            'question': question.question_text
        }, status=status_code)
    else:
        # If generation failed, result is a Response object
        return result

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_theory_answer(request):
    user = request.user
    question_id = request.data.get('question_id')
    user_answer = request.data.get('answer')

    if not question_id or not user_answer:
        return Response({'error': 'Question ID and answer are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        question = TheoryQuestion.objects.get(id=question_id)
    except TheoryQuestion.DoesNotExist:
        return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)

    # Prepare the prompt for GPT
    prompt = (
        f"Evaluate the following answer to the question: '{question.question_text}'.\n"
        f"User's answer: '{user_answer}'.\n"
        f"Respond with 'Correct Answer' if the answer is correct, or 'Incorrect Answer' followed by a hint if it is not."
    )

    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    if not api_key:
        return Response({'error': 'OpenAI API key not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.7,
        'max_tokens': 1500,
    }

    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        result = response.json()
        feedback = result['choices'][0]['message']['content'].strip()
        # Extract only 'Correct Answer' or 'Incorrect Answer' with a hint
        if 'Correct Answer' in feedback:
            return Response({'feedback': 'Correct Answer'}, status=status.HTTP_200_OK)
        elif 'Incorrect Answer' in feedback:
            # Adjust the regex to capture the hint correctly
            hint_match = re.search(r"Incorrect Answer\. Hint: (.+)", feedback)
            hint = hint_match.group(1) if hint_match else ""
            return Response({'feedback': 'Incorrect Answer', 'hint': hint}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Unexpected response format'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({'error': 'Failed to verify answer'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_quiz(request):
    user = request.user
    language_id = request.data.get('language_id')
    level_id = request.data.get('level_id')
    num_questions = int(request.data.get('num_questions', 10))  # Default to 10 questions
    
    try:
        language = ProgrammingLanguage.objects.get(id=language_id)
        level = ExpertiseLevel.objects.get(id=level_id)
    except (ProgrammingLanguage.DoesNotExist, ExpertiseLevel.DoesNotExist):
        return Response({'error': 'Invalid language or expertise level'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create a new quiz
    quiz = Quiz.objects.create(
        user=user,
        programming_language=language,
        expertise_level=level,
        total_questions=num_questions
    )
    
    # Get previously answered questions by this user for this language and level
    previous_responses = QuizQuestionResponse.objects.filter(
        quiz__user=user,
        quiz__programming_language=language,
        quiz__expertise_level=level
    )
    
    previously_answered_coding = previous_responses.filter(question_type='coding').values_list('question_id', flat=True)
    previously_answered_theory = previous_responses.filter(question_type='theory').values_list('question_id', flat=True)
    previously_answered_mcq = previous_responses.filter(question_type='mcq').values_list('question_id', flat=True)
    
    # Count available unique questions
    coding_count = QuizQuestion.objects.filter(
        programming_language=language,
        expertise_level=level
    ).exclude(id__in=previously_answered_coding).count()
    
    theory_count = TheoryQuestion.objects.filter(
        programming_language=language,
        expertise_level=level
    ).exclude(id__in=previously_answered_theory).count()
    
    mcq_count = MCQQuestion.objects.filter(
        programming_language=language,
        expertise_level=level
    ).exclude(id__in=previously_answered_mcq).count()
    
    total_available = coding_count + theory_count + mcq_count
    
    # If total available exceeds requested number, cap it
    if total_available > num_questions:
        # We already have more than enough questions, no need to generate more
        print(f"Already have {total_available} questions available, capping at {num_questions}")
        
        # We'll set the actual counts when returning the response
        total_available = num_questions
    # If no questions are available or too few questions, try to generate more
    elif total_available < num_questions:
        print(f"Not enough questions available. Generating more questions for {language.name} ({level.level})...")
        from django.core.management import call_command
        
        # Calculate how many more questions we need
        questions_needed = num_questions - total_available
        
        # Calculate how many questions to generate of each type to reach the exact number needed
        target_per_type = num_questions // 3  # Ideal number of each type
        
        # Calculate how many more of each type we need
        coding_to_generate = max(0, min(questions_needed, target_per_type - coding_count))
        questions_needed -= coding_to_generate
        
        theory_to_generate = max(0, min(questions_needed, target_per_type - theory_count))
        questions_needed -= theory_to_generate
        
        mcq_to_generate = max(0, min(questions_needed, target_per_type - mcq_count))
        questions_needed -= mcq_to_generate
        
        # If we still need more questions, distribute the remaining evenly
        if questions_needed > 0:
            types_to_generate = []
            if coding_count < target_per_type * 2:  # Allow up to 2x the target for any type
                types_to_generate.append('coding')
            if theory_count < target_per_type * 2:
                types_to_generate.append('theory')
            if mcq_count < target_per_type * 2:
                types_to_generate.append('mcq')
            
            # If no types can take more questions, just distribute evenly
            if not types_to_generate:
                types_to_generate = ['coding', 'theory', 'mcq']
            
            # Distribute remaining questions
            while questions_needed > 0 and types_to_generate:
                for q_type in types_to_generate:
                    if questions_needed <= 0:
                        break
                    if q_type == 'coding':
                        coding_to_generate += 1
                    elif q_type == 'theory':
                        theory_to_generate += 1
                    else:  # mcq
                        mcq_to_generate += 1
                    questions_needed -= 1
        
        print(f"Generating additional questions: {coding_to_generate} coding, {theory_to_generate} theory, {mcq_to_generate} MCQ")
        
        # Generate questions of each type for this language and level
        try:
            if coding_to_generate > 0 or theory_to_generate > 0 or mcq_to_generate > 0:
                call_command('generate_questions', 
                            coding=coding_to_generate,
                            theory=theory_to_generate,
                            mcq=mcq_to_generate,
                            language=str(language.id), 
                            level=str(level.id))
            
            # Recalculate available questions after generation
            coding_count = QuizQuestion.objects.filter(
                programming_language=language,
                expertise_level=level
            ).exclude(id__in=previously_answered_coding).count()
            
            theory_count = TheoryQuestion.objects.filter(
                programming_language=language,
                expertise_level=level
            ).exclude(id__in=previously_answered_theory).count()
            
            mcq_count = MCQQuestion.objects.filter(
                programming_language=language,
                expertise_level=level
            ).exclude(id__in=previously_answered_mcq).count()
            
            total_available = min(coding_count + theory_count + mcq_count, num_questions)
            print(f"After generation: {total_available} questions available (capped at {num_questions})")
        except Exception as e:
            print(f"Error generating questions: {e}")
        
    # If still not enough questions after generation
    if total_available == 0:
        quiz.delete()
        return Response({
            'error': 'No questions available for this language and level, and failed to generate new ones',
            'available_questions': {
                'coding': 0,
                'theory': 0,
                'mcq': 0,
                'total': 0
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # If we have questions but fewer than requested
    if total_available < num_questions:
        # Adjust quiz total_questions to match available
        quiz.total_questions = total_available
        quiz.save()
        
        return Response({
            'quiz_id': quiz.id,
            'language': language.name,
            'level': level.level,
            'num_questions': total_available,
            'note': f"Only {total_available} questions available. Quiz created with {total_available} questions instead of {num_questions}.",
            'available_questions': {
                'coding': min(coding_count, total_available // 3 + (total_available % 3 > 0)),
                'theory': min(theory_count, total_available // 3 + (total_available % 3 > 1)),
                'mcq': min(mcq_count, total_available // 3),
                'total': total_available
            }
        }, status=status.HTTP_201_CREATED)
    
    # Calculate the balanced distribution of question types (exactly num_questions total)
    # We want to distribute questions evenly across types, but not exceed the available count for each type
    base_per_type = num_questions // 3
    remainder = num_questions % 3
    
    balanced_coding = min(coding_count, base_per_type + (1 if remainder > 0 else 0))
    balanced_theory = min(theory_count, base_per_type + (1 if remainder > 1 else 0))
    balanced_mcq = min(mcq_count, base_per_type)
    
    # Adjust if we didn't use all questions due to imbalance
    remaining = num_questions - (balanced_coding + balanced_theory + balanced_mcq)
    if remaining > 0:
        if coding_count > balanced_coding:
            additional = min(remaining, coding_count - balanced_coding)
            balanced_coding += additional
            remaining -= additional
        if remaining > 0 and theory_count > balanced_theory:
            additional = min(remaining, theory_count - balanced_theory)
            balanced_theory += additional
            remaining -= additional
        if remaining > 0 and mcq_count > balanced_mcq:
            additional = min(remaining, mcq_count - balanced_mcq)
            balanced_mcq += additional
            remaining -= additional
    
    # Return the quiz information with full requested questions
    return Response({
        'quiz_id': quiz.id,
        'language': language.name,
        'level': level.level,
        'num_questions': num_questions,
        'available_questions': {
            'coding': balanced_coding,
            'theory': balanced_theory,
            'mcq': balanced_mcq,
            'total': balanced_coding + balanced_theory + balanced_mcq
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_next_quiz_question(request, quiz_id):
    user = request.user
    
    try:
        quiz = Quiz.objects.get(id=quiz_id, user=user)
    except Quiz.DoesNotExist:
        return Response({'error': 'Quiz not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # If quiz is already completed, return appropriate message
    if quiz.completed_at is not None:
        return Response({'message': 'Quiz already completed'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get questions already answered in this quiz
    answered_questions = QuizQuestionResponse.objects.filter(quiz=quiz)
    answered_coding = answered_questions.filter(question_type='coding').values_list('question_id', flat=True)
    answered_theory = answered_questions.filter(question_type='theory').values_list('question_id', flat=True)
    answered_mcq = answered_questions.filter(question_type='mcq').values_list('question_id', flat=True)
    
    # Check if we've reached the number of questions for this quiz
    total_answered = answered_questions.count()
    if total_answered >= quiz.total_questions:
        # Auto-complete the quiz if we've answered all questions
        quiz.completed_at = timezone.now()
        quiz.calculate_score()
        quiz.save()
        return Response({
            'message': 'All questions for this quiz have been answered. Quiz has been completed.',
            'score': quiz.score,
            'total_questions': quiz.total_questions
        }, status=status.HTTP_200_OK)
    
    # Get all questions previously answered by this user for this language and level
    previous_quizzes = Quiz.objects.filter(
        user=user,
        programming_language=quiz.programming_language,
        expertise_level=quiz.expertise_level
    ).exclude(id=quiz.id)
    
    previously_answered_coding = QuizQuestionResponse.objects.filter(
        quiz__in=previous_quizzes,
        question_type='coding'
    ).values_list('question_id', flat=True)
    
    previously_answered_theory = QuizQuestionResponse.objects.filter(
        quiz__in=previous_quizzes,
        question_type='theory'
    ).values_list('question_id', flat=True)
    
    previously_answered_mcq = QuizQuestionResponse.objects.filter(
        quiz__in=previous_quizzes,
        question_type='mcq'
    ).values_list('question_id', flat=True)
    
    # Get available questions excluding previously answered ones and ones already in this quiz
    coding_questions = QuizQuestion.objects.filter(
        programming_language=quiz.programming_language,
        expertise_level=quiz.expertise_level
    ).exclude(
        Q(id__in=previously_answered_coding) | Q(id__in=answered_coding)
    )
    
    theory_questions = TheoryQuestion.objects.filter(
        programming_language=quiz.programming_language,
        expertise_level=quiz.expertise_level
    ).exclude(
        Q(id__in=previously_answered_theory) | Q(id__in=answered_theory)
    )
    
    mcq_questions = MCQQuestion.objects.filter(
        programming_language=quiz.programming_language,
        expertise_level=quiz.expertise_level
    ).exclude(
        Q(id__in=previously_answered_mcq) | Q(id__in=answered_mcq)
    )
    
    # Count how many of each type we've answered so far
    coding_answered = answered_coding.count()
    theory_answered = answered_theory.count()
    mcq_answered = answered_mcq.count()
    
    # Calculate how many of each type should be in this quiz (same logic as in create_quiz)
    base_per_type = quiz.total_questions // 3
    remainder = quiz.total_questions % 3
    
    # Calculate the target number of each question type for this quiz
    target_coding = base_per_type + (1 if remainder > 0 else 0)
    target_theory = base_per_type + (1 if remainder > 1 else 0)
    target_mcq = base_per_type
    
    # Choose from available question types, prioritizing the types we need more of
    available_types = []
    
    # Only add a type if we haven't reached our target for that type
    if coding_questions.exists() and coding_answered < target_coding:
        available_types.append('coding')
    if theory_questions.exists() and theory_answered < target_theory:
        available_types.append('theory')
    if mcq_questions.exists() and mcq_answered < target_mcq:
        available_types.append('mcq')
    
    # If we've reached our targets but still need more questions, add any available type
    if not available_types and total_answered < quiz.total_questions:
        if coding_questions.exists():
            available_types.append('coding')
        if theory_questions.exists():
            available_types.append('theory')
        if mcq_questions.exists():
            available_types.append('mcq')
    
    if not available_types:
        # If we've run out of questions, mark the quiz as complete
        if answered_questions.exists():
            quiz.completed_at = timezone.now()
            quiz.calculate_score()
            quiz.save()
            return Response({
                'message': 'No more questions available. Quiz has been completed.',
                'score': quiz.score,
                'total_questions': quiz.total_questions
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No questions available for this quiz'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Prioritize types that are furthest from their target
    if len(available_types) > 1:
        # Calculate how far each type is from its target
        type_distance = {
            'coding': (target_coding - coding_answered) / target_coding if target_coding > 0 else 0,
            'theory': (target_theory - theory_answered) / target_theory if target_theory > 0 else 0,
            'mcq': (target_mcq - mcq_answered) / target_mcq if target_mcq > 0 else 0
        }
        
        # Sort available types by distance from target (descending)
        available_types.sort(key=lambda t: type_distance[t], reverse=True)
        
        # 80% chance to pick the most needed type, 20% chance for random selection
        if random.random() < 0.8:
            question_type = available_types[0]
        else:
            question_type = random.choice(available_types)
    else:
        question_type = available_types[0]
    
    # Select a random question of the chosen type
    if question_type == 'coding':
        question = random.choice(list(coding_questions))
        return Response({
            'question_id': question.id,
            'question_type': 'coding',
            'question_text': question.question_text
        }, status=status.HTTP_200_OK)
    elif question_type == 'theory':
        question = random.choice(list(theory_questions))
        return Response({
            'question_id': question.id,
            'question_type': 'theory',
            'question_text': question.question_text
        }, status=status.HTTP_200_OK)
    elif question_type == 'mcq':
        question = random.choice(list(mcq_questions))
        return Response({
            'question_id': question.id,
            'question_type': 'mcq',
            'question_text': question.question_text,
            'options': {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d
            }
        }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_quiz_answer(request, quiz_id):
    user = request.user
    question_id = request.data.get('question_id')
    question_type = request.data.get('question_type')
    user_answer = request.data.get('answer')
    
    if not question_id or not question_type or not user_answer:
        return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        quiz = Quiz.objects.get(id=quiz_id, user=user)
    except Quiz.DoesNotExist:
        return Response({'error': 'Quiz not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if the quiz is already completed
    if quiz.completed_at is not None:
        return Response({'error': 'Quiz already completed'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if the question has already been answered in this quiz
    if QuizQuestionResponse.objects.filter(quiz=quiz, question_type=question_type, question_id=question_id).exists():
        return Response({'error': 'Question already answered'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate and process the answer based on question type
    evaluation = None
    is_correct = False
    feedback = ""
    
    if question_type == 'coding':
        try:
            question = QuizQuestion.objects.get(id=question_id)
        except QuizQuestion.DoesNotExist:
            return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Use evaluation module for code evaluation
            test_cases = TestCase.objects.filter(question=question)
            evaluation = evaluate_code_answer(
                user_code=user_answer,
                question_text=question.question_text,
                language=quiz.programming_language.name.lower(),
                test_cases=test_cases
            )
            
            is_correct = evaluation['is_correct']
            feedback = evaluation['feedback']
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error in submit_quiz_answer (coding): {error_details}")
            return Response({'error': f'Error evaluating coding answer: {str(e)}'}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    elif question_type == 'theory':
        try:
            question = TheoryQuestion.objects.get(id=question_id)
        except TheoryQuestion.DoesNotExist:
            return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Use evaluation module for theory evaluation
            evaluation = evaluate_theory_answer(
                user_answer=user_answer,
                question_text=question.question_text
            )
            
            is_correct = evaluation['is_correct']
            feedback = evaluation['feedback']
            
        except Exception as e:
            logger.error(f"Error in submit_quiz_answer (theory): {str(e)}")
            return Response({'error': f'Error evaluating theory answer: {str(e)}'}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    elif question_type == 'mcq':
        try:
            question = MCQQuestion.objects.get(id=question_id)
        except MCQQuestion.DoesNotExist:
            return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # For MCQs, simply check against the correct option in the database
        is_correct = user_answer == question.correct_option
        feedback = "Correct Answer" if is_correct else f"Incorrect Answer. The correct answer is {question.correct_option}"
    
    else:
        return Response({'error': 'Invalid question type'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Save the response with scoring fields
    response_data = {
        'quiz': quiz,
        'question_type': question_type,
        'question_id': question_id,
        'user_response': user_answer,
        'is_correct': is_correct,
    }
    
    # Add scoring fields based on question type and evaluation results
    if evaluation:
        response_data['score'] = evaluation.get('score', 0.0)
        
        if question_type == 'coding':
            response_data['code_similarity'] = evaluation.get('code_similarity')
            response_data['code_quality_score'] = evaluation.get('code_quality_score')
            response_data['test_pass_rate'] = evaluation.get('test_pass_rate')
        elif question_type == 'theory':
            response_data['semantic_similarity'] = evaluation.get('semantic_similarity')
    
    response = QuizQuestionResponse.objects.create(**response_data)
    
    # Check if this was the last question in the quiz
    # Count the number of responses for this quiz
    total_responses = QuizQuestionResponse.objects.filter(quiz=quiz).count()
    quiz_auto_complete = False
    quiz_result = None
    
    # If this was the last question based on the quiz's total_questions setting
    if total_responses >= quiz.total_questions:
        # Auto-complete the quiz
        quiz.completed_at = timezone.now()
        quiz.calculate_score()
        quiz.save()
        quiz_auto_complete = True
        
        # Get the quiz completion time (time between first and last question)
        first_response = QuizQuestionResponse.objects.filter(quiz=quiz).order_by('created_at').first()
        last_response = QuizQuestionResponse.objects.filter(quiz=quiz).order_by('-created_at').first()
        
        if first_response and last_response:
            quiz_duration = (last_response.created_at - first_response.created_at).total_seconds()
        else:
            quiz_duration = 0
            
        # Calculate total correct answers
        correct_answers = QuizQuestionResponse.objects.filter(quiz=quiz, is_correct=True).count()
        
        quiz_result = {
            'quiz_id': quiz.id,
            'total_questions': total_responses,
            'correct_answers': correct_answers,
            'score': quiz.score,
            'completed_at': quiz.completed_at,
            'duration_seconds': quiz_duration
        }
    
    # Include quiz completion info in the response if this was the last question
    response_data = {
        'is_correct': is_correct,
        'feedback': feedback
    }
    
    # Add scoring fields to response if evaluation was performed
    if evaluation:
        response_data['score'] = evaluation.get('score', 0.0)
        
        if question_type == 'coding':
            response_data['code_similarity'] = evaluation.get('code_similarity')
            response_data['code_quality_score'] = evaluation.get('code_quality_score')
            response_data['test_pass_rate'] = evaluation.get('test_pass_rate')
        elif question_type == 'theory':
            response_data['semantic_similarity'] = evaluation.get('semantic_similarity')
    
    if quiz_auto_complete:
        response_data['quiz_completed'] = True
        response_data['quiz_result'] = quiz_result
    
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_quiz(request, quiz_id):
    user = request.user
    
    try:
        quiz = Quiz.objects.get(id=quiz_id, user=user)
    except Quiz.DoesNotExist:
        return Response({'error': 'Quiz not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if the quiz is already completed
    if quiz.completed_at is not None:
        return Response({'error': 'Quiz already completed'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Mark the quiz as completed
    quiz.completed_at = timezone.now()
    quiz.calculate_score()
    quiz.save()
    
    # Get the quiz results
    total_questions = quiz.quizquestionresponse_set.count()
    correct_answers = quiz.quizquestionresponse_set.filter(is_correct=True).count()
    
    return Response({
        'quiz_id': quiz.id,
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'score': quiz.score,
        'completed_at': quiz.completed_at
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_history(request):
    user = request.user
    quizzes = Quiz.objects.filter(user=user).order_by('-created_at')
    
    results = []
    for quiz in quizzes:
        total_questions = quiz.quizquestionresponse_set.count()
        correct_answers = quiz.quizquestionresponse_set.filter(is_correct=True).count()
        
        results.append({
            'quiz_id': quiz.id,
            'language': quiz.programming_language.name,
            'level': quiz.expertise_level.level,
            'created_at': quiz.created_at,
            'completed_at': quiz.completed_at,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'score': quiz.score,
            'is_completed': quiz.completed_at is not None
        })
    
    return Response(results, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_details(request, quiz_id):
    user = request.user
    
    try:
        quiz = Quiz.objects.get(id=quiz_id, user=user)
    except Quiz.DoesNotExist:
        return Response({'error': 'Quiz not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get all responses for this quiz
    responses = QuizQuestionResponse.objects.filter(quiz=quiz).order_by('created_at')
    
    # Organize responses by question type
    response_data = []
    for response in responses:
        question_text = ""
        options = None
        
        # Get question details based on type
        if response.question_type == 'coding':
            try:
                question = QuizQuestion.objects.get(id=response.question_id)
                question_text = question.question_text
            except QuizQuestion.DoesNotExist:
                question_text = "Question not found"
                
        elif response.question_type == 'theory':
            try:
                question = TheoryQuestion.objects.get(id=response.question_id)
                question_text = question.question_text
            except TheoryQuestion.DoesNotExist:
                question_text = "Question not found"
                
        elif response.question_type == 'mcq':
            try:
                question = MCQQuestion.objects.get(id=response.question_id)
                question_text = question.question_text
                options = {
                    'A': question.option_a,
                    'B': question.option_b,
                    'C': question.option_c,
                    'D': question.option_d,
                    'correct_option': question.correct_option
                }
            except MCQQuestion.DoesNotExist:
                question_text = "Question not found"
        
        response_data.append({
            'id': response.id,
            'question_type': response.question_type,
            'question_id': response.question_id,
            'question_text': question_text,
            'options': options,
            'user_response': response.user_response,
            'is_correct': response.is_correct,
            'created_at': response.created_at
        })
    
    # Return detailed quiz information
    return Response({
        'quiz_id': quiz.id,
        'language': quiz.programming_language.name,
        'level': quiz.expertise_level.level,
        'created_at': quiz.created_at,
        'completed_at': quiz.completed_at,
        'score': quiz.score,
        'total_questions': quiz.total_questions,
        'score_percentage': quiz.get_score_percentage(),
        'progress': quiz.get_progress(),
        'remaining_questions': quiz.get_remaining_questions(),
        'responses': response_data,
        'is_completed': quiz.completed_at is not None
    }, status=status.HTTP_200_OK)

class GenerateAssignmentView(APIView):
    permission_classes = [IsAuthenticated]

    NUM_CODING = 8
    NUM_THEORY = 2
    MAX_GENERATION_ATTEMPTS = 5 # Max attempts to generate a *single* unique, unseen question

    def post(self, request):
        user = request.user
        language_id = request.data.get('language_id')
        level_id = request.data.get('level_id')

        if not language_id or not level_id:
            return Response({'error': 'language_id and level_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            language = ProgrammingLanguage.objects.get(id=language_id)
            level = ExpertiseLevel.objects.get(id=level_id)
        except ProgrammingLanguage.DoesNotExist:
            return Response({'error': f'ProgrammingLanguage with id {language_id} not found.'}, status=status.HTTP_404_NOT_FOUND)
        except ExpertiseLevel.DoesNotExist:
            return Response({'error': f'ExpertiseLevel with id {level_id} not found.'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
             return Response({'error': 'Invalid ID format for language or level.'}, status=status.HTTP_400_BAD_REQUEST)


        # 1. Get IDs of questions previously seen by the user for this language/level
        # FROM QUIZZES
        quiz_seen_responses = QuizQuestionResponse.objects.filter(
            quiz__user=user,
            quiz__programming_language=language,
            quiz__expertise_level=level
        ).values('question_type', 'question_id')

        seen_coding_ids = {r['question_id'] for r in quiz_seen_responses if r['question_type'] == 'coding'}
        seen_theory_ids = {r['question_id'] for r in quiz_seen_responses if r['question_type'] == 'theory'}

        # --- ADD QUESTIONS SEEN IN PREVIOUS ASSIGNMENTS ---
        assignment_seen_responses = AssignmentResponse.objects.filter(
            assignment__user=user,
            assignment__programming_language=language,
            assignment__expertise_level=level
        ).values('question_type', 'question_id')

        for r in assignment_seen_responses:
            if r['question_type'] == 'coding':
                seen_coding_ids.add(r['question_id'])
            elif r['question_type'] == 'theory':
                seen_theory_ids.add(r['question_id'])
        # --- END ADDITION ---
        
        logger.info(f"User {user.id} has seen {len(seen_coding_ids)} coding and {len(seen_theory_ids)} theory questions (from quizzes and assignments) for {language.name}/{level.level}.")

        # 2. Fetch existing unseen questions from DB
        coding_questions_qs = QuizQuestion.objects.filter(
            programming_language=language,
            expertise_level=level
        ).exclude(id__in=seen_coding_ids)

        theory_questions_qs = TheoryQuestion.objects.filter(
            programming_language=language,
            expertise_level=level
        ).exclude(id__in=seen_theory_ids)

        # Use lists to hold the final questions
        final_coding_questions = list(coding_questions_qs[:self.NUM_CODING])
        final_theory_questions = list(theory_questions_qs[:self.NUM_THEORY])

        needed_coding = self.NUM_CODING - len(final_coding_questions)
        needed_theory = self.NUM_THEORY - len(final_theory_questions)

        logger.info(f"Found {len(final_coding_questions)} existing coding questions. Need to generate {needed_coding}.")
        logger.info(f"Found {len(final_theory_questions)} existing theory questions. Need to generate {needed_theory}.")

        # 3. Generate new questions if needed
        generation_errors = []

        # Generate Coding Questions
        for _ in range(needed_coding):
            generated_question = None
            for attempt in range(self.MAX_GENERATION_ATTEMPTS):
                logger.info(f"Attempt {attempt + 1}/{self.MAX_GENERATION_ATTEMPTS} to generate unique unseen coding question for {language.name}/{level.level}")
                success, result, status_code = generate_coding_question(language, level)

                if success:
                    # Check if the generated question (even if it's a fallback existing one) has been seen
                    if result.id not in seen_coding_ids:
                        generated_question = result
                        seen_coding_ids.add(result.id) # Add to seen set immediately to avoid duplicates in this assignment
                        logger.info(f"Successfully generated unique unseen coding question ID: {result.id}")
                        break # Got a usable question
                    else:
                        logger.warning(f"Generated coding question ID {result.id} was already seen by user {user.id}. Retrying generation...")
                else:
                    # Generation failed entirely for this attempt
                    logger.error(f"Failed to generate coding question on attempt {attempt + 1}: Status {status_code}, Response: {result.data if isinstance(result, Response) else 'N/A'}")
                    # If it's the last attempt, log the final failure
                    if attempt == self.MAX_GENERATION_ATTEMPTS - 1:
                         generation_errors.append(f"Failed to generate a coding question after {self.MAX_GENERATION_ATTEMPTS} attempts.")

            if generated_question:
                final_coding_questions.append(generated_question)
            else:
                logger.error(f"Could not generate a unique unseen coding question after {self.MAX_GENERATION_ATTEMPTS} attempts.")
                # Decide whether to break or continue trying to fill other slots
                # For now, let's record the error and continue for theory questions


        # Generate Theory Questions
        for _ in range(needed_theory):
            generated_question = None
            for attempt in range(self.MAX_GENERATION_ATTEMPTS):
                logger.info(f"Attempt {attempt + 1}/{self.MAX_GENERATION_ATTEMPTS} to generate unique unseen theory question for {language.name}/{level.level}")
                # Assuming generate_theory_question_util follows a similar return pattern (success, result, status_code)
                # We might need to adjust generation_utils if it doesn't
                success, result, status_code = generate_theory_question_util(language, level)

                if success:
                    if result.id not in seen_theory_ids:
                        generated_question = result
                        seen_theory_ids.add(result.id)
                        logger.info(f"Successfully generated unique unseen theory question ID: {result.id}")
                        break
                    else:
                        logger.warning(f"Generated theory question ID {result.id} was already seen by user {user.id}. Retrying generation...")
                else:
                    logger.error(f"Failed to generate theory question on attempt {attempt + 1}: Status {status_code}, Response: {result.data if isinstance(result, Response) else 'N/A'}")
                    if attempt == self.MAX_GENERATION_ATTEMPTS - 1:
                        generation_errors.append(f"Failed to generate a theory question after {self.MAX_GENERATION_ATTEMPTS} attempts.")

            if generated_question:
                final_theory_questions.append(generated_question)
            else:
                logger.error(f"Could not generate a unique unseen theory question after {self.MAX_GENERATION_ATTEMPTS} attempts.")


        # 4. Check if we have enough questions finally
        if len(final_coding_questions) < self.NUM_CODING or len(final_theory_questions) < self.NUM_THEORY:
            error_message = "Failed to generate the required number of questions."
            if generation_errors:
                error_message += " Details: " + "; ".join(generation_errors)
            # Optionally return partial list or error
            # For now, returning an error as the requirement was 8+2
            return Response({
                'error': error_message,
                'coding_questions_found': len(final_coding_questions),
                'theory_questions_found': len(final_theory_questions),
                # Optionally include the partial list here if desired
                # 'coding_questions': QuizQuestionSerializer(final_coding_questions, many=True).data,
                # 'theory_questions': TheoryQuestionSerializer(final_theory_questions, many=True).data,
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) # Or maybe 404/400? 500 suggests server issue


        # 5. Serialize and return the results
        coding_serializer = QuizQuestionSerializer(final_coding_questions, many=True)
        theory_serializer = TheoryQuestionSerializer(final_theory_questions, many=True)

        # <<< NEW: Create the Assignment record >>>
        try:
            assignment = Assignment.objects.create(
                user=user,
                programming_language=language,
                expertise_level=level,
                # score and completed_at are set upon submission
            )
            logger.info(f"Created Assignment {assignment.id} for user {user.id}.")
        except Exception as e:
            logger.error(f"Failed to create Assignment record for user {user.id}: {e}")
            return Response({
                'error': 'Failed to create assignment record after generating questions.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # <<< END NEW >>>

        return Response({
            'assignment_id': assignment.id, # <<< Include assignment ID
            'coding_questions': coding_serializer.data,
            'theory_questions': theory_serializer.data
        }, status=status.HTTP_200_OK)


# <<< NEW ASSIGNMENT SUBMISSION VIEW >>>
class SubmitAssignmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assignment_id):
        user = request.user

        try:
            assignment = Assignment.objects.get(id=assignment_id, user=user)
        except Assignment.DoesNotExist:
            return Response({'error': 'Assignment not found or does not belong to the user.'}, status=status.HTTP_404_NOT_FOUND)

        if assignment.completed_at:
            return Response({'error': 'Assignment has already been submitted and scored.'}, status=status.HTTP_400_BAD_REQUEST)

        submitted_answers = request.data.get('answers') # Expect a list of answer objects
        if not isinstance(submitted_answers, list) or len(submitted_answers) != assignment.total_questions:
            return Response({'error': f'Invalid answers format. Expected a list of {assignment.total_questions} answer objects.'}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Processing submission for Assignment {assignment_id} by user {user.id}.")

        correct_count = 0
        assignment_responses = []
        evaluation_errors = []

        # Pre-fetch API key once
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
             logger.error("OpenAI API key not found during assignment submission.")
             # Decide if we should proceed without LLM checks or return error
             # return Response({'error': 'OpenAI API key not configured.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Evaluate each submitted answer
        for answer_data in submitted_answers:
            question_type = answer_data.get('question_type')
            question_id = answer_data.get('question_id')
            user_response = answer_data.get('answer')

            if not all([question_type, question_id, user_response is not None]): # Allow empty string for answer
                evaluation_errors.append(f"Skipping invalid answer data: {answer_data}")
                continue

            is_correct = False
            feedback = "Evaluation skipped due to error or invalid data."

            try:
                if question_type == 'coding':
                    try:
                        question = QuizQuestion.objects.get(id=question_id,
                                                            programming_language=assignment.programming_language,
                                                            expertise_level=assignment.expertise_level)
                        language_name = assignment.programming_language.name.lower()
                        
                        # LLM Verification (only if API key exists)
                        if api_key:
                            problem_statement_match = re.search(r'Question:\\s*(.+?)(?=Sample Input:|$)', question.question_text, re.DOTALL)
                            problem_statement = problem_statement_match.group(1).strip() if problem_statement_match else question.question_text

                            llm_prompt = (
                                f"You are an AI code checker responsible for evaluating the correctness of submitted code. Your task is to analyze the provided code snippet, determine if it correctly implements a solution to the given problem, and provide helpful feedback. Respond only with the JSON response.\\n"
                                f"### Problem Description:\\n{problem_statement}\\n\\n"
                                f"### Submitted Code ({language_name}):\\n```\\n{user_response}\\n```\\n\\n"
                                f"### Instructions:\\n"
                                f"1. Determine if the code correctly solves the problem based on the problem description and your understanding.\\n"
                                f"2. Use the provided local test case results as a strong reference but not the sole factor if your analysis differs.\\n"
                                f"3. Include brief, constructive feedback about the solution.\\n\\n"
                                f"Respond with a JSON object in the following format:\\n"
                                f"```json\\n"
                                f"{{\\n"
                                f'  "correct": true/false,\\n'
                                f'  "feedback": "Brief explanation of the evaluation result (e.g., issues found, or confirmation of correctness).",\\n'
                                f'  "failed_test_cases": [] // If you identify specific failing logical cases or test inputs based on your analysis, list them here briefly.\\n'
                                f"}}\\n"
                                f"```"
                            )

                            llm_data = {
                                'model': 'gpt-4o-mini',
                                'messages': [
                                    {'role': 'system', 'content': 'You are a code verification assistant that provides accurate and helpful feedback.'},
                                    {'role': 'user', 'content': llm_prompt}
                                ],
                                'temperature': 0,
                                'max_tokens': 1500, 
                                'response_format': {"type": "json_object"}
                            }
                            
                            llm_response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=llm_data, timeout=30)
                            
                            if llm_response.status_code == 200:
                                try:
                                    llm_full_result_text = llm_response.json()['choices'][0]['message']['content'].strip()
                                    clean_llm_result = re.sub(r'```json|```', '', llm_full_result_text).strip()
                                    verification_json = json.loads(clean_llm_result)
                                    
                                    is_correct = verification_json.get('correct', False)
                                    feedback = verification_json.get('feedback', 'No feedback provided by LLM.')
                                except (json.JSONDecodeError, KeyError, IndexError) as json_err:
                                    logger.error(f"Error parsing LLM JSON response for coding Q{question_id}: {json_err} - Response: {llm_response.text}")
                                    is_correct = False # Default to False if LLM response is problematic
                                    feedback = f"Error parsing LLM response. Please review manually."
                            else:
                                logger.error(f"LLM API error for coding Q{question_id}: {llm_response.status_code} - {llm_response.text}")
                                is_correct = False # Default to False on API error
                                feedback = f"LLM API error during evaluation."
                        else: # No API Key
                            is_correct = False # Cannot determine correctness without LLM
                            feedback = f"LLM evaluation skipped: API key not configured."

                    except QuizQuestion.DoesNotExist:
                        feedback = "Coding question not found."
                        evaluation_errors.append(feedback)
                        is_correct = False
                    except Exception as eval_err:
                        logger.error(f"Error evaluating coding Q{question_id} for assignment {assignment_id}: {eval_err}", exc_info=True)
                        feedback = f"Error during evaluation: {eval_err}"
                        evaluation_errors.append(feedback)
                        is_correct = False

                elif question_type == 'theory':
                    try:
                        question = TheoryQuestion.objects.get(id=question_id,
                                                               programming_language=assignment.programming_language,
                                                               expertise_level=assignment.expertise_level)
                        
                        if api_key:
                            prompt = (
                                f"Evaluate correctness. Respond ONLY JSON: {{}}'correct': true/false, 'feedback': 'reason'{{}}\n"
                                f"Question: {question.question_text}\\nAnswer: {user_response}"
                            )
                            llm_data = {
                                'model': 'gpt-4o-mini', 
                                'messages': [{'role': 'user', 'content': prompt}],
                                'temperature': 0.5, 'max_tokens': 500,
                                'response_format': {"type": "json_object"}
                            }
                            
                            llm_response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=llm_data, timeout=30)
                            
                            if llm_response.status_code == 200:
                                try:
                                    llm_full_result_text = llm_response.json()['choices'][0]['message']['content'].strip()
                                    clean_llm_result = re.sub(r'```json|```', '', llm_full_result_text).strip()
                                    verification_json = json.loads(clean_llm_result)
                                    is_correct = verification_json.get('correct', False)
                                    feedback = verification_json.get('feedback', 'No feedback provided by LLM.')
                                except (json.JSONDecodeError, KeyError, IndexError) as json_err:
                                    logger.error(f"Error parsing LLM JSON response for theory Q{question_id}: {json_err} - Response: {llm_response.text}")
                                    feedback = "Error parsing LLM response for theory question."
                                    is_correct = False
                            else:
                                logger.error(f"LLM API error for theory Q{question_id}: {llm_response.status_code} - {llm_response.text}")
                                feedback = "LLM API error during theory evaluation."
                                is_correct = False
                        else: # No API Key
                            feedback = "LLM evaluation for theory question skipped: API key not configured."
                            is_correct = False
                            evaluation_errors.append(f"Skipped theory Q{question_id} evaluation (no API key).")
                    
                    except TheoryQuestion.DoesNotExist:
                        feedback = "Theory question not found."
                        evaluation_errors.append(feedback)
                        is_correct = False
                    except Exception as eval_err:
                        logger.error(f"Error evaluating theory Q{question_id} for assignment {assignment_id}: {eval_err}", exc_info=True)
                        feedback = f"Error during theory evaluation: {eval_err}"
                        evaluation_errors.append(feedback)
                        is_correct = False

                else:
                    feedback = f"Invalid question type '{question_type}' provided."
                    evaluation_errors.append(feedback)
                    is_correct = False
                    # For invalid type, we might not want to save an AssignmentResponse, 
                    # or save it with an error flag. Current logic skips saving by `continue` earlier.
                    # If it reaches here, it means `all([question_type, question_id, user_response is not None])` was true.
                    # So, we should ensure `is_correct` is False and `feedback` indicates the problem.
            
            except Exception as outer_eval_err: 
                 logger.error(f"Unexpected error processing answer for Q{question_id} (type {question_type}) in assignment {assignment_id}: {outer_eval_err}", exc_info=True)
                 feedback = f"Unexpected error during processing: {outer_eval_err}"
                 evaluation_errors.append(feedback)
                 is_correct = False

            # Store the response result, now including feedback
            assignment_responses.append(AssignmentResponse(
                assignment=assignment,
                question_type=question_type,
                question_id=question_id,
                user_response=user_response,
                is_correct=is_correct,
                feedback=feedback  # <-- Save feedback here
            ))
            if is_correct:
                correct_count += 1
        
        # Bulk create responses for efficiency
        try:
            AssignmentResponse.objects.bulk_create(assignment_responses)
            logger.info(f"Saved {len(assignment_responses)} responses for Assignment {assignment_id}.")
        except Exception as bulk_err:
            logger.error(f"Failed to bulk save responses for Assignment {assignment_id}: {bulk_err}")
            # Individual saving fallback could be added here if critical
            return Response({'error': 'Failed to save assignment responses.', 'details': str(bulk_err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Update Assignment score and completion time
        assignment.score = correct_count
        assignment.completed_at = timezone.now()
        assignment.save()
        logger.info(f"Assignment {assignment_id} completed with score {correct_count}/{assignment.total_questions}.")

        # Update UserProgress
        try:
            user_progress, created = UserProgress.objects.get_or_create(user=user)
            # Treat assignment submission as contributing 10 attempts
            user_progress.total_attempts = F('total_attempts') + assignment.total_questions 
            user_progress.correct_answers = F('correct_answers') + correct_count
            # Save first to get updated counts before calculating accuracy
            user_progress.save()
            user_progress.refresh_from_db() # Get the updated values
            # Recalculate accuracy
            if user_progress.total_attempts > 0:
                 user_progress.accuracy = (user_progress.correct_answers / user_progress.total_attempts) * 100.0
            else:
                 user_progress.accuracy = 0.0
            # Note: We are not updating average_time_per_question here, as assignments are submitted bulk
            user_progress.save() 
            logger.info(f"Updated UserProgress for user {user.id}. New accuracy: {user_progress.accuracy:.2f}%")
        except Exception as progress_err:
            logger.error(f"Failed to update UserProgress for user {user.id} after assignment {assignment_id}: {progress_err}")
            # Log error but proceed, scoring the assignment is more critical

        # Prepare response
        final_results = [{
            'question_id': resp.question_id,
            'question_type': resp.question_type,
            'is_correct': resp.is_correct,
            'feedback': resp.feedback # <-- Include feedback in the response
        } for resp in assignment_responses]

        return Response({
            'assignment_id': assignment.id,
            'score': assignment.score,
            'total_questions': assignment.total_questions,
            'results': final_results,
            'evaluation_warnings': evaluation_errors # Return any non-critical errors
        }, status=status.HTTP_200_OK)

# <<< END NEW ASSIGNMENT SUBMISSION VIEW >>>

# <<< NEW ASSIGNMENT RETRIEVAL VIEWS >>>

class AssignmentListView(ListAPIView):
    """Lists all assignments (consider adding IsAdminUser permission later)."""
    queryset = Assignment.objects.select_related(
        'user', 'programming_language', 'expertise_level'
    ).order_by('-created_at')
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated] # Start with authenticated users, can restrict to admin later
    # Note: This serializer includes responses, which might be heavy for a list view.
    # Consider creating a simpler AssignmentListSerializer if performance is an issue.

class MyAssignmentListView(ListAPIView):
    """Lists assignments belonging to the currently authenticated user."""
    serializer_class = AssignmentSerializer # Same serializer, but queryset is filtered
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Assignment.objects.filter(user=user).select_related(
            'user', 'programming_language', 'expertise_level'
        ).order_by('-created_at')
    # Again, consider a simpler list serializer if nested responses are too much data.

class AssignmentDetailView(RetrieveAPIView):
    """Retrieves details of a specific assignment, including responses."""
    queryset = Assignment.objects.select_related(
        'user', 'programming_language', 'expertise_level'
    ).prefetch_related(
        'assignmentresponse_set' # Fetch responses efficiently
    )
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated] # User can only view their own assignments (enforced by lookup field/queryset)

    def get_queryset(self):
        # Ensure users can only retrieve their own assignments by detail view
        user = self.request.user
        return super().get_queryset().filter(user=user)
    
    # The lookup field is 'pk' by default, which corresponds to the assignment ID in the URL

# <<< END NEW ASSIGNMENT RETRIEVAL VIEWS >>>

