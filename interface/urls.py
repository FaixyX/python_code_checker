from django.urls import path, include
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)
from . import views
from django.urls import reverse_lazy
from django.views.generic import RedirectView
from authemail.views import (PasswordReset, PasswordResetVerified,
                              SignupVerify, PasswordChange)
from authemail.views import Signup
from .views import (UserProfileUpdateView, leaderboard, compare_user_progress, 
                    generate_mcq_question, generate_theory_question, create_quiz, 
                    get_next_quiz_question, submit_quiz_answer, complete_quiz, 
                    get_quiz_history, get_quiz_details, user_submissions, quiz_leaderboard,
                    ProgrammingLanguageListCreateView, ProgrammingLanguageDetailView,
                    ExpertiseLevelListCreateView, ExpertiseLevelDetailView,
                    GenerateAssignmentView, SubmitAssignmentView,
                    AssignmentListView, MyAssignmentListView, AssignmentDetailView, CustomSignupView, ChangePasswordView)

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('signup/verify/', SignupVerify.as_view(), name='signup-verify'),
    path('password/reset/', PasswordReset.as_view(), name='password-reset'),
    path('password/reset/verified/', PasswordResetVerified.as_view(), name='password-reset-verified'),
    path('password/change/', PasswordChange.as_view(), name='password-change'),
    path('accounts/', include('authemail.urls')),
    path('google-login/', views.GoogleLoginView.as_view(), name='google_login'),
    path('google-callback/', views.GoogleCallbackView.as_view(), name='google_callback'),
    path('signup/', Signup.as_view(), name="signup"),
    path('social-auth/', RedirectView.as_view(url=reverse_lazy('social:begin', args=['google-oauth2'])), name='social-auth'),
    path('accounts/', include('authemail.urls')),
    path('update-profile/', UserProfileUpdateView.as_view()),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('sign-up/', CustomSignupView.as_view()),
    
    # Programming Language and Expertise Level CRUD APIs
    path('programming-languages/', ProgrammingLanguageListCreateView.as_view(), name='programming_language_list'),
    path('programming-languages/<int:pk>/', ProgrammingLanguageDetailView.as_view(), name='programming_language_detail'),
    path('expertise-levels/', ExpertiseLevelListCreateView.as_view(), name='expertise_level_list'),
    path('expertise-levels/<int:pk>/', ExpertiseLevelDetailView.as_view(), name='expertise_level_detail'),
    
    # User APIs
    path('generate-quiz-question/', views.generate_quiz_question, name='generate_quiz_question'),
    path('submit-answer/', views.submit_answer, name='submit_answer'),
    path('leaderboard/', leaderboard, name='leaderboard'),
    path('compare/<int:friend_id>/', compare_user_progress, name='compare_user_progress'),
    path('generate-mcq-question/', generate_mcq_question, name='generate_mcq_question'),
    path('generate-theory-question/', generate_theory_question, name='generate_theory_question'),
    path('submit-theory-answer/', views.submit_theory_answer, name='submit_theory_answer'),
    
    # Quiz APIs
    path('create-quiz/', create_quiz, name='create_quiz'),
    path('quiz/<int:quiz_id>/next-question/', get_next_quiz_question, name='get_next_quiz_question'),
    path('quiz/<int:quiz_id>/submit-answer/', submit_quiz_answer, name='submit_quiz_answer'),
    path('quiz/<int:quiz_id>/complete/', complete_quiz, name='complete_quiz'),
    path('quiz/<int:quiz_id>/details/', get_quiz_details, name='get_quiz_details'),
    path('quiz-history/', get_quiz_history, name='get_quiz_history'),
    
    # New Leaderboard and User Submission APIs
    path('quiz-leaderboard/', quiz_leaderboard, name='quiz_leaderboard'),
    path('user-submissions/', user_submissions, name='my_submissions'),
    path('user-submissions/<int:user_id>/', user_submissions, name='user_submissions'),

    # New path for assignment generation
    path('assignments/generate/', GenerateAssignmentView.as_view(), name='generate-assignment'),
    # New path for assignment submission
    path('assignments/<int:assignment_id>/submit/', SubmitAssignmentView.as_view(), name='submit-assignment'),
    # New retrieval paths
    path('assignments/', AssignmentListView.as_view(), name='assignment-list-all'), # Potentially admin only
    path('assignments/my/', MyAssignmentListView.as_view(), name='assignment-list-my'),
    path('assignments/<int:pk>/', AssignmentDetailView.as_view(), name='assignment-detail'), # pk is assignment_id
]
