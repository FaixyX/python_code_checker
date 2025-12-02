from rest_framework import serializers
from .models import MyUser, ProgrammingLanguage, ExpertiseLevel, QuizQuestion, TheoryQuestion, AssignmentResponse, Assignment


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        exclude = ('email' , 'password')


class UserProfileRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        exclude = ('password', )


class ProgrammingLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgrammingLanguage
        fields = '__all__'


class ExpertiseLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertiseLevel
        fields = '__all__'


class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = ['id', 'question_text', 'programming_language', 'expertise_level', 'created_at']


class TheoryQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TheoryQuestion
        fields = ['id', 'question_text', 'programming_language', 'expertise_level', 'created_at']


class AssignmentResponseSerializer(serializers.ModelSerializer):
    """Serializer for individual responses within an assignment."""
    class Meta:
        model = AssignmentResponse
        fields = ['id', 'question_type', 'question_id', 'user_response', 'is_correct', 'created_at']


class AssignmentSerializer(serializers.ModelSerializer):
    """Serializer for the Assignment model, including nested details."""
    # Use nested serializers for related fields to provide more context
    user = UserProfileRetrieveSerializer(read_only=True) # Use existing user serializer
    programming_language = ProgrammingLanguageSerializer(read_only=True)
    expertise_level = ExpertiseLevelSerializer(read_only=True)
    # Nest responses when retrieving a specific assignment detail
    responses = AssignmentResponseSerializer(many=True, read_only=True, source='assignmentresponse_set')

    class Meta:
        model = Assignment
        fields = [
            'id', 'user', 'programming_language', 'expertise_level', 
            'created_at', 'completed_at', 'score', 'total_questions',
            'responses' # Include the nested responses
        ]
        read_only_fields = ['created_at', 'completed_at', 'score', 'total_questions', 'responses']


class CustomUserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = MyUser
        fields = ('email', 'password', 'first_name', 'last_name')

    def validate_email(self, value):
        """Check if the email already exists."""
        if MyUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def create(self, validated_data):
        user = MyUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
            # is_active is set to True by default by authemail's _create_user
            # is_verified will be False by default from authemail's create_user
        )
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        return user


class ChangePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate_email(self, value):
        """
        Check that the user with this email exists.
        """
        if not MyUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value
