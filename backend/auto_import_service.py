"""
Advanced Income Tracking System - Auto Import Service
AI-powered SMS/Email transaction parsing with OpenAI GPT-5
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Import Emergent LLM integration
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Import local modules
from database import (
    check_duplicate_transaction, 
    get_user_transaction_patterns,
    get_user_learning_feedback
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoImportService:
    """AI-powered transaction parsing service"""
    
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment variables")
        
        # Income source categories for detection
        self.income_sources = {
            "freelance": ["freelance", "upwork", "fiverr", "freelancer", "project", "gig", "consultation"],
            "salary": ["salary", "wage", "payroll", "employment", "monthly pay", "bi-weekly", "weekly pay"],
            "scholarship": ["scholarship", "grant", "bursary", "fellowship", "education aid", "student aid"],
            "investment": ["dividend", "interest", "investment", "stock", "mutual fund", "sip", "return"],
            "part_time": ["part time", "part-time", "hourly", "temp", "temporary", "casual work"]
        }
        
        # Common transaction patterns
        self.bank_patterns = {
            "amount": [
                r'(?:rs\.?|₹|inr)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:rs\.?|₹|inr)',
                r'amount\s*:?\s*(?:rs\.?|₹|inr)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
            ],
            "merchant": [
                r'at\s+([a-zA-Z0-9\s&.-]+?)(?:\s+on|\s+via|\s*$)',
                r'to\s+([a-zA-Z0-9\s&.-]+?)(?:\s+on|\s+via|\s*$)',
                r'from\s+([a-zA-Z0-9\s&.-]+?)(?:\s+on|\s+via|\s*$)'
            ],
            "date": [
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{2,4})'
            ]
        }

    async def parse_content(self, content: str, content_type: str, user_id: str) -> Dict[str, Any]:
        """
        Parse SMS/Email content using AI to extract transaction information
        """
        try:
            # Get user's transaction patterns for context
            user_patterns = await get_user_transaction_patterns(user_id, days=30)
            user_feedback = await get_user_learning_feedback(user_id, limit=20)
            
            # Create AI chat instance
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"auto_import_{user_id}_{datetime.now().timestamp()}",
                system_message=self._build_system_message(user_patterns, user_feedback)
            ).with_model("openai", "gpt-5")
            
            # Build prompt for transaction parsing
            prompt = self._build_parsing_prompt(content, content_type)
            
            # Send message to AI
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            # Parse AI response
            parsed_data = self._parse_ai_response(response)
            
            # Add confidence scoring
            parsed_data["confidence_score"] = self._calculate_confidence_score(content, parsed_data)
            
            # Add metadata
            parsed_data["processing_metadata"] = {
                "content_type": content_type,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "ai_model": "gpt-5",
                "content_length": len(content)
            }
            
            logger.info(f"Successfully parsed {content_type} content for user {user_id}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing content for user {user_id}: {str(e)}")
            # Fallback to rule-based parsing
            return await self._fallback_parsing(content, content_type)

    def _build_system_message(self, user_patterns: List[Dict], user_feedback: List[Dict]) -> str:
        """Build system message with user context for AI"""
        
        system_msg = """You are an expert AI financial transaction parser for the EarnAura app. 
        Your job is to extract transaction details from SMS and email content with high accuracy.

        CORE TASK: Parse financial transaction content and return structured JSON data.

        INCOME SOURCE CATEGORIES:
        - freelance: Freelance work, gigs, project payments, consultations
        - salary: Regular employment, monthly/bi-weekly wages, payroll
        - scholarship: Educational grants, scholarships, fellowships, student aid
        - investment: Dividends, interest, investment returns, SIP, mutual funds
        - part_time: Part-time work, hourly jobs, temporary employment

        TRANSACTION TYPES:
        - income: Money received (salary, freelance payment, scholarship, etc.)
        - expense: Money spent (purchases, bills, subscriptions, etc.)

        REQUIRED OUTPUT FORMAT:
        {
            "transaction_type": "income" or "expense",
            "amount": <numeric_value>,
            "merchant_or_source": "<entity_name>",
            "description": "<clear_description>",
            "category": "<appropriate_category>",
            "income_source": "<source_type_if_income>",
            "date": "<YYYY-MM-DD>",
            "is_duplicate_likely": true/false,
            "parsing_confidence": 0.0-1.0
        }

        IMPORTANT RULES:
        1. Always return valid JSON
        2. Extract amounts accurately (handle Indian currency format: ₹, Rs., commas)
        3. Identify transaction type correctly (income vs expense)
        4. For income, always classify the source type
        5. Use clear, descriptive language
        6. Set parsing_confidence based on data clarity
        7. Mark is_duplicate_likely as true if transaction seems repetitive"""

        # Add user-specific context if available
        if user_patterns:
            common_categories = [p["_id"]["category"] for p in user_patterns[:5]]
            system_msg += f"\n\nUSER'S COMMON CATEGORIES: {', '.join(common_categories)}"
            
        return system_msg

    def _build_parsing_prompt(self, content: str, content_type: str) -> str:
        """Build specific parsing prompt for the content"""
        
        prompt = f"""Parse this {content_type.upper()} content and extract transaction information:

CONTENT TO PARSE:
---
{content}
---

INSTRUCTIONS:
1. Identify if this is an income or expense transaction
2. Extract the exact amount (handle Indian currency symbols: ₹, Rs.)
3. Identify the merchant/source name
4. Determine appropriate category
5. If income, classify the source type (freelance, salary, scholarship, investment, part_time)
6. Extract or estimate transaction date
7. Write a clear description
8. Assess if this might be a duplicate transaction
9. Rate your parsing confidence (0.0-1.0)

Return ONLY the JSON output as specified in the system message."""

        return prompt

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response and extract JSON data"""
        try:
            # Clean response to extract JSON
            response = response.strip()
            
            # Find JSON content
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON
            parsed_data = json.loads(response)
            
            # Validate required fields
            required_fields = ["transaction_type", "amount", "merchant_or_source", "description"]
            for field in required_fields:
                if field not in parsed_data:
                    raise ValueError(f"Missing required field: {field}")
            
            return parsed_data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.error(f"AI Response: {response}")
            raise ValueError("Invalid AI response format")

    async def _fallback_parsing(self, content: str, content_type: str) -> Dict[str, Any]:
        """Fallback rule-based parsing when AI fails"""
        logger.info("Using fallback rule-based parsing")
        
        parsed_data = {
            "transaction_type": "unknown",
            "amount": 0.0,
            "merchant_or_source": "Unknown",
            "description": content[:100] + "..." if len(content) > 100 else content,
            "category": "Other",
            "income_source": None,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "is_duplicate_likely": False,
            "parsing_confidence": 0.3
        }
        
        # Try to extract amount using regex
        for pattern in self.bank_patterns["amount"]:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    parsed_data["amount"] = float(amount_str)
                    parsed_data["parsing_confidence"] = 0.6
                    break
                except ValueError:
                    continue
        
        # Determine transaction type based on keywords
        income_keywords = ["credit", "received", "salary", "payment", "refund", "cashback"]
        expense_keywords = ["debit", "paid", "purchase", "spent", "withdraw"]
        
        content_lower = content.lower()
        if any(keyword in content_lower for keyword in income_keywords):
            parsed_data["transaction_type"] = "income"
            parsed_data["category"] = "Income"
            # Try to determine income source
            for source, keywords in self.income_sources.items():
                if any(keyword in content_lower for keyword in keywords):
                    parsed_data["income_source"] = source
                    break
        elif any(keyword in content_lower for keyword in expense_keywords):
            parsed_data["transaction_type"] = "expense"
            parsed_data["category"] = "Expense"
        
        return parsed_data

    def _calculate_confidence_score(self, content: str, parsed_data: Dict[str, Any]) -> float:
        """Calculate confidence score for parsed data"""
        confidence = 0.0
        
        # Base confidence from AI
        if "parsing_confidence" in parsed_data:
            confidence = parsed_data["parsing_confidence"]
        
        # Adjust confidence based on data quality
        if parsed_data.get("amount", 0) > 0:
            confidence += 0.2
        
        if parsed_data.get("merchant_or_source") and parsed_data["merchant_or_source"] != "Unknown":
            confidence += 0.2
        
        if parsed_data.get("transaction_type") in ["income", "expense"]:
            confidence += 0.1
        
        # Cap confidence at 1.0
        return min(confidence, 1.0)

    async def detect_duplicates(self, user_id: str, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect potential duplicate transactions"""
        try:
            amount = parsed_data.get("amount", 0)
            if amount <= 0:
                return []
            
            # Check for duplicates in different time windows
            potential_duplicates = []
            
            # Check last 24 hours
            recent_transactions = await check_duplicate_transaction(user_id, amount, 24)
            if recent_transactions:
                potential_duplicates.extend([
                    {
                        **tx,
                        "duplicate_reason": "Same amount within 24 hours",
                        "similarity_score": 0.9
                    } for tx in recent_transactions
                ])
            
            # Check last week for similar amounts (within 10% range)
            amount_range = amount * 0.1  # 10% tolerance
            week_transactions = await check_duplicate_transaction(user_id, amount, 168)  # 7 days
            
            for tx in week_transactions:
                if abs(tx["amount"] - amount) <= amount_range:
                    potential_duplicates.append({
                        **tx,
                        "duplicate_reason": "Similar amount within 1 week",
                        "similarity_score": 0.7
                    })
            
            return potential_duplicates
            
        except Exception as e:
            logger.error(f"Error detecting duplicates: {e}")
            return []

    async def categorize_income_source(self, description: str, merchant: str) -> Optional[str]:
        """Categorize income source based on description and merchant"""
        text = f"{description} {merchant}".lower()
        
        for source, keywords in self.income_sources.items():
            if any(keyword in text for keyword in keywords):
                return source
        
        return None

    async def get_categorization_suggestions(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get smart categorization suggestions based on parsed data"""
        suggestions = {
            "categories": [],
            "sources": [],
            "confidence": 0.0
        }
        
        transaction_type = parsed_data.get("transaction_type")
        description = parsed_data.get("description", "").lower()
        merchant = parsed_data.get("merchant_or_source", "").lower()
        
        if transaction_type == "income":
            # Suggest income categories
            suggestions["categories"] = ["Salary", "Freelance", "Investment", "Other Income"]
            
            # Suggest income sources
            detected_source = await self.categorize_income_source(description, merchant)
            if detected_source:
                suggestions["sources"] = [detected_source]
                suggestions["confidence"] = 0.8
            else:
                suggestions["sources"] = list(self.income_sources.keys())
                suggestions["confidence"] = 0.4
        
        elif transaction_type == "expense":
            # Suggest expense categories based on merchant/description
            expense_categories = [
                "Food", "Transportation", "Shopping", "Entertainment", 
                "Utilities", "Rent", "Healthcare", "Education", "Other"
            ]
            suggestions["categories"] = expense_categories
            suggestions["confidence"] = 0.6
        
        return suggestions

# Initialize the service
auto_import_service = AutoImportService()
