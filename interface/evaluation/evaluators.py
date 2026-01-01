"""
Evaluation module for quiz answers.
Provides ML-style evaluation interface using OpenAI backend.
Mimics the structure of ML-based evaluation for easy future migration.
"""
import requests
import json
import re
from django.conf import settings
from interface.models import TestCase
from interface.utils import run_code  # Import from utils to avoid circular import
import logging

logger = logging.getLogger(__name__)


def _get_openai_headers():
    """Get OpenAI API headers"""
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    if not api_key:
        raise ValueError("OpenAI API key not found in settings")
    return {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }


def _call_openai(messages, response_format=None, temperature=0.3, max_tokens=1500):
    """Centralized OpenAI API call with error handling"""
    headers = _get_openai_headers()
    data = {
        'model': 'gpt-4o-mini',
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }
    if response_format:
        data['response_format'] = response_format
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            return {'success': True, 'content': content}
        else:
            logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            return {'success': False, 'error': f"API error: {response.status_code}"}
    except Exception as e:
        logger.error(f"OpenAI API exception: {str(e)}")
        return {'success': False, 'error': str(e)}


def _parse_json(content):
    """Parse JSON from OpenAI response, handling markdown code blocks"""
    try:
        # Remove markdown code blocks if present
        clean = re.sub(r'```json|```', '', content).strip()
        return json.loads(clean)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        logger.debug(f"Content: {content[:200]}")
        return None


def evaluate_theory_answer(user_answer: str, question_text: str) -> dict:
    """
    Evaluate theory answer - returns ML-style metrics using OpenAI
    
    This function mimics the interface of an ML-based evaluator but uses OpenAI
    to generate semantic similarity scores and overall evaluation.
    
    Args:
        user_answer: The student's answer text
        question_text: The theory question text
    
    Returns:
        dict with keys:
            - score: float (0-100) - Overall score
            - semantic_similarity: float (0-1) - Semantic similarity to correct answer
            - feedback: str - Detailed feedback
            - is_correct: bool - Whether answer meets threshold
    """
    prompt = (
        f"You are evaluating a student's answer to a theory question. "
        f"Provide a detailed evaluation with semantic similarity score.\n\n"
        f"Question: {question_text}\n\n"
        f"Student's Answer: {user_answer}\n\n"
        f"Evaluate the answer and respond with ONLY a JSON object in this exact format:\n"
        f'{{\n'
        f'  "score": 85.0,  // Overall score from 0-100\n'
        f'  "semantic_similarity": 0.88,  // Float between 0-1 indicating how semantically similar the answer is to a correct answer\n'
        f'  "feedback": "Your answer correctly explains the concept but misses some details about..."\n'
        f'}}\n\n'
        f"Guidelines:\n"
        f"- semantic_similarity: 0.9-1.0 = excellent match, 0.7-0.89 = good match, 0.5-0.69 = fair match, <0.5 = poor match\n"
        f"- score: Should correlate with semantic_similarity but can be adjusted based on completeness and accuracy\n"
        f"- feedback: Provide constructive feedback explaining what's correct and what could be improved"
    )
    
    messages = [
        {'role': 'system', 'content': 'You are an expert evaluator that provides accurate semantic similarity scores and detailed feedback.'},
        {'role': 'user', 'content': prompt}
    ]
    
    result = _call_openai(
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=1000
    )
    
    if not result['success']:
        logger.error(f"Theory evaluation failed: {result.get('error')}")
        # Fallback: return default scores
        return {
            'score': 0.0,
            'semantic_similarity': 0.0,
            'feedback': 'Evaluation failed. Please try again.',
            'is_correct': False
        }
    
    parsed = _parse_json(result['content'])
    
    if not parsed:
        # Fallback parsing - try to extract scores from text
        return _fallback_parse_theory(result['content'], user_answer)
    
    # Validate and normalize scores
    score = float(parsed.get('score', 0.0))
    semantic_similarity = float(parsed.get('semantic_similarity', 0.0))
    feedback = parsed.get('feedback', 'No feedback provided.')
    
    # Ensure scores are in valid ranges
    score = max(0.0, min(100.0, score))
    semantic_similarity = max(0.0, min(1.0, semantic_similarity))
    
    # Determine is_correct based on threshold
    threshold = getattr(settings, 'EVALUATION_THRESHOLD', 70.0)
    
    return {
        'score': round(score, 2),
        'semantic_similarity': round(semantic_similarity, 4),
        'feedback': feedback,
        'is_correct': score >= threshold
    }


def _fallback_parse_theory(content: str, user_answer: str) -> dict:
    """Fallback parser if JSON parsing fails"""
    # Try to extract scores using regex
    similarity_match = re.search(r'"semantic_similarity":\s*([\d.]+)', content)
    score_match = re.search(r'"score":\s*([\d.]+)', content)
    feedback_match = re.search(r'"feedback":\s*"([^"]+)"', content)
    
    semantic_similarity = float(similarity_match.group(1)) if similarity_match else 0.5
    score = float(score_match.group(1)) if score_match else 50.0
    feedback = feedback_match.group(1) if feedback_match else content[:200]
    
    threshold = getattr(settings, 'EVALUATION_THRESHOLD', 70.0)
    
    return {
        'score': round(max(0.0, min(100.0, score)), 2),
        'semantic_similarity': round(max(0.0, min(1.0, semantic_similarity)), 4),
        'feedback': feedback,
        'is_correct': score >= threshold
    }


def _run_test_cases(user_code: str, test_cases, language: str) -> dict:
    """
    Run test cases and return results
    
    Args:
        user_code: The user's submitted code
        test_cases: QuerySet of TestCase objects
        language: Programming language name
    
    Returns:
        dict with keys:
            - pass_rate: float (0-1)
            - passed_count: int
            - total_count: int
    """
    if not test_cases.exists():
        return {
            'pass_rate': 0.0,
            'passed_count': 0,
            'total_count': 0
        }
    
    passed = 0
    total = test_cases.count()
    
    for test_case in test_cases:
        try:
            if run_code(user_code, test_case.input_data, test_case.expected_output, language):
                passed += 1
        except Exception as e:
            logger.error(f"Test case error: {str(e)}")
    
    pass_rate = passed / total if total > 0 else 0.0
    
    return {
        'pass_rate': round(pass_rate, 4),
        'passed_count': passed,
        'total_count': total
    }


def evaluate_code_answer(user_code: str, question_text: str, language: str, test_cases) -> dict:
    """
    Evaluate code answer - returns ML-style metrics using OpenAI + test cases
    
    This function mimics the interface of an ML-based evaluator but uses OpenAI
    to generate code similarity and quality scores, combined with actual test results.
    
    Args:
        user_code: The student's submitted code
        question_text: The coding question/problem description
        language: Programming language name (e.g., 'python', 'java')
        test_cases: QuerySet of TestCase objects
    
    Returns:
        dict with keys:
            - score: float (0-100) - Final weighted score
            - code_similarity: float (0-1) - Similarity to ideal solution
            - code_quality_score: float (0-1) - Code quality (style, best practices)
            - test_pass_rate: float (0-1) - Test case pass rate
            - feedback: str - Detailed feedback
            - is_correct: bool - Whether answer meets threshold
    """
    # Run actual test cases first
    test_results = _run_test_cases(user_code, test_cases, language)
    
    # Get OpenAI evaluation for similarity and quality
    prompt = (
        f"You are evaluating a code solution. Provide scoring metrics.\n\n"
        f"Problem Description:\n{question_text}\n\n"
        f"Submitted Code ({language}):\n```\n{user_code}\n```\n\n"
        f"Test Results: {test_results['passed_count']}/{test_results['total_count']} test cases passed\n\n"
        f"Evaluate the code and respond with ONLY a JSON object:\n"
        f'{{\n'
        f'  "code_similarity": 0.88,  // Float 0-1: How similar is this code to an ideal solution? (0.9+ = very similar, 0.7-0.89 = similar, 0.5-0.69 = somewhat similar, <0.5 = different approach)\n'
        f'  "code_quality": 0.82,  // Float 0-1: Code quality score considering readability, best practices, efficiency, style (0.9+ = excellent, 0.7-0.89 = good, 0.5-0.69 = fair, <0.5 = poor)\n'
        f'  "feedback": "Brief explanation of the evaluation, including what works well and what could be improved"\n'
        f'}}\n'
    )
    
    messages = [
        {'role': 'system', 'content': 'You are an expert code evaluator that assesses code similarity to ideal solutions and code quality.'},
        {'role': 'user', 'content': prompt}
    ]
    
    result = _call_openai(
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=1000
    )
    
    if not result['success']:
        logger.error(f"Code evaluation failed: {result.get('error')}")
        # Fallback: use test results only
        code_similarity = test_results['pass_rate']
        code_quality = 0.8
        feedback = f"Tests: {test_results['passed_count']}/{test_results['total_count']} passed. OpenAI evaluation unavailable."
    else:
        parsed = _parse_json(result['content'])
        if parsed:
            code_similarity = max(0.0, min(1.0, float(parsed.get('code_similarity', test_results['pass_rate']))))
            code_quality = max(0.0, min(1.0, float(parsed.get('code_quality', 0.8))))
            feedback = parsed.get('feedback', f"Tests: {test_results['passed_count']}/{test_results['total_count']} passed.")
        else:
            # Fallback if parsing fails
            code_similarity = test_results['pass_rate']
            code_quality = 0.8
            feedback = f"Tests: {test_results['passed_count']}/{test_results['total_count']} passed."
    
    # Calculate final score using weighted combination
    weights = getattr(settings, 'CODE_SCORE_WEIGHTS', {
        'test_rate': 0.4,
        'similarity': 0.3,
        'quality': 0.3
    })
    
    final_score = (
        weights['test_rate'] * test_results['pass_rate'] +
        weights['similarity'] * code_similarity +
        weights['quality'] * code_quality
    ) * 100
    
    # Determine is_correct based on threshold
    threshold = getattr(settings, 'EVALUATION_THRESHOLD', 70.0)
    
    return {
        'score': round(final_score, 2),
        'code_similarity': round(code_similarity, 4),
        'code_quality_score': round(code_quality, 4),
        'test_pass_rate': round(test_results['pass_rate'], 4),
        'feedback': feedback,
        'is_correct': final_score >= threshold
    }

