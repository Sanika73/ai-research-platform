#!/usr/bin/env python3
"""
Vercel-compatible FastAPI application for AI Research Platform
Simplified version for serverless deployment
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import os
import uuid
from datetime import datetime

# Create FastAPI app
app = FastAPI(title="AI Research Platform", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage for this session
session_storage = {}

# Try to initialize OpenAI client
openai_client = None
try:
    import openai
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        openai_client = openai.OpenAI(api_key=api_key)
        print("✓ OpenAI client initialized")
    else:
        print("❌ OPENAI_API_KEY not found")
except Exception as e:
    print(f"❌ OpenAI initialization failed: {e}")

class ResearchRequest(BaseModel):
    query: str
    model: str = "gpt-4"
    research_type: str = "custom"
    enrich_prompt: bool = True

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main web interface"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Research Platform - Vercel</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <div x-data="researchApp()" class="container mx-auto px-4 py-8">
            <div class="text-center mb-8">
                <h1 class="text-4xl font-bold text-gray-900 mb-2">AI Research Platform</h1>
                <p class="text-gray-600">Powered by OpenAI on Vercel Serverless</p>
                <div class="mt-2">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        ✓ Serverless Ready
                    </span>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow-md p-6 mb-8">
                <form @submit.prevent="submitResearch()" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Research Query</label>
                        <textarea 
                            x-model="query" 
                            rows="3" 
                            class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Enter your research question...">
                        </textarea>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Model</label>
                        <select x-model="model" class="w-full border border-gray-300 rounded-md px-3 py-2">
                            <option value="gpt-4">GPT-4 (Recommended)</option>
                            <option value="gpt-3.5-turbo">GPT-3.5 Turbo (Faster)</option>
                        </select>
                    </div>

                    <button 
                        type="submit" 
                        :disabled="!query || isLoading"
                        class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50">
                        <span x-show="!isLoading">🔍 Start Research</span>
                        <span x-show="isLoading">⏳ Processing...</span>
                    </button>
                </form>
            </div>

            <div x-show="results.length > 0" class="space-y-6">
                <h2 class="text-2xl font-bold text-gray-900">Research Results</h2>
                <template x-for="result in results" :key="result.task_id">
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <div class="mb-4">
                            <h3 class="text-lg font-semibold text-gray-900" x-text="result.query"></h3>
                            <div class="flex items-center space-x-2 mt-2">
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800" 
                                      x-text="result.model"></span>
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                                      :class="result.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                                      x-text="result.status"></span>
                            </div>
                        </div>
                        
                        <div x-show="result.status === 'completed' && result.content">
                            <div class="prose prose-sm max-w-none bg-gray-50 p-4 rounded">
                                <div x-html="formatContent(result.content)"></div>
                            </div>
                        </div>

                        <div x-show="result.status === 'error'" class="bg-red-50 border border-red-200 rounded-md p-4">
                            <p class="text-red-800 text-sm" x-text="result.error"></p>
                        </div>
                    </div>
                </template>
            </div>
        </div>

        <script>
            function researchApp() {
                return {
                    query: '',
                    model: 'gpt-4',
                    isLoading: false,
                    results: [],

                    async submitResearch() {
                        if (!this.query.trim()) return;
                        
                        this.isLoading = true;
                        try {
                            const response = await fetch('/api/research', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    query: this.query,
                                    model: this.model,
                                    research_type: 'custom'
                                })
                            });

                            const result = await response.json();
                            this.results.unshift(result);
                            this.query = '';
                        } catch (error) {
                            console.error('Error:', error);
                            alert('Research failed: ' + error.message);
                        } finally {
                            this.isLoading = false;
                        }
                    },

                    formatContent(content) {
                        if (!content) return '';
                        return content.replace(/\\n/g, '<br>').replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
                    }
                }
            }
        </script>
    </body>
    </html>
    """

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "platform": "vercel-serverless",
        "openai_available": openai_client is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/models")
async def get_models():
    """Get available models"""
    return {
        "gpt-4": {
            "name": "GPT-4",
            "description": "Most capable model for complex research",
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

@app.post("/api/research")
async def conduct_research(request: ResearchRequest):
    """Conduct research using OpenAI"""
    if not openai_client:
        return {
            "task_id": str(uuid.uuid4()),
            "status": "error",
            "query": request.query,
            "model": request.model,
            "error": "OpenAI client not initialized. Please check API key configuration.",
            "timestamp": datetime.now().isoformat()
        }
    
    task_id = str(uuid.uuid4())
    
    try:
        # Create research prompt based on type
        if request.research_type == "validation":
            prompt = f"Conduct a comprehensive business idea validation analysis for: {request.query}. Include market opportunity, target audience, competition, feasibility, and risks."
        elif request.research_type == "market":
            prompt = f"Perform detailed market research analysis for: {request.query}. Include market size, growth trends, customer segments, competitive landscape, and market entry barriers."
        elif request.research_type == "financial":
            prompt = f"Conduct financial feasibility analysis for: {request.query}. Include revenue projections, cost analysis, break-even analysis, funding requirements, and ROI calculations."
        else:
            prompt = f"Conduct comprehensive research on: {request.query}. Provide detailed analysis with insights, data, and actionable recommendations."

        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model=request.model,
            messages=[
                {"role": "system", "content": "You are an expert research analyst. Provide comprehensive, well-structured analysis with actionable insights. Use clear headings and bullet points for readability."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        
        result = {
            "task_id": task_id,
            "status": "completed",
            "query": request.query,
            "model": request.model,
            "research_type": request.research_type,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
        # Store in session
        session_storage[task_id] = result
        
        return result
        
    except Exception as e:
        error_result = {
            "task_id": task_id,
            "status": "error",
            "query": request.query,
            "model": request.model,
            "research_type": request.research_type,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        session_storage[task_id] = error_result
        return error_result

@app.get("/api/research/{task_id}")
async def get_research_result(task_id: str):
    """Get research result by ID"""
    if task_id in session_storage:
        return session_storage[task_id]
    raise HTTPException(status_code=404, detail="Research result not found")

@app.get("/api/research")
async def get_all_results():
    """Get all research results from current session"""
    return list(session_storage.values())

# This is the entry point for Vercel
# The app variable will be automatically detected by Vercel's Python runtime
