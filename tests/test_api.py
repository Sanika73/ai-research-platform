"""
Basic tests for AI Research Platform API endpoints
"""

import pytest
from unittest.mock import patch, Mock


def test_health_endpoint(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_home_endpoint(client):
    """Test the home page endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_models_endpoint(client):
    """Test the models endpoint"""
    with patch('services.research_client.OpenAIResearchClient') as mock_client:
        mock_instance = Mock()
        mock_instance.get_available_models.return_value = {
            "o3-deep-research": {
                "name": "O3 Deep Research",
                "description": "Test model"
            }
        }
        mock_client.return_value = mock_instance
        
        response = client.get("/api/models")
        assert response.status_code == 200
        data = response.json()
        assert "o3-deep-research" in data


def test_research_endpoint_validation(client, sample_research_request):
    """Test research endpoint input validation"""
    # Test with missing query
    invalid_request = sample_research_request.copy()
    del invalid_request["query"]
    
    response = client.post("/api/research", json=invalid_request)
    assert response.status_code == 422  # Validation error


def test_research_status_not_found(client):
    """Test research status for non-existent task"""
    response = client.get("/api/research/non-existent-task-id/status")
    assert response.status_code == 404


def test_research_result_not_found(client):
    """Test research result for non-existent task"""
    response = client.get("/api/research/non-existent-task-id/result")
    assert response.status_code == 404


def test_dashboard_endpoints(client):
    """Test dashboard endpoints"""
    response = client.get("/api/dashboard/overview")
    assert response.status_code == 200
    
    response = client.get("/api/dashboard/ideas")
    assert response.status_code == 200
    data = response.json()
    assert "ideas" in data


class TestResearchTypes:
    """Test different research types"""
    
    @pytest.mark.parametrize("research_type", [
        "custom", "validation", "market", "financial", "comprehensive"
    ])
    def test_valid_research_types(self, client, research_type):
        """Test that all research types are accepted"""
        request_data = {
            "query": "Test query",
            "model": "o3-deep-research",
            "research_type": research_type,
            "enrich_prompt": True
        }
        
        with patch('services.research_client.OpenAIResearchClient'):
            with patch('services.research_client.ResearchWorkflow'):
                response = client.post("/api/research", json=request_data)
                # Should not return validation error for research_type
                assert response.status_code != 422 or "research_type" not in response.text


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_extract_citations(self):
        """Test citation extraction function"""
        from app import extract_citations
        
        text_with_citations = """
        This is a research report with [Source 1](http://example.com) and 
        [Another Source](http://example2.com) citations.
        """
        
        citations = extract_citations(text_with_citations)
        assert citations == 2
        
        # Test with no citations
        text_without_citations = "This text has no citations."
        citations = extract_citations(text_without_citations)
        assert citations == 0
    
    def test_format_research_output(self):
        """Test research output formatting"""
        from app import format_research_output
        
        sample_result = {
            "output": "This is sample research output with [citation](http://example.com)"
        }
        
        formatted = format_research_output(sample_result, "custom")
        assert "citations" in formatted
        assert "word_count" in formatted
        assert formatted["citations"] == 1
