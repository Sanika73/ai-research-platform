# AI Research Platform

A comprehensive FastAPI-based research platform that leverages OpenAI's advanced models (O3, O4-Mini) to conduct in-depth research, idea validation, market analysis, and financial assessments.

## 🚀 Features

- **Multi-Model Research**: Support for O3 Deep Research and O4 Mini Deep Research models
- **Research Types**:
  - Custom Research: General-purpose research queries
  - Idea Validation: Comprehensive startup/business idea analysis
  - Market Research: Market analysis and competitive landscape
  - Financial Analysis: Financial feasibility and projections
  - Comprehensive Analysis: All three research types combined
- **Progressive Results**: Real-time updates for comprehensive research
- **Web Interface**: Modern, responsive web UI with live progress tracking
- **Data Persistence**: SQLite database for storing research history
- **Export Options**: Download reports as Markdown files
- **RESTful API**: Complete API for programmatic access

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **AI Models**: OpenAI O3, O4-Mini Deep Research
- **Database**: SQLite with custom ORM
- **Frontend**: HTML/CSS/JavaScript with Alpine.js
- **Styling**: Tailwind CSS
- **API**: RESTful endpoints with automatic documentation

## 📋 Prerequisites

- Python 3.8 or higher
- OpenAI API key with access to research models
- Git (for cloning)

## 🔧 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ai-research-platform.git
   cd ai-research-platform
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r config/requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Initialize the database**:
   ```bash
   python -c "from models.database import init_db; init_db()"
   ```

## 🚀 Usage

### Starting the Server

```bash
python app.py
```

The application will be available at:
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Using the Web Interface

1. Open http://localhost:8000 in your browser
2. Select your preferred research model
3. Choose research type
4. Enter your research query
5. Monitor real-time progress
6. Download or copy results when complete

### API Usage

#### Start a Research Task
```bash
curl -X POST "http://localhost:8000/api/research" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "AI app for construction workers",
       "model": "o3-deep-research",
       "research_type": "comprehensive",
       "enrich_prompt": true
     }'
```

#### Check Task Status
```bash
curl "http://localhost:8000/api/research/{task_id}/status"
```

#### Get Results
```bash
curl "http://localhost:8000/api/research/{task_id}/result"
```

## 📊 Research Types

### 1. Custom Research
General-purpose research for any query with intelligent prompt enrichment.

### 2. Idea Validation
Comprehensive startup/business idea analysis including:
- Market opportunity assessment
- Target audience analysis
- Competition landscape
- Technical feasibility
- Risk assessment

### 3. Market Research
Detailed market analysis covering:
- Market size and growth
- Customer segments
- Competitive analysis
- Market trends
- Entry barriers

### 4. Financial Analysis
Financial feasibility assessment including:
- Revenue projections
- Cost analysis
- Break-even analysis
- Funding requirements
- ROI calculations

### 5. Comprehensive Analysis
Combines all three research types for complete business intelligence.

## 🗂️ Project Structure

```
ai-research-platform/
├── app.py                 # Main FastAPI application
├── config/
│   ├── __init__.py
│   └── requirements.txt   # Python dependencies
├── models/
│   ├── __init__.py
│   └── database.py        # Database models and operations
├── services/
│   ├── __init__.py
│   ├── research_client.py # OpenAI research client
│   ├── storage_service.py # Data persistence layer
│   └── document_manager.py # Document handling
├── research_documents/    # Generated research reports
│   ├── archives/
│   ├── comprehensive_research/
│   ├── custom_research/
│   ├── financial_analysis/
│   ├── idea_validation/
│   ├── market_research/
│   └── metadata/
├── .env                   # Environment variables (create this)
├── .gitignore
└── README.md
```

## 🔌 API Endpoints

### Research Operations
- `POST /api/research` - Start new research task
- `GET /api/research/{task_id}/status` - Get task status
- `GET /api/research/{task_id}/result` - Get completed results
- `GET /api/research/{task_id}/progressive` - Get progressive results
- `GET /api/research/results` - Get all results
- `DELETE /api/research/{task_id}` - Delete research result

### System Operations
- `GET /api/models` - Get available research models
- `GET /api/dashboard/overview` - Dashboard metrics
- `GET /api/dashboard/ideas` - All ideas data
- `GET /health` - Health check

## 🎨 Features in Detail

### Progressive Research Updates
For comprehensive research, the system provides real-time updates as each research phase completes:
1. Idea validation phase
2. Market research phase  
3. Financial analysis phase

### Smart Caching
Results are cached in SQLite database with metadata for quick retrieval and historical analysis.

### Export Options
- Markdown format downloads
- Clipboard copy functionality
- Structured JSON API responses

### Model Selection
Choose between different OpenAI models based on your needs:
- **O3 Deep Research**: Maximum depth and accuracy
- **O4 Mini Deep Research**: Faster, cost-effective option

## 🔧 Configuration

### Environment Variables
```env
OPENAI_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///research_platform.db  # Optional, defaults to local SQLite
DEBUG=false  # Optional, for development
```

### Model Configuration
Models can be configured in `services/research_client.py` with custom parameters for:
- Maximum tool calls
- Timeout settings
- Response formatting

## 🚦 Development

### Running in Development Mode
```bash
# Enable debug mode
export DEBUG=true
python app.py
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Code Structure
The application follows a modular architecture:
- **app.py**: Main FastAPI application and routes
- **services/**: Business logic and external integrations
- **models/**: Data models and database operations
- **config/**: Configuration and dependencies

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/ai-research-platform/issues) page
2. Create a new issue with detailed information
3. Contact the maintainers

## 🎯 Roadmap

- [ ] Integration with additional AI models
- [ ] Advanced data visualization dashboard
- [ ] Export to multiple formats (PDF, DOCX)
- [ ] Collaborative research features
- [ ] API rate limiting and usage analytics
- [ ] Docker containerization
- [ ] Cloud deployment guides

## 📈 Performance

- Typical research completion: 2-5 minutes
- Concurrent request handling: Up to 10 parallel research tasks
- Database: Optimized for quick retrieval with indexing
- Memory usage: ~100MB base + active research tasks

---

**Built with ❤️ using OpenAI's advanced research capabilities**
