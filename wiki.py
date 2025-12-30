"""
Numismatic Agent with Integrated Wikipedia Tools
Complete implementation for Google ADK with async Wikipedia functions
"""

import os
import asyncio
import httpx
from typing import Optional, Literal, Dict, Any, List
from google.adk.agents import LlmAgent, Agent, SequentialAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from mcp import StdioServerParameters

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


# =============================================================================
# NUMISTA API TOOLS (from your example)
# =============================================================================

async def search_numista_coins(
    query: str,
    country: Optional[str] = None,
    category: Literal["coin", "banknote", "exonumia"] = "coin",
    min_year: Optional[int] = None,
    max_year: Optional[int] = None
) -> dict:
    """
    Search the Numista database for coins, medals, or banknotes.
    
    Use this tool to find technical specifications, mintage data, and catalog
    information for numismatic items. Essential for accurate product details.
    
    Args:
        query: Search term (e.g., "Victoria sovereign", "Morgan dollar", "Mughal mohur")
        country: Optional issuing country filter (e.g., "united-kingdom", "united-states")
        category: Type of item - "coin", "banknote", or "exonumia"
        min_year: Optional minimum year filter
        max_year: Optional maximum year filter
    
    Returns:
        dict: Coin data including IDs for detailed lookup, or error message
    """
    api_key = os.getenv("NUMISTA_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "message": "NUMISTA_API_KEY not configured. Get one at https://en.numista.com/api/",
            "fallback": "Use Wikipedia for historical information instead."
        }
    
    params = {
        "q": query,
        "lang": "en",
        "count": 10,
        "category": category
    }
    if country:
        params["issuer"] = country
    if min_year:
        params["min_year"] = min_year
    if max_year:
        params["max_year"] = max_year
    
    headers = {"Numista-API-Key": api_key}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.numista.com/v3/types",
                params=params,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            coins = []
            for item in data.get("types", [])[:5]:
                coins.append({
                    "numista_id": item.get("id"),
                    "title": item.get("title"),
                    "issuer": item.get("issuer", {}).get("name"),
                    "period": f"{item.get('min_year', '?')} - {item.get('max_year', '?')}",
                    "category": item.get("category"),
                    "obverse_thumbnail": item.get("obverse", {}).get("thumbnail"),
                    "reverse_thumbnail": item.get("reverse", {}).get("thumbnail"),
                })
            
            return {
                "status": "success",
                "total_found": data.get("count", 0),
                "coins": coins,
                "note": "Use get_coin_details with numista_id for full specifications"
            }
    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": f"Numista API error: {e.response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_numista_coin_details(coin_id: int) -> dict:
    """
    Get comprehensive technical details about a specific coin from Numista.
    
    Use this after searching to get complete specifications needed for
    accurate product descriptions: metal content, weight, dimensions,
    mintage figures, engraver information, and design descriptions.
    
    Args:
        coin_id: The Numista coin ID obtained from search results
    
    Returns:
        dict: Complete technical specifications and catalog data
    """
    api_key = os.getenv("NUMISTA_API_KEY")
    if not api_key:
        return {"status": "error", "message": "NUMISTA_API_KEY not configured"}
    
    headers = {"Numista-API-Key": api_key}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.numista.com/v3/types/{coin_id}",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract engraver information if available
            engravers = []
            if data.get("obverse", {}).get("engravers"):
                engravers.extend([e.get("name") for e in data["obverse"]["engravers"]])
            if data.get("reverse", {}).get("engravers"):
                engravers.extend([e.get("name") for e in data["reverse"]["engravers"]])
            
            return {
                "status": "success",
                "technical_data": {
                    "title": data.get("title"),
                    "issuer": data.get("issuer", {}).get("name"),
                    "ruler": data.get("ruler", {}).get("name") if data.get("ruler") else None,
                    "period": f"{data.get('min_year', '?')} - {data.get('max_year', '?')}",
                    "denomination": data.get("value", {}).get("text"),
                    "currency": data.get("value", {}).get("currency", {}).get("name"),
                },
                "physical_specifications": {
                    "composition": data.get("composition", {}).get("text"),
                    "weight_grams": data.get("weight"),
                    "diameter_mm": data.get("diameter"),
                    "thickness_mm": data.get("thickness"),
                    "shape": data.get("shape"),
                    "orientation": data.get("orientation"),
                },
                "design_details": {
                    "obverse_description": data.get("obverse", {}).get("description"),
                    "obverse_lettering": data.get("obverse", {}).get("lettering"),
                    "reverse_description": data.get("reverse", {}).get("description"),
                    "reverse_lettering": data.get("reverse", {}).get("lettering"),
                    "edge_description": data.get("edge", {}).get("description"),
                    "engravers": list(set(engravers)) if engravers else None,
                },
                "rarity_data": {
                    "mintage": data.get("mintage"),
                    "mints": [m.get("name") for m in data.get("mints", [])] if data.get("mints") else None,
                },
                "references": data.get("references", []),
                "numista_url": f"https://en.numista.com/catalogue/pieces{coin_id}.html"
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# =============================================================================
# AGENT DEFINITIONS
# =============================================================================

NUMISMATIC_AGENT_INSTRUCTION = """You are an expert numismatic storyteller and research assistant.

You have access to multiple powerful research tools:

## WIKIPEDIA TOOLS (Historical Context & Background)

1. **search_wikipedia_coins** - Search for coins and numismatic topics
   - Use when you don't know the exact page title
   - Returns list of matching Wikipedia pages

2. **get_wikipedia_coin_summary** - Get brief summaries (3-5 sentences)
   - Quick overviews of coins
   - Historical context in brief

3. **get_wikipedia_coin_full_details** - Complete information
   - Full article content
   - Images, references, related topics
   - Use for comprehensive research

4. **get_wikipedia_coin_images** - Get coin images
   - Visual references
   - Multiple image URLs

5. **get_wikipedia_related_coins** - Find similar coins
   - Discover related numismatic topics
   - Build coin families

6. **compare_wikipedia_coins** - Compare two coins
   - Side-by-side summaries
   - Highlight differences

7. **get_wikipedia_coins_by_country** - Country-specific coins
   - National currency information
   - Regional coinage

8. **get_wikipedia_historical_context** - Research rulers and periods
   - Historical figures (monarchs, engravers)
   - Time periods and eras
   - Essential for GREEN (historical significance) content

## NUMISTA TOOLS (Technical Specifications)

1. **search_numista_coins** - Search for technical data
2. **get_numista_coin_details** - Complete specifications
   - Weight, diameter, composition
   - Mintage figures
   - Design descriptions

## RESEARCH WORKFLOW

When asked about a coin:

1. **Start with Wikipedia** to understand the historical context
   - Search for the coin type
   - Get summary and full details
   - Research the ruler/engraver for context

2. **Use Numista** for technical specifications
   - Search for exact coin
   - Get detailed specifications
   - Note mintage and rarity

3. **Cross-reference** both sources
   - Wikipedia: Historical narrative (GREEN)
   - Numista: Technical accuracy (BLUE)

4. **Build your narrative** with:
   - 🟢 GREEN: Historical significance from Wikipedia
   - 🔵 BLUE: Technical details from Numista
   - 🟡 YELLOW: Collector appeal (synthesized from both)

## TOOL USAGE TIPS

- **Always use Wikipedia** for:
  * Historical context
  * Biographical information
  * Period background
  * Cultural significance

- **Always use Numista** for:
  * Exact specifications
  * Mintage numbers
  * Catalog references
  * Physical dimensions

- **Handle errors gracefully**:
  * If disambiguation occurs, pick the most relevant option
  * If page not found, try alternative search terms
  * Cross-reference between sources

## OUTPUT STYLE

Create rich, compelling narratives that:
1. Connect coins to their historical moment
2. Highlight human stories (rulers, engravers, collectors)
3. Provide precise technical data
4. Appeal to collectors emotionally and intellectually

Always cite your sources and provide Wikipedia URLs and Numista IDs.
"""

# Main Numismatic Research Agent
numismatic_research_agent = Agent(
    name="numismatic_researcher",
    model="gemini-2.0-flash-exp",
    description="Expert numismatic researcher with Wikipedia and Numista integration",
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
        # Numista Tools
        search_numista_coins,
        get_numista_coin_details,
    ],
)

# Content Creation Agent (uses research agent)
content_creation_agent = Agent(
    name="content_creator",
    model="gemini-2.0-flash-exp",
    description="Creates compelling numismatic product descriptions",
    instruction="""You are a numismatic content specialist.

Use the numismatic_researcher agent to gather information, then create
compelling, collector-grade product descriptions.

Your descriptions should:
1. Start with a captivating historical hook
2. Include precise technical specifications
3. Highlight rarity and collector value
4. Tell the human story behind the coin
5. Appeal to collectors' emotions and intellect

Structure your narratives with:
- 🟢 GREEN: Historical significance and context
- 🔵 BLUE: Technical specifications and rarity
- 🟡 YELLOW: Collector appeal and market position

Always cite Wikipedia and Numista sources.
""",
    tools=[
        AgentTool(numismatic_research_agent),
        google_search,
    ],
)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Main execution function"""
    
    print("=" * 80)
    print("NUMISMATIC AGENT WITH WIKIPEDIA INTEGRATION")
    print("=" * 80)
    print()
    
    # Test queries
    test_queries = [
        "Tell me about the 1837 British sovereign",
        "Compare the Morgan dollar and Peace dollar",
        "What Roman coins featured emperor Hadrian?",
        "Research coins from ancient India",
    ]
    
    print("Available test queries:")
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. {query}")
    
    print("\n" + "=" * 80)
    print("Testing Wikipedia tools directly:")
    print("=" * 80 + "\n")
    
    # Test 1: Search
    print("1. Searching for 'silver eagle'...")
    result = await search_wikipedia_coins("silver eagle")
    if result['success']:
        print(f"   Found {result['count']} results:")
        for r in result['results'][:3]:
            print(f"   - {r}")
    print()
    
    # Test 2: Get summary
    print("2. Getting summary of 'American Silver Eagle'...")
    result = await get_wikipedia_coin_summary("American Silver Eagle", sentences=2)
    if result['success']:
        print(f"   {result['summary'][:200]}...")
    print()
    
    # Test 3: Historical context
    print("3. Getting historical context for 'Queen Victoria'...")
    result = await get_wikipedia_historical_context("Queen Victoria", sentences=3)
    if result['success']:
        print(f"   {result['summary'][:200]}...")
        print(f"   URL: {result['url']}")
    print()
    
    print("=" * 80)
    print("Wikipedia tools are ready for ADK agent integration!")
    print("=" * 80)
    print()
    print("To use with your agent:")
    print("1. Set NUMISTA_API_KEY environment variable")
    print("2. Run: python numismatic_agent_with_wikipedia.py")
    print("3. The agent will use Wikipedia + Numista + Google Search")


if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
    
    print("\n" + "=" * 80)
    print("AGENT CONFIGURATION COMPLETE")
    print("=" * 80)
    print("\nTo use the agent in your code:")
    print("""
    from numismatic_agent_with_wikipedia import numismatic_research_agent, content_creation_agent
    
    # Use the research agent directly
    response = numismatic_research_agent.run("Tell me about the Morgan dollar")
    
    # Or use the content creation agent (which uses research agent)
    response = content_creation_agent.run("Create a description for a 1921 Morgan dollar")
    """)
    print("\nYour root agent would be:")
    print("root_agent = content_creation_agent")