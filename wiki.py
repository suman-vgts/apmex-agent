"""
Numismatic Agent with Integrated Wikipedia Tools
Complete implementation for Google ADK with async Wikipedia functions
"""

import os
import asyncio
import httpx
from typing import Optional, Literal, Dict, Any, List
from google.adk.agents import LlmAgent, Agent
# Import Wikipedia library
try:
    import wikipedia
except ImportError:
    print("Warning: wikipedia package not installed. Install with: pip install wikipedia")
    wikipedia = None


# =============================================================================
# WIKIPEDIA TOOLS - Async Functions for ADK Integration
# =============================================================================

async def search_wikipedia_coins(
    query: str,
    results: int = 10
) -> Dict[str, Any]:
    """
    Search Wikipedia for coins, currencies, or numismatic topics.
    Returns a list of matching page titles.
    
    Use this tool when:
    - User asks about a type of coin they don't know the exact name of
    - You need to find the correct Wikipedia article title
    - Exploring different coin types or periods
    
    Args:
        query: Search term (e.g., "American Eagle coin", "Roman denarius", "Victorian sovereign")
        results: Maximum number of search results to return (default: 10)
    
    Returns:
        dict: Search results with matching page titles
        
    Example:
        result = await search_wikipedia_coins("silver dollar")
        # Returns: {"success": True, "results": ["Morgan dollar", "Peace dollar", ...]}
    """
    if wikipedia is None:
        return {
            "success": False,
            "error": "Wikipedia package not installed",
            "query": query,
            "results": [],
            "count": 0
        }
    
    try:
        # Run synchronous Wikipedia search in thread pool
        loop = asyncio.get_event_loop()
        search_results = await loop.run_in_executor(
            None, 
            lambda: wikipedia.search(query, results=results)
        )
        
        return {
            "success": True,
            "query": query,
            "results": search_results,
            "count": len(search_results),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "results": [],
            "count": 0,
            "error": str(e)
        }


async def get_wikipedia_coin_summary(
    page_title: str,
    sentences: int = 5
) -> Dict[str, Any]:
    """
    Get a brief summary of a coin or numismatic topic from Wikipedia.
    Perfect for quick overviews without full details.
    
    Use this tool when:
    - You need a quick overview of a coin
    - Answering "What is..." questions
    - Providing brief historical context
    
    Args:
        page_title: Wikipedia page title (e.g., "Morgan dollar", "Gold sovereign")
        sentences: Number of sentences to include in summary (default: 5)
    
    Returns:
        dict: Summary text and metadata
        
    Example:
        result = await get_wikipedia_coin_summary("Morgan dollar", sentences=3)
        # Returns brief summary of Morgan dollar
    """
    if wikipedia is None:
        return {
            "success": False,
            "error": "Wikipedia package not installed",
            "title": page_title,
            "summary": None
        }
    
    try:
        loop = asyncio.get_event_loop()
        summary = await loop.run_in_executor(
            None,
            lambda: wikipedia.summary(page_title, sentences=sentences)
        )
        
        return {
            "success": True,
            "title": page_title,
            "summary": summary,
            "sentences": sentences,
            "disambiguation_options": None,
            "error": None
        }
    except wikipedia.exceptions.DisambiguationError as e:
        return {
            "success": False,
            "title": page_title,
            "summary": None,
            "sentences": sentences,
            "disambiguation_options": e.options[:10],
            "error": f"Ambiguous search. Multiple pages found. Please specify one of: {', '.join(e.options[:5])}"
        }
    except wikipedia.exceptions.PageError:
        return {
            "success": False,
            "title": page_title,
            "summary": None,
            "sentences": sentences,
            "disambiguation_options": None,
            "error": f"Page not found: {page_title}"
        }
    except Exception as e:
        return {
            "success": False,
            "title": page_title,
            "summary": None,
            "sentences": sentences,
            "disambiguation_options": None,
            "error": str(e)
        }


async def get_wikipedia_coin_full_details(
    page_title: str
) -> Dict[str, Any]:
    """
    Get comprehensive details about a coin from Wikipedia.
    Includes full content, images, references, related links, and categories.
    
    Use this tool when:
    - You need complete historical information
    - Accessing references and citations
    - Finding related Wikipedia pages
    - Getting images of the coin
    
    Args:
        page_title: Wikipedia page title
    
    Returns:
        dict: Complete page information including content, images, and references
        
    Example:
        result = await get_wikipedia_coin_full_details("Double Eagle")
        # Returns complete information about the Double Eagle coin
    """
    if wikipedia is None:
        return {
            "success": False,
            "error": "Wikipedia package not installed",
            "title": page_title
        }
    
    try:
        loop = asyncio.get_event_loop()
        page = await loop.run_in_executor(
            None,
            lambda: wikipedia.page(page_title)
        )
        
        return {
            "success": True,
            "title": page.title,
            "url": page.url,
            "content": page.content,
            "summary": page.summary,
            "images": page.images[:10],  # Limit to first 10 images
            "references": page.references[:20],  # Limit to first 20 references
            "links": page.links[:50],  # Limit to first 50 links
            "categories": page.categories,
            "error": None
        }
    except wikipedia.exceptions.DisambiguationError as e:
        return {
            "success": False,
            "title": page_title,
            "url": None,
            "content": None,
            "summary": None,
            "images": [],
            "references": [],
            "links": [],
            "categories": [],
            "error": f"Ambiguous page. Options: {', '.join(e.options[:5])}"
        }
    except wikipedia.exceptions.PageError:
        return {
            "success": False,
            "title": page_title,
            "url": None,
            "content": None,
            "summary": None,
            "images": [],
            "references": [],
            "links": [],
            "categories": [],
            "error": f"Page not found: {page_title}"
        }
    except Exception as e:
        return {
            "success": False,
            "title": page_title,
            "url": None,
            "content": None,
            "summary": None,
            "images": [],
            "references": [],
            "links": [],
            "categories": [],
            "error": str(e)
        }


async def get_wikipedia_coin_images(
    page_title: str,
    max_images: int = 5
) -> Dict[str, Any]:
    """
    Get image URLs for a specific coin or numismatic topic from Wikipedia.
    Useful when you need visual references of coins.
    
    Use this tool when:
    - User asks to see what a coin looks like
    - Creating visual product descriptions
    - Comparing coin designs
    
    Args:
        page_title: Wikipedia page title
        max_images: Maximum number of images to return (default: 5)
    
    Returns:
        dict: List of image URLs
        
    Example:
        result = await get_wikipedia_coin_images("Krugerrand")
        # Returns image URLs of Krugerrand coins
    """
    if wikipedia is None:
        return {
            "success": False,
            "error": "Wikipedia package not installed",
            "title": page_title,
            "images": []
        }
    
    try:
        loop = asyncio.get_event_loop()
        page = await loop.run_in_executor(
            None,
            lambda: wikipedia.page(page_title)
        )
        
        images = page.images[:max_images]
        
        return {
            "success": True,
            "title": page.title,
            "images": images,
            "count": len(images),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "title": page_title,
            "images": [],
            "count": 0,
            "error": str(e)
        }


async def get_wikipedia_related_coins(
    page_title: str,
    max_links: int = 20
) -> Dict[str, Any]:
    """
    Find related coins and numismatic topics by analyzing Wikipedia page links.
    Perfect for discovering similar or related coins.
    
    Use this tool when:
    - User asks "what other coins are similar?"
    - Building a collection of related coins
    - Exploring coin families or series
    
    Args:
        page_title: Wikipedia page title
        max_links: Maximum number of related links to return (default: 20)
    
    Returns:
        dict: List of related page titles
        
    Example:
        result = await get_wikipedia_related_coins("Lincoln cent")
        # Returns related topics like "Wheat cent", "Indian Head cent", etc.
    """
    if wikipedia is None:
        return {
            "success": False,
            "error": "Wikipedia package not installed",
            "title": page_title,
            "related_topics": []
        }
    
    try:
        loop = asyncio.get_event_loop()
        page = await loop.run_in_executor(
            None,
            lambda: wikipedia.page(page_title)
        )
        
        all_links = page.links
        
        # Common numismatic keywords to filter relevant links
        numismatic_keywords = [
            'coin', 'currency', 'dollar', 'cent', 'penny', 'nickel', 
            'dime', 'quarter', 'mint', 'numismatic', 'bullion',
            'eagle', 'sovereign', 'franc', 'mark', 'pound', 'yen',
            'peso', 'rupee', 'dinar', 'shekel', 'denarius', 'gold',
            'silver', 'bronze', 'copper'
        ]
        
        # Try to find numismatic-related links
        relevant_links = [
            link for link in all_links 
            if any(keyword in link.lower() for keyword in numismatic_keywords)
        ]
        
        # If not enough relevant links, return general links
        if len(relevant_links) < 5:
            relevant_links = all_links[:max_links]
        else:
            relevant_links = relevant_links[:max_links]
        
        return {
            "success": True,
            "title": page.title,
            "related_topics": relevant_links,
            "count": len(relevant_links),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "title": page_title,
            "related_topics": [],
            "count": 0,
            "error": str(e)
        }


async def compare_wikipedia_coins(
    coin1: str,
    coin2: str
) -> Dict[str, Any]:
    """
    Compare two coins or currencies by retrieving their Wikipedia summaries.
    Useful for side-by-side comparison of different coins.
    
    Use this tool when:
    - User asks to compare two coins
    - Highlighting differences between similar coins
    - Investment comparisons
    
    Args:
        coin1: First coin/currency page title
        coin2: Second coin/currency page title
    
    Returns:
        dict: Summaries of both coins for comparison
        
    Example:
        result = await compare_wikipedia_coins("American Gold Eagle", "Canadian Gold Maple Leaf")
        # Returns summaries of both coins for comparison
    """
    try:
        summary1 = await get_wikipedia_coin_summary(coin1, sentences=4)
        summary2 = await get_wikipedia_coin_summary(coin2, sentences=4)
        
        return {
            "success": True,
            "coin1": {
                "title": coin1,
                "summary": summary1.get("summary"),
                "success": summary1.get("success")
            },
            "coin2": {
                "title": coin2,
                "summary": summary2.get("summary"),
                "success": summary2.get("success")
            },
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "coin1": None,
            "coin2": None,
            "error": str(e)
        }


async def get_wikipedia_coins_by_country(
    country: str
) -> Dict[str, Any]:
    """
    Search for coins and currency information by country on Wikipedia.
    
    Use this tool when:
    - User asks about a country's currency
    - Researching regional coinage
    - Building country-specific collections
    
    Args:
        country: Country name (e.g., "United States", "Japan", "India")
    
    Returns:
        dict: List of coin/currency related pages for the country
        
    Example:
        result = await get_wikipedia_coins_by_country("India")
        # Returns Indian Rupee, ancient Indian coins, etc.
    """
    if wikipedia is None:
        return {
            "success": False,
            "error": "Wikipedia package not installed",
            "country": country,
            "search_results": []
        }
    
    try:
        # Search for country currency and coins
        queries = [
            f"{country} coins",
            f"{country} currency",
            f"{country} numismatics"
        ]
        
        all_results = []
        loop = asyncio.get_event_loop()
        
        for query in queries:
            results = await loop.run_in_executor(
                None,
                lambda q=query: wikipedia.search(q, results=5)
            )
            all_results.extend(results)
        
        # Remove duplicates while preserving order
        unique_results = list(dict.fromkeys(all_results))
        
        return {
            "success": True,
            "country": country,
            "search_results": unique_results,
            "count": len(unique_results),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "country": country,
            "search_results": [],
            "count": 0,
            "error": str(e)
        }


async def get_wikipedia_historical_context(
    person_or_period: str,
    sentences: int = 8
) -> Dict[str, Any]:
    """
    Get historical context about a ruler, period, or historical figure from Wikipedia.
    Essential for understanding the era in which coins were minted.
    
    Use this tool when:
    - Researching the ruler on a coin
    - Understanding the historical period
    - Adding historical context to coin descriptions
    
    Args:
        person_or_period: Name of ruler, period, or historical figure
                         (e.g., "Queen Victoria", "Roman Empire", "William Wyon")
        sentences: Number of sentences to include (default: 8)
    
    Returns:
        dict: Historical context and summary
        
    Example:
        result = await get_wikipedia_historical_context("Queen Victoria")
        # Returns biographical and historical information about Queen Victoria
    """
    if wikipedia is None:
        return {
            "success": False,
            "error": "Wikipedia package not installed",
            "subject": person_or_period,
            "summary": None
        }
    
    try:
        loop = asyncio.get_event_loop()
        
        # First search to find the right page
        search_results = await loop.run_in_executor(
            None,
            lambda: wikipedia.search(person_or_period, results=1)
        )
        
        if not search_results:
            return {
                "success": False,
                "subject": person_or_period,
                "summary": None,
                "error": f"No Wikipedia page found for: {person_or_period}"
            }
        
        page_title = search_results[0]
        
        # Get the summary
        summary = await loop.run_in_executor(
            None,
            lambda: wikipedia.summary(page_title, sentences=sentences)
        )
        
        # Get the page for URL
        page = await loop.run_in_executor(
            None,
            lambda: wikipedia.page(page_title)
        )
        
        return {
            "success": True,
            "subject": person_or_period,
            "actual_page": page.title,
            "summary": summary,
            "url": page.url,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "subject": person_or_period,
            "summary": None,
            "error": str(e)
        }


NUMISMATIC_AGENT_INSTRUCTION = """You are a numismatic historical specialist. Your goal is to provide deep historical and technical insights using Wikipedia.

**USAGE RULE**: You should be called at most TWICE per workflow:
1. First call: Identify the coin (search).
2. Second call: Retrieve comprehensive data (full details/context).

Provide rich, accurate data. Do not perform redundant searches.

Available actions:
- search_wikipedia_coins: Find coins and numismatic topics by query.
- get_wikipedia_coin_summary: Get a brief 3-5 sentence overview.
- get_wikipedia_coin_full_details: Get complete article content, specs, and references.
- get_wikipedia_coin_images: Retrieve image URLs for visual reference.
- get_wikipedia_related_coins: Find similar or related coin families.
- compare_wikipedia_coins: Side-by-side comparison of two coins.
- get_wikipedia_coins_by_country: Search for regional or national currency sets.
- get_wikipedia_historical_context: Research the rulers, eras, or engravers.

Be efficient—one search and one detail lookup is usually sufficient. Always cite Wikipedia URLs."""

# Main Wikipedia Research Agent
wikipedia_research_agent = Agent(
    name="wikipedia_researcher",
    model="gemini-2.5-pro",
    description="Expert numismatic researcher with Wikipedia integration",
    instruction=NUMISMATIC_AGENT_INSTRUCTION,
    tools=[
        # Wikipedia Tools
        search_wikipedia_coins,
        get_wikipedia_coin_summary,
        get_wikipedia_coin_full_details,
        get_wikipedia_coin_images,
        get_wikipedia_related_coins,
        compare_wikipedia_coins,
        get_wikipedia_coins_by_country,
        get_wikipedia_historical_context,
    ],
)
