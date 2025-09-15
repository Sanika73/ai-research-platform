#!/usr/bin/env python3
"""
OpenAI Research Client - Consolidated Implementation
Combines all research functionality into a single, comprehensive client
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ResearchConfig:
    """Configuration for research requests"""
    model: str = "o3-deep-research"
    background: bool = True
    max_tool_calls: int = 40
    tools: Optional[List[Dict[str, Any]]] = None

class OpenAIResearchClient:
    """
    Comprehensive OpenAI Research API client with all functionality consolidated
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(
            api_key=self.api_key,
            timeout=3600
        )
        
        # Available models for research
        self.available_models = {
            "o3-deep-research": {
                "name": "O3 Deep Research",
                "description": "Most comprehensive research model with advanced reasoning capabilities",
                "best_for": "Complex analysis, detailed reports, comprehensive research",
                "cost": "Higher",
                "speed": "Slower"
            },
            "o4-mini-deep-research": {
                "name": "O4 Mini Deep Research", 
                "description": "Faster, cost-effective research model for quicker insights",
                "best_for": "Quick research, initial exploration, cost-sensitive tasks",
                "cost": "Lower",
                "speed": "Faster"
            }
        }
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get list of available research models with their capabilities"""
        return self.available_models
    
    def create_response(
        self,
        model: str,
        input_text: str,
        background: bool = True,
        tools: Optional[List[Dict[str, Any]]] = None,
        instructions: Optional[str] = None,
        reasoning: Optional[Dict[str, str]] = None,
        max_tool_calls: Optional[int] = None
    ):
        """
        Create a new research response with the specified model and parameters
        """
        request_data = {
            "model": model,
            "input": input_text,
            "background": background
        }
        
        if tools:
            request_data["tools"] = tools
        if instructions:
            request_data["instructions"] = instructions
        if reasoning:
            request_data["reasoning"] = reasoning
        if max_tool_calls:
            request_data["max_tool_calls"] = max_tool_calls
        
        try:
            response = self.client.responses.create(**request_data)
            return response
        except Exception as e:
            print(f"Error creating research response: {e}")
            return None
    
    def get_response(self, response_id: str):
        """Get a specific research response by ID"""
        try:
            return self.client.responses.retrieve(response_id)
        except Exception as e:
            print(f"Error retrieving response {response_id}: {e}")
            return None
    
    def list_responses(self, limit: int = 20, order: str = "desc"):
        """List research responses"""
        try:
            return self.client.responses.list(limit=limit, order=order)
        except Exception as e:
            print(f"Error listing responses: {e}")
            return None
    
    def wait_for_completion(self, response_id: str, check_interval: int = 5, max_wait: int = 3600):
        """Wait for a background research task to complete"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = self.get_response(response_id)
            
            if response and hasattr(response, 'status'):
                if response.status == 'completed':
                    return response
                elif response.status == 'failed':
                    raise Exception(f"Research task failed: {response}")
            
            time.sleep(check_interval)
        
        raise TimeoutError(f"Research task did not complete within {max_wait} seconds")
    
    def enrich_prompt(self, user_request: str, research_type: str = "general") -> str:
        """
        Enrich the user prompt to make it more detailed and specific for deep research
        """
        enrichment_instructions = f"""
        You will be given a research task by a user. Your job is to produce a set of
        instructions for a researcher that will complete the task. Do NOT complete the
        task yourself, just provide instructions on how to complete it.

        RESEARCH TYPE: {research_type}

        GUIDELINES:
        1. **Maximize Specificity and Detail**
        - Include all known user preferences and explicitly list key attributes or dimensions to consider
        - It is of utmost importance that all details from the user are included in the instructions

        2. **Fill in Unstated But Necessary Dimensions as Open-Ended**
        - If certain attributes are essential for a meaningful output but the user has not provided them, 
          explicitly state that they are open-ended or default to no specific constraint

        3. **Avoid Unwarranted Assumptions**
        - If the user has not provided a particular detail, do not invent one
        - Instead, state the lack of specification and guide the researcher to treat it as flexible

        4. **Use the First Person**
        - Phrase the request from the perspective of the user

        5. **Tables and Formatting**
        - If tables would help organize information, explicitly request them
        - Include expected output format with appropriate headers and structure

        6. **Sources**
        - Specify which sources should be prioritized
        - For product research: prefer official brand sites and reputable e-commerce platforms
        - For academic queries: prefer original papers and official journal publications
        - Always request inline citations with full source metadata
        """
        
        try:
            response = self.client.responses.create(
                model="gpt-4.1",
                input=user_request,
                instructions=enrichment_instructions
            )
            return response.output_text if hasattr(response, 'output_text') else user_request
        except Exception as e:
            print(f"Error enriching prompt: {e}")
            return user_request

class ResearchWorkflow:
    """
    Comprehensive research workflows for different types of analysis
    """
    
    def __init__(self, client: OpenAIResearchClient):
        self.client = client
    
    def _prepare_tools(self, use_web_search: bool = True, 
                       use_file_search: bool = False,
                       use_code_interpreter: bool = False,
                       vector_store_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Prepare the tools configuration for research"""
        tools = []
        
        if use_web_search:
            tools.append({"type": "web_search_preview"})
        
        if use_file_search and vector_store_ids:
            tools.append({
                "type": "file_search",
                "vector_store_ids": vector_store_ids
            })
        
        if use_code_interpreter:
            tools.append({
                "type": "code_interpreter",
                "container": {"type": "auto"}
            })
        
        return tools
    
    def validate_idea(self, idea: str, model: str = "o4-mini-deep-research") -> Dict[str, Any]:
        """
        Validate a startup or product idea following the template structure
        """
        validation_prompt = f"""
        You are an idea validation analyst. Analyze the following startup/product idea:

        {idea}

        Provide a comprehensive validation report following this structure:

        ## 1. Idea Restatement
        - Restate the idea clearly in simple terms
        - Define the core problem it is solving
        - Identify the target users/customers
        - Determine whether the idea is a must-have or nice-to-have

        ## 2. Problem Validation
        - Assess whether the problem is significant enough to warrant a solution
        - Evaluate current solutions/alternatives and their limitations
        - Identify pain point severity (low, medium, high)
        - Indicate whether users are actively searching for solutions

        ## 3. Solution Validation
        - Analyze if the proposed solution is realistic and feasible with current technology
        - Identify the unique selling point (USP)
        - Highlight possible technical or adoption challenges
        - Evaluate how well the solution matches the problem

        ## 4. Customer Validation
        - Define customer personas (early adopters, mainstream users)
        - Assess customer willingness to pay
        - Evaluate demand signals (search trends, forums, existing communities)
        - Identify potential early adopter segments

        IMPORTANT: Limit your research to the top 10 most relevant and reliable sources. Focus on quality over quantity for citations and references.
        """
        
        tools = self._prepare_tools(use_web_search=True, use_code_interpreter=True)
        
        response = self.client.create_response(
            model=model,
            input_text=validation_prompt,
            background=True,
            tools=tools
        )
        
        if response and response.id:
            completed_response = self.client.wait_for_completion(response.id)
            return {
                "type": "idea_validation",
                "response_id": response.id,
                "output": completed_response.output_text if hasattr(completed_response, 'output_text') else None,
                "status": "completed"
            }
        
        return {"type": "idea_validation", "status": "failed", "response": response}
    
    def market_research(self, idea: str, model: str = "o3-deep-research") -> Dict[str, Any]:
        """
        Conduct comprehensive market research for a product idea
        """
        market_prompt = f"""
        You are a market research and strategy expert. Conduct comprehensive market research for:

        {idea}

        Generate a detailed market research report with the following sections:

        ## 1. Idea Summary
        - Restate the idea clearly in plain language
        - Define the problem it solves
        - Identify the intended audience or customer segments
        - Classify whether it is B2B, B2C, or B2B2C

        ## 2. Market Overview
        - Estimate market size (TAM, SAM, SOM if possible)
        - Provide growth trends (past 3-5 years + next 5 years projection)
        - Identify key geographic regions driving demand
        - Highlight seasonality or cyclical patterns

        ## 3. Customer & Demand Analysis
        - Define the primary customers or users
        - Identify pain points, needs, and current alternatives
        - Evaluate customer willingness to pay and price sensitivity
        - Note adoption challenges (technical, cultural, behavioral)

        ## 4. Competitive Landscape
        - Identify direct competitors (same solution)
        - Identify indirect competitors (alternative solutions)
        - Identify substitutes (manual or non-digital options)
        - Provide a competitor SWOT analysis
        - Highlight gaps and market opportunities not addressed by current players

        ## 5. Differentiation & Value Proposition
        - Explain what makes this idea unique
        - Identify potential competitive advantages
        - Discuss barriers to entry (IP, network effects, switching costs)

        ## 6. Business Model Potential
        - Suggest possible revenue models
        - Recommend customer acquisition channels
        - Suggest retention strategies

        ## 7. Opportunities & Recommendations
        - Recommend the best initial market entry strategy
        - Suggest a niche or early adopter segment
        - Identify potential partnerships or collaborations
        - Suggest future expansion opportunities

        IMPORTANT: Limit your research to the top 10 most relevant and current sources. Prioritize recent industry reports, credible market research, and authoritative publications.
        """
        
        tools = self._prepare_tools(use_web_search=True, use_code_interpreter=True)
        
        response = self.client.create_response(
            model=model,
            input_text=market_prompt,
            background=True,
            tools=tools,
            max_tool_calls=50
        )
        
        if response and response.id:
            completed_response = self.client.wait_for_completion(response.id)
            return {
                "type": "market_research",
                "response_id": response.id,
                "output": completed_response.output_text if hasattr(completed_response, 'output_text') else None,
                "status": "completed"
            }
        
        return {"type": "market_research", "status": "failed", "response": response}
    
    def financial_analysis(self, idea: str, model: str = "o3-deep-research") -> Dict[str, Any]:
        """
        Conduct comprehensive financial analysis for a startup idea
        """
        finance_prompt = f"""
        You are a finance analyst specializing in startups and product evaluation. 
        Conduct a comprehensive financial analysis for:

        {idea}

        Generate a detailed financial analysis report with the following sections:

        ## 1. Idea Summary
        - Restate the idea briefly in financial context
        - Define the revenue-generating potential of the product/service
        - Clarify whether it is B2B, B2C, or mixed

        ## 2. Market Financial Overview
        - Estimate total addressable revenue opportunity
        - Highlight key financial benchmarks in this industry
        - Compare market financial health (growth rates, margins, capital intensity)

        ## 3. Revenue Model Analysis
        - Outline potential revenue streams
        - Estimate ARPU (Average Revenue per User) or average contract value
        - Suggest possible pricing strategies

        ## 4. Key Metrics & KPIs
        - CAC (Customer Acquisition Cost)
        - LTV (Customer Lifetime Value)
        - Churn rate
        - Gross margin %
        - Burn rate and runway
        - Payback period on CAC

        ## 5. Scenario & Sensitivity Analysis
        - Best-case, base-case, and worst-case financial projections
        - Key assumptions (adoption rate, retention, pricing)
        - Sensitivity of profitability to changes in CAC, retention, pricing, and market growth

        ## 6. Strategic Recommendations
        - Optimal financial strategy for launch
        - Best approach for capital efficiency
        - Recommendations on scaling vs. focusing on niche
        - Steps to reach sustainable profitability

        IMPORTANT: Limit your research to the top 10 most relevant financial sources. Focus on credible industry benchmarks, financial reports, and authoritative business publications.
        """
        
        tools = self._prepare_tools(use_web_search=True, use_code_interpreter=True)
        
        response = self.client.create_response(
            model=model,
            input_text=finance_prompt,
            background=True,
            tools=tools,
            max_tool_calls=50
        )
        
        if response and response.id:
            completed_response = self.client.wait_for_completion(response.id)
            return {
                "type": "financial_analysis",
                "response_id": response.id,
                "output": completed_response.output_text if hasattr(completed_response, 'output_text') else None,
                "status": "completed"
            }
        
        return {"type": "financial_analysis", "status": "failed", "response": response}
    
    def comprehensive_research(self, idea: str, model: str = "o3-deep-research") -> Dict[str, Any]:
        """
        Conduct all three types of research (validation, market, financial) for an idea
        """
        print(f"Starting comprehensive research for: {idea}")
        print("-" * 50)
        
        results = {}
        
        print("1. Starting Idea Validation...")
        validation_result = self.validate_idea(idea, model="o4-mini-deep-research")
        results["validation"] = validation_result
        print(f"   Validation completed. Response ID: {validation_result.get('response_id')}")
        
        print("2. Starting Market Research...")
        market_result = self.market_research(idea, model)
        results["market_research"] = market_result
        print(f"   Market research completed. Response ID: {market_result.get('response_id')}")
        
        print("3. Starting Financial Analysis...")
        financial_result = self.financial_analysis(idea, model)
        results["financial_analysis"] = financial_result
        print(f"   Financial analysis completed. Response ID: {financial_result.get('response_id')}")
        
        print("-" * 50)
        print("Comprehensive research completed!")
        
        return results
    
    def custom_research(self, query: str, model: str = "o3-deep-research", 
                       research_type: str = "general", enrich_prompt: bool = True) -> Dict[str, Any]:
        """
        Conduct custom research with optional prompt enrichment
        """
        research_prompt = query
        
        if enrich_prompt:
            print("Enriching prompt...")
            research_prompt = self.client.enrich_prompt(query, research_type)
        
        tools = self._prepare_tools(use_web_search=True, use_code_interpreter=True)
        
        response = self.client.create_response(
            model=model,
            input_text=research_prompt,
            background=True,
            tools=tools,
            max_tool_calls=40
        )
        
        if response and response.id:
            completed_response = self.client.wait_for_completion(response.id)
            return {
                "type": "custom_research",
                "response_id": response.id,
                "output": completed_response.output_text if hasattr(completed_response, 'output_text') else None,
                "status": "completed",
                "original_query": query,
                "enriched_prompt": research_prompt if enrich_prompt else None
            }
        
        return {"type": "custom_research", "status": "failed", "response": response}

def test_connection():
    """Test the OpenAI API connection and configuration"""
    print("OpenAI Research API Connection Test")
    print("=" * 50)
    
    try:
        client = OpenAIResearchClient()
        print("✓ Research client initialized successfully")
        
        # Test basic API connection
        simple_response = client.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'API connection successful'"}],
            max_tokens=10
        )
        
        if simple_response.choices[0].message.content:
            print("✓ API connection successful")
            print(f"  Response: {simple_response.choices[0].message.content}")
        
        # Show available models
        models = client.get_available_models()
        print("\n✓ Available Research Models:")
        for model_id, info in models.items():
            print(f"  • {info['name']} ({model_id})")
            print(f"    - {info['description']}")
            print(f"    - Best for: {info['best_for']}")
            print(f"    - Cost: {info['cost']}, Speed: {info['speed']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    # Test connection first
    if test_connection():
        print("\n" + "=" * 50)
        print("Ready to use! You can now:")
        print("1. Start the web interface: python app.py")
        print("2. Use the client programmatically")
        print("\nExample usage:")
        print("-" * 30)
        print("""
from research_client import OpenAIResearchClient, ResearchWorkflow

client = OpenAIResearchClient()
workflow = ResearchWorkflow(client)

# Custom research
result = workflow.custom_research(
    "What are the latest AI trends in 2025?",
    model="o4-mini-deep-research"
)
print(result["output"])

# Startup validation
validation = workflow.validate_idea("AI-powered fitness app")
print(validation["output"])
""")
