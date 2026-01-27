# """
# Amazon shopping automation using Browser-Use.

# This module provides functionality to automatically search for products on Amazon India
# and add them to cart based on natural language product intents.
# """
# # pyright: reportMissingImports=false
# import logging
# from browser_use import Agent, Browser, ChatOpenAI, ChatBrowserUse
# from models import CartResult, ProductIntent
# from dotenv import load_dotenv
# from typing import Optional

# load_dotenv()

# # Set up logger for this module
# logger = logging.getLogger(__name__)

# # =========================================================
# # CONFIGURATION
# # =========================================================

# AMAZON_URL = "https://www.amazon.in"

# SPONSORED_URL_PATTERNS = (
#     "/sspa/",
#     "sp_atk",
#     "sp_csd",
#     "sp_btf",
#     "sp_",
# )

# MAX_FILTER_ATTEMPTS = 2
# MAX_SCROLL_ATTEMPTS = 2
# MAX_AGENT_STEPS = 40

# # Use ChatBrowserUse by default (recommended for browser automation)
# # Fallback to ChatOpenAI if BROWSER_USE_API_KEY is not set
# MODEL_NAME = "gpt-4o-mini"


# # =========================================================
# # VALIDATION
# # =========================================================

# def validate_intent(intent: ProductIntent) -> None:
#     """Fail fast on invalid intent"""
#     logger.debug(f"Validating intent: product={intent.product}, constraints={intent.hard_constraints}")
    
#     if not intent.product or not intent.product.strip():
#         logger.error("Product name is required but was empty")
#         raise ValueError("Product name is required")

#     if intent.min_price and intent.max_price:
#         if intent.min_price > intent.max_price:
#             logger.error(f"Invalid price range: min_price ({intent.min_price}) > max_price ({intent.max_price})")
#             raise ValueError("min_price cannot exceed max_price")

#     if intent.min_rating:
#         if not (0 < intent.min_rating <= 5):
#             logger.error(f"Invalid rating: {intent.min_rating} (must be between 0 and 5)")
#             raise ValueError("min_rating must be between 0 and 5")
    
#     logger.info(f"Intent validated successfully: {intent.product}")


# # =========================================================
# # HELPER FUNCTIONS
# # =========================================================

# def is_sponsored(product: dict) -> bool:
#     """
#     Robust Amazon sponsored-product detection.
#     Designed for AI-driven browser automation.
    
#     Args:
#         product: Dictionary containing product information with keys like:
#                 - url: Product URL
#                 - labels: Product labels/text
#                 - aria_label: Accessibility label
#                 - sponsoredLoggingUrl: Amazon ad tracking URL
#                 - spAttributionURL: Sponsored attribution URL
#                 - adId: Ad identifier
#                 - clickTrackingParams: Click tracking parameters
#                 - data_ad_id: Data attribute for ad ID
#                 - data_ad: Data attribute for ad
#                 - data_sponsored: Data attribute for sponsored status
    
#     Returns:
#         True if product is sponsored, False otherwise
#     """
#     logger.debug(f"Checking if product is sponsored: {product.get('title', 'Unknown')[:50]}")
    
#     # Normalize once
#     url = (product.get("url") or "").lower()
#     labels = (product.get("labels") or "").lower()
#     aria = (product.get("aria_label") or "").lower()

#     # 1️⃣ Explicit Amazon ad infrastructure (STRONGEST)
#     if (
#         product.get("sponsoredLoggingUrl")
#         or product.get("spAttributionURL")
#         or product.get("adId")
#         or product.get("clickTrackingParams")
#     ):
#         logger.debug("Product is sponsored: explicit ad infrastructure detected")
#         return True

#     # 2️⃣ URL patterns Amazon never uses for organic results
#     if any(pattern in url for pattern in SPONSORED_URL_PATTERNS):
#         logger.debug(f"Product is sponsored: URL pattern detected in {url[:100]}")
#         return True

#     # 3️⃣ DOM / metadata indicators
#     if (
#         product.get("data_ad_id")
#         or product.get("data_ad")
#         or product.get("data_sponsored")
#     ):
#         logger.debug("Product is sponsored: DOM/metadata indicators detected")
#         return True

#     # 4️⃣ Visible disclosure text
#     if "sponsored" in labels:
#         logger.debug("Product is sponsored: 'sponsored' text found in labels")
#         return True

#     # 5️⃣ Accessibility labels
#     if "sponsored" in aria:
#         logger.debug("Product is sponsored: 'sponsored' text found in aria label")
#         return True

#     logger.debug("Product is NOT sponsored")
#     return False


# def build_product_extraction_js(min_rating: Optional[float] = None) -> str:
#     """
#     Build JavaScript code to extract product information and check sponsored status from DOM elements.
    
#     Args:
#         min_rating: Optional minimum rating to filter products (e.g., 4.0)
    
#     Returns:
#         JavaScript code string with functions to check sponsored status and extract product info
#     """
#     logger.debug(f"Building product extraction JavaScript code with min_rating={min_rating}")
#     min_rating_js = str(min_rating) if min_rating is not None else "null"
#     return """
#     (function() {
#     // Check if a product card is sponsored
#     function isSponsored(card) {
#         if (!card || !card.querySelector) {
#             return false;
#         }
        
#         // A. Ad-specific DOM attributes
#         if (card.querySelector('[data-ad-id], [data-sponsored], [data-ad-slot]')) {
#             return true;
#         }
        
#         // B. Sponsored routing / tracking links
#         for (const a of card.querySelectorAll('a[href]')) {
#             const href = a.href || '';
#             if (
#                 href.includes('/sspa/') ||
#                 href.includes('/gp/slredirect/') ||
#                 href.includes('sp_atk=') ||
#                 href.includes('sp_csd=') ||
#                 href.includes('sp_btf=')
#             ) {
#                 return true;
#             }
#         }
        
#         // C. Disclosure text (last line of defense)
#         if (card.innerText.toLowerCase().includes('sponsored')) {
#             return true;
#         }
        
#         return false;
#     }
    
#     // Extract price from product card
#     function extractPrice(card) {
#         const priceEl = card.querySelector('.a-price .a-offscreen');
#         if (!priceEl) return null;
        
#         return parseInt(
#             priceEl.textContent.replace(/[₹,]/g, ''),
#             10
#         );
#     }
    
#     // Extract rating from product card
#     function extractRating(card) {
#         const ratingEl = card.querySelector(
#             'i[data-cy="reviews-ratings-slot"] span.a-icon-alt'
#         );
        
#         if (!ratingEl) {
#             // Fallback to other selectors
#             const fallbackEl = card.querySelector('.a-icon-alt, [aria-label*="stars"]');
#             if (!fallbackEl) return null;
#             const ratingText = fallbackEl.innerText || fallbackEl.getAttribute('aria-label') || '';
#             const match = ratingText.match(/([\\d.]+)\\s*out of\\s*5/i);
#             return match ? parseFloat(match[1]) : null;
#         }
        
#         const match = ratingEl.textContent.match(/([\\d.]+)\\s*out of\\s*5/i);
#         return match ? parseFloat(match[1]) : null;
#     }
    
#     // Extract product information from DOM element
#     function extractProduct(card) {
#         if (!card) {
#             return null;
#         }
        
#         // Extract ASIN
#         const asin = card.getAttribute('data-asin') || null;
        
#         // Extract title
#         const titleEl = card.querySelector('h2 span, h2 a span, .s-title-instructions-style span');
#         const title = titleEl?.innerText?.trim() || 
#                      card.querySelector('h2')?.innerText?.trim() || 
#                      null;
        
#         // Extract price using extractPrice function
#         const price = extractPrice(card);
        
#         // Extract rating using extractRating function
#         const rating = extractRating(card);
        
#         // Extract URL
#         const linkEl = card.querySelector('a[href*="/dp/"], a[href*="/gp/product/"]');
#         let url = null;
#         if (linkEl) {
#             url = linkEl.href || linkEl.getAttribute('href');
#             // Make absolute if relative
#             if (url && url.startsWith('/')) {
#                 url = 'https://www.amazon.in' + url;
#             }
#         }
        
#         // Check sponsored status
#         const sponsored = isSponsored(card);
        
#         return {
#             asin: asin,
#             title: title,
#             price: price,
#             rating: rating,
#             url: url,
#             sponsored: sponsored
#         };
#     }
    
#     // Extract all products from search results page
#     function extractAllProducts() {
#         // Find all product cards using the most specific selector
#         const organicResults = Array.from(
#             document.querySelectorAll(
#                 'div[role="listitem"][data-component-type="s-search-result"][data-asin]'
#             )
#         ).filter(card => !isSponsored(card));
        
#         // Fallback: try other selectors if the main one doesn't work
#         let productElements = organicResults;
#         if (productElements.length === 0) {
#             const fallbackSelectors = [
#                 '[data-component-type="s-search-result"][data-asin]',
#                 '.s-result-item[data-asin]',
#                 '[data-asin]:not([data-asin=""])'
#             ];
            
#             for (const selector of fallbackSelectors) {
#                 const elements = document.querySelectorAll(selector);
#                 if (elements.length > 0) {
#                     productElements = Array.from(elements).filter(card => !isSponsored(card));
#                     break;
#                 }
#             }
#         }
        
#         // Extract product info from each element
#         const products = [];
#         for (const card of productElements) {
#             const product = extractProduct(card);
#             if (product && product.asin) {
#                 products.push(product);
#             }
#         }
        
#         // Filter by rating if min_rating is specified (after price check)
#         const minRating = {min_rating_js};
#         if (minRating !== null && minRating !== undefined) {{
#             const highRated = products.filter(product => {{
#                 const rating = product.rating;
#                 return rating !== null && rating >= minRating;
#             }});
#             return highRated;
#         }}
        
#         return products;
#     }
    
#     // Execute extraction immediately and return results
#     try {
#         const products = extractAllProducts();
#         return {
#             success: true,
#             products: products,
#             count: products.length
#         };
#     } catch (error) {
#         return {
#             success: false,
#             error: error.message,
#             products: []
#         };
#     }
#     })();
#     """


# def fix_product_url(url: str) -> str:
#     """
#     Fix malformed Amazon product URLs.
#     Handles relative URLs, incomplete URLs, and ensures proper domain.
#     """
#     logger.debug(f"Fixing product URL: {url[:100]}")
    
#     if not url or not url.strip():
#         logger.error("URL is empty")
#         raise ValueError("URL cannot be empty")
    
#     url = url.strip()
    
#     # If already a complete URL with protocol, validate domain
#     if url.startswith("http://") or url.startswith("https://"):
#         # Check if it's an Amazon URL
#         if "amazon.in" in url:
#             return url
#         # If it has protocol but wrong domain, try to extract product ID
#         if "/dp/" in url:
#             # Extract product ID and rebuild
#             parts = url.split("/dp/")
#             if len(parts) > 1:
#                 product_id = parts[1].split("/")[0].split("?")[0]
#                 fixed_url = f"{AMAZON_URL}/dp/{product_id}"
#                 logger.debug(f"Fixed URL by extracting product ID: {fixed_url}")
#                 return fixed_url
    
#     # If relative URL (starts with /)
#     if url.startswith("/"):
#         fixed_url = f"{AMAZON_URL}{url}"
#         logger.debug(f"Fixed relative URL: {fixed_url}")
#         return fixed_url
    
#     # If URL contains /dp/ but no domain
#     if "/dp/" in url:
#         # Extract product ID
#         parts = url.split("/dp/")
#         if len(parts) > 1:
#             product_id = parts[1].split("/")[0].split("?")[0]
#             fixed_url = f"{AMAZON_URL}/dp/{product_id}"
#             logger.debug(f"Fixed URL by extracting product ID from /dp/: {fixed_url}")
#             return fixed_url
    
#     # If it's just a product ID
#     if url.startswith("B") and len(url) == 10:
#         fixed_url = f"{AMAZON_URL}/dp/{url}"
#         logger.debug(f"Fixed URL from product ID: {fixed_url}")
#         return fixed_url
    
#     # Default: prepend Amazon domain
#     if not url.startswith("http"):
#         if url.startswith("/"):
#             fixed_url = f"{AMAZON_URL}{url}"
#         else:
#             fixed_url = f"{AMAZON_URL}/{url}"
#         logger.debug(f"Fixed URL by prepending domain: {fixed_url}")
#         return fixed_url
    
#     logger.debug(f"URL already valid: {url}")
#     return url


# # =========================================================
# # INTENT MODE
# # =========================================================

# def is_generic_intent(intent: ProductIntent) -> bool:
#     """
#     Generic intent:
#     - No hard brand constraint
#     - Minimal hard constraints
#     - Very short product name
#     """
#     has_hard_brand = intent.hard_constraints.get('brand')
#     has_many_attributes = len(intent.attributes) > 2
#     has_specific_model = len(intent.product.split()) > 2
    
#     return (
#         not has_hard_brand
#         and not has_many_attributes
#         and not has_specific_model
#     )


# def build_search_query(intent: ProductIntent, brand_override: Optional[str] = None) -> str:
#     """
#     Build Amazon search query from product + attributes + soft preferences.
    
#     Args:
#         intent: ProductIntent with search criteria
#         brand_override: If provided, use this brand instead of intent brands (for multi-brand search)
#     """
#     logger.debug(f"Building search query: product={intent.product}, brand_override={brand_override}")
#     parts = [intent.product]
    
#     # Add attributes to search (color, connectivity, type, etc.)
#     if intent.attributes:
#         parts.extend(intent.attributes.values())
    
#     # Add hard brand constraint if present
#     hard_brand = intent.hard_constraints.get('brand')
#     if hard_brand:
#         parts.insert(0, hard_brand)
#         return " ".join(str(p) for p in parts if p)
    
#     # Use brand override if provided (for multi-brand iteration)
#     if brand_override:
#         parts.insert(0, brand_override)
#         return " ".join(str(p) for p in parts if p)
    
#     # Add soft brand preference to search (helps ranking)
#     soft_brand = intent.soft_preferences.get('brand')
#     if soft_brand:
#         parts.insert(0, soft_brand)
    
#     # Check for multiple brands (list)
#     soft_brands = intent.soft_preferences.get('brands')
#     if soft_brands and isinstance(soft_brands, list) and soft_brands:
#         # Use first brand for initial search
#         parts.insert(0, soft_brands[0])
    
#     return " ".join(str(p) for p in parts if p)


# # def build_price_slider_js(min_price: Optional[float], max_price: Optional[float]) -> Optional[str]:
# #     """
# #     Build JavaScript code to directly manipulate Amazon price range sliders via DOM.
# #     Uses reverse engineering to set slider values directly.
    
# #     Args:
# #         min_price: Minimum price in rupees
# #         max_price: Maximum price in rupees
    
# #     Returns:
# #         JavaScript code string to execute, or None if no price filter needed
# #     """
# #     if min_price is None and max_price is None:
# #         return None
    
# #     # Build JavaScript with actual price values
# #     min_price_js = str(int(min_price)) if min_price is not None else 'null'
# #     max_price_js = str(int(max_price)) if max_price is not None else 'null'
    
# #     js_code = f"""
# #     (function() {{
# #         // First, try to find and click a matching quick filter button (more reliable)
# #         const targetMin = {min_price_js};
# #         const targetMax = {max_price_js};
# #         let quickFilterUsed = false;
        
# #         // Look for quick filter buttons that match our target range
# #         // Try multiple selectors to find price filter links
# #         const quickFilterSelectors = [
# #             'a[href*="price"]',
# #             'span.a-list-item a',
# #             'li[data-value] a',
# #             '.a-link-normal[href*="price"]',
# #             '.a-list-item a[href*="price"]',
# #             'ul.a-unordered-list li a'
# #         ];
        
# #         let allFilters = [];
# #         for (const selector of quickFilterSelectors) {{
# #             const filters = document.querySelectorAll(selector);
# #             allFilters = allFilters.concat(Array.from(filters));
# #         }}
        
# #         // Remove duplicates
# #         const uniqueFilters = Array.from(new Set(allFilters));
        
# #         for (const filter of uniqueFilters) {{
# #             const text = (filter.textContent || filter.innerText || '').trim();
# #             if (!text) continue;
            
# #             // Check if it matches our target range (e.g., "₹300 – ₹800" for target ₹300-₹600)
# #             if (targetMin !== null && targetMax !== null) {{
# #                 const rangeMatch = text.match(/₹([\\d,]+)\\s*[–-]\\s*₹([\\d,]+)/);
# #                 if (rangeMatch) {{
# #                     const filterMin = parseFloat(rangeMatch[1].replace(/,/g, ''));
# #                     const filterMax = parseFloat(rangeMatch[2].replace(/,/g, ''));
# #                     // Check if this range includes our target range (flexible matching)
# #                     if (filterMin <= targetMin && filterMax >= targetMax) {{
# #                         filter.click();
# #                         quickFilterUsed = true;
# #                         break;
# #                     }}
# #                     // Also try if the filter starts at our min price (we can adjust max with slider)
# #                     if (filterMin === targetMin && filterMax >= targetMin) {{
# #                         filter.click();
# #                         quickFilterUsed = true;
# #                         break;
# #                     }}
# #                 }}
# #             }} else if (targetMax !== null && targetMin === null) {{
# #                 // For "Under ₹X" - look for "Up to ₹X" or ranges ending at X or higher
# #                 const underMatch = text.match(/Up to ₹([\\d,]+)/i);
# #                 if (underMatch) {{
# #                     const filterMax = parseFloat(underMatch[1].replace(/,/g, ''));
# #                     if (filterMax >= targetMax) {{
# #                         filter.click();
# #                         quickFilterUsed = true;
# #                         break;
# #                     }}
# #                 }}
# #             }}
# #         }}
        
# #         if (quickFilterUsed) {{
# #             return {{ success: true, message: 'Used quick filter button' }};
# #         }}
        
# #         // If no quick filter found, use slider manipulation
# #         // Find price slider elements
# #         const minSlider = document.querySelector('input[id*="lower-bound-slider"]');
# #         const maxSlider = document.querySelector('input[id*="upper-bound-slider"]');
        
# #         if (!minSlider || !maxSlider) {{
# #             return {{ success: false, message: 'Price sliders not found' }};
# #         }}
        
# #         // Get slider min/max index range
# #         const sliderMin = parseFloat(minSlider.min) || 0;
# #         const sliderMax = parseFloat(maxSlider.max) || 174;
        
# #         // Extract price from text
# #         const extractPrice = (text) => {{
# #             if (!text) return null;
# #             const match = text.match(/[₹]?([\\d,]+)/);
# #             return match ? parseFloat(match[1].replace(/,/g, '')) : null;
# #         }};
        
# #         // Get current slider positions and prices to understand the mapping
# #         const currentMinIndex = parseFloat(minSlider.value) || 0;
# #         const currentMaxIndex = parseFloat(maxSlider.value) || 174;
# #         const currentMinPrice = extractPrice(minSlider.getAttribute('aria-valuetext') || '') || 0;
# #         const currentMaxPrice = extractPrice(maxSlider.getAttribute('aria-valuetext') || '') || 10000;
        
# #         // Better approach: Calculate both indices based on absolute price range
# #         // First, try to understand the full price range by checking slider extremes
# #         // Store original values
# #         const originalMinValue = minSlider.value;
# #         const originalMaxValue = maxSlider.value;
        
# #         // Temporarily move sliders to extremes to understand full range
# #         minSlider.value = sliderMin;
# #         minSlider.dispatchEvent(new Event('input', {{ bubbles: true }}));
# #         const absoluteMinPrice = extractPrice(minSlider.getAttribute('aria-valuetext') || '') || currentMinPrice;
        
# #         maxSlider.value = sliderMax;
# #         maxSlider.dispatchEvent(new Event('input', {{ bubbles: true }}));
# #         const absoluteMaxPrice = extractPrice(maxSlider.getAttribute('aria-valuetext') || '') || currentMaxPrice;
        
# #         // Restore original values
# #         minSlider.value = originalMinValue;
# #         maxSlider.value = originalMaxValue;
# #         minSlider.dispatchEvent(new Event('input', {{ bubbles: true }}));
# #         maxSlider.dispatchEvent(new Event('input', {{ bubbles: true }}));
        
# #         // Now calculate both indices based on absolute range
# #         const fullPriceRange = absoluteMaxPrice - absoluteMinPrice;
# #         const fullIndexRange = sliderMax - sliderMin;
# #         const absolutePricePerIndex = fullPriceRange > 0 && fullIndexRange > 0 ? fullPriceRange / fullIndexRange : 0;
        
# #         // Calculate slider indices from target prices using absolute range
# #         const calculateSliderIndex = (targetPrice) => {{
# #             if (absolutePricePerIndex > 0) {{
# #                 // Map price to index proportionally across full range
# #                 const priceRatio = (targetPrice - absoluteMinPrice) / fullPriceRange;
# #                 const sliderIndex = sliderMin + priceRatio * fullIndexRange;
# #                 return Math.max(sliderMin, Math.min(sliderMax, Math.round(sliderIndex)));
# #             }}
# #             // Fallback: use a simple linear mapping
# #             const ratio = targetPrice / 5000;
# #             return Math.round(sliderMin + ratio * (sliderMax - sliderMin));
# #         }};
        
# #         // Set min price slider by index
# #         let minIndexSet = null;
# #         if ({min_price_js} !== null) {{
# #             minIndexSet = calculateSliderIndex({min_price_js});
# #             minSlider.value = minIndexSet;
# #             // Trigger multiple events to ensure Amazon's JS recognizes the change
# #             minSlider.dispatchEvent(new Event('input', {{ bubbles: true, cancelable: true }}));
# #             minSlider.dispatchEvent(new Event('change', {{ bubbles: true, cancelable: true }}));
# #             minSlider.dispatchEvent(new MouseEvent('mousedown', {{ bubbles: true }}));
# #             minSlider.dispatchEvent(new MouseEvent('mouseup', {{ bubbles: true }}));
# #         }}
        
# #         // Set max price slider by index (using same absolute calculation)
# #         let maxIndexSet = null;
# #         if ({max_price_js} !== null) {{
# #             maxIndexSet = calculateSliderIndex({max_price_js});
# #             // Ensure max is always >= min
# #             if (minIndexSet !== null && maxIndexSet < minIndexSet) {{
# #                 maxIndexSet = minIndexSet + 1;
# #             }}
# #             maxSlider.value = maxIndexSet;
# #             // Trigger multiple events to ensure Amazon's JS recognizes the change
# #             maxSlider.dispatchEvent(new Event('input', {{ bubbles: true, cancelable: true }}));
# #             maxSlider.dispatchEvent(new Event('change', {{ bubbles: true, cancelable: true }}));
# #             maxSlider.dispatchEvent(new MouseEvent('mousedown', {{ bubbles: true }}));
# #             maxSlider.dispatchEvent(new MouseEvent('mouseup', {{ bubbles: true }}));
# #         }}
        
# #         // Try to find and click "Go" or apply button after a short delay
# #         setTimeout(() => {{
# #             const applyButtons = document.querySelectorAll(
# #                 'button[id*="price"], button[class*="price"], .a-button[class*="price"], ' +
# #                 'button[aria-label*="Go"], span.a-button-inner input[type="submit"], ' +
# #                 'input[type="submit"][value*="Go"], .a-button input[type="submit"]'
# #             );
# #             for (const btn of applyButtons) {{
# #                 const text = (btn.textContent || btn.innerText || btn.value || '').toLowerCase();
# #                 if (text.includes('go') || text.includes('apply') || text.trim() === 'go') {{
# #                     btn.click();
# #                     break;
# #                 }}
# #             }}
# #         }}, 500);
        
# #         // Return immediately with the values we set (verification happens after delay)
# #         return {{ 
# #             success: true, 
# #             message: 'Price sliders set: min={min_price_js} (index: ' + minIndexSet + '), max={max_price_js} (index: ' + maxIndexSet + ')',
# #             minIndex: minIndexSet,
# #             maxIndex: maxIndexSet,
# #             currentMinPrice: currentMinPrice,
# #             currentMaxPrice: currentMaxPrice,
# #             pricePerIndex: pricePerIndex
# #         }};
# #     }})();
# #     """
    
# #     return js_code
# def build_price_slider_js(min_price: Optional[float], max_price: Optional[float]) -> Optional[str]:
#     logger.debug(f"Building price slider JS: min_price={min_price}, max_price={max_price}")
    
#     if min_price is None and max_price is None:
#         logger.debug("No price constraints, skipping slider JS")
#         return None

#     min_js = str(int(min_price)) if min_price is not None else "null"
#     max_js = str(int(max_price)) if max_price is not None else "null"
#     logger.debug(f"Price slider JS generated: min={min_js}, max={max_js}")

#     return f"""
# (function () {{
#     const targetMin = {min_js};
#     const targetMax = {max_js};

#     const minSlider = document.querySelector('input[id*="lower-bound-slider"]');
#     const maxSlider = document.querySelector('input[id*="upper-bound-slider"]');

#     if (!minSlider || !maxSlider) {{
#         return {{ success: false, reason: "Sliders not found" }};
#     }}

#     const extractPrice = (text) => {{
#         if (!text) return null;
#         const m = text.match(/[₹]?([\\d,]+)/);
#         return m ? parseInt(m[1].replace(/,/g, ""), 10) : null;
#     }};

#     const setByPrice = (slider, target) => {{
#         const maxIndex = parseInt(slider.max, 10);
#         for (let i = 0; i <= maxIndex; i++) {{
#             slider.value = i;
#             slider.dispatchEvent(new Event("input", {{ bubbles: true }}));
#             const price = extractPrice(slider.getAttribute("aria-valuetext"));
#             if (price !== null && price >= target) {{
#                 slider.dispatchEvent(new Event("change", {{ bubbles: true }}));
#                 return {{ index: i, price }};
#             }}  
#         }}
#         return null;
#     }};

#     let minResult = null;
#     let maxResult = null;

#     if (targetMin !== null) {{
#         minResult = setByPrice(minSlider, targetMin);
#     }}

#     if (targetMax !== null) {{
#         maxResult = setByPrice(maxSlider, targetMax);
#     }}

#     // Safety: ensure max >= min
#     if (minResult && maxResult && maxResult.index < minResult.index) {{
#         maxSlider.value = minResult.index + 1;
#         maxSlider.dispatchEvent(new Event("input", {{ bubbles: true }}));
#         maxSlider.dispatchEvent(new Event("change", {{ bubbles: true }}));
#     }}

#     return {{
#         success: true,
#         min: minResult,
#         max: maxResult
#     }};
# }})();
# """


# def build_filter_instructions(intent: ProductIntent) -> tuple[str, str, str, Optional[float], Optional[float]]:
#     """
#     Build filter instructions for price, rating, and discount.
#     Returns (price_text, rating_text, discount_text, min_price, max_price)
#     """
#     logger.debug("Building filter instructions from intent")
#     price_text = ""
#     rating_text = ""
#     discount_text = ""
    
#     # Price filter
#     price_constraint = intent.hard_constraints.get('price', {})
#     min_price = price_constraint.get('min')
#     max_price = price_constraint.get('max')
    
#     if min_price and max_price:
#         price_text = f"₹{min_price} – ₹{max_price}"
#     elif max_price:
#         price_text = f"Under ₹{max_price}"
#     elif min_price:
#         price_text = f"Over ₹{min_price}"
    
#     # Rating filter
#     rating_constraint = intent.hard_constraints.get('rating', {})
#     min_rating = rating_constraint.get('min')
    
#     if min_rating:
#         rating_text = f"{min_rating} Stars & Up"
    
#     # Discount filter
#     discount_constraint = intent.hard_constraints.get('discount', {})
#     min_discount = discount_constraint.get('min')
    
#     if min_discount:
#         # Find closest Amazon discount filter
#         # Amazon typically has: 10%, 25%, 50%, 60% filters
#         if min_discount >= 50:
#             discount_text = "50% Off or more"
#         elif min_discount >= 25:
#             discount_text = "25% Off or more"
#         elif min_discount >= 10:
#             discount_text = "10% Off or more"
#         else:
#             discount_text = f"{min_discount}% Off or more"
    
#     logger.info(f"Filter instructions: price={price_text}, rating={rating_text}, discount={discount_text}, min_price={min_price}, max_price={max_price}")
#     return price_text, rating_text, discount_text, min_price, max_price


# def build_selection_rules(intent: ProductIntent, generic_mode: bool) -> str:
#     """
#     Build product selection rules based on intent.
#     """
#     rules = []
    
#     # Hard constraints (MUST satisfy)
#     rules.append("HARD CONSTRAINTS (MUST SATISFY):")
    
#     # Price constraint
#     price_constraint = intent.hard_constraints.get('price', {})
#     min_price = price_constraint.get('min')
#     max_price = price_constraint.get('max')
#     if min_price:
#         rules.append(f"- Price ≥ ₹{min_price}")
#     if max_price:
#         rules.append(f"- Price ≤ ₹{max_price}")
    
#     # Rating constraint
#     rating_constraint = intent.hard_constraints.get('rating', {})
#     min_rating = rating_constraint.get('min')
#     max_rating = rating_constraint.get('max')
#     if min_rating:
#         rules.append(f"- Rating ≥ {min_rating} stars")
#     if max_rating:
#         rules.append(f"- Rating ≤ {max_rating} stars")
    
#     # Discount constraint
#     discount_constraint = intent.hard_constraints.get('discount', {})
#     min_discount = discount_constraint.get('min')
#     if min_discount:
#         rules.append(f"- Discount ≥ {min_discount}%")
    
#     # Hard brand constraint
#     hard_brand = intent.hard_constraints.get('brand')
#     if hard_brand and not generic_mode:
#         rules.append(f"- Brand MUST be: {hard_brand}")
    
#     # Product attributes (should match search context)
#     if intent.attributes and not generic_mode:
#         rules.append("\nPRODUCT ATTRIBUTES (should be present in listing):")
#         for attr_name, attr_value in intent.attributes.items():
#             rules.append(f"- {attr_name.title()}: {attr_value}")
    
#     # Soft preferences (nice to have, use for sorting)
#     if intent.soft_preferences:
#         rules.append("\nSOFT PREFERENCES (prefer but not required):")
        
#         # Single brand preference
#         soft_brand = intent.soft_preferences.get('brand')
#         if soft_brand:
#             rules.append(f"- PREFER {soft_brand} but accept other brands if constraints met")
        
#         # Multiple brands preference
#         soft_brands = intent.soft_preferences.get('brands')
#         if soft_brands and isinstance(soft_brands, list):
#             brands_str = " OR ".join(soft_brands)
#             rules.append(f"- PREFER {brands_str} (try each brand one by one)")
#             rules.append(f"  Search order: {' → '.join(soft_brands)} → generic")
        
#         # Other preferences
#         for pref_name, pref_value in intent.soft_preferences.items():
#             if pref_name not in ('brand', 'brands'):
#                 rules.append(f"- Prefer {pref_name}: {pref_value}")
    
#     if not rules[1:]:  # Only header, no actual rules
#         rules.append("- None (select first valid non-sponsored product)")
    
#     return "\n".join(rules)


# # =========================================================
# # TASK BUILDER
# # =========================================================

# def build_task(intent: ProductIntent) -> str:
#     logger.info("Building task instructions for agent...")
#     validate_intent(intent)

#     generic_mode = is_generic_intent(intent)
#     logger.debug(f"Generic mode: {generic_mode}")
#     search_query = build_search_query(intent)
#     price_text, rating_text, discount_text, min_price, max_price = build_filter_instructions(intent)
#     selection_rules = build_selection_rules(intent, generic_mode)
#     logger.debug(f"Selection rules built: {len(selection_rules)} characters")
    
#     # Get min_rating for JavaScript filtering
#     rating_constraint = intent.hard_constraints.get('rating', {})
#     min_rating = rating_constraint.get('min')
    
#     # Extract key search terms for title validation
#     search_terms = search_query.lower().split()
#     # Remove common stop words that might cause false negatives
#     stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'including', 'against', 'among', 'throughout', 'despite', 'towards', 'upon', 'concerning', 'to', 'of', 'in', 'for', 'on', 'at', 'by', 'with', 'from', 'up', 'about', 'into', 'through', 'during', 'including', 'against', 'among', 'throughout', 'despite', 'towards', 'upon', 'concerning'}
#     key_search_terms = [term for term in search_terms if term not in stop_words and len(term) > 2]
#     # Fallback to original search query if no key terms found
#     if not key_search_terms:
#         key_search_terms = search_terms[:3]  # Use first 3 terms as fallback
#     key_search_terms_str = ", ".join(f'"{term}"' for term in key_search_terms[:5])  # Limit to first 5 terms
#     logger.debug(f"Key search terms for title validation: {key_search_terms_str}")
    
#     # Check for multiple preferred brands
#     soft_brands = intent.soft_preferences.get('brands', [])
#     has_multiple_brands = isinstance(soft_brands, list) and len(soft_brands) > 1
#     brand_search_instructions = ""
    
#     if has_multiple_brands:
#         brand_list = ", ".join(f"'{b}'" for b in soft_brands)
#         brand_search_instructions = f"""
# MULTI-BRAND SEARCH STRATEGY:
# You have multiple preferred brands: {brand_list}

# Try each brand ONE BY ONE:
# 1. Search "{soft_brands[0]} {intent.product}" first
# 2. Apply filters, scroll, extract products
# 3. If valid non-sponsored product found → NAVIGATE to it → Add to cart → DONE
# 4. If NO valid product found:
#    - Go back to Amazon home
#    - Search "{soft_brands[1] if len(soft_brands) > 1 else 'next'} {intent.product}"
#    - Apply filters again
#    - Extract products
#    - If valid product found → NAVIGATE → Add to cart → DONE
# {f'5. If still not found, try "{soft_brands[2]} {intent.product}"' if len(soft_brands) > 2 else ''}
# {f'6. If no preferred brands work, search generic "{intent.product}"' if soft_brands else ''}

# IMPORTANT:
# - Try each brand separately with fresh search
# - Only move to next brand if current brand has NO valid products
# - Don't mix products from different brand searches
# """
#     else:
#         brand_search_instructions = ""

#     return f"""
# You are a REAL HUMAN shopping on Amazon India.

# ==================================================
# ABSOLUTE RULES (NEVER BREAK)
# ==================================================

# 1. ❌ NO SPONSORED PRODUCTS
#    - If label shows: Sponsored / Ad / Promoted → DISCARD
#    - If URL contains any of:
#      {", ".join(SPONSORED_URL_PATTERNS)}
#      → DISCARD IMMEDIATELY

# 2. 🛑 ADD TO CART EXACTLY ONCE
#    - One click only
#    - No retries
#    - No alternatives

# 3. 🎯 MODE
#    - {"GENERIC MODE (flexible matching)" if generic_mode else "SPECIFIC MODE (match attributes + constraints)"}
# {brand_search_instructions}
# 4. 🚫 ANTI-HALLUCINATION RULES
#    - ONLY use actions that exist: navigate, click, input, extract, scroll, wait, evaluate, done
#    - DO NOT try to input() into elements that don't exist
#    - DO NOT use element indices from extracted data - use URLs
#    - After finding valid product → NAVIGATE to its URL immediately
#    - DO NOT scroll indefinitely - max {MAX_SCROLL_ATTEMPTS} scrolls
#    - If stuck → FAIL with clear error, don't loop
#    - DO NOT try to sign in or provide credentials
#    - DO NOT proceed to checkout/payment
#    - Task ends at "Add to Cart" - nothing after that

# ==================================================
# STEP 1 — SEARCH
# ==================================================

# - Go to {AMAZON_URL}
# - Wait 4–5 seconds
# - Search for: "{search_query}"
# - Press Enter
# - Wait for results to load

# ==================================================
# STEP 2 — APPLY FILTERS FIRST (CRITICAL - DO THIS IMMEDIATELY AFTER SEARCH)
# ==================================================

# ⚠️ IMPORTANT: Apply filters BEFORE extracting products. This reduces irrelevant results!

# Amazon has filters in the LEFT SIDEBAR. USE THEM FIRST - they improve results quality!

# FILTER DISCOVERY:
# - Scroll down LEFT sidebar to see all available filters
# - Common filters: Price, Rating, Discount, Brand, Size, Color, etc.

# FILTERS TO APPLY (in order):

# 1. PRICE FILTER (if price constraint exists):
# {f"   - Look for 'Price' section in left sidebar" if price_text else "   - Skip (no price constraint)"}
# {f"   - Target filter: '{price_text}'" if price_text else ""}
# {f"   - FILTER APPLICATION STRATEGY (try in this order):" if price_text else ""}
# {f"     * METHOD 1 (RECOMMENDED - Direct DOM manipulation):" if price_text else ""}
# {f"       Use evaluate() action with this JavaScript code to directly set price sliders:" if price_text else ""}
# {f"       {build_price_slider_js(min_price, max_price) if build_price_slider_js(min_price, max_price) else ''}" if price_text else ""}
# {f"       - This directly manipulates the price range sliders in the DOM" if price_text else ""}
# {f"       - After executing, wait 3-4 seconds for results to update" if price_text else ""}
# {f"       - VERIFY the filter was applied: Check the slider shows approximately ₹{int(min_price) if min_price else 'N/A'} – ₹{int(max_price) if max_price else 'N/A'}" if price_text else ""}
# {f"       - If verification shows wrong range, try METHOD 2 (click filter buttons)" if price_text else ""}
# {f"       - If this works correctly, skip to STEP 3 (extract products)" if price_text else ""}
# {f"     * METHOD 2 (Fallback - Click filter buttons):" if price_text else ""}
# {f"       - Try to find EXACT match: '{price_text}'" if price_text else ""}
# {f"     * If exact match NOT found:" if price_text and max_price else ""}
# {f"       - For 'Under ₹{int(max_price)}': Look for a range that INCLUDES or GOES UP TO ₹{int(max_price)}" if price_text and max_price else ""}
# {f"       - Good options (in priority order):" if price_text and max_price else ""}
# {f"         1. '₹200 - ₹{int(max_price)}' (if exists and {int(max_price)} >= 200)" if price_text and max_price and max_price >= 200 else ""}
# {f"         2. '₹300 - ₹{int(max_price)}' (if exists and {int(max_price)} >= 300)" if price_text and max_price and max_price >= 300 else ""}
# {f"         3. 'Up to ₹{int(max_price)}' (if exists)" if price_text and max_price else ""}
# {f"         4. Any range ending at ₹{int(max_price)} or higher" if price_text and max_price else ""}
# {f"       - CRITICAL: DO NOT pick a range with maximum LESS than ₹{int(max_price)}" if price_text and max_price else ""}
# {f"       - ❌ WRONG EXAMPLES:" if price_text and max_price and max_price > 200 else ""}
# {f"         * 'Up to ₹200' if you need 'Under ₹{int(max_price)}' (WRONG - too restrictive!)" if price_text and max_price and max_price > 200 else ""}
# {f"         * 'Up to ₹{int(max_price // 2)}' if you need 'Under ₹{int(max_price)}' (WRONG!)" if price_text and max_price and max_price >= 400 else ""}
# {f"     * If exact match NOT found:" if price_text and min_price and not max_price else ""}
# {f"       - For 'Over ₹{int(min_price)}': Look for ranges starting from ₹{int(min_price)} or lower" if price_text and min_price and not max_price else ""}
# {f"     * If range '{price_text.split('–')[0] if '–' in price_text else price_text} - {price_text.split('–')[1] if '–' in price_text else ''}' NOT found:" if price_text and min_price and max_price else ""}
# {f"       - Look for range that includes both ₹{int(min_price)} and ₹{int(max_price)}" if price_text and min_price and max_price else ""}
# {f"       - Or use 'Under ₹{int(max_price)}' if available" if price_text and min_price and max_price else ""}
# {f"   - After selecting filter, wait 3-4 seconds for results to update" if price_text else ""}
# {f"   - Verify filter applied correctly by checking URL or visible price ranges" if price_text else ""}

# 2. RATING FILTER (if rating constraint exists):
# {f"   - Look for 'Customer Review' or 'Avg. Customer Review' section" if rating_text else "   - Skip (no rating constraint)"}
# {f"   - Click on: '{rating_text}' or '⭐⭐⭐⭐ & Up'" if rating_text else ""}
# {f"   - Wait 3-4 seconds after applying" if rating_text else ""}

# 3. DISCOUNT FILTER (if discount constraint exists):
# {f"   - Look for 'Discount' or 'Offers' section in left sidebar" if discount_text else "   - Skip (no discount constraint)"}
# {f"   - Scroll down sidebar if not visible initially" if discount_text else ""}
# {f"   - Click on: '{discount_text}' or closest matching option" if discount_text else ""}
# {f"   - Common options: '10% Off or more', '25% Off or more', '50% Off or more'" if discount_text else ""}
# {f"   - Wait 3-4 seconds after applying" if discount_text else ""}

# 4. ATTRIBUTE FILTERS (size, color, brand):
# {f"   - SIZE: Look for 'Size' filter, select '{intent.attributes.get('size')}'" if intent.attributes.get('size') else "   - Skip size (not specified)"}
# {f"   - COLOR: Look for 'Colour' filter, select '{intent.attributes.get('color')}'" if intent.attributes.get('color') else "   - Skip color (not specified)"}
# {f"   - BRAND: Look for 'Brand' filter, select '{intent.hard_constraints.get('brand')}'" if intent.hard_constraints.get('brand') else "   - Skip brand filter (not a hard constraint)"}

# FILTERING STRATEGY:
# - Try each relevant filter (max {MAX_FILTER_ATTEMPTS} attempts per filter)
# - If a filter is not visible, scroll down the LEFT sidebar
# - If a filter doesn't work after {MAX_FILTER_ATTEMPTS} attempts → skip it and continue
# - Filters significantly reduce irrelevant results - use them when possible!

# FILTER VERIFICATION (after applying price filter):
# {f"- Check if filter was applied correctly:" if price_text and max_price else ""}
# {f"  * Look at URL - should contain price filter parameters" if price_text and max_price else ""}
# {f"  * Check visible products - prices should be ≤ ₹{int(max_price)}" if price_text and max_price else ""}
# {f"  * If wrong filter applied (e.g., 'Up to ₹200' instead of 'Under ₹{int(max_price)}'):" if price_text and max_price else ""}
# {f"    - Clear the filter and try again with correct one" if price_text and max_price else ""}

# ==================================================
# STEP 3 — EXTRACT PRODUCTS (AFTER FILTERS APPLIED)
# ==================================================

# After filters are applied, extract ALL visible products on screen.

# METHOD 1 (RECOMMENDED - DOM-based extraction):
# ⚠️ CRITICAL: Use evaluate() action (NOT extract() action) with this JavaScript code:

# {build_product_extraction_js(min_rating)}

# ❌ DO NOT use extract() action!
# ✅ USE evaluate() action with the code parameter set to the JavaScript code above!

# This SINGLE evaluate() call will:
# 1. Define all necessary functions (isSponsoredProduct, extractProduct, extractAllProducts)
# 2. Automatically extract all products from the page
# 3. Return a result object with success status and products array

# The result will have this structure (JavaScript object):
# - success: true or false
# - products: array of product objects
# - count: number of products found
# - error: error message (only if success is false)

# Each product object in the products array contains:
#    - asin: Product ASIN identifier
#    - title: Product name
#    - price: Numeric price value
#    - rating: Numeric rating value
#    - url: Full product URL
#    - sponsored: Boolean indicating if product is sponsored

# ⚠️ CRITICAL: 
# - If the result.success is false, check result.error for the error message and use METHOD 2 (LLM extraction) as fallback.
# - If you get a JavaScript error, the functions might not be defined - make sure you're using evaluate() action, not extract() action!

# METHOD 2 (Fallback - LLM extraction):
# ONLY use this if METHOD 1 fails. Use extract() action:
# - Get products in DISPLAY ORDER (top to bottom)
# - For EACH product collect:
#   - name (full product name)
#   - price (numeric value only, e.g. 78, 149)
#   - rating (numeric value, e.g. 4.0, 4.3)
#   - sponsored status (check for "Sponsored" label)
#   - FULL URL (must include /dp/ or product identifier)

# EXTRACTION NOTES:
# - Extract products AFTER filters are applied
# - Get products in DISPLAY ORDER (top to bottom)
# - Valid non-sponsored products may be visible already

# ==================================================
# STEP 4 — CHECK PRODUCTS (AVOID SPONSORED, VERIFY ALL CONDITIONS)
# ==================================================

# Process extracted products IN ORDER (top to bottom):

# FOR EACH PRODUCT (check systematically, one at a time):

# 1. ❌ AVOID SPONSORED PRODUCTS (skip immediately):
   
#    If you used METHOD 1 (DOM extraction) in STEP 3, check the result object:
#    - Access products: result.products (array of product objects)
#    - Each product has a 'sponsored' field already set
#    - If product.sponsored === true → SKIP to next product immediately
#    - DO NOT check price/rating for sponsored products
   
#    If you used extract() action instead, check manually:
#    - Has "Sponsored" label? → SKIP to next product
#    - URL contains /sspa/ or sp_atk or sp_csd or sp_btf or sp_? → SKIP to next product
#    - DO NOT check price/rating for sponsored products
   
# 2. ✅ IF NON-SPONSORED, VERIFY ALL QUERY CONDITIONS:
   
#    FIRST: Check product title relevance (CRITICAL - PREVENTS WRONG PRODUCTS):
#    - ✓ Product title must contain key terms from search query: {key_search_terms_str}
#    - ✓ If title doesn't contain at least ONE key search term → SKIP immediately (wrong product type)
#    - Example: If searching for "protein bar", title must contain "protein" OR "bar" (or related terms like "protein", "bar", "snack")
#    - ❌ WRONG: "Electric Kettle" when searching for "protein bar" → SKIP (no match)
#    - ❌ WRONG: "Mouse" when searching for "keyboard" → SKIP (no match)
#    - ✅ CORRECT: "Protein Bar 20g" when searching for "protein bar" → Continue checking
   
#    THEN: Check other conditions:
#    {selection_rules}
   
#    CHECK ALL CONDITIONS FROM QUERY:
#    - ✓ Title matches search query? (MUST PASS - see above)
#    - ✓ Price within range? (if price constraint exists)
#    - ✓ Rating meets minimum? (if rating constraint exists)
#    - ✓ Discount meets minimum? (if discount constraint exists)
#    - ✓ Attributes match? (if attributes specified)
#    - ✓ Brand matches? (if hard brand constraint exists)
   
#    ALL CONDITIONS MUST BE MET to select this product.
   
# 3. IF NON-SPONSORED + ALL CONDITIONS MET:
#    - ✅ This is your product! 
#    - ⚠️ IMPORTANT: REMEMBER this product's details:
#      * Product name: [EXACT NAME FROM EXTRACTION]
#      * Product price: [EXACT PRICE FROM EXTRACTION]
#      * Product URL: [EXACT URL FROM EXTRACTION]
#      * Product rating: [EXACT RATING FROM EXTRACTION if available]
#    - You will need these details in STEP 6 to verify the product page matches
#    - STOP checking other products
#    - Proceed to STEP 5 (Open product page)
   
# 4. IF SPONSORED OR ANY CONDITION NOT MET:
#    - ❌ Skip this product
#    - Continue to next product in list

# EXAMPLE FLOW (Query: "mouse under ₹100, rating 4+"):
# Product 1: "Dell Mouse" - Sponsored ❌ → Skip (don't check price/rating)
# Product 2: "HP Mouse ₹299, 4.5★" - Non-sponsored ✓, but price ₹299 > ₹100 ❌ → Skip
# Product 3: "Logitech Mouse ₹89, 3.8★" - Non-sponsored ✓, price ₹89 < ₹100 ✓, but rating 3.8 < 4.0 ❌ → Skip
# Product 4: "Generic Mouse ₹78, 4.2★" - Non-sponsored ✓, price ₹78 < ₹100 ✓, rating 4.2 ≥ 4.0 ✓ → SELECT THIS!
# Stop checking, navigate to Product 4

# AFTER CHECKING ALL VISIBLE PRODUCTS:
# - If valid non-sponsored product found → Go to STEP 5 (Open product page)
# - If NO valid product found → Go to STEP 4.1 (Scroll)

# ==================================================
# STEP 4.1 — SCROLL (ONLY IF NO VALID PRODUCT FOUND)
# ==================================================

# ONLY execute this if NO valid products found in visible area.

# - Scroll down 1 full screen height
# - Wait 2 seconds for new products to load
# - Extract newly visible products
# - Repeat STEP 4 (check each product sequentially for sponsored + conditions)

# SCROLL LIMITS:
# - Maximum {MAX_SCROLL_ATTEMPTS} scroll attempts
# - If still no valid products after {MAX_SCROLL_ATTEMPTS} scrolls → FAIL with error

# ==================================================
# STEP 5 — OPEN PRODUCT PAGE
# ==================================================

# You have identified a valid non-sponsored product that meets ALL query conditions.

# OPEN THE PRODUCT PAGE:

# 1. GET THE PRODUCT URL from Step 4
#    - Example: https://www.amazon.in/dp/B074N7X12P
#    - URL must be complete and valid
   
# 2. ⚠️ CRITICAL: FIX THE URL BEFORE NAVIGATING
#    - Check if URL starts with "http://" or "https://"
#    - If NOT, it's a relative/incomplete URL - you MUST fix it:
#      * If URL starts with "/" → prepend "https://www.amazon.in"
#      * If URL contains "/dp/" but no domain → extract product ID and build: "https://www.amazon.in/dp/PRODUCT_ID"
#      * If URL is just a product ID (starts with "B" and 10 chars) → build: "https://www.amazon.in/dp/PRODUCT_ID"
#      * Always ensure URL format: "https://www.amazon.in/dp/BXXXXXXXXXX"
   
#    EXAMPLES OF URL FIXING:
#    - "/dp/B074N7X12P" → "https://www.amazon.in/dp/B074N7X12P"
#    - "MILTON-Stainless-Electric-Protection-Cool-touch/dp/B0G3PX33RC" → "https://www.amazon.in/dp/B0G3PX33RC"
#    - "B0G3PX33RC" → "https://www.amazon.in/dp/B0G3PX33RC"
#    - "https://MILTON-Stainless-Electric-Protection-Cool-touch/dp/B0G3PX33RC" → "https://www.amazon.in/dp/B0G3PX33RC"
   
#    URL FIXING LOGIC:
#    - If URL has "https://" or "http://" but wrong domain → extract product ID from "/dp/PRODUCT_ID" and rebuild
#    - If URL contains "/dp/" anywhere → extract the product ID (the part after "/dp/" before any "/" or "?")
#    - Product ID format: starts with "B" followed by 9 alphanumeric characters (e.g., "B0G3PX33RC")
#    - Final URL must be: "https://www.amazon.in/dp/PRODUCT_ID"
   
# 3. NAVIGATE to the FIXED URL:
#    - Use navigate(url=FIXED_PRODUCT_URL) action
#    - DO NOT navigate with malformed URLs
#    - DO NOT try to click elements by index
#    - DO NOT open new tabs
   
# 4. Wait 4-5 seconds for product page to load

# 5. You should now be on the product detail page (/dp/ URL)

# IMPORTANT:
# - ALWAYS fix URLs before navigating - malformed URLs cause navigation failures (ERR_NAME_NOT_RESOLVED)
# - Product is already verified (non-sponsored + meets all conditions)
# - Just open the page - no additional checking needed

# ==================================================
# STEP 6 — VERIFY PRODUCT PAGE (CRITICAL - PREVENTS LOOPS)
# ==================================================

# You should now be on the product detail page (/dp/ URL).

# ⚠️ CRITICAL: You MUST verify this is the CORRECT product that you selected in STEP 4!

# VERIFICATION STEPS:

# 1. BASIC PAGE CHECK:
#    - Check current URL using evaluate: window.location.href
#    - URL should contain /dp/ or /gp/aw/d/
#    - Product page should load correctly (not error page)
#    - If page didn't load → treat as "WRONG PRODUCT" and follow error handling below

# 2. VERIFY PRODUCT MATCHES SELECTED PRODUCT:
#    - Extract product details from current page using extract() action:
#      * Extract product name (title/heading)
#      * Extract product price
#      * Extract product URL (from window.location.href)
#      * Extract product rating (if visible)
   
#    - COMPARE with the product you selected in STEP 4:
#      * Does the URL match (or contain the same product ID)?
#      * Does the product name match (or is very similar)?
#      * Does the price match (or is within reasonable range - prices can vary slightly)?
   
#    - ✅ IF PRODUCT MATCHES:
#      * URL matches AND name matches → This is the correct product!
#      * Proceed to STEP 7 (Add to cart)
   
#    - ❌ IF PRODUCT DOES NOT MATCH:
#      * URL different OR name completely different → WRONG PRODUCT!
#      * Treat as "WRONG PRODUCT" and follow error handling below

# IF PAGE DIDN'T LOAD OR WRONG PRODUCT:
#   ⚠️ CRITICAL: Follow these steps EXACTLY to avoid infinite loops:
  
#   1. Go BACK to search results using go_back() action
#   2. Wait 2-3 seconds for page to load
#   3. VERIFY you're on search results page:
#      - Use evaluate: window.location.href to check URL
#      - URL MUST contain /s?k= (search results pattern)
#      - If URL still contains /dp/ → you're still on product page!
   
#   4. IF NOT ON SEARCH RESULTS (URL still has /dp/):
#      - Navigate back again using go_back() one more time
#      - OR navigate directly to search URL if you remember it
#      - Wait 2-3 seconds
#      - Verify URL contains /s?k= again
   
#   5. IF ON SEARCH RESULTS (URL contains /s?k=):
#      - You already have extracted products from Step 3
#      - DO NOT extract products again (this causes loops!)
#      - Instead: Skip the current failed product
#      - Try the NEXT product from your previously extracted list
#      - Navigate to that product's URL
#      - Repeat STEP 6 verification
   
#   6. IF ALL PRODUCTS FROM EXTRACTION FAILED:
#      - Extract products again (only if on search results with /s?k=)
#      - Check each product sequentially
#      - Maximum 3 product attempts before failing

# IMPORTANT ANTI-LOOP RULES:
# - ❌ NEVER extract products if URL contains /dp/ (product page)
# - ✅ ALWAYS verify URL contains /s?k= before extracting
# - ✅ If you already extracted products, reuse that list
# - ✅ Skip failed products and try next one
# - ❌ Don't extract products repeatedly from same page

# ==================================================
# STEP 7 — ADD TO CART
# ==================================================

# ADD THE PRODUCT TO CART:

# 1. Click "Add to Cart" button ONCE
#    - Look for button with text "Add to Cart" or id="add-to-cart-button"
#    - Click it exactly ONCE
   
# 2. Wait 4–5 seconds for confirmation

# 3. Close any popups if shown:
#    - Warranty/protection plan popups → Click "No thanks" or close
#    - DO NOT click "Proceed to Buy" or "Go to Cart"

# 🚫 ADD TO CART RULES:
# - NEVER click "Add to Cart" on search/results pages
# - ONLY add to cart on product detail page (/dp/ or /gp/aw/d/)
# - Click exactly ONCE - no retries

# ==================================================
# STEP 8 — VERIFY ADDED & END TASK
# ==================================================

# VERIFY ITEM WAS ADDED by checking ANY of:
# 1. "Added to Cart" confirmation message appears
# 2. Cart icon shows count increased (e.g., "1" badge on cart)
# 3. "Go to Cart" button visible
# 4. Can see "Subtotal" or cart summary

# IF VERIFICATION SUCCEEDS:
# - Extract final product details (name, price, rating, URL)
# - Use DONE action
# - Return CartResult JSON with the product
# - TASK COMPLETE - STOP HERE

# IF SIGN-IN PAGE APPEARS:
# - Task is ALREADY COMPLETE (item was added to cart)
# - Don't try to sign in
# - Don't fill any forms
# - Just return the CartResult

# FINAL RULES:
# ❌ DO NOT click "Proceed to Buy" or "Proceed to Checkout"
# ❌ DO NOT try to complete purchase
# ❌ DO NOT fill in any forms or sign-in pages
# ❌ DO NOT navigate to checkout/payment pages
# ✅ After adding to cart → DONE immediately
# ✅ After DONE → STOP (no retries, no additional actions)
# """


# # =========================================================
# # RUNNER
# # =========================================================

# async def run_browser_agent(intent: ProductIntent, use_browser_use_llm: bool = True) -> CartResult:
#     """
#     Run browser agent to add product to Amazon cart.
    
#     Args:
#         intent: ProductIntent with product search criteria
#         use_browser_use_llm: If True, use ChatBrowserUse (recommended). 
#                            If False, use ChatOpenAI.
    
#     Returns:
#         CartResult with the added product or error information
#     """
#     logger.info(f"Starting browser agent for product: {intent.product}")
#     logger.info(f"Intent details: {intent.hard_constraints}, {intent.soft_preferences}")
    
#     validate_intent(intent)

#     # Choose LLM based on preference and API key availability
#     import os
#     if use_browser_use_llm and os.getenv('BROWSER_USE_API_KEY'):
#         logger.info("Using ChatBrowserUse LLM")
#         llm = ChatBrowserUse()
#     else:
#         logger.info(f"Using ChatOpenAI LLM with model: {MODEL_NAME}")
#         llm = ChatOpenAI(model=MODEL_NAME)

#     logger.debug("Building task instructions...")
#     task = build_task(intent)
#     logger.debug(f"Task built, length: {len(task)} characters")
    
#     logger.info("Creating agent with browser...")
#     agent = Agent(
#         browser=Browser(headless=False),
#         llm=llm,
#         task=task,
#         output_model_schema=CartResult,
#         max_steps=MAX_AGENT_STEPS,
#     )

#     logger.info(f"Running agent (max_steps={MAX_AGENT_STEPS})...")
#     history = await agent.run()
#     logger.info(f"Agent completed. Steps taken: {history.number_of_steps()}")

#     # Try to get structured output
#     logger.debug("Extracting result from agent history...")
#     result = history.structured_output
    
#     # Fallback: try to get structured output using the method
#     if result is None:
#         logger.debug("No structured_output found, trying get_structured_output method...")
#         result = history.get_structured_output(CartResult)
    
#     # If still None, create a failure result
#     if result is None:
#         logger.warning("No structured output found, attempting to extract from history...")
#         # Check if task was completed successfully
#         if history.is_done():
#             logger.info("Task marked as done, extracting final result...")
#             # Task completed but no structured output - try to extract from final result
#             final_result = history.final_result()
#             if final_result:
#                 try:
#                     # Try to parse as JSON
#                     import json
#                     logger.debug(f"Parsing final result as JSON: {final_result[:200]}")
#                     data = json.loads(final_result)
#                     result = CartResult(**data)
#                     logger.info("Successfully parsed CartResult from final result")
#                 except (json.JSONDecodeError, Exception) as e:
#                     logger.warning(f"Failed to parse JSON from final result: {e}")
#                     # If parsing fails, create a basic success result
#                     result = CartResult(
#                         success=True,
#                         message="Product added to cart successfully",
#                         items=[]
#                     )
#                     logger.info("Created fallback success result")
#             else:
#                 logger.warning("Task done but no final result found")
#                 result = CartResult(
#                     success=False,
#                     message="Task completed but no product information found",
#                     items=[]
#                 )
#         else:
#             # Task failed
#             logger.error("Task failed - agent did not complete successfully")
#             errors = history.errors()
#             error_msg = "Unknown error occurred"
#             if errors:
#                 error_list = [e for e in errors if e is not None]
#                 if error_list:
#                     error_msg = "; ".join(str(e) for e in error_list[:3])  # First 3 errors
#                     logger.error(f"Errors encountered: {error_msg}")
            
#             result = CartResult(
#                 success=False,
#                 message=f"Failed to add product to cart: {error_msg}",
#                 items=[]
#             )

#     # Log final result
#     if result.success:
#         logger.info(f"✅ Task completed successfully! Product: {result.product.name if result.product else 'N/A'}")
#         if result.product:
#             logger.info(f"   Price: ₹{result.product.price}, Rating: {result.product.rating}")
#     else:
#         logger.error(f"❌ Task failed: {result.message}")
    
#     return result
