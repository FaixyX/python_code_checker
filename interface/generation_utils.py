import openai
import re
import logging
import requests
from django.conf import settings
from .models import QuizQuestion, TestCase, TheoryQuestion, MCQQuestion
from .embeddings import is_question_duplicate, store_question_embedding
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)

def generate_coding_question(language, level, max_attempts=3):
    """
    Generate a coding question with duplicate detection and handling.
    
    Args:
        language: ProgrammingLanguage model instance
        level: ExpertiseLevel model instance
        max_attempts: Maximum number of attempts to generate a unique question
        
    Returns:
        tuple: (success, response_or_question, status_code)
            - success: Boolean indicating whether generation was successful
            - response_or_question: Either Response object (if failure) or QuizQuestion object (if success)
            - status_code: HTTP status code
    """
    prompt = f"""Generate a high-quality {level.level} coding challenge for {language.name} programming language. 
    
The question should:
1. Test problem-solving skills appropriate for {level.level} level
2. Have a clear problem statement with examples
3. Include sample input and expected output
4. Be solvable with efficient algorithms in {language.name}

Format your response exactly as follows:
```
Question: [Detailed problem statement with clear requirements]

Sample Input:
[Provide sample input that illustrates the problem]

Expected Output:
[Provide expected output for the sample input]

Explanation:
[Brief explanation of the solution approach]
```

The question should be challenging but solvable for a {level.level} programmer."""

    logger.info(f"Generating coding question for {language.name} ({level.level})")
    
    for attempt in range(1, max_attempts + 1):
        logger.info(f"Attempt {attempt} to generate a unique coding question")
        
        try:
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                logger.error("OpenAI API key not found")
                return False, Response({'error': 'OpenAI API key not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR), status.HTTP_500_INTERNAL_SERVER_ERROR

            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            data = {
                'model': 'gpt-4',
                'messages': [
                    {
                        'role': 'system', 
                        'content': 'You are a specialized assistant for creating programming assessments. You create challenging but fair coding questions that test both algorithmic thinking and language-specific knowledge.'
                    },
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.7 + (attempt * 0.1),  # Increase temperature slightly with each attempt
                'max_tokens': 2000,
            }

            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                question_text = result['choices'][0]['message']['content'].strip()
                logger.info(f"Generated question text: {question_text[:100]}...")
                
                # Check for duplicate questions
                try:
                    is_duplicate, similar_question = is_question_duplicate(question_text, 'coding')
                    
                    if is_duplicate:
                        logger.info(f"Generated question is a duplicate (similarity: {similar_question.get('similarity', 0):.4f})")
                        
                        # If this is our last attempt, return the most similar question
                        if attempt >= max_attempts:
                            try:
                                existing_question = QuizQuestion.objects.get(
                                    id=similar_question.get('question_id')
                                )
                                return True, existing_question, 200
                            except QuizQuestion.DoesNotExist:
                                # If the similar question doesn't exist anymore, continue with creating a new one
                                pass
                        
                        # Try again with a different generation
                        continue
                except Exception as e:
                    # If there's an error in duplicate detection, log it but proceed with saving the question
                    logger.error(f"Error in duplicate detection: {str(e)}")
                
                # Create the question
                question = QuizQuestion.objects.create(
                    question_text=question_text,
                    programming_language=language,
                    expertise_level=level
                )
                
                # Store the embedding for future duplicate detection
                try:
                    store_question_embedding(question.id, 'coding', question_text)
                except Exception as embedding_error:
                    logger.error(f"Error storing question embedding: {str(embedding_error)}")
                
                # Try to extract sample input and output to create test case
                try:
                    # Extract sample input and expected output using regex
                    sample_input_match = re.search(r'Sample Input:\s*(.+?)(?=Expected Output:|$)', question_text, re.DOTALL)
                    expected_output_match = re.search(r'Expected Output:\s*(.+?)(?=Explanation:|$)', question_text, re.DOTALL)
                    
                    if sample_input_match and expected_output_match:
                        sample_input = sample_input_match.group(1).strip()
                        expected_output = expected_output_match.group(1).strip()
                        
                        # Create a test case with the sample data
                        TestCase.objects.create(
                            question=question,
                            input_data=sample_input,
                            expected_output=expected_output
                        )
                        logger.info(f"Created test case for question {question.id}")
                except Exception as test_case_error:
                    logger.error(f"Error creating test case: {test_case_error}")
                
                return True, question, 201
            else:
                logger.error(f"OpenAI API Error: {response.status_code}, {response.text}")
                if attempt >= max_attempts:
                    return False, Response({
                        'error': 'Failed to generate question',
                        'details': response.text
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR), status.HTTP_500_INTERNAL_SERVER_ERROR

        except Exception as e:
            logger.error(f"Error during OpenAI API call: {str(e)}")
            
            # If it's the last attempt, use fallback
            if attempt >= max_attempts:
                # Fallback mechanism
                fallback_question = QuizQuestion.objects.filter(
                    programming_language=language,
                    expertise_level=level
                ).order_by('?').first()
                
                if fallback_question:
                    logger.info(f"Using fallback question {fallback_question.id}")
                    return True, fallback_question, 200
                
                logger.error("No fallback question available")
                return False, Response({
                    'error': 'Failed to generate question and no fallback available.',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR), status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # We should not reach here, but just in case
    return False, Response({
        'error': 'Failed to generate a unique question after multiple attempts'
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR), status.HTTP_500_INTERNAL_SERVER_ERROR

def generate_theory_question(language, level, max_attempts=3):
    """
    Generate a theory question with duplicate detection and handling.
    
    Args:
        language: ProgrammingLanguage model instance
        level: ExpertiseLevel model instance
        max_attempts: Maximum number of attempts to generate a unique question
        
    Returns:
        tuple: (success, response_or_question, status_code)
    """
    prompt = (
        f"Generate a high-quality theory question for {level.level} level in {language.name}. "
        f"The question should test conceptual understanding and not require code implementation. "
        f"Format the response EXACTLY as follows: \n"
        f"Question: <question_text>\n"
        f"Model Answer: <detailed explanation that would be considered correct>\n"
    )
    
    logger.info(f"Generating theory question for {language.name} ({level.level})")
    
    for attempt in range(1, max_attempts + 1):
        logger.info(f"Attempt {attempt} to generate a unique theory question")
        
        try:
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                logger.error("OpenAI API key not found")
                return False, Response({'error': 'OpenAI API key not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR), status.HTTP_500_INTERNAL_SERVER_ERROR

            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            data = {
                'model': 'gpt-4o-mini',
                'messages': [
                    {
                        'role': 'system', 
                        'content': 'You are a helpful assistant specialized in creating programming theory assessment questions.'
                    },
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.7 + (attempt * 0.1),
                'max_tokens': 2000,
            }

            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result['choices'][0]['message']['content'].strip()
                
                # Extract the question text and model answer using regex
                question_match = re.search(r"Question:\s*(.+?)(?=Model Answer:|$)", response_text, re.DOTALL)
                answer_match = re.search(r"Model Answer:\s*(.+?)$", response_text, re.DOTALL)
                
                if question_match:
                    question_text = question_match.group(1).strip()
                    model_answer = answer_match.group(1).strip() if answer_match else ""
                    
                    # Check for duplicate questions
                    try:
                        is_duplicate, similar_question = is_question_duplicate(question_text, 'theory')
                        
                        if is_duplicate:
                            logger.info(f"Generated theory question is a duplicate (similarity: {similar_question.get('similarity', 0):.4f})")
                            
                            # If this is our last attempt, return the most similar question
                            if attempt >= max_attempts:
                                try:
                                    existing_question = TheoryQuestion.objects.get(
                                        id=similar_question.get('question_id')
                                    )
                                    return True, existing_question, 200
                                except TheoryQuestion.DoesNotExist:
                                    pass
                            
                            # Try again with a different generation
                            continue
                    except Exception as e:
                        logger.error(f"Error in duplicate detection: {str(e)}")
                    
                    # Create the question
                    theory_question = TheoryQuestion.objects.create(
                        question_text=question_text,
                        programming_language=language,
                        expertise_level=level
                    )
                    
                    # Store the embedding for future duplicate detection
                    try:
                        store_question_embedding(theory_question.id, 'theory', question_text)
                    except Exception as embedding_error:
                        logger.error(f"Error storing question embedding: {str(embedding_error)}")
                    
                    return True, theory_question, 201
                else:
                    # If regex fails, just use the entire response as the question
                    if attempt >= max_attempts:
                        try:
                            theory_question = TheoryQuestion.objects.create(
                                question_text=response_text,
                                programming_language=language,
                                expertise_level=level
                            )
                            
                            # Store the embedding
                            try:
                                store_question_embedding(theory_question.id, 'theory', response_text)
                            except Exception as embedding_error:
                                logger.error(f"Error storing question embedding: {str(embedding_error)}")
                                
                            return True, theory_question, 201
                        except Exception as inner_e:
                            return False, Response({'error': f'Failed to create question: {str(inner_e)}'}, 
                                              status=status.HTTP_500_INTERNAL_SERVER_ERROR), status.HTTP_500_INTERNAL_SERVER_ERROR
            else:
                logger.error(f"OpenAI API Error: {response.status_code}, {response.text}")
                if attempt >= max_attempts:
                    return False, Response({'error': f"OpenAI API error: {response.status_code} - {response.text}"}, 
                                      status=status.HTTP_500_INTERNAL_SERVER_ERROR), status.HTTP_500_INTERNAL_SERVER_ERROR
                                      
        except Exception as e:
            logger.error(f"Error generating theory question: {str(e)}")
            
            if attempt >= max_attempts:
                # Try to find a fallback question
                fallback_question = TheoryQuestion.objects.filter(
                    programming_language=language,
                    expertise_level=level
                ).order_by('?').first()
                
                if fallback_question:
                    return True, fallback_question, 200
                
                return False, Response({'error': f"Error generating theory question: {str(e)}"}, 
                                     status=status.HTTP_500_INTERNAL_SERVER_ERROR), status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return False, Response({'error': 'Failed to generate a unique theory question after multiple attempts'}, 
                         status=status.HTTP_500_INTERNAL_SERVER_ERROR), status.HTTP_500_INTERNAL_SERVER_ERROR

def generate_mcq_question(language, level, max_attempts=3):
    """
    Generate an MCQ with duplicate detection and handling.
    
    Args:
        language: ProgrammingLanguage model instance
        level: ExpertiseLevel model instance
        max_attempts: Maximum number of attempts to generate a unique question
        
    Returns:
        tuple: (success, response_or_question, status_code)
    """
    prompt = (
        f"Generate a high-quality multiple-choice question for {level.level} level in {language.name}. DO NOT include any code snippets in the question. "
        f"Provide four options labeled A, B, C, and D, and specify the correct option. "
        f"Format the response EXACTLY as follows: \n"
        f"Question: <question_text>\n"
        f"Options:\n"
        f"A) <option_1>\n"
        f"B) <option_2>\n"
        f"C) <option_3>\n"
        f"D) <option_4>\n"
        f"Correct Answer: <correct_option>"
    )
    
    logger.info(f"Generating MCQ for {language.name} ({level.level})")
    
    for attempt in range(1, max_attempts + 1):
        logger.info(f"Attempt {attempt} to generate a unique MCQ")
        
        try:
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                logger.error("OpenAI API key not found")
                return False, Response({'error': 'OpenAI API key not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR), status.HTTP_500_INTERNAL_SERVER_ERROR

            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            data = {
                'model': 'gpt-4o-mini',
                'messages': [
                    {
                        'role': 'system', 
                        'content': 'You are a helpful assistant specialized in creating programming assessment questions.'
                    },
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.7 + (attempt * 0.1),
                'max_tokens': 1500,
            }

            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result['choices'][0]['message']['content'].strip()

                # Use regex to extract the question, options, and correct answer
                question_match = re.search(r"Question:\s*(.+?)(?:\n|$)", response_text, re.DOTALL)
                options_matches = {
                    'A': re.search(r"A\)\s*(.+?)(?:\n|$)", response_text, re.DOTALL),
                    'B': re.search(r"B\)\s*(.+?)(?:\n|$)", response_text, re.DOTALL),
                    'C': re.search(r"C\)\s*(.+?)(?:\n|$)", response_text, re.DOTALL),
                    'D': re.search(r"D\)\s*(.+?)(?:\n|$)", response_text, re.DOTALL)
                }
                correct_answer_match = re.search(r"Correct Answer:\s*([A-D])", response_text)

                if question_match and all(options_matches.values()) and correct_answer_match:
                    question_text = question_match.group(1).strip()
                    options = {
                        'A': options_matches['A'].group(1).strip(),
                        'B': options_matches['B'].group(1).strip(),
                        'C': options_matches['C'].group(1).strip(),
                        'D': options_matches['D'].group(1).strip()
                    }
                    correct_option = correct_answer_match.group(1)
                    
                    # Check for duplicate questions
                    try:
                        is_duplicate, similar_question = is_question_duplicate(question_text, 'mcq')
                        
                        if is_duplicate:
                            logger.info(f"Generated MCQ is a duplicate (similarity: {similar_question.get('similarity', 0):.4f})")
                            
                            # If this is our last attempt, return the most similar question
                            if attempt >= max_attempts:
                                try:
                                    existing_question = MCQQuestion.objects.get(
                                        id=similar_question.get('question_id')
                                    )
                                    return True, existing_question, 200
                                except MCQQuestion.DoesNotExist:
                                    pass
                            
                            # Try again with a different generation
                            continue
                    except Exception as e:
                        logger.error(f"Error in duplicate detection: {str(e)}")

                    mcq_question = MCQQuestion.objects.create(
                        question_text=question_text,
                        option_a=options['A'],
                        option_b=options['B'],
                        option_c=options['C'],
                        option_d=options['D'],
                        correct_option=correct_option,
                        programming_language=language,
                        expertise_level=level
                    )
                    
                    # Store the embedding for future duplicate detection
                    try:
                        store_question_embedding(mcq_question.id, 'mcq', question_text)
                    except Exception as embedding_error:
                        logger.error(f"Error storing question embedding: {str(embedding_error)}")
                    
                    return True, mcq_question, 201
                else:
                    logger.error("Failed to parse MCQ response format")
                    if attempt >= max_attempts:
                        return False, Response({'error': 'Failed to parse the response format'}, 
                                            status=status.HTTP_500_INTERNAL_SERVER_ERROR), status.HTTP_500_INTERNAL_SERVER_ERROR
            else:
                logger.error(f"OpenAI API Error: {response.status_code}, {response.text}")
                if attempt >= max_attempts:
                    return False, Response({'error': f"OpenAI API error: {response.status_code} - {response.text}"}, 
                                      status=status.HTTP_500_INTERNAL_SERVER_ERROR), status.HTTP_500_INTERNAL_SERVER_ERROR
        
        except Exception as e:
            logger.error(f"Error generating MCQ question: {str(e)}")
            
            if attempt >= max_attempts:
                # Try to find a fallback question
                fallback_question = MCQQuestion.objects.filter(
                    programming_language=language,
                    expertise_level=level
                ).order_by('?').first()
                
                if fallback_question:
                    return True, fallback_question, 200
                
                return False, Response({'error': f"Error generating MCQ question: {str(e)}"}, 
                                     status=status.HTTP_500_INTERNAL_SERVER_ERROR), status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return False, Response({'error': 'Failed to generate a unique MCQ after multiple attempts'}, 
                         status=status.HTTP_500_INTERNAL_SERVER_ERROR), status.HTTP_500_INTERNAL_SERVER_ERROR 