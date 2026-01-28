# pyright: reportMissingImports=false
import logging
from browser_use import Agent, Browser, ChatOpenAI, ChatBrowserUse
from models import CartResult, ProductIntent, ProductListResult, ProductItem
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Set up logger for this module
logger = logging.getLogger(__name__)

# =========================================================
# CONFIGURATION
# =========================================================

AMAZON_URL = "https://www.amazon.in"

SPONSORED_URL_PATTERNS = (
    "/sspa/",
    "sp_atk",
    "sp_csd",
    "sp_btf",
    "sp_",
)

MAX_FILTER_ATTEMPTS = 2
MAX_SCROLL_ATTEMPTS = 2
MAX_AGENT_STEPS = 40


# MODEL_NAME = "gpt-4.1-mini"
MODEL_NAME = "gpt-5.1"


# =========================================================
# VALIDATION
# =========================================================

def validate_intent(intent: ProductIntent) -> None:
    """Fail fast on invalid intent"""
    logger.debug(f"Validating intent: product={intent.product}, constraints={intent.hard_constraints}")
    
    if not intent.product or not intent.product.strip():
        logger.error("Product name is required but was empty")
        raise ValueError("Product name is required")

    if intent.min_price and intent.max_price:
        if intent.min_price > intent.max_price:
            logger.error(f"Invalid price range: min_price ({intent.min_price}) > max_price ({intent.max_price})")
            raise ValueError("min_price cannot exceed max_price")

    if intent.min_rating:
        if not (0 < intent.min_rating <= 5):
            logger.error(f"Invalid rating: {intent.min_rating} (must be between 0 and 5)")
            raise ValueError("min_rating must be between 0 and 5")
    
    logger.info(f"Intent validated successfully: {intent.product}")


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def is_sponsored(product: dict) -> bool:
    
    logger.debug(f"Checking if product is sponsored: {product.get('title', 'Unknown')[:50]}")
    
    # Normalize once
    url = (product.get("url") or "").lower()
    labels = (product.get("labels") or "").lower()
    aria = (product.get("aria_label") or "").lower()

    # 1️⃣ Explicit Amazon ad infrastructure (STRONGEST)
    if (
        product.get("sponsoredLoggingUrl")
        or product.get("spAttributionURL")
        or product.get("adId")
        or product.get("clickTrackingParams")
    ):
        logger.debug("Product is sponsored: explicit ad infrastructure detected")
        return True

    # 2️⃣ URL patterns Amazon never uses for organic results
    if any(pattern in url for pattern in SPONSORED_URL_PATTERNS):
        logger.debug(f"Product is sponsored: URL pattern detected in {url[:100]}")
        return True

    # 3️⃣ DOM / metadata indicators
    if (
        product.get("data_ad_id")
        or product.get("data_ad")
        or product.get("data_sponsored")
    ):
        logger.debug("Product is sponsored: DOM/metadata indicators detected")
        return True

    # 4️⃣ Visible disclosure text
    if "sponsored" in labels:
        logger.debug("Product is sponsored: 'sponsored' text found in labels")
        return True

    # 5️⃣ Accessibility labels
    if "sponsored" in aria:
        logger.debug("Product is sponsored: 'sponsored' text found in aria label")
        return True

    logger.debug("Product is NOT sponsored")
    return False


def build_product_extraction_js(min_rating: Optional[float] = None) -> str:
    
    logger.debug(f"Building product extraction JavaScript code with min_rating={min_rating}")
    min_rating_js = str(min_rating) if min_rating is not None else "null"
    return """
    (function() {
    // Check if a product card is sponsored
    function isSponsored(card) {
        if (!card || !card.querySelector) {
            return false;
        }
        
        // A. Ad-specific DOM attributes
        if (card.querySelector('[data-ad-id], [data-sponsored], [data-ad-slot]')) {
            return true;
        }
        
        // B. Sponsored routing / tracking links
        for (const a of card.querySelectorAll('a[href]')) {
            const href = a.href || '';
            if (
                href.includes('/sspa/') ||
                href.includes('/gp/slredirect/') ||
                href.includes('sp_atk=') ||
                href.includes('sp_csd=') ||
                href.includes('sp_btf=')
            ) {
                return true;
            }
        }
        
        // C. Disclosure text (last line of defense)
        if (card.innerText.toLowerCase().includes('sponsored')) {
            return true;
        }
        
        return false;
    }
    
    // Extract price from product card
    function extractPrice(card) {
        const priceEl = card.querySelector('.a-price .a-offscreen');
        if (!priceEl) return null;
        
        return parseInt(
            priceEl.textContent.replace(/[₹,]/g, ''),
            10
        );
    }
    
    // Extract rating from product card
    function extractRating(card) {
        const ratingEl = card.querySelector(
            'i[data-cy="reviews-ratings-slot"] span.a-icon-alt'
        );
        
        if (!ratingEl) {
            // Fallback to other selectors
            const fallbackEl = card.querySelector('.a-icon-alt, [aria-label*="stars"]');
            if (!fallbackEl) return null;
            const ratingText = fallbackEl.innerText || fallbackEl.getAttribute('aria-label') || '';
            const match = ratingText.match(/([\\d.]+)\\s*out of\\s*5/i);
            return match ? parseFloat(match[1]) : null;
        }
        
        const match = ratingEl.textContent.match(/([\\d.]+)\\s*out of\\s*5/i);
        return match ? parseFloat(match[1]) : null;
    }
    
    // Extract product information from DOM element
    function extractProduct(card) {
        if (!card) {
            return null;
        }
        
        // Extract ASIN
        const asin = card.getAttribute('data-asin') || null;
        
        // Extract title
        const titleEl = card.querySelector('h2 span, h2 a span, .s-title-instructions-style span');
        const title = titleEl?.innerText?.trim() || 
                     card.querySelector('h2')?.innerText?.trim() || 
                     null;
        
        // Extract price using extractPrice function
        const price = extractPrice(card);
        
        // Extract rating using extractRating function
        const rating = extractRating(card);
        
        // Extract URL
        const linkEl = card.querySelector('a[href*="/dp/"], a[href*="/gp/product/"]');
        let url = null;
        if (linkEl) {
            url = linkEl.href || linkEl.getAttribute('href');
            // Make absolute if relative
            if (url && url.startsWith('/')) {
                url = 'https://www.amazon.in' + url;
            }
        }
        
        // Check sponsored status
        const sponsored = isSponsored(card);
        
        return {
            asin: asin,
            title: title,
            price: price,
            rating: rating,
            url: url,
            sponsored: sponsored
        };
    }
    
    // Extract all products from search results page
    function extractAllProducts() {
        // Find all product cards using the most specific selector
        const organicResults = Array.from(
            document.querySelectorAll(
                'div[role="listitem"][data-component-type="s-search-result"][data-asin]'
            )
        ).filter(card => !isSponsored(card));
        
        // Fallback: try other selectors if the main one doesn't work
        let productElements = organicResults;
        if (productElements.length === 0) {
            const fallbackSelectors = [
                '[data-component-type="s-search-result"][data-asin]',
                '.s-result-item[data-asin]',
                '[data-asin]:not([data-asin=""])'
            ];
            
            for (const selector of fallbackSelectors) {
                const elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    productElements = Array.from(elements).filter(card => !isSponsored(card));
                    break;
                }
            }
        }
        
        // Extract product info from each element
        const products = [];
        for (const card of productElements) {
            const product = extractProduct(card);
            if (product && product.asin) {
                products.push(product);
            }
        }
        
        // Filter by rating if min_rating is specified (after price check)
        const minRating = {min_rating_js};
        if (minRating !== null && minRating !== undefined) {{
            const highRated = products.filter(product => {{
                const rating = product.rating;
                return rating !== null && rating >= minRating;
            }});
            return highRated;
        }}
        
        return products;
    }
    
    // Execute extraction immediately and return results
    try {
        const products = extractAllProducts();
        return {
            success: true,
            products: products,
            count: products.length
        };
    } catch (error) {
        return {
            success: false,
            error: error.message,
            products: []
        };
    }
    })();
    """


def fix_product_url(url: str) -> str:
    """
    Fix malformed Amazon product URLs.
    Handles relative URLs, incomplete URLs, and ensures proper domain.
    """
    logger.debug(f"Fixing product URL: {url[:100]}")
    
    if not url or not url.strip():
        logger.error("URL is empty")
        raise ValueError("URL cannot be empty")
    
    url = url.strip()
    
    # If already a complete URL with protocol, validate domain
    if url.startswith("http://") or url.startswith("https://"):
        # Check if it's an Amazon URL
        if "amazon.in" in url:
            return url
        # If it has protocol but wrong domain, try to extract product ID
        if "/dp/" in url:
            # Extract product ID and rebuild
            parts = url.split("/dp/")
            if len(parts) > 1:
                product_id = parts[1].split("/")[0].split("?")[0]
                fixed_url = f"{AMAZON_URL}/dp/{product_id}"
                logger.debug(f"Fixed URL by extracting product ID: {fixed_url}")
                return fixed_url
    
    # If relative URL (starts with /)
    if url.startswith("/"):
        fixed_url = f"{AMAZON_URL}{url}"
        logger.debug(f"Fixed relative URL: {fixed_url}")
        return fixed_url
    
    # If URL contains /dp/ but no domain
    if "/dp/" in url:
        # Extract product ID
        parts = url.split("/dp/")
        if len(parts) > 1:
            product_id = parts[1].split("/")[0].split("?")[0]
            fixed_url = f"{AMAZON_URL}/dp/{product_id}"
            logger.debug(f"Fixed URL by extracting product ID from /dp/: {fixed_url}")
            return fixed_url
    
    # If it's just a product ID
    if url.startswith("B") and len(url) == 10:
        fixed_url = f"{AMAZON_URL}/dp/{url}"
        logger.debug(f"Fixed URL from product ID: {fixed_url}")
        return fixed_url
    
    # Default: prepend Amazon domain
    if not url.startswith("http"):
        if url.startswith("/"):
            fixed_url = f"{AMAZON_URL}{url}"
        else:
            fixed_url = f"{AMAZON_URL}/{url}"
        logger.debug(f"Fixed URL by prepending domain: {fixed_url}")
        return fixed_url
    
    logger.debug(f"URL already valid: {url}")
    return url


# =========================================================
# INTENT MODE
# =========================================================

def is_generic_intent(intent: ProductIntent) -> bool:
    """
    Generic intent:
    - No hard brand constraint
    - Minimal hard constraints
    - Very short product name
    """
    has_hard_brand = intent.hard_constraints.get('brand')
    has_many_attributes = len(intent.attributes) > 2
    has_specific_model = len(intent.product.split()) > 2
    
    return (
        not has_hard_brand
        and not has_many_attributes
        and not has_specific_model
    )


def build_search_query(intent: ProductIntent, brand_override: Optional[str] = None) -> str:
    """
    Build Amazon search query from product + attributes + soft preferences.
    
    Args:
        intent: ProductIntent with search criteria
        brand_override: If provided, use this brand instead of intent brands (for multi-brand search)
    """
    logger.debug(f"Building search query: product={intent.product}, brand_override={brand_override}")
    parts = [intent.product]
    
    # Add attributes to search (color, connectivity, type, etc.)
    if intent.attributes:
        parts.extend(intent.attributes.values())
    
    # Add hard brand constraint if present
    hard_brand = intent.hard_constraints.get('brand')
    if hard_brand:
        parts.insert(0, hard_brand)
        return " ".join(str(p) for p in parts if p)
    
    # Use brand override if provided (for multi-brand iteration)
    if brand_override:
        parts.insert(0, brand_override)
        return " ".join(str(p) for p in parts if p)
    
    # Add soft brand preference to search (helps ranking)
    soft_brand = intent.soft_preferences.get('brand')
    if soft_brand:
        parts.insert(0, soft_brand)
    
    # Check for multiple brands (list)
    soft_brands = intent.soft_preferences.get('brands')
    if soft_brands and isinstance(soft_brands, list) and soft_brands:
        # Use first brand for initial search
        parts.insert(0, soft_brands[0])
    
    return " ".join(str(p) for p in parts if p)


def build_price_slider_js(min_price: Optional[float], max_price: Optional[float]) -> Optional[str]:
    logger.debug(f"Building price slider JS: min_price={min_price}, max_price={max_price}")
    
    if min_price is None and max_price is None:
        logger.debug("No price constraints, skipping slider JS")
        return None

    min_js = str(int(min_price)) if min_price is not None else "null"
    max_js = str(int(max_price)) if max_price is not None else "null"
    logger.debug(f"Price slider JS generated: min={min_js}, max={max_js}")

    return f"""
(function () {{
    const targetMin = {min_js};
    const targetMax = {max_js};

    const minSlider = document.querySelector('input[id*="lower-bound-slider"]');
    const maxSlider = document.querySelector('input[id*="upper-bound-slider"]');

    if (!minSlider || !maxSlider) {{
        return {{ success: false, reason: "Sliders not found" }};
    }}

    const extractPrice = (text) => {{
        if (!text) return null;
        const m = text.match(/[₹]?([\\d,]+)/);
        return m ? parseInt(m[1].replace(/,/g, ""), 10) : null;
    }};

    const setByPrice = (slider, target) => {{
        const maxIndex = parseInt(slider.max, 10);
        for (let i = 0; i <= maxIndex; i++) {{
            slider.value = i;
            slider.dispatchEvent(new Event("input", {{ bubbles: true }}));
            const price = extractPrice(slider.getAttribute("aria-valuetext"));
            if (price !== null && price >= target) {{
                slider.dispatchEvent(new Event("change", {{ bubbles: true }}));
                return {{ index: i, price }};
            }}  
        }}
        return null;
    }};

    let minResult = null;
    let maxResult = null;

    if (targetMin !== null) {{
        minResult = setByPrice(minSlider, targetMin);
    }}

    if (targetMax !== null) {{
        maxResult = setByPrice(maxSlider, targetMax);
    }}

    // Safety: ensure max >= min
    if (minResult && maxResult && maxResult.index < minResult.index) {{
        maxSlider.value = minResult.index + 1;
        maxSlider.dispatchEvent(new Event("input", {{ bubbles: true }}));
        maxSlider.dispatchEvent(new Event("change", {{ bubbles: true }}));
    }}

    return {{
        success: true,
        min: minResult,
        max: maxResult
    }};
}})();
"""


def build_filter_instructions(intent: ProductIntent) -> tuple[str, str, str, Optional[float], Optional[float]]:
    """
    Build filter instructions for price, rating, and discount.
    Returns (price_text, rating_text, discount_text, min_price, max_price)
    """
    logger.debug("Building filter instructions from intent")
    price_text = ""
    rating_text = ""
    discount_text = ""
    
    # Price filter
    price_constraint = intent.hard_constraints.get('price', {})
    min_price = price_constraint.get('min')
    max_price = price_constraint.get('max')
    
    if min_price and max_price:
        price_text = f"₹{min_price} – ₹{max_price}"
    elif max_price:
        price_text = f"Under ₹{max_price}"
    elif min_price:
        price_text = f"Over ₹{min_price}"
    
    # Rating filter
    rating_constraint = intent.hard_constraints.get('rating', {})
    min_rating = rating_constraint.get('min')
    
    if min_rating:
        rating_text = f"{min_rating} Stars & Up"
    
    # Discount filter
    discount_constraint = intent.hard_constraints.get('discount', {})
    min_discount = discount_constraint.get('min')
    
    if min_discount:
        # Find closest Amazon discount filter
        # Amazon typically has: 10%, 25%, 50%, 60% filters
        if min_discount >= 50:
            discount_text = "50% Off or more"
        elif min_discount >= 25:
            discount_text = "25% Off or more"
        elif min_discount >= 10:
            discount_text = "10% Off or more"
        else:
            discount_text = f"{min_discount}% Off or more"
    
    logger.info(f"Filter instructions: price={price_text}, rating={rating_text}, discount={discount_text}, min_price={min_price}, max_price={max_price}")
    return price_text, rating_text, discount_text, min_price, max_price


def build_selection_rules(intent: ProductIntent, generic_mode: bool) -> str:
    """
    Build product selection rules based on intent.
    """
    rules = []
    
    # Hard constraints (MUST satisfy)
    rules.append("HARD CONSTRAINTS (MUST SATISFY):")
    
    # Price constraint
    price_constraint = intent.hard_constraints.get('price', {})
    min_price = price_constraint.get('min')
    max_price = price_constraint.get('max')
    if min_price:
        rules.append(f"- Price ≥ ₹{min_price}")
    if max_price:
        rules.append(f"- Price ≤ ₹{max_price}")
    
    # Rating constraint
    rating_constraint = intent.hard_constraints.get('rating', {})
    min_rating = rating_constraint.get('min')
    max_rating = rating_constraint.get('max')
    if min_rating:
        rules.append(f"- Rating ≥ {min_rating} stars")
    if max_rating:
        rules.append(f"- Rating ≤ {max_rating} stars")
    
    # Discount constraint
    discount_constraint = intent.hard_constraints.get('discount', {})
    min_discount = discount_constraint.get('min')
    if min_discount:
        rules.append(f"- Discount ≥ {min_discount}%")
    
    # Hard brand constraint
    hard_brand = intent.hard_constraints.get('brand')
    if hard_brand and not generic_mode:
        rules.append(f"- Brand MUST be: {hard_brand}")
    
    # Product attributes (should match search context)
    if intent.attributes and not generic_mode:
        rules.append("\nPRODUCT ATTRIBUTES (should be present in listing):")
        for attr_name, attr_value in intent.attributes.items():
            rules.append(f"- {attr_name.title()}: {attr_value}")
    
    # Soft preferences (nice to have, use for sorting)
    if intent.soft_preferences:
        rules.append("\nSOFT PREFERENCES (prefer but not required):")
        
        # Single brand preference
        soft_brand = intent.soft_preferences.get('brand')
        if soft_brand:
            rules.append(f"- PREFER {soft_brand} but accept other brands if constraints met")
        
        # Multiple brands preference
        soft_brands = intent.soft_preferences.get('brands')
        if soft_brands and isinstance(soft_brands, list):
            brands_str = " OR ".join(soft_brands)
            rules.append(f"- PREFER {brands_str} (try each brand one by one)")
            rules.append(f"  Search order: {' → '.join(soft_brands)} → generic")
        
        # Other preferences
        for pref_name, pref_value in intent.soft_preferences.items():
            if pref_name not in ('brand', 'brands'):
                rules.append(f"- Prefer {pref_name}: {pref_value}")
    
    if not rules[1:]:  # Only header, no actual rules
        rules.append("- None (select first valid non-sponsored product)")
    
    return "\n".join(rules)





# =========================================================
# RUNNER
# =========================================================

async def run_browser_agent(query_or_intent: str | ProductIntent, use_browser_use_llm: bool = True) -> CartResult:
    """
    Run browser agent to add product to Amazon cart.
    
    Args:
        query_or_intent: Either a string query (natural language) or ProductIntent object
        use_browser_use_llm: If True, use ChatBrowserUse (recommended). 
                           If False, use ChatOpenAI.
    
    Returns:
        CartResult with the added product or error information
    """
    # If it's a string, use it directly as the task
    if isinstance(query_or_intent, str):
        logger.info(f"Starting browser agent with query: {query_or_intent[:100]}...")
        # Try to extract price constraints from query (simple regex)
        import re

        # First try to match "between X and Y" or "priced between X and Y" patterns
        between_match = re.search(r'(?:priced\s+)?between\s+[₹]?\s*(\d+)\s+(?:and|to|-)\s+[₹]?\s*(\d+)', query_or_intent.lower())
        if between_match:
            min_price = float(between_match.group(1))
            max_price = float(between_match.group(2))
        else:
            # Fallback to individual patterns - be specific to avoid matching rating patterns
            # Only match if preceded by price-related keywords or ₹ symbol
            price_match = re.search(r'(?:price[ds]?\s+)?(?:under|below|max|upto|up to|less than)\s+[₹]?\s*(\d+)', query_or_intent.lower())
            max_price = float(price_match.group(1)) if price_match else None
            # Only match if preceded by price-related keywords or ₹ symbol (not "rating above")
            price_match_min = re.search(r'(?:price[ds]?\s+)?(?:over|above|min|more than|greater than)\s+[₹]?\s*(\d+)', query_or_intent.lower())
            min_price = float(price_match_min.group(1)) if price_match_min else None
        
        # Extract rating constraints separately
        rating_match = re.search(r'rating\s+(?:above|over|at least|>=|≥)\s*(\d+(?:\.\d+)?)', query_or_intent.lower())
        min_rating = float(rating_match.group(1)) if rating_match else None
        
        # Build price slider JS if price constraints found
        price_slider_js = build_price_slider_js(min_price, max_price)
        price_filter_instructions = ""
        if price_slider_js:
            price_filter_instructions = f"""
PRICE FILTER (RECOMMENDED METHOD):
- After searching, use the evaluate() action with this JavaScript code to set price filters:
{price_slider_js}
- Wait 5-8 seconds after executing for results to update
- Verify the filter was applied by checking visible product prices
- If sliders not found, fall back to clicking price filter buttons in the left sidebar
"""
        
        # Build product extraction JavaScript
        product_extraction_js = build_product_extraction_js(min_rating)
        product_extraction_instructions = f"""
PRODUCT EXTRACTION (CRITICAL - USE THIS METHOD):
- ⚠️ DO NOT use extract() action - it returns empty results and causes navigation errors
- ✅ ALWAYS use evaluate() action with this JavaScript code to extract products:
{product_extraction_js}
- This will return a result object with:
  * success: true/false
  * products: array of product objects with asin, title, price, rating, url, sponsored
  * count: number of products found
- After executing, check result.success and result.products
- If result.success is false, check result.error and try again
- Navigate to products using result.products[0].url (or first non-sponsored product)
- ⚠️ NEVER navigate to "about:blank" - always use a valid product URL from the extraction result
"""
        
        # Build task string from the query
        task = f"""
You are shopping on Amazon India. Your task is to:

{query_or_intent}

IMPORTANT RULES:
- Go to https://www.amazon.in
- Search for the product using the query above
{price_filter_instructions}
{product_extraction_instructions}
- Find a first valid non-sponsored product that matches the requirements
- Add it to cart only if it matches the requirements
- ⚠️ CRITICAL: When navigating to product pages, ALWAYS use navigate(url="...", new_tab=False) to open in the SAME tab
- ⚠️ NEVER use new_tab=True or open new tabs - this causes loops and confusion
- Only One product should be added to cart
- Return the product details when done and stop the task

PAGE LOADING PATIENCE (CRITICAL):
- ⚠️ Amazon pages can take 5-10 seconds to fully load, especially search results and product pages
- ⚠️ DO NOT evaluate pages as "empty" or "blank" immediately after navigation
- ⚠️ ALWAYS wait at least 5-8 seconds after navigation before evaluating page state
- ⚠️ Check the DOM content and browser_state, not just visual appearance - pages may look empty but have content loading
- ⚠️ If you see products in the browser_state or DOM, the page IS loaded - don't say it's empty
- ⚠️ Only consider a page truly empty if: (1) waited 10+ seconds, (2) DOM has no product elements, (3) browser_state shows no content
- ⚠️ If page appears empty but browser_state shows content, wait 3-5 more seconds before deciding

HANDLING EMPTY PAGES:
- If search results page appears empty after applying price filter:
  1. Wait 10-15 seconds FIRST - Amazon pages load slowly
  2. Check browser_state and DOM content - if products are listed there, page IS loaded
  3. Only if truly empty after 15 seconds: Try refreshing the page (navigate to same URL again with new_tab=False)
  4. If still empty, try search WITHOUT price filter first to verify products exist
  5. If products exist without filter, try applying price filter again
  6. If price filter causes empty pages, relax constraints slightly (e.g., increase max price by 20%)
- Only Non Sponsored products should be added to cart
- DO NOT loop more than 3 times - if price filter consistently causes empty pages, proceed without price filter and manually verify products match requirements
- Only Open the Product page if it matches the requirements
- ⚠️ CRITICAL: Use navigate(url=product_url, new_tab=False) to open product page in SAME tab
- ⚠️ DO NOT click on product links - use navigate() action instead to avoid opening new tabs
- ⚠️ After navigating to product page, wait 8-10 seconds before evaluating - product pages load slowly
- Only One product should be added to cart
- Return the product details when done and stop the task

ANTI-LOOP RULES:
- After extracting products using evaluate(), navigate to the FIRST valid non-sponsored product URL using navigate(url=url, new_tab=False)
- Wait 8-10 seconds after navigation before evaluating product page
- If navigation fails or wrong product page loads, use go_back() ONCE, then try the NEXT product from your list
- DO NOT use extract() action - it returns empty results and causes navigation errors
- DO NOT navigate to "about:blank" - always use a valid product URL from evaluate() result
- DO NOT extract products repeatedly from the same page
- DO NOT navigate back and forth more than 2 times - if first 2 products fail, stop and report error
- DO NOT refresh or go back if page is just loading slowly - be patient and wait
"""
    else:
        # It's a ProductIntent object - use the existing logic
        intent = query_or_intent
        logger.info(f"Starting browser agent for product: {intent.product}")
        logger.info(f"Intent details: {intent.hard_constraints}, {intent.soft_preferences}")
        
        validate_intent(intent)
        logger.debug("Building task instructions...")
        # Build task string from ProductIntent
        search_query = build_search_query(intent)
        selection_rules = build_selection_rules(intent, is_generic_intent(intent))
        
        # Get price constraints for price slider JS
        price_constraint = intent.hard_constraints.get('price', {})
        min_price = price_constraint.get('min')
        max_price = price_constraint.get('max')
        price_slider_js = build_price_slider_js(min_price, max_price)
        
        # Build price filter instructions
        price_filter_instructions = ""
        if price_slider_js:
            price_filter_instructions = f"""
PRICE FILTER (RECOMMENDED METHOD):
- After searching, use the evaluate() action with this JavaScript code to set price filters:
{price_slider_js}
- Wait 5-8 seconds after executing for results to update
- Verify the filter was applied by checking visible product prices
- If sliders not found (returns success: false), fall back to clicking price filter buttons in the left sidebar
- Look for price ranges like "Under ₹{int(max_price) if max_price else 'N/A'}" or "₹{int(min_price) if min_price else 'N/A'} - ₹{int(max_price) if max_price else 'N/A'}"
"""
        
        task = f"""
You are shopping on Amazon India. Your task is to:

Find and add to cart: {intent.product}

SEARCH QUERY: {search_query}

SELECTION RULES:
{selection_rules}

IMPORTANT RULES:
- Go to https://www.amazon.in
- Search for the product using the search query above
{price_filter_instructions}
- Always find a first valid non-sponsored product that matches the requirements
- Add it to cart only if it matches the requirements
- ⚠️ CRITICAL: When navigating to product pages, ALWAYS use navigate(url="...", new_tab=False) to open in the SAME tab
- ⚠️ NEVER use new_tab=True or open new tabs - this causes loops and confusion
- Only One product should be added to cart
- Return the product details when done and stop the task

PAGE LOADING PATIENCE (CRITICAL):
- ⚠️ Amazon pages can take 5-10 seconds to fully load, especially search results and product pages
- ⚠️ DO NOT evaluate pages as "empty" or "blank" immediately after navigation
- ⚠️ ALWAYS wait at least 5-8 seconds after navigation before evaluating page state
- ⚠️ Check the DOM content and browser_state, not just visual appearance - pages may look empty but have content loading
- ⚠️ If you see products in the browser_state or DOM, the page IS loaded - don't say it's empty
- ⚠️ Only consider a page truly empty if: (1) waited 10+ seconds, (2) DOM has no product elements, (3) browser_state shows no content
- ⚠️ If page appears empty but browser_state shows content, wait 3-5 more seconds before deciding

HANDLING EMPTY PAGES:
- If search results page appears empty after applying price filter:
  1. Wait 10-15 seconds FIRST - Amazon pages load slowly
  2. Check browser_state and DOM content - if products are listed there, page IS loaded
  3. Only if truly empty after 15 seconds: Try refreshing the page (navigate to same URL again with new_tab=False)
  4. If still empty, try search WITHOUT price filter first to verify products exist
  5. If products exist without filter, try applying price filter again
  6. If price filter causes empty pages, relax constraints slightly (e.g., increase max price by 20%)
- Only Non Sponsored products should be added to cart
- DO NOT loop more than 3 times - if price filter consistently causes empty pages, proceed without price filter and manually verify products match requirements
- Only Open the Product page if it matches the requirements
- ⚠️ CRITICAL: Use navigate(url=product_url, new_tab=False) to open product page in SAME tab
- ⚠️ DO NOT click on product links - use navigate() action instead to avoid opening new tabs
- ⚠️ After navigating to product page, wait 8-10 seconds before evaluating - product pages load slowly
- Only One product should be added to cart
- Return the product details when done and stop the task

ANTI-LOOP RULES:
- After extracting products using evaluate(), navigate to the FIRST valid non-sponsored product URL using navigate(url=url, new_tab=False)
- Wait 8-10 seconds after navigation before evaluating product page
- If navigation fails or wrong product page loads, use go_back() ONCE, then try the NEXT product from your list
- DO NOT use extract() action - it returns empty results and causes navigation errors
- DO NOT navigate to "about:blank" - always use a valid product URL from evaluate() result
- DO NOT extract products repeatedly from the same page
- DO NOT navigate back and forth more than 2 times - if first 2 products fail, stop and report error
- DO NOT refresh or go back if page is just loading slowly - be patient and wait
"""
        logger.debug(f"Task built, length: {len(task)} characters")

    # Choose LLM based on preference and API key availability
    import os
    if use_browser_use_llm and os.getenv('BROWSER_USE_API_KEY'):
        logger.info("Using ChatBrowserUse LLM")
        llm = ChatBrowserUse(
            timeout=180.0,  # Increase from 120s to 180s
            max_retries=8,  # Increase from 5 to 8
            retry_max_delay=120.0,  # Allow longer delays between retries
        )
    else:
        logger.info(f"Using ChatOpenAI LLM with model: {MODEL_NAME}")
        llm = ChatOpenAI(model=MODEL_NAME)
    
    # Setup fallback LLM to handle empty JSON errors
    fallback_llm = None
    if use_browser_use_llm and os.getenv('BROWSER_USE_API_KEY'):
        # If primary is ChatBrowserUse, use ChatOpenAI as fallback
        if os.getenv('OPENAI_API_KEY'):
            fallback_llm = ChatOpenAI(model=MODEL_NAME)
            logger.info(f"Fallback LLM: ChatOpenAI with model {MODEL_NAME}")
    else:
        # If primary is ChatOpenAI, use ChatBrowserUse as fallback
        if os.getenv('BROWSER_USE_API_KEY'):
            fallback_llm = ChatBrowserUse(timeout=180.0, max_retries=8, retry_max_delay=120.0)
            logger.info("Fallback LLM: ChatBrowserUse")
    
    logger.info("Creating agent with browser (high timeouts for slow pages and LLM calls)...")
    agent = Agent(
        browser=Browser(
            headless=False,
            minimum_wait_page_load_time=3.0,  # Increased from 2.0 to 3.0 for Amazon pages
            wait_for_network_idle_page_load_time=8.0,  # Increased from 5.0 to 8.0 for slow Amazon pages
            wait_between_actions=2.0,  # Increased from 1.5 to 2.0
        ),
        llm=llm,
        fallback_llm=fallback_llm,
        task=task,
        output_model_schema=CartResult,
        max_steps=MAX_AGENT_STEPS,
        llm_timeout=180,  # Increased from 120s to match ChatBrowserUse timeout
        step_timeout=300,  
        max_failures=5,  
    )

    logger.info(f"Running agent (max_steps={MAX_AGENT_STEPS})...")
    history = await agent.run()
    logger.info(f"Agent completed. Steps taken: {history.number_of_steps()}")

    # Try to get structured output
    logger.debug("Extracting result from agent history...")
    result = history.structured_output
    
    # Fallback: try to get structured output using the method
    if result is None:
        logger.debug("No structured_output found, trying get_structured_output method...")
        result = history.get_structured_output(CartResult)
    
    # If still None, create a failure result
    if result is None:
        logger.warning("No structured output found, attempting to extract from history...")
        # Check if task was completed successfully
        if history.is_done():
            logger.info("Task marked as done, extracting final result...")
            # Task completed but no structured output - try to extract from final result
            final_result = history.final_result()
            if final_result:
                try:
                    # Try to parse as JSON
                    import json
                    logger.debug(f"Parsing final result as JSON: {final_result[:200]}")
                    data = json.loads(final_result)
                    result = CartResult(**data)
                    logger.info("Successfully parsed CartResult from final result")
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(f"Failed to parse JSON from final result: {e}")
                    # If parsing fails, create a basic success result
                    result = CartResult(
                        success=True,
                        message="Product added to cart successfully",
                        items=[]
                    )
                    logger.info("Created fallback success result")
            else:
                logger.warning("Task done but no final result found")
                result = CartResult(
                    success=False,
                    message="Task completed but no product information found",
                    items=[]
                )
        else:
            # Task failed
            logger.error("Task failed - agent did not complete successfully")
            errors = history.errors()
            error_msg = "Unknown error occurred"
            if errors:
                error_list = [e for e in errors if e is not None]
                if error_list:
                    error_msg = "; ".join(str(e) for e in error_list[:3])  # First 3 errors
                    logger.error(f"Errors encountered: {error_msg}")
            
            result = CartResult(
                success=False,
                message=f"Failed to add product to cart: {error_msg}",
                items=[]
            )

    # Log final result
    if result.success:
        logger.info(f"✅ Task completed successfully! Product: {result.product.name if result.product else 'N/A'}")
        if result.product:
            logger.info(f"   Price: ₹{result.product.price}, Rating: {result.product.rating}")
    else:
        logger.error(f"❌ Task failed: {result.message}")
    
    return result


async def run_browser_agent_list(query_or_intent: str | ProductIntent, use_browser_use_llm: bool = True, max_products: int = 5) -> ProductListResult:
    """
    Run browser agent to extract and list filtered products (without adding to cart).
    
    Args:
        query_or_intent: Either a string query (natural language) or ProductIntent object
        use_browser_use_llm: If True, use ChatBrowserUse (recommended). 
                           If False, use ChatOpenAI.
        max_products: Maximum number of products to return (default: 5)
    
    Returns:
        ProductListResult with the filtered products
    """
    # If it's a string, use it directly as the task
    if isinstance(query_or_intent, str):
        logger.info(f"Starting browser agent list with query: {query_or_intent[:100]}...")
        # Try to extract price constraints from query (simple regex)
        import re

        # First try to match "between X and Y" or "priced between X and Y" patterns
        between_match = re.search(r'(?:priced\s+)?between\s+[₹]?\s*(\d+)\s+(?:and|to|-)\s+[₹]?\s*(\d+)', query_or_intent.lower())
        if between_match:
            min_price = float(between_match.group(1))
            max_price = float(between_match.group(2))
        else:
            # Fallback to individual patterns
            price_match = re.search(r'(?:price[ds]?\s+)?(?:under|below|max|upto|up to|less than)\s+[₹]?\s*(\d+)', query_or_intent.lower())
            max_price = float(price_match.group(1)) if price_match else None
            price_match_min = re.search(r'(?:price[ds]?\s+)?(?:over|above|min|more than|greater than)\s+[₹]?\s*(\d+)', query_or_intent.lower())
            min_price = float(price_match_min.group(1)) if price_match_min else None
        
        # Extract rating constraints separately
        rating_match = re.search(r'rating\s+(?:above|over|at least|>=|≥)\s*(\d+(?:\.\d+)?)', query_or_intent.lower())
        min_rating = float(rating_match.group(1)) if rating_match else None
        
        # Build price slider JS if price constraints found
        price_slider_js = build_price_slider_js(min_price, max_price)
        price_filter_instructions = ""
        if price_slider_js:
            price_filter_instructions = f"""
PRICE FILTER (RECOMMENDED METHOD):
- After searching, use the evaluate() action with this JavaScript code to set price filters:
{price_slider_js}
- Wait 5-8 seconds after executing for results to update
- Verify the filter was applied by checking visible product prices
- If sliders not found, fall back to clicking price filter buttons in the left sidebar
"""
        
        # Build product extraction JavaScript
        product_extraction_js = build_product_extraction_js(min_rating)
        
        # Build task string from the query
        task = f"""
You are shopping on Amazon India. Your task is to:

Find and list the first {max_products} products that match: {query_or_intent}

IMPORTANT RULES:
- Go to https://www.amazon.in
- Search for the product using the query above
{price_filter_instructions}
- After searching and applying filters, use the evaluate() action with this JavaScript code to extract products:
{product_extraction_js}
- This will return a result object with:
  * success: true/false
  * products: array of product objects with asin, title, price, rating, url, sponsored
  * count: number of products found
- Extract the first {max_products} non-sponsored products that match the requirements
- ⚠️ DO NOT add products to cart - only extract and list them
- ⚠️ DO NOT navigate to product pages - stay on the search results page
- Return the product list when done and stop the task

PAGE LOADING PATIENCE (CRITICAL):
- ⚠️ Amazon pages can take 5-10 seconds to fully load, especially search results
- ⚠️ DO NOT evaluate pages as "empty" or "blank" immediately after navigation
- ⚠️ ALWAYS wait at least 5-8 seconds after navigation before evaluating page state
- ⚠️ Check the DOM content and browser_state, not just visual appearance

HANDLING EMPTY PAGES:
- If search results page appears empty after applying price filter:
  1. Wait 10-15 seconds FIRST - Amazon pages load slowly
  2. Check browser_state and DOM content - if products are listed there, page IS loaded
  3. Only if truly empty after 15 seconds: Try refreshing the page
  4. If still empty, try search WITHOUT price filter first to verify products exist
- Only Non Sponsored products should be included in the list
- Return the first {max_products} products that satisfy the conditions
"""
    else:
        # It's a ProductIntent object
        intent = query_or_intent
        logger.info(f"Starting browser agent list for product: {intent.product}")
        
        validate_intent(intent)
        search_query = build_search_query(intent)
        selection_rules = build_selection_rules(intent, is_generic_intent(intent))
        
        # Get price constraints for price slider JS
        price_constraint = intent.hard_constraints.get('price', {})
        min_price = price_constraint.get('min')
        max_price = price_constraint.get('max')
        price_slider_js = build_price_slider_js(min_price, max_price)
        
        # Get rating constraint
        rating_constraint = intent.hard_constraints.get('rating', {})
        min_rating = rating_constraint.get('min')
        product_extraction_js = build_product_extraction_js(min_rating)
        
        # Build price filter instructions
        price_filter_instructions = ""
        if price_slider_js:
            price_filter_instructions = f"""
PRICE FILTER (RECOMMENDED METHOD):
- After searching, use the evaluate() action with this JavaScript code to set price filters:
{price_slider_js}
- Wait 5-8 seconds after executing for results to update
- Verify the filter was applied by checking visible product prices
- If sliders not found (returns success: false), fall back to clicking price filter buttons in the left sidebar
"""
        
        task = f"""
You are shopping on Amazon India. Your task is to:

Find and list the first {max_products} products that match: {intent.product}

SEARCH QUERY: {search_query}

SELECTION RULES:
{selection_rules}

IMPORTANT RULES:
- Go to https://www.amazon.in
- Search for the product using the search query above
{price_filter_instructions}
- After searching and applying filters, use the evaluate() action with this JavaScript code to extract products:
{product_extraction_js}
- This will return a result object with:
  * success: true/false
  * products: array of product objects with asin, title, price, rating, url, sponsored
  * count: number of products found
- Extract the first {max_products} non-sponsored products that match the requirements
- ⚠️ DO NOT add products to cart - only extract and list them
- ⚠️ DO NOT navigate to product pages - stay on the search results page
- Return the product list when done and stop the task

PAGE LOADING PATIENCE (CRITICAL):
- ⚠️ Amazon pages can take 5-10 seconds to fully load, especially search results
- ⚠️ DO NOT evaluate pages as "empty" or "blank" immediately after navigation
- ⚠️ ALWAYS wait at least 5-8 seconds after navigation before evaluating page state
- ⚠️ Check the DOM content and browser_state, not just visual appearance

HANDLING EMPTY PAGES:
- If search results page appears empty after applying price filter:
  1. Wait 10-15 seconds FIRST - Amazon pages load slowly
  2. Check browser_state and DOM content - if products are listed there, page IS loaded
  3. Only if truly empty after 15 seconds: Try refreshing the page
  4. If still empty, try search WITHOUT price filter first to verify products exist
- Only Non Sponsored products should be included in the list
- Return the first {max_products} products that satisfy the conditions
"""
        logger.debug(f"Task built, length: {len(task)} characters")

    # Choose LLM based on preference and API key availability
    import os
    if use_browser_use_llm and os.getenv('BROWSER_USE_API_KEY'):
        logger.info("Using ChatBrowserUse LLM")
        llm = ChatBrowserUse(
            timeout=180.0,
            max_retries=8,
            retry_max_delay=120.0,
        )
    else:
        logger.info(f"Using ChatOpenAI LLM with model: {MODEL_NAME}")
        llm = ChatOpenAI(model=MODEL_NAME)
    
    # Setup fallback LLM
    fallback_llm = None
    if use_browser_use_llm and os.getenv('BROWSER_USE_API_KEY'):
        if os.getenv('OPENAI_API_KEY'):
            fallback_llm = ChatOpenAI(model=MODEL_NAME)
            logger.info(f"Fallback LLM: ChatOpenAI with model {MODEL_NAME}")
    else:
        if os.getenv('BROWSER_USE_API_KEY'):
            fallback_llm = ChatBrowserUse(timeout=180.0, max_retries=8, retry_max_delay=120.0)
            logger.info("Fallback LLM: ChatBrowserUse")
    
    logger.info("Creating agent with browser for product listing...")
    agent = Agent(
        browser=Browser(
            headless=False,
            minimum_wait_page_load_time=3.0,
            wait_for_network_idle_page_load_time=8.0,
            wait_between_actions=2.0,
        ),
        llm=llm,
        fallback_llm=fallback_llm,
        task=task,
        max_steps=MAX_AGENT_STEPS,
        llm_timeout=180,
        step_timeout=300,
        max_failures=5,
    )

    logger.info(f"Running agent for product listing (max_steps={MAX_AGENT_STEPS})...")
    history = await agent.run()
    logger.info(f"Agent completed. Steps taken: {history.number_of_steps()}")

    # Extract products from agent history
    logger.debug("Extracting products from agent history...")
    products = []
    
    # Try to extract products from the final result or history
    final_result = history.final_result()
    if final_result and not products:
        try:
            import json
            import re
            # Try to parse as JSON first
            data = None
            if isinstance(final_result, str):
                try:
                    data = json.loads(final_result)
                except json.JSONDecodeError:
                    # Try to find JSON object in text
                    json_match = re.search(r'\{[^{}]*"products"[^{}]*\[.*?\][^{}]*\}', final_result, re.DOTALL)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(0))
                        except json.JSONDecodeError:
                            pass
            else:
                data = final_result
            
            # Check if it's a product list result in JSON format
            if isinstance(data, dict) and 'products' in data:
                product_list = data['products'][:max_products]
                for p in product_list:
                    if not p.get('sponsored', False) and p.get('asin'):
                        url = p.get('url', '')
                        if url:
                            try:
                                url = fix_product_url(url)
                            except Exception:
                                pass
                        products.append(ProductItem(
                            name=p.get('title', 'Unknown'),
                            price=p.get('price'),
                            rating=p.get('rating'),
                            url=url
                        ))
            elif isinstance(final_result, str):
                # Try parsing formatted text (fallback)
                logger.debug("Trying to parse formatted text from final result...")
                # Pattern to match product entries in formatted text
                # Accepts both `1)` / `1.` numbering, quoted or unquoted Title,
                # and Sponsored as yes/no/true/false (any case).
                product_pattern = (
                    r'(?:^|\n)\s*'                # line start
                    r'(\d+)[\)\.]'                # 1) or 1.
                    r'\s+([^\n]+?)\s*'            # product heading line
                    r'\n-\s*ASIN:\s*([A-Z0-9]+)\s*'
                    # Title: optional quotes -> capture inner or whole line
                    r'\n-\s*Title:\s*(?:"([^"\n]+)"|([^\n]+))\s*'
                    r'\n-\s*Price:\s*₹?(\d+)\s*'
                    r'\n-\s*Rating:\s*([\d.]+)\s*out of 5\s*'
                    r'\n-\s*URL:\s*([^\s\n]+)\s*'
                    r'\n-\s*Sponsored:\s*(\w+)\s*'
                )
                matches = list(re.finditer(product_pattern, final_result, re.MULTILINE))
                logger.debug(f"Regex found {len(matches)} product matches in final result")
                
                for match_idx, match in enumerate(matches):
                    try:
                        product_name = match.group(2).strip()
                        asin = match.group(3)
                        # Title: prefer quoted group, else unquoted
                        title = (match.group(4) or match.group(5) or "").strip()
                        price_str = match.group(6)
                        rating_str = match.group(7)
                        url = match.group(8)
                        sponsored_str = (match.group(9) or "").strip().lower()
                        
                        logger.debug(f"Match {match_idx + 1}: title={title[:50]}, price={price_str}, rating={rating_str}, sponsored={sponsored_str}")
                        
                        # Skip if sponsored (true/yes)
                        if sponsored_str in ('yes', 'true'):
                            logger.debug(f"Skipping sponsored product: {title[:50]}")
                            continue
                        
                        price = float(price_str) if price_str else None
                        rating = float(rating_str) if rating_str else None
                        
                        # Fix URL if needed
                        if url:
                            try:
                                url = fix_product_url(url)
                            except Exception:
                                pass
                        
                        product_item = ProductItem(
                            name=title or product_name,
                            price=price,
                            rating=rating,
                            url=url
                        )
                        products.append(product_item)
                        logger.info(f"✅ Extracted product {len(products)}: {title[:50]} - ₹{price}, {rating}⭐")
                    except Exception as e:
                        logger.warning(f"Failed to parse product from match {match_idx + 1}: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
                        continue
                
                if products:
                    logger.info(f"✅ Successfully parsed {len(products)} products from formatted text")
                else:
                    logger.warning(f"⚠️ Regex found {len(matches)} matches but no products were added")
        except Exception as e:
            logger.warning(f"Failed to parse products from final result: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    # Also check action results for product extraction (more reliable - from evaluate() action)
    if not products:
        action_results = history.action_results()
        logger.debug(f"Checking {len(action_results)} action results for products...")
        for idx, action_result in enumerate(action_results):
            if action_result and action_result.extracted_content:
                try:
                    import json
                    content = action_result.extracted_content
                    logger.debug(f"Action result {idx}: type={type(content)}, preview={str(content)[:200] if content else 'None'}")
                    
                    data = None
                    if isinstance(content, str):
                        try:
                            data = json.loads(content)
                        except json.JSONDecodeError:
                            # Try brace matching for nested JSON
                            brace_start = content.find('{')
                            if brace_start != -1:
                                brace_count = 0
                                for i in range(brace_start, len(content)):
                                    if content[i] == '{':
                                        brace_count += 1
                                    elif content[i] == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            json_str = content[brace_start:i+1]
                                            try:
                                                data = json.loads(json_str)
                                                logger.debug(f"Parsed JSON using brace matching")
                                                break
                                            except json.JSONDecodeError:
                                                pass
                    elif isinstance(content, (dict, list)):
                        data = content
                    
                    if isinstance(data, dict) and 'products' in data and isinstance(data['products'], list):
                        logger.info(f"Found {len(data['products'])} products in action result {idx}")
                        product_list = data['products'][:max_products]
                        for p in product_list:
                            if not p.get('sponsored', False) and p.get('asin') and p.get('title'):
                                url = p.get('url', '')
                                if url:
                                    try:
                                        url = fix_product_url(url)
                                    except Exception:
                                        pass
                                products.append(ProductItem(
                                    name=p.get('title', 'Unknown'),
                                    price=p.get('price'),
                                    rating=p.get('rating'),
                                    url=url
                                ))
                        if products:
                            logger.info(f"Successfully extracted {len(products)} products from action results")
                            break  # Use first successful extraction
                except Exception as e:
                    logger.debug(f"Failed to parse products from action result {idx}: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                    continue
    
    # Limit to max_products
    products = products[:max_products]
    
    if products:
        result = ProductListResult(
            success=True,
            products=products,
            count=len(products),
            message=f"Found {len(products)} products matching the criteria"
        )
        logger.info(f"✅ Successfully extracted {len(products)} products")
    else:
        result = ProductListResult(
            success=False,
            products=[],
            count=0,
            message="No products found matching the criteria"
        )
        logger.warning("❌ No products extracted")
    
    return result 