import numpy as np
import openai
from openai import OpenAI
from django.conf import settings
from .models import QuestionEmbedding, QuizQuestion, TheoryQuestion, MCQQuestion
from typing import List, Tuple, Optional, Dict, Any
import logging
from django.db import connection

logger = logging.getLogger(__name__)

def get_openai_embedding(text: str) -> List[float]:
    """
    Generate an embedding for the given text using OpenAI's embedding model.
    
    Args:
        text (str): The text to generate an embedding for
        
    Returns:
        List[float]: The embedding vector
        
    Raises:
        Exception: If the OpenAI API call fails
    """
    try:
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            raise ValueError("OpenAI API key not found in settings")
        
        # Initialize the OpenAI client with the API key
        client = OpenAI(api_key=api_key)
        
        # Make API call to OpenAI's embedding endpoint using new client format
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        
        # Extract the embedding from the response (new response format)
        embedding = response.data[0].embedding
        return embedding
    
    except Exception as e:
        logger.error(f"Error generating OpenAI embedding: {str(e)}")
        raise

def calculate_cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate the cosine similarity between two embeddings.
    
    Args:
        embedding1 (List[float]): First embedding vector
        embedding2 (List[float]): Second embedding vector
        
    Returns:
        float: Cosine similarity between the two embeddings (0-1)
    """
    embedding1_np = np.array(embedding1)
    embedding2_np = np.array(embedding2)
    
    # Calculate cosine similarity: dot product / (magnitude of a * magnitude of b)
    dot_product = np.dot(embedding1_np, embedding2_np)
    magnitude1 = np.linalg.norm(embedding1_np)
    magnitude2 = np.linalg.norm(embedding2_np)
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    similarity = dot_product / (magnitude1 * magnitude2)
    return similarity

def find_similar_questions(
    embedding: List[float], 
    question_type: str,
    similarity_threshold: float = 0.87
) -> List[Dict[str, Any]]:
    """
    Find questions similar to the given embedding in the database.
    
    Args:
        embedding (List[float]): The embedding to compare against
        question_type (str): Type of question ('coding', 'theory', or 'mcq')
        similarity_threshold (float): Minimum similarity score to consider a match
        
    Returns:
        List[Dict[str, Any]]: List of similar questions with their similarity scores
    """
    try:
        # Use raw SQL with pgvector extension for optimal performance
        with connection.cursor() as cursor:
            # Convert embedding list to PostgreSQL array string format
            # Using square brackets format instead of curly braces for pgvector compatibility
            embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
            
            # Execute query to find similar questions using cosine similarity
            query = """
            SELECT qe.question_id, qe.question_type, 
                   1 - (qe.embedding <=> %s::vector) as similarity
            FROM question_embeddings qe
            WHERE qe.question_type = %s
              AND 1 - (qe.embedding <=> %s::vector) > %s
            ORDER BY similarity DESC
            LIMIT 5;
            """
            
            cursor.execute(query, [embedding_str, question_type, embedding_str, similarity_threshold])
            similar_questions = []
            
            for row in cursor.fetchall():
                question_id, question_type, similarity = row
                question_text = get_question_text(question_id, question_type)
                
                similar_questions.append({
                    'question_id': question_id,
                    'question_type': question_type,
                    'similarity': similarity,
                    'question_text': question_text
                })
            
            return similar_questions
                
    except Exception as e:
        logger.error(f"Error finding similar questions: {str(e)}")
        # Fall back to Python implementation if pgvector operation fails
        return find_similar_questions_python(embedding, question_type, similarity_threshold)

def find_similar_questions_python(
    embedding: List[float], 
    question_type: str,
    similarity_threshold: float = 0.87
) -> List[Dict[str, Any]]:
    """
    Python implementation of similarity search as fallback if pgvector fails.
    """
    similar_questions = []
    
    embeddings = QuestionEmbedding.objects.filter(question_type=question_type)
    
    for stored_embedding in embeddings:
        if stored_embedding.embedding:
            similarity = calculate_cosine_similarity(embedding, stored_embedding.embedding)
            
            if similarity > similarity_threshold:
                question_text = get_question_text(
                    stored_embedding.question_id, 
                    stored_embedding.question_type
                )
                
                similar_questions.append({
                    'question_id': stored_embedding.question_id,
                    'question_type': stored_embedding.question_type,
                    'similarity': similarity,
                    'question_text': question_text
                })
    
    # Sort by similarity descending
    similar_questions.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_questions[:5]

def get_question_text(question_id: int, question_type: str) -> str:
    """
    Retrieve the text of a question based on its ID and type.
    
    Args:
        question_id (int): ID of the question
        question_type (str): Type of question ('coding', 'theory', or 'mcq')
        
    Returns:
        str: Question text
    """
    try:
        if question_type == 'coding':
            question = QuizQuestion.objects.get(id=question_id)
            return question.question_text
        elif question_type == 'theory':
            question = TheoryQuestion.objects.get(id=question_id)
            return question.question_text
        elif question_type == 'mcq':
            question = MCQQuestion.objects.get(id=question_id)
            return question.question_text
        return "Question not found"
    except Exception as e:
        logger.error(f"Error retrieving question text: {str(e)}")
        return "Question not found"

def is_question_duplicate(question_text: str, question_type: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if a question is semantically similar to existing questions.
    
    Args:
        question_text (str): Text of the question to check
        question_type (str): Type of question ('coding', 'theory', or 'mcq')
        
    Returns:
        Tuple[bool, Dict[str, Any]]: (is_duplicate, most_similar_question)
    """
    try:
        # Generate embedding for the new question
        embedding = get_openai_embedding(question_text)
        
        # Find similar questions
        similar_questions = find_similar_questions(embedding, question_type)
        
        if similar_questions:
            # Most similar question is the first one
            most_similar = similar_questions[0]
            
            # Consider it a duplicate if similarity is above the threshold
            if most_similar['similarity'] > 0.87:  # This threshold can be adjusted
                return True, most_similar
        
        # Not a duplicate
        return False, {}
        
    except Exception as e:
        logger.error(f"Error checking for duplicate questions: {str(e)}")
        # If there's an error, assume it's not a duplicate to be safe
        return False, {}

def store_question_embedding(question_id: int, question_type: str, question_text: str) -> None:
    """
    Generate and store embedding for a question.
    
    Args:
        question_id (int): ID of the question
        question_type (str): Type of question ('coding', 'theory', or 'mcq')
        question_text (str): Text of the question
        
    Returns:
        None
    """
    try:
        # Generate embedding
        embedding = get_openai_embedding(question_text)
        
        # Create or update question embedding
        QuestionEmbedding.objects.update_or_create(
            question_id=question_id,
            question_type=question_type,
            defaults={'embedding': embedding}
        )
        
        logger.info(f"Stored embedding for {question_type} question #{question_id}")
        
    except Exception as e:
        logger.error(f"Error storing question embedding: {str(e)}") 