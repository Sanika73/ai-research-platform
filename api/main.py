#!/usr/bin/env python3
"""
Vercel-compatible FastAPI Web Interface for OpenAI Research Client
Full-featured version matching the original app.py
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import asyncio
import uuid
from datetime import datetime
import os
import sys
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Global variables for client and storage
openai_client = None
session_storage = {}

def get_openai_client():
    """Lazy initialization of OpenAI client to avoid startup crashes"""
    global openai_client
    if openai_client is None:
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                # Initialize with minimal configuration for Vercel compatibility
                openai_client = OpenAI(
                    api_key=api_key,
                    timeout=30.0,
                    max_retries=2
                )
        except Exception as e:
            print(f"Failed to initialize OpenAI client: {e}")
            openai_client = False  # Mark as failed to avoid retrying
    return openai_client if openai_client is not False else None

# Try to import services, fallback to simplified versions
try:
    from services.research_client import OpenAIResearchClient, ResearchWorkflow
except ImportError:
    OpenAIResearchClient = None
    ResearchWorkflow = None

app = FastAPI(title="OpenAI Research Interface", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for research tasks
research_tasks = {}
completed_results = {}

# Initialize research client
try:
    if OpenAIResearchClient:
        research_client = OpenAIResearchClient()
        research_workflow = ResearchWorkflow(research_client)
        print("✓ Research client initialized successfully")
    else:
        # Fallback OpenAI client
        import openai
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            research_client = openai.OpenAI(api_key=api_key)
            research_workflow = None
            print("✓ Fallback OpenAI client initialized")
        else:
            research_client = None
            research_workflow = None
            print("❌ OPENAI_API_KEY not found")
except Exception as e:
    print(f"❌ Failed to initialize research client: {e}")
    research_client = None
    research_workflow = None

class ResearchRequest(BaseModel):
    query: str
    model: str = "o3-deep-research"
    research_type: str = "custom"  # custom, validation, market, financial, comprehensive
    enrich_prompt: bool = True

class ResearchStatus(BaseModel):
    task_id: str
    status: str  # pending, running, completed, failed
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

def extract_citations(text: str) -> int:
    """Extract citation count from research text"""
    if not text:
        return 0
    # Count markdown links and various citation formats
    citations = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
    return len(citations)

def format_research_output(result: Dict[str, Any], research_type: str) -> Dict[str, Any]:
    """Format research result for better display"""
    if not result or not result.get("output"):
        return result
    
    output_text = result["output"]
    
    # Extract metadata
    citation_count = extract_citations(output_text)
    word_count = len(output_text.split()) if output_text else 0
    
    # For comprehensive research, format each section
    if research_type == "comprehensive" and isinstance(result, dict):
        formatted_sections = {}
        total_citations = 0
        
        for section_name, section_data in result.items():
            if isinstance(section_data, dict) and section_data.get("output"):
                section_output = section_data["output"]
                section_citations = extract_citations(section_output)
                total_citations += section_citations
                
                formatted_sections[section_name] = {
                    **section_data,
                    "formatted_output": section_output,
                    "citations": section_citations,
                    "word_count": len(section_output.split())
                }
        
        return {
            "type": "comprehensive",
            "sections": formatted_sections,
            "total_citations": total_citations,
            "total_words": sum(s.get("word_count", 0) for s in formatted_sections.values())
        }
    
    # For single research types
    return {
        **result,
        "formatted_output": output_text,
        "citations": citation_count,
        "word_count": word_count
    }

async def conduct_fallback_research(query: str, model: str, research_type: str) -> Dict[str, Any]:
    """Fallback research function using direct OpenAI API"""
    if not research_client or not hasattr(research_client, 'chat'):
        raise Exception("OpenAI client not available")
    
    # Create research prompt based on type
    if research_type == "validation":
        prompt = f"""Conduct a comprehensive business idea validation analysis for: {query}

Please provide a detailed analysis covering:
1. Market Opportunity Assessment
2. Target Audience Analysis  
3. Competition Landscape
4. Technical Feasibility
5. Risk Assessment
6. Implementation Roadmap

Format the response with clear sections and actionable insights."""
    elif research_type == "market":
        prompt = f"""Perform detailed market research analysis for: {query}

Please provide comprehensive analysis covering:
1. Market Size and Growth Trends
2. Customer Segments and Demographics
3. Competitive Landscape Analysis
4. Market Entry Barriers
5. Pricing Strategy Recommendations
6. Market Opportunities and Threats

Format with clear sections and data-driven insights."""
    elif research_type == "financial":
        prompt = f"""Conduct financial feasibility analysis for: {query}

Please provide detailed financial analysis covering:
1. Revenue Projections and Models
2. Cost Analysis and Structure
3. Break-even Analysis
4. Funding Requirements
5. ROI Calculations
6. Financial Risk Assessment

Format with clear sections and numerical projections where applicable."""
    else:
        prompt = f"""Conduct comprehensive research on: {query}

Please provide detailed analysis with:
1. Overview and Context
2. Key Insights and Findings
3. Data and Statistics
4. Trends and Patterns
5. Recommendations and Next Steps
6. Sources and References

Format with clear sections and actionable recommendations."""

    try:
        response = research_client.chat.completions.create(
            model="gpt-4" if model in ["o3-deep-research", "gpt-4"] else "gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert research analyst. Provide comprehensive, well-structured analysis with actionable insights, data, and clear formatting using markdown headers and bullet points."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0.7
        )
        
        return {
            "status": "completed",
            "output": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main web interface - exact replica of original app.py"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OpenAI Research Interface</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <div x-data="researchApp()" class="container mx-auto px-4 py-8">
            <!-- Header -->
            <div class="text-center mb-8">
                <h1 class="text-4xl font-bold text-gray-900 mb-2">OpenAI Research Interface</h1>
                <p class="text-gray-600">Conduct comprehensive research using advanced AI models</p>
            </div>

            <!-- Model Selection & Research Form -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-8">
                <form @submit.prevent="submitResearch()" class="space-y-6">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Select Research Model</label>
                        <select x-model="selectedModel" class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <template x-for="model in models" :key="model.id">
                                <option :value="model.id" x-text="model.name"></option>
                            </template>
                        </select>
                        <div x-show="selectedModelInfo" class="mt-2 p-3 bg-blue-50 rounded-md">
                            <p class="text-sm text-blue-800" x-text="selectedModelInfo?.description"></p>
                            <div class="mt-1 text-xs text-blue-600">
                                <span x-text="'Best for: ' + selectedModelInfo?.best_for"></span> |
                                <span x-text="'Cost: ' + selectedModelInfo?.cost"></span> |
                                <span x-text="'Speed: ' + selectedModelInfo?.speed"></span>
                            </div>
                        </div>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Research Type</label>
                        <select x-model="researchType" class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="custom">Custom Research</option>
                            <option value="validation">Idea Validation</option>
                            <option value="market">Market Research</option>
                            <option value="financial">Financial Analysis</option>
                            <option value="comprehensive">Comprehensive Analysis (All Three)</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Research Query</label>
                        <textarea 
                            x-model="query" 
                            rows="4" 
                            class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Enter your research question or startup idea...">
                        </textarea>
                    </div>

                    <div class="flex items-center">
                        <input type="checkbox" x-model="enrichPrompt" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
                        <label class="ml-2 block text-sm text-gray-700">Enrich prompt automatically (recommended)</label>
                    </div>

                    <button 
                        type="submit" 
                        :disabled="!query || isLoading"
                        class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed">
                        <span x-show="!isLoading">Start Research</span>
                        <span x-show="isLoading">Starting Research...</span>
                    </button>
                </form>
            </div>

            <!-- Research Status -->
            <div x-show="currentTask" class="bg-white rounded-lg shadow-md p-6 mb-8">
                <h3 class="text-lg font-semibold mb-4">Research Progress</h3>
                
                <!-- Progress Steps -->
                <div class="mb-6">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm font-medium">Progress</span>
                        <span class="text-sm text-gray-600" x-text="getProgressPercentage() + '%'"></span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-3">
                        <div class="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-1000 ease-out" 
                             :style="'width: ' + getProgressPercentage() + '%'"></div>
                    </div>
                </div>

                <!-- Current Status -->
                <div class="bg-blue-50 rounded-lg p-4">
                    <div class="flex items-center space-x-2">
                        <div x-show="currentTask?.status === 'running'" class="flex-shrink-0">
                            <div class="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                        </div>
                        <div>
                            <p class="text-sm font-medium text-blue-900" x-text="currentTask?.progress || 'Processing...'"></p>
                            <p class="text-xs text-blue-700">
                                <span x-text="'Model: ' + (currentTask?.model || 'Unknown')"></span> • 
                                <span x-text="'Type: ' + (currentTask?.research_type || 'custom')"></span>
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Research Results -->
            <div x-show="results.length > 0" class="space-y-6">
                <h2 class="text-2xl font-bold text-gray-900">Research Results</h2>
                <template x-for="result in results" :key="result.task_id">
                    <div class="bg-white rounded-lg shadow-md overflow-hidden">
                        <!-- Result Header -->
                        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b">
                            <div class="flex items-center justify-between mb-2">
                                <h3 class="text-lg font-semibold text-gray-900" x-text="result.query"></h3>
                                <div class="flex items-center space-x-2">
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800" 
                                          x-text="result.model"></span>
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800" 
                                          x-text="result.research_type"></span>
                                </div>
                            </div>
                            
                            <!-- Metadata Row -->
                            <div class="flex items-center justify-between text-sm text-gray-600">
                                <div class="flex items-center space-x-4">
                                    <span x-show="result.result?.processing_time_formatted" class="flex items-center space-x-1">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                        </svg>
                                        <span x-text="result.result.processing_time_formatted"></span>
                                    </span>
                                    <span x-show="getCitationCount(result)" class="flex items-center space-x-1">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                        </svg>
                                        <span x-text="getCitationCount(result) + ' citations'"></span>
                                    </span>
                                    <span x-show="getWordCount(result)" class="flex items-center space-x-1">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                                        </svg>
                                        <span x-text="getWordCount(result) + ' words'"></span>
                                    </span>
                                </div>
                                <span class="text-xs" x-text="'Completed: ' + new Date(result.completed_at).toLocaleString()"></span>
                            </div>
                        </div>

                        <!-- Result Content -->
                        <div class="p-6">
                            <div x-show="result.status === 'completed' && result.result">
                                <!-- Comprehensive Research Display -->
                                <div x-show="result.research_type === 'comprehensive'" class="space-y-6">
                                    <template x-for="(section, sectionName) in result.result?.sections || {}" :key="sectionName">
                                        <div class="border border-gray-200 rounded-lg">
                                            <div class="bg-gray-50 px-4 py-3 border-b">
                                                <h4 class="font-medium text-gray-900 capitalize" x-text="sectionName.replace('_', ' ')"></h4>
                                                <div class="flex items-center space-x-3 text-sm text-gray-600 mt-1">
                                                    <span x-show="section.citations" x-text="section.citations + ' citations'"></span>
                                                    <span x-show="section.word_count" x-text="section.word_count + ' words'"></span>
                                                </div>
                                            </div>
                                            <div class="p-4 max-h-64 overflow-y-auto">
                                                <div class="prose prose-sm max-w-none" x-html="formatMarkdown(section.formatted_output || section.output)"></div>
                                            </div>
                                        </div>
                                    </template>
                                </div>

                                <!-- Single Research Display -->
                                <div x-show="result.research_type !== 'comprehensive'" class="max-h-96 overflow-y-auto">
                                    <div class="prose prose-sm max-w-none" x-html="formatMarkdown(result.result?.formatted_output || result.result?.output || formatResult(result.result))"></div>
                                </div>

                                <!-- Action Buttons -->
                                <div class="mt-6 flex space-x-3">
                                    <button 
                                        @click="downloadResult(result)"
                                        class="inline-flex items-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                        </svg>
                                        Download Report
                                    </button>
                                    <button 
                                        @click="copyResult(result)"
                                        class="inline-flex items-center px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                                        </svg>
                                        Copy to Clipboard
                                    </button>
                                </div>
                            </div>

                            <div x-show="result.status === 'failed'" class="bg-red-50 border border-red-200 rounded-md p-4">
                                <div class="flex items-center">
                                    <svg class="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L5.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                                    </svg>
                                    <p class="text-red-800 text-sm font-medium">Research Failed</p>
                                </div>
                                <p class="text-red-700 text-sm mt-1" x-text="result.error"></p>
                            </div>
                        </div>
                    </div>
                </template>
            </div>
        </div>

        <script>
            function researchApp() {
                return {
                    models: [],
                    selectedModel: 'o3-deep-research',
                    researchType: 'custom',
                    query: '',
                    enrichPrompt: true,
                    isLoading: false,
                    currentTask: null,
                    results: [],

                    async init() {
                        await this.loadModels();
                        this.checkPendingTasks();
                        // Poll for updates every 5 seconds
                        setInterval(() => this.checkPendingTasks(), 5000);
                    },

                    get selectedModelInfo() {
                        return this.models.find(m => m.id === this.selectedModel);
                    },

                    async loadModels() {
                        try {
                            console.log('Loading models...');
                            const response = await fetch('/api/models');
                            console.log('Response status:', response.status);
                            if (!response.ok) {
                                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                            }
                            const data = await response.json();
                            console.log('Models data received:', data);
                            this.models = Object.entries(data).map(([id, info]) => ({
                                id,
                                name: info.name,
                                description: info.description,
                                best_for: info.best_for,
                                cost: info.cost,
                                speed: info.speed
                            }));
                            console.log('Models array:', this.models);
                        } catch (error) {
                            console.error('Failed to load models:', error);
                            // Fallback models if API fails
                            this.models = [
                                {
                                    id: 'o3-deep-research',
                                    name: 'O3 Deep Research',
                                    description: 'Most comprehensive research model with advanced reasoning capabilities',
                                    best_for: 'Complex analysis, detailed reports, comprehensive research',
                                    cost: 'Higher',
                                    speed: 'Slower'
                                },
                                {
                                    id: 'o4-mini-deep-research',
                                    name: 'O4 Mini Deep Research',
                                    description: 'Faster, cost-effective research model for quicker insights',
                                    best_for: 'Quick research, initial exploration, cost-sensitive tasks',
                                    cost: 'Lower',
                                    speed: 'Faster'
                                }
                            ];
                        }
                    },

                    async submitResearch() {
                        if (!this.query.trim()) return;

                        this.isLoading = true;
                        try {
                            const response = await fetch('/api/research', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    query: this.query,
                                    model: this.selectedModel,
                                    research_type: this.researchType,
                                    enrich_prompt: this.enrichPrompt
                                })
                            });

                            if (response.ok) {
                                const task = await response.json();
                                this.currentTask = task;
                                this.results.unshift(task);
                                this.query = '';
                            } else {
                                alert('Failed to start research');
                            }
                        } catch (error) {
                            console.error('Error submitting research:', error);
                            alert('Error submitting research');
                        } finally {
                            this.isLoading = false;
                        }
                    },

                    async checkPendingTasks() {
                        // This would normally check for task updates
                        // For now, mark as completed after a few seconds
                    },

                    getProgressPercentage() {
                        if (!this.currentTask) return 0;
                        const status = this.currentTask.status;
                        
                        if (status === 'pending') return 10;
                        if (status === 'running') return 75;
                        if (status === 'completed') return 100;
                        return 0;
                    },

                    getCitationCount(result) {
                        if (result.research_type === 'comprehensive') {
                            return result.result?.total_citations || 0;
                        }
                        return result.result?.citations || 0;
                    },

                    getWordCount(result) {
                        if (result.research_type === 'comprehensive') {
                            return result.result?.total_words || 0;
                        }
                        return result.result?.word_count || 0;
                    },

                    formatMarkdown(text) {
                        if (!text) return '';
                        
                        // Simple markdown to HTML conversion
                        return text
                            .replace(/### (.*?)\\n/g, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>')
                            .replace(/## (.*?)\\n/g, '<h2 class="text-xl font-bold mt-6 mb-3">$1</h2>')
                            .replace(/# (.*?)\\n/g, '<h1 class="text-2xl font-bold mt-8 mb-4">$1</h1>')
                            .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                            .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                            .replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '<a href="$2" class="text-blue-600 underline" target="_blank">$1</a>')
                            .replace(/\\n- (.*?)(?=\\n|$)/g, '\\n<li class="ml-4">$1</li>')
                            .replace(/(<li.*?>.*?<\\/li>)/gs, '<ul class="list-disc ml-6 mb-2">$1</ul>')
                            .replace(/\\n\\n/g, '</p><p class="mb-3">')
                            .replace(/^/, '<p class="mb-3">')
                            .replace(/$/, '</p>');
                    },

                    formatResult(result) {
                        if (typeof result === 'string') return result;
                        if (result?.formatted_output) return result.formatted_output;
                        if (result?.output) return result.output;
                        return JSON.stringify(result, null, 2);
                    },

                    downloadResult(result) {
                        let content = '';
                        
                        if (result.research_type === 'comprehensive') {
                            content = `# Research Report: ${result.query}\\n\\n`;
                            content += `**Model:** ${result.model}\\n`;
                            content += `**Processing Time:** ${result.result?.processing_time_formatted}\\n`;
                            content += `**Total Citations:** ${this.getCitationCount(result)}\\n`;
                            content += `**Total Words:** ${this.getWordCount(result)}\\n\\n`;
                            content += `---\\n\\n`;
                            
                            for (const [sectionName, section] of Object.entries(result.result?.sections || {})) {
                                content += `# ${sectionName.replace('_', ' ').toUpperCase()}\\n\\n`;
                                content += section.formatted_output || section.output || '';
                                content += `\\n\\n---\\n\\n`;
                            }
                        } else {
                            content = `# Research Report: ${result.query}\\n\\n`;
                            content += `**Model:** ${result.model}\\n`;
                            content += `**Type:** ${result.research_type}\\n`;
                            content += `**Processing Time:** ${result.result?.processing_time_formatted}\\n`;
                            content += `**Citations:** ${this.getCitationCount(result)}\\n`;
                            content += `**Words:** ${this.getWordCount(result)}\\n\\n`;
                            content += `---\\n\\n`;
                            content += this.formatResult(result.result);
                        }
                        
                        const blob = new Blob([content], { type: 'text/markdown' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `research_${result.query.substring(0, 30).replace(/[^a-zA-Z0-9]/g, '_')}.md`;
                        a.click();
                        URL.revokeObjectURL(url);
                    },

                    async copyResult(result) {
                        const content = this.formatResult(result.result);
                        try {
                            await navigator.clipboard.writeText(content);
                            alert('Result copied to clipboard!');
                        } catch (error) {
                            console.error('Failed to copy to clipboard:', error);
                        }
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
    client = get_openai_client()
    return {
        "status": "healthy",
        "platform": "vercel-serverless",
        "openai_available": client is not None,
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
    client = get_openai_client()
    if not client:
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
        response = client.chat.completions.create(
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
