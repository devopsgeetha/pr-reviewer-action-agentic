"""
Unit tests for review service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.review_service import ReviewService


class TestReviewService:
    """Test cases for ReviewService"""
    
    @pytest.fixture
    def review_service(self):
        """Create review service instance with mocked LLM"""
        with patch('app.services.review_service.LLMService') as mock_llm:
            mock_llm_instance = MagicMock()
            mock_llm.return_value = mock_llm_instance
            service = ReviewService()
            service.llm_service = mock_llm_instance
            return service
    
    @pytest.fixture
    def sample_diff_data(self):
        """Sample diff data for testing"""
        return {
            'pr_number': 123,
            'title': 'Add new feature',
            'description': 'This PR adds a new feature',
            'repository': 'owner/repo',
            'files': [
                {
                    'filename': 'app.py',
                    'patch': 'def hello():\n    print("Hello")',
                    'language': 'python'
                }
            ]
        }
    
    @patch('app.services.review_service.LLMService')
    def test_analyze_code(self, mock_llm_class, review_service, sample_diff_data):
        """Test code analysis"""
        # Mock LLM response
        review_service.llm_service.analyze_code_changes.return_value = {
            'issues': [
                {
                    'severity': 'low',
                    'category': 'style',
                    'message': 'Use single quotes',
                    'file': 'app.py'
                }
            ],
            'suggestions': ['Consider adding docstrings']
        }
        
        review_service.llm_service.generate_summary.return_value = 'Code looks good overall'
        
        # Analyze
        result = review_service.analyze_code(sample_diff_data)
        
        # Assertions
        assert result['pr_number'] == 123
        assert result['repository'] == 'owner/repo'
        assert len(result['issues']) > 0
        assert result['overall_score'] >= 0
        assert result['overall_score'] <= 100
    
    def test_calculate_score(self, review_service):
        """Test score calculation"""
        # No issues - perfect score
        result = {'issues': []}
        score = review_service._calculate_score(result)
        assert score == 100
        
        # High severity issues
        result = {
            'issues': [
                {'severity': 'high'},
                {'severity': 'high'}
            ]
        }
        score = review_service._calculate_score(result)
        assert score == 70  # 100 - (15 * 2)
        
        # Mixed severity
        result = {
            'issues': [
                {'severity': 'high'},
                {'severity': 'medium'},
                {'severity': 'low'}
            ]
        }
        score = review_service._calculate_score(result)
        assert score == 70  # 100 - 15 - 10 - 5
