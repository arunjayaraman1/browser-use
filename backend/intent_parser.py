# # pyright: reportMissingImports=false
# """
# Intent parser for converting natural language queries into structured ProductIntent.
# Uses LangChain for LLM-based parsing.
# """
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import ChatPromptTemplate
# from models import ProductIntent
# import json
# import re
# from dotenv import load_dotenv

# load_dotenv()

# llm = ChatOpenAI(model="gpt-4.1-mini")

# prompt = ChatPromptTemplate.from_template(
#     """
# You are an expert at extracting shopping intent from natural language queries for Amazon India.

# Extract shopping intent and return ONLY valid JSON with dynamic attributes.

# =============================================================
# CORE EXTRACTION RULES
# =============================================================

# 1. PRODUCT NAME (required)
#    - Extract the BASE product type (e.g., "mouse", "laptop", "phone", "t-shirt")
#    - Remove adjectives/attributes from product name
#    - Examples:
#      * "wired mouse" → product: "mouse"
#      * "blue cotton t-shirt" → product: "t-shirt"
#      * "Logitech wireless mouse" → product: "mouse"
#      * "Oneplus 15r" → product: "Oneplus 15r" (brand model is the product)

# 2. ATTRIBUTES (product characteristics)
#    - Extract ANY product characteristic mentioned:
#      * Connectivity: "wired", "wireless", "bluetooth", "USB"
#      * Color: "black", "white", "blue", "red", etc.
#      * Size: "XL", "large", "small", "10 inch", etc.
#      * Material: "cotton", "leather", "plastic", "metal"
#      * Type: "gaming", "office", "sports", "casual"
#      * Any other descriptive attribute
   
#    - Store in attributes object:
#      {{"connectivity": "wired", "color": "black", "size": "L"}}

# 3. HARD CONSTRAINTS (must satisfy)
#    - Price constraints:
#      * "under X", "below X", "less than X", "maximum X" → {{"price": {{"max": X}}}}
#      * "above X", "over X", "more than X", "minimum X" → {{"price": {{"min": X}}}}
#      * "between X and Y" → {{"price": {{"min": X, "max": Y}}}}
   
#    - Rating constraints:
#      * "rating above X", "minimum X stars", "at least X stars" → {{"rating": {{"min": X}}}}
#      * "rating below X", "maximum X stars" → {{"rating": {{"max": X}}}}
#      * "good rating", "high rating", "well rated" → {{"rating": {{"min": 4.0}}}}
   
#    - Discount constraints:
#      * "at least X% discount", "minimum X% off", "X% off or more" → {{"discount": {{"min": X}}}}
#      * "with discount", "on sale", "discounted" → {{"discount": {{"min": 10}}}}
#      * Extract numeric discount percentage (e.g., "30% discount" → 30)
   
#    - Required features:
#      * "must have X", "needs X", "requires X", "with X" → add to hard_constraints
#      * "from BRAND" (without softeners) → {{"brand": "BRAND"}}

# 4. SOFT PREFERENCES (nice to have, not required)
#    - Detect softening keywords:
#      * "preferably", "preferred", "ideally", "if possible"
#      * "better if", "nice to have", "would like"
   
#    - When detected, place in soft_preferences instead of hard_constraints:
#      * "preferably from Logitech" → {{"brand": "Logitech"}}
#      * "preferably from Philips or Prestige" → {{"brands": ["Philips", "Prestige"]}}
#      * "ideally Nike or Adidas" → {{"brands": ["Nike", "Adidas"]}}
#      * "ideally blue" → {{"color": "blue"}}
#      * "better if wireless" → {{"connectivity": "wireless"}}
   
#    - For multiple brands with "or":
#      * Extract as LIST of brands in "brands" field (not "brand")
#      * Example: "Philips or Prestige" → ["Philips", "Prestige"]
#      * Agent will try each brand one by one

# 5. SORT PREFERENCES
#    - "cheapest", "lowest price", "affordable" → "price_asc"
#    - "expensive", "highest price", "premium" → "price_desc"
#    - "best rated", "top rated", "highest rating" → "rating_desc"
#    - "worst rated", "lowest rating" → "rating_asc"

# =============================================================
# DECISION TREE: HARD vs SOFT
# =============================================================

# IF query contains "preferably", "preferred", "ideally", "if possible", "nice to have":
#    → Place that requirement in soft_preferences
# ELSE IF query says "must", "required", "needs", "only", "from BRAND":
#    → Place in hard_constraints
# ELSE IF it's a price/rating constraint:
#    → Place in hard_constraints
# ELSE IF it's a descriptive attribute (color, size, type):
#    → Place in attributes (search context)

# =============================================================
# RETURN FORMAT (ONLY valid JSON)
# =============================================================

# {{
#   "product": "base product name",
#   "attributes": {{
#     // Product characteristics for search
#     // e.g. "color": "black", "connectivity": "wired", "size": "L"
#   }},
#   "hard_constraints": {{
#     // Must satisfy
#     // e.g. "price": {{"min": 300, "max": 600}}, "rating": {{"min": 4.0}}
#   }},
#   "soft_preferences": {{
#     // Nice to have, not required
#     // e.g. "brand": "Logitech"
#   }},
#   "sort_by": "price_asc|price_desc|rating_asc|rating_desc|null"
# }}

# =============================================================
# EXAMPLES
# =============================================================

# Query: "Add a wired mouse to the cart priced between ₹300 and ₹600, with user rating above 4 stars, preferably from Logitech"
# Response: {{
#   "product": "mouse",
#   "attributes": {{"connectivity": "wired"}},
#   "hard_constraints": {{
#     "price": {{"min": 300, "max": 600}},
#     "rating": {{"min": 4.0}}
#   }},
#   "soft_preferences": {{"brand": "Logitech"}},
#   "sort_by": null
# }}

# Query: "add black Logitech mouse under 500"
# Response: {{
#   "product": "mouse",
#   "attributes": {{"color": "black"}},
#   "hard_constraints": {{
#     "price": {{"max": 500}},
#     "brand": "Logitech"
#   }},
#   "soft_preferences": {{}},
#   "sort_by": null
# }}

# Query: "add cheapest laptop with good rating"
# Response: {{
#   "product": "laptop",
#   "attributes": {{}},
#   "hard_constraints": {{
#     "rating": {{"min": 4.0}}
#   }},
#   "soft_preferences": {{}},
#   "sort_by": "price_asc"
# }}

# Query: "blue cotton t-shirt size L under ₹500 ideally from Nike"
# Response: {{
#   "product": "t-shirt",
#   "attributes": {{
#     "color": "blue",
#     "material": "cotton",
#     "size": "L"
#   }},
#   "hard_constraints": {{
#     "price": {{"max": 500}}
#   }},
#   "soft_preferences": {{"brand": "Nike"}},
#   "sort_by": null
# }}

# Query: "wireless gaming mouse from Logitech with high rating"
# Response: {{
#   "product": "mouse",
#   "attributes": {{
#     "connectivity": "wireless",
#     "type": "gaming"
#   }},
#   "hard_constraints": {{
#     "brand": "Logitech",
#     "rating": {{"min": 4.0}}
#   }},
#   "soft_preferences": {{}},
#   "sort_by": null
# }}

# Query: "electric kettle 1500W, ₹800-1500, rating 4+, preferably Philips or Prestige"
# Response: {{
#   "product": "electric kettle",
#   "attributes": {{
#     "power": "1500W"
#   }},
#   "hard_constraints": {{
#     "price": {{"min": 800, "max": 1500}},
#     "rating": {{"min": 4.0}}
#   }},
#   "soft_preferences": {{
#     "brands": ["Philips", "Prestige"]
#   }},
#   "sort_by": null
# }}

# Query: "pen with price less than 20 rs"
# Response: {{
#   "product": "pen",
#   "attributes": {{}},
#   "hard_constraints": {{
#     "price": {{"max": 20}}
#   }},
#   "soft_preferences": {{}},
#   "sort_by": null
# }}

# Query: "men's cotton t-shirt size M under ₹500 with at least 30% discount and rating above 4"
# Response: {{
#   "product": "cotton t-shirt",
#   "attributes": {{
#     "gender": "men",
#     "material": "cotton",
#     "size": "M"
#   }},
#   "hard_constraints": {{
#     "price": {{"max": 500}},
#     "discount": {{"min": 30}},
#     "rating": {{"min": 4.0}}
#   }},
#   "soft_preferences": {{}},
#   "sort_by": null
# }}

# =============================================================
# User query:
# {query}

# Return ONLY the JSON object, no additional text:
#     """
# )


# def parse_intent(query: str) -> ProductIntent:
#     """
#     Parse natural language query into structured ProductIntent using LangChain.
#     Handles various query formats like:
#     - "add pen with price less than 20 rs"
#     - "add pen with more user rating"
#     - "add laptop under 50000 with good rating"
#     """
#     response = llm.invoke(prompt.format(query=query))
#     # Extract content - handle both string and list types
#     if hasattr(response, 'content'):
#         raw_content = response.content
#         # Handle case where content might be a list
#         if isinstance(raw_content, list):
#             content_str = ' '.join(str(item) for item in raw_content)
#         else:
#             content_str = str(raw_content)
#     else:
#         content_str = str(response)
#     content = content_str.strip()
    
#     # Remove markdown code blocks if present (```json ... ```)
#     if content.startswith("```"):
#         lines = content.split("\n")
#         # Remove first line (```json or ```)
#         if lines and lines[0].startswith("```"):
#             lines = lines[1:]
#         # Remove last line (```)
#         if lines and lines[-1].strip() == "```":
#             lines = lines[:-1]
#         content = "\n".join(lines).strip()
    
#     # Try to parse JSON directly
#     try:
#         data = json.loads(content)
#     except json.JSONDecodeError:
#         # If direct parsing fails, try to extract JSON object using regex
#         # This handles nested objects and arrays
#         # Find the first complete JSON object (handles nested braces)
#         brace_count = 0
#         start_idx = content.find('{')
#         if start_idx == -1:
#             raise ValueError(f"No JSON object found in response: {content[:200]}")
        
#         end_idx = start_idx
#         for i in range(start_idx, len(content)):
#             if content[i] == '{':
#                 brace_count += 1
#             elif content[i] == '}':
#                 brace_count -= 1
#                 if brace_count == 0:
#                     end_idx = i + 1
#                     break
        
#         if brace_count != 0:
#             # Unbalanced braces, try simple regex as fallback
#             json_match = re.search(r'\{.*\}', content, re.DOTALL)
#             if json_match:
#                 json_str = json_match.group()
#             else:
#                 raise ValueError(f"Malformed JSON in response: {content[:200]}")
#         else:
#             json_str = content[start_idx:end_idx]
        
#         try:
#             data = json.loads(json_str)
#         except json.JSONDecodeError as e:
#             raise ValueError(f"Failed to parse JSON from LLM response: {content[:200]}. Error: {str(e)}")
    
#     # Validate and create ProductIntent
#     try:
#         return ProductIntent(**data)
#     except Exception as e:
#         raise ValueError(f"Failed to create ProductIntent from parsed data: {data}. Error: {str(e)}")



from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
import re
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-5.1")

prompt = ChatPromptTemplate.from_template(
    """
You are an expert at extracting shopping intent from natural language queries for Amazon India.
Extract shopping intent and return a list of intents separated by commas.
Each intent should be a string.
Each intent should be a valid intent.

Examples: 
Query: "Add a wired mouse to the cart priced between ₹300 and ₹600, with user rating above 4 stars, preferably from Logitech"
Response: 
[1.Add a wired mouse to the cart, 2. Priced between ₹300 and ₹600, 3. With user rating above 4 stars, 4. Preferably from Logitech]

Now extract intents from this query:
{query}

Return only the list of intents in the format shown above:
"""
)



def parse_intent(query: str) -> list[str]:
    """
    Parse natural language query into a list of intent strings.
    
    Args:
        query: Natural language shopping query
        
    Returns:
        List of intent strings extracted from the query
    """
    response = llm.invoke(prompt.format(query=query))
    content = str(response.content).strip()
    
    # Remove markdown code blocks if present
    if content.startswith("```"):
        lines = content.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()
    
    # Extract list if it's in bracket format [1. intent, 2. intent, ...]
    if content.startswith("[") and content.endswith("]"):
        # Remove brackets
        content = content[1:-1].strip()
        # Split by comma, but handle numbered items like "1. intent, 2. intent"
        # Use regex to split by ", " followed by a number and period
        # Split by pattern: ", " followed by optional number and period
        intents = re.split(r',\s*(?=\d+\.)', content)
        # Clean up each intent (remove leading numbers and periods)
        cleaned_intents = []
        for intent in intents:
            intent = intent.strip()
            # Remove leading number and period if present (e.g., "1. " or "1.")
            intent = re.sub(r'^\d+\.\s*', '', intent)
            if intent:
                cleaned_intents.append(intent)
        return cleaned_intents if cleaned_intents else [content]
    else:
        # If not in list format, return as single intent
        return [content.strip()]
    
# if __name__ == "__main__":
#     query = "Add 1 kg basmati rice to the cart with rating 4+ and price below ₹200."
#     print(parse_intent(query))