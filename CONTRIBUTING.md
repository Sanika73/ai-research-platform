# Contributing to AI Research Platform

Thank you for your interest in contributing to the AI Research Platform! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)

## 🤝 Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect different viewpoints and experiences
- Accept responsibility for mistakes and learn from them

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Git
- OpenAI API key (for testing with real API)

### Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/your-username/ai-research-platform.git
   cd ai-research-platform
   ```

2. **Set up development environment**:
   ```bash
   ./setup.sh
   ```

3. **Activate virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

4. **Run tests to ensure everything works**:
   ```bash
   ./dev.sh test
   ```

## 🔄 Development Process

### Branch Naming Convention

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Workflow

1. **Create a new branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Test your changes**:
   ```bash
   ./dev.sh test
   ./dev.sh lint
   ```

4. **Commit your changes** with clear, descriptive messages:
   ```bash
   git add .
   git commit -m "feat: add new research export functionality
   
   - Add CSV export option for research results
   - Implement batch export for multiple results
   - Update UI with export buttons
   
   Closes #123"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** with detailed description

## 📝 Pull Request Process

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] Tests pass (`./dev.sh test`)
- [ ] Code is properly formatted (`./dev.sh format`)
- [ ] Documentation is updated if needed
- [ ] Commit messages are clear and descriptive

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Screenshots (if applicable)

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code where necessary
- [ ] I have made corresponding changes to documentation
- [ ] My changes generate no new warnings
- [ ] Tests pass locally
```

### Review Process

1. **Automated checks** must pass (CI/CD pipeline)
2. **Code review** by at least one maintainer
3. **Testing** on different environments if needed
4. **Approval** from maintainer
5. **Merge** into main branch

## 🎨 Coding Standards

### Python Style

- Follow **PEP 8** style guide
- Use **type hints** where appropriate
- Write **docstrings** for all public functions and classes
- Use **meaningful variable names**
- Keep functions focused and small

### Code Formatting

We use automated formatting tools:

```bash
# Format code
./dev.sh format

# Check formatting
./dev.sh lint
```

### Example Code Style

```python
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ResearchService:
    """Service for handling research operations."""
    
    def __init__(self, api_key: str) -> None:
        """Initialize the research service.
        
        Args:
            api_key: OpenAI API key for authentication
        """
        self.api_key = api_key
        self._client: Optional[OpenAI] = None
    
    async def conduct_research(
        self, 
        query: str, 
        research_type: str = "custom"
    ) -> Dict[str, Any]:
        """Conduct research based on query and type.
        
        Args:
            query: Research question or topic
            research_type: Type of research to conduct
            
        Returns:
            Dictionary containing research results
            
        Raises:
            ValueError: If query is empty or invalid
            APIError: If OpenAI API request fails
        """
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        logger.info(f"Starting {research_type} research for: {query}")
        
        # Implementation here...
        return {"status": "completed", "results": []}
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
./dev.sh test

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Writing Tests

- Write tests for all new functionality
- Use descriptive test names
- Follow the AAA pattern (Arrange, Act, Assert)
- Mock external dependencies (OpenAI API, etc.)

### Test Example

```python
def test_research_request_validation():
    """Test that research requests are properly validated."""
    # Arrange
    client = TestClient(app)
    invalid_request = {"model": "test-model"}  # Missing required 'query'
    
    # Act
    response = client.post("/api/research", json=invalid_request)
    
    # Assert
    assert response.status_code == 422
    assert "query" in response.json()["detail"][0]["loc"]
```

## 📚 Documentation

### Updating Documentation

- Update README.md for major feature changes
- Add docstrings to new functions and classes
- Update API documentation if endpoints change
- Add examples for new features

### Documentation Style

- Use clear, concise language
- Include code examples
- Provide context for why changes were made
- Use markdown formatting consistently

## 🐛 Issue Reporting

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check documentation** for solutions
3. **Test with latest version** if possible

### Issue Template

```markdown
**Bug Report**

**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g. macOS, Ubuntu]
- Python version: [e.g. 3.9.0]
- Project version: [e.g. 1.0.0]

**Additional context**
Any other context about the problem.
```

### Feature Requests

```markdown
**Feature Request**

**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Other solutions you've thought of.

**Additional context**
Any other context about the feature request.
```

## 🏷️ Labels and Priority

### Issue Labels

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements to documentation
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `priority:high` - High priority
- `priority:medium` - Medium priority
- `priority:low` - Low priority

## 🎯 Areas for Contribution

### High Priority
- [ ] Additional AI model integrations
- [ ] Performance optimizations
- [ ] Enhanced error handling
- [ ] Better test coverage

### Medium Priority
- [ ] UI/UX improvements
- [ ] Additional export formats
- [ ] Caching improvements
- [ ] API rate limiting

### Low Priority
- [ ] Code refactoring
- [ ] Documentation improvements
- [ ] Example projects
- [ ] Deployment guides

## ✨ Recognition

Contributors will be recognized in the following ways:

- Added to the `CONTRIBUTORS.md` file
- Mentioned in release notes for significant contributions
- Featured in project documentation for major features

## 📞 Getting Help

If you need help or have questions:

1. **Check the documentation** in the README
2. **Search existing issues** for similar questions
3. **Create a new issue** with the `question` label
4. **Join discussions** in the repository

## 🙏 Thank You

We appreciate all contributions, whether it's:

- Reporting bugs
- Suggesting features
- Writing code
- Improving documentation
- Helping other users

Every contribution makes the project better for everyone!

---

**Happy coding! 🚀**
