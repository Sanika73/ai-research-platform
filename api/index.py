#!/usr/bin/env python3
"""
Vercel-compatible FastAPI application for AI Research Platform
This version is adapted for serverless deployment on Vercel
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import os
import uuid
from datetime import datetime
import asyncio

# Import services (will need to adapt for serverless)
try:
    import sys
    import os
    # Add parent directory to path for imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from services.research_client import OpenAIResearchClient, ResearchWorkflow
    from services.vercel_storage import VercelStorageService
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback for development
    OpenAIResearchClient = None
    ResearchWorkflow = None
    VercelStorageService = None

app = FastAPI(title="AI Research Platform", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for research tasks (using environment/external storage for serverless)
storage_service = None

# Initialize research client
try:
    if os.getenv("OPENAI_API_KEY"):
        research_client = OpenAIResearchClient()
        research_workflow = ResearchWorkflow(research_client) if OpenAIResearchClient else None
        storage_service = VercelStorageService() if VercelStorageService else None
        print("✓ Research client initialized for Vercel")
    else:
        research_client = None
        research_workflow = None
        print("❌ OPENAI_API_KEY not found in environment")
except Exception as e:
    print(f"❌ Failed to initialize research client: {e}")
    research_client = None
    research_workflow = None

class ResearchRequest(BaseModel):
    query: str
    model: str = "gpt-4"  # Default to more reliable model for serverless
    research_type: str = "custom"
    enrich_prompt: bool = True

class ResearchStatus(BaseModel):
    task_id: str
    status: str
    created_at: str
    query: str
    model: str
    research_type: str
    progress: Optional[str] = None
    error: Optional[str] = None

class ResearchResult(BaseModel):
    task_id: str
    status: str
    query: str
    model: str
    research_type: str
    result: Optional[Dict[str, Any]] = None
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main web interface"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Research Platform - Deployed on Vercel</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <div x-data="researchApp()" class="container mx-auto px-4 py-8">
            <!-- Header -->
            <div class="text-center mb-8">
                <h1 class="text-4xl font-bold text-gray-900 mb-2">AI Research Platform</h1>
                <p class="text-gray-600">Deployed on Vercel with Serverless Architecture</p>
                <div class="mt-2">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        ✓ Serverless Ready
                    </span>
                </div>
            </div>

            <!-- Quick Research Form -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-8">
                <form @submit.prevent="submitQuickResearch()" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Quick Research Query</label>
                        <textarea 
                            x-model="quickQuery" 
                            rows="3" 
                            class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Enter your research question...">
                        </textarea>
                    </div>

                    <button 
                        type="submit" 
                        :disabled="!quickQuery || isLoading"
                        class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed">
                        <span x-show="!isLoading">🔍 Start Research</span>
                        <span x-show="isLoading">⏳ Processing...</span>
                    </button>
                </form>
            </div>

            <!-- Results Display -->
            <div x-show="results.length > 0" class="space-y-6">
                <h2 class="text-2xl font-bold text-gray-900">Research Results</h2>
                <template x-for="result in results" :key="result.task_id">
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <div class="mb-4">
                            <h3 class="text-lg font-semibold text-gray-900" x-text="result.query"></h3>
                            <div class="flex items-center space-x-2 mt-2">
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800" 
                                      x-text="result.model"></span>
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800" 
                                      x-text="result.status"></span>
                            </div>
                        </div>
                        
                        <div x-show="result.status === 'completed' && result.result">
                            <div class="prose prose-sm max-w-none">
                                <div x-html="formatResult(result.result)"></div>
                            </div>
                        </div>

                        <div x-show="result.status === 'error'" class="bg-red-50 border border-red-200 rounded-md p-4">
                            <p class="text-red-800 text-sm" x-text="result.error"></p>
                        </div>
                    </div>
                </template>
            </div>

            <!-- API Information -->
            <div class="mt-12 bg-blue-50 rounded-lg p-6">
                <h3 class="text-lg font-semibold text-blue-900 mb-4">API Endpoints</h3>
                <div class="space-y-2 text-sm">
                    <div><code class="bg-blue-100 px-2 py-1 rounded">GET /api/health</code> - Health check</div>
                    <div><code class="bg-blue-100 px-2 py-1 rounded">GET /api/models</code> - Available models</div>
                    <div><code class="bg-blue-100 px-2 py-1 rounded">POST /api/research</code> - Start research</div>
                    <div><code class="bg-blue-100 px-2 py-1 rounded">GET /api/research/{id}/status</code> - Check status</div>
                </div>
            </div>
        </div>

        <script>
            function researchApp() {
                return {
                    quickQuery: '',
                    isLoading: false,
                    results: [],

                    async submitQuickResearch() {
                        if (!this.quickQuery.trim()) return;

                        this.isLoading = true;
                        try {
                            const response = await fetch('/api/research', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    query: this.quickQuery,
                                    model: 'gpt-4',
                                    research_type: 'custom',
                                    enrich_prompt: true
                                })
                            });

                            if (response.ok) {
                                const result = await response.json();
                                this.results.unshift(result);
                                this.quickQuery = '';
                            } else {
                                const error = await response.json();
                                alert('Research failed: ' + (error.detail || 'Unknown error'));
                            }
                        } catch (error) {
                            console.error('Error:', error);
                            alert('Network error occurred');
                        } finally {
                            this.isLoading = false;
                        }
                    },

                    formatResult(result) {
                        if (typeof result === 'string') return result.replace(/\\n/g, '<br>');
                        if (result?.output) return result.output.replace(/\\n/g, '<br>');
                        return JSON.stringify(result, null, 2);
                    }
                }
            }
        </script>
    </body>
    </html>
    """

@app.get("/api/health")
async def health_check():
    """Health check endpoint optimized for serverless"""
    return {
        "status": "healthy",
        "platform": "vercel",
        "research_client_initialized": research_client is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/models")
async def get_models():
    """Get available research models"""
    if not research_client:
        # Return default models if client not initialized
        return {
            "gpt-4": {
                "name": "GPT-4",
                "description": "Most capable model for complex research tasks",
                "best_for": "Detailed analysis, comprehensive research",
                "cost": "Higher",
                "speed": "Moderate"
            },
            "gpt-3.5-turbo": {
                "name": "GPT-3.5 Turbo",
                "description": "Fast and efficient for general research",
                "best_for": "Quick research, general queries",
                "cost": "Lower",
                "speed": "Fast"
            }
        }
    
    return research_client.get_available_models()

@app.post("/api/research")
async def start_research(request: ResearchRequest):
    """Start a research task - adapted for serverless"""
    if not research_client or not research_workflow:
        raise HTTPException(status_code=500, detail="Research client not initialized. Please check OPENAI_API_KEY.")
    
    task_id = str(uuid.uuid4())
    
    try:
        # For serverless, we need to handle research synchronously
        # or use external queue system for background processing
        
        if request.research_type == "validation":
            result = research_workflow.validate_idea(request.query, request.model)
        elif request.research_type == "market":
            result = research_workflow.market_research(request.query, request.model)
        elif request.research_type == "financial":
            result = research_workflow.financial_analysis(request.query, request.model)
        else:  # custom research
            result = research_workflow.custom_research(
                request.query, 
                request.model, 
                "general", 
                request.enrich_prompt
            )
        
        # Format result for return
        formatted_result = {
            "task_id": task_id,
            "status": "completed" if result.get("status") == "completed" else "error",
            "query": request.query,
            "model": request.model,
            "research_type": request.research_type,
            "result": result,
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        }
        
        # Store in external storage if available
        if storage_service:
            try:
                if hasattr(storage_service, 'save_result'):
                    if asyncio.iscoroutinefunction(storage_service.save_result):
                        await storage_service.save_result(task_id, formatted_result)
                    else:
                        storage_service.save_result(task_id, formatted_result)
            except Exception as storage_error:
                print(f"Storage error: {storage_error}")
        
        return formatted_result
        
    except Exception as e:
        error_result = {
            "task_id": task_id,
            "status": "error",
            "query": request.query,
            "model": request.model,
            "research_type": request.research_type,
            "created_at": datetime.now().isoformat(),
            "error": str(e)
        }
        return error_result

@app.get("/api/research/{task_id}/status")
async def get_research_status(task_id: str):
    """Get research status - for serverless, results are immediate"""
    if storage_service:
        try:
            if hasattr(storage_service, 'get_result'):
                if asyncio.iscoroutinefunction(storage_service.get_result):
                    result = await storage_service.get_result(task_id)
                else:
                    result = storage_service.get_result(task_id)
                if result:
                    return result
        except Exception as storage_error:
            print(f"Storage retrieval error: {storage_error}")
    
    raise HTTPException(status_code=404, detail="Task not found")

@app.get("/api/research/results")
async def get_all_results():
    """Get all research results"""
    if storage_service:
        try:
            if hasattr(storage_service, 'get_all_results'):
                if asyncio.iscoroutinefunction(storage_service.get_all_results):
                    return await storage_service.get_all_results()
                else:
                    return storage_service.get_all_results()
        except Exception as storage_error:
            print(f"Storage get all error: {storage_error}")
    
    return []

# Export the FastAPI app for Vercel
# Vercel expects the ASGI application to be available at module level
# No need for custom handler function

# For local development
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI Research Platform for Vercel...")
    print("📍 Running locally - will be serverless on Vercel")
    uvicorn.run(app, host="0.0.0.0", port=8000)
