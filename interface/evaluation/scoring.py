"""
Scoring utilities for combining evaluation metrics.
Currently used for code evaluation score combination.
"""
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def final_code_score(test_rate: float, similarity: float, quality: float) -> float:
    """
    Combine code evaluation metrics into final score
    
    Args:
        test_rate: Test pass rate (0-1)
        similarity: Code similarity score (0-1)
        quality: Code quality score (0-1)
    
    Returns:
        float: Final score (0-100)
    """
    # Get weights from settings or use defaults
    weights = getattr(settings, 'CODE_SCORE_WEIGHTS', {
        'test_rate': 0.4,
        'similarity': 0.3,
        'quality': 0.3
    })
    
    # Validate inputs
    test_rate = max(0.0, min(1.0, test_rate))
    similarity = max(0.0, min(1.0, similarity))
    quality = max(0.0, min(1.0, quality))
    
    # Calculate weighted score
    final_score = (
        weights['test_rate'] * test_rate +
        weights['similarity'] * similarity +
        weights['quality'] * quality
    ) * 100
    
    return round(final_score, 2)


def get_is_correct_threshold():
    """Get the threshold for determining is_correct"""
    return getattr(settings, 'EVALUATION_THRESHOLD', 70.0)

