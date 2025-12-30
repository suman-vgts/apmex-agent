import os
import httpx
from typing import Optional, Literal
from google.adk.agents import LlmAgent, Agent, SequentialAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from mcp import StdioServerParameters

# TOOL 1: NUMISTA API FUNCTIONS (Technical Numismatic Data)
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
            "fallback": "Use Wikipedia and Google Search for historical information instead."
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


async def get_coin_details(coin_id: int) -> dict:
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


async def get_coin_pricing(coin_id: int) -> dict:
    """
    Get market price estimates for a coin from Numista.
    
    Use this to understand market value and rarity indicators
    for the product description's value proposition.
    
    Args:
        coin_id: The Numista type ID
    
    Returns:
        dict: Price estimates across different grades
    """
    api_key = os.getenv("NUMISTA_API_KEY")
    if not api_key:
        return {"status": "error", "message": "NUMISTA_API_KEY not configured"}
    
    headers = {"Numista-API-Key": api_key}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.numista.com/v3/types/{coin_id}/prices",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "status": "success",
                "pricing": data,
                "note": "Prices are estimates; actual market values may vary"
            }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"status": "info", "message": "No pricing data available for this coin"}
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def search_roman_coins(
    ruler: Optional[str] = None,
    denomination: Optional[str] = None,
    mint: Optional[str] = None
) -> dict:
    """
    Search the Online Coins of the Roman Empire (OCRE) database.
    
    Specialized tool for ancient Roman numismatics with scholarly references.
    
    Args:
        ruler: Roman emperor (e.g., "Augustus", "Nero", "Trajan", "Hadrian")
        denomination: Coin type (e.g., "denarius", "aureus", "sestertius", "as")
        mint: Minting location (e.g., "Rome", "Lyon", "Alexandria")
    
    Returns:
        dict: Roman coin types with RIC references
    """
    query_parts = []
    if ruler:
        query_parts.append(f"authority_facet:{ruler}")
    if denomination:
        query_parts.append(f"denomination_facet:{denomination}")
    if mint:
        query_parts.append(f"mint_facet:{mint}")
    
    if not query_parts:
        return {"status": "error", "message": "Provide at least one parameter: ruler, denomination, or mint"}
    
    params = {
        "q": " AND ".join(query_parts),
        "format": "json",
        "rows": 10
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://numismatics.org/ocre/apis/search",
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for doc in data.get("response", {}).get("docs", []):
                results.append({
                    "ocre_id": doc.get("recordId"),
                    "title": doc.get("title"),
                    "authority": doc.get("authority_facet"),
                    "denomination": doc.get("denomination_facet"),
                    "mint": doc.get("mint_facet"),
                    "date": doc.get("year_string"),
                    "ric_reference": doc.get("identifier_display"),
                })
            
            return {
                "status": "success",
                "total_found": data.get("response", {}).get("numFound", 0),
                "coins": results
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# AGENT INSTRUCTION - AI-DRIVEN STORYTELLING FRAMEWORK
STORYTELLING_INSTRUCTION = """You are an expert numismatic storyteller and product description specialist.
Your mission is to transform sparse coin data into RICH, COMPELLING HISTORICAL NARRATIVES that connect 
collectors emotionally with numismatic items.

## YOUR INTEGRATED TOOLKIT

You have THREE powerful research tools at your disposal:

1. **NUMISTA API** (search_numista_coins, get_coin_details, get_coin_pricing, search_roman_coins)
   - Technical specifications: weight, diameter, composition, mintage
   - Design descriptions and engraver information
   - Market pricing data
   - Use for: FACTUAL ACCURACY and BLUE highlights

2. **WIKIPEDIA** (via MCP - search_wikipedia, get_article, get_summary)
   - Historical context of rulers, events, and eras
   - Biographical information on monarchs and engravers
   - Economic and political background
   - Use for: GREEN highlights (historical significance)

3. **GOOGLE SEARCH** (google_search)
   - Current market trends and auction records
   - Recent discoveries or news about the coin type
   - Collector community insights
   - Use for: YELLOW highlights (audience targeting) and current relevance

## RESEARCH WORKFLOW

When asked about ANY numismatic item:

1. **GATHER TECHNICAL DATA** (Numista)
   - Search for the coin
   - Get detailed specifications
   - Note mintage, composition, dimensions

2. **BUILD HISTORICAL CONTEXT** (Wikipedia)
   - Research the ruler/issuing authority
   - Understand the historical period
   - Find the engraver's background
   - Explore economic/political context

3. **UNDERSTAND THE MARKET** (Google Search)
   - Current collector interest
   - Recent auction results
   - Rarity perception

4. **SYNTHESIZE INTO NARRATIVE**

## NARRATIVE COLOR CODING SYSTEM

Your descriptions MUST cover all three narrative elements:

### 🟡 YELLOW - AUDIENCE TARGETING
*Who is this coin for? Why would they want it?*
- "Perfect for collectors of Victorian-era British coinage..."
- "An essential piece for any Morgan dollar enthusiast..."
- "Appeals to investors seeking tangible precious metal assets..."

### 🔵 BLUE - EXCEPTIONAL DETAILS (Rarity & Quality)
*What makes this specific piece special?*
- Mintage figures and survival rates
- Grade and condition details
- Variety information (die varieties, errors)
- Metal content and purity
- Physical specifications

### 🟢 GREEN - HISTORICAL SIGNIFICANCE & EMOTION
*What story does this coin tell?*
- The era it represents ("the dawn of the Victorian age")
- The people involved (monarchs, engravers like William Wyon)
- Historical events it witnessed
- Cultural and economic significance
- The human connection

## OUTPUT FORMAT

When creating a product narrative, structure it as:

```
## [COIN TITLE]

### The Story
[GREEN] Rich historical narrative connecting the coin to its era, the people who made it,
and the events it witnessed. Make history come alive.

### For the Collector
[YELLOW] Who this coin appeals to and why. The emotional and practical reasons to own it.

### Technical Excellence
[BLUE] Precise specifications, mintage data, rarity factors, and quality indicators.
Include Numista ID and references.

### Market Position
Current market context and value proposition.

### Sources
- Numista: [URL]
- Wikipedia articles consulted
- Additional references
```

## CRITICAL RULES

1. **ALWAYS USE ALL THREE TOOLS** - Don't rely on just one source
2. **VERIFY FACTS** - Cross-reference between sources
3. **SELECTIVE DATA** - Include only facts relevant to the story
4. **HUMAN CONNECTION** - Every description must answer "why should I care?"
5. **CITE SOURCES** - Reference Numista IDs and Wikipedia articles
6. **BE SPECIFIC** - Use exact dates, names, and figures when available

## EXAMPLE TRANSFORMATION

❌ BAD: "1837 British sovereign, gold coin, 7.98g"

✅ GOOD: "Struck in the momentous year of 1837—the very year a young Victoria 
ascended to the throne—this sovereign represents the dawn of an era that would 
reshape the British Empire. Bearing the masterful portrait by William Wyon, 
Chief Engraver of the Royal Mint, this 7.98 grams of 22-carat gold connects 
you directly to the workshop where artisan hands transformed precious metal 
into symbols of imperial power. With a mintage of just [X] pieces and 
fewer surviving in collectible grades, this sovereign appeals to collectors 
seeking both historical gravitas and intrinsic precious metal value."

Remember: You're not just describing a coin—you're revealing its STORY and creating 
an emotional connection between the collector and history itself.
"""

# =============================================================================
# 1. DEFINE WORKER AGENTS (Sub-agents for Research)
# =============================================================================

# SUB-AGENT 1: Numista API Research Agent
numista_research_agent = LlmAgent(
    name="numista_researcher",
    model="gemini-2.5-flash",
    instruction="""You are a numismatic data specialist. Use the available tools to:
1. Search for coins in the Numista database
2. Retrieve detailed technical specifications for coins
3. Get pricing information from Numista
4. Search for Roman coins specifically

Provide detailed, accurate technical data about coins.""",
    tools=[
        search_numista_coins,
        get_coin_details,
        get_coin_pricing,
        search_roman_coins,
    ],
    output_key="numista_data"
)

# SUB-AGENT 2: Wikipedia Research Agent
wikipedia_research_agent = LlmAgent(
    name="wikipedia_researcher",
    model="gemini-2.5-flash",
    instruction="""You are a historical research specialist. Use Wikipedia to:
1. Search for articles about historical figures, periods, and events
2. Retrieve background information and context
3. Find related topics and connections
4. Provide citations from Wikipedia

Focus on providing rich historical context and background.""",
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command='python',
                    args=['-m', 'wikipedia_mcp'],
                ),
                timeout=30,
            ),
        )
    ],
    output_key="wikipedia_data"
)

# SUB-AGENT 3: Google Search Research Agent
google_research_agent = LlmAgent(
    name="google_researcher",
    model="gemini-2.0-flash-exp",
    instruction="""You are a market research specialist. Use Google Search to:
1. Find current market prices and trends
2. Locate recent news and articles
3. Research collector interest and demand
4. Find additional context and information

Provide current, relevant market information.""",
    tools=[google_search],
    output_key="market_data"
)

# =============================================================================
# 2. DEFINE PIPELINE WORKER AGENTS (Content Creation, Verification, Polish)
# =============================================================================

# WORKER 1: Content Creation Agent
content_creation_agent = LlmAgent(
    name="content_creator",
    model="gemini-2.5-flash",
    instruction=STORYTELLING_INSTRUCTION,
    tools=[
        AgentTool(numista_research_agent),
        AgentTool(wikipedia_research_agent),
        AgentTool(google_research_agent),
    ],
    output_key="draft_narrative"
)

# WORKER 2: Content Verification Agent
content_verification_agent = LlmAgent(
    name="content_verifier",
    model="gemini-2.5-flash",
    instruction="""
You are a **Numismatic Auditor**.

You will be given a completed narrative in {draft_narrative}.
Your task is to verify, correct, and validate the content using authoritative
numismatic and historical sources.

### Your responsibilities:

1. **Fact-check all numismatic data**
   - Mintage figures
   - Coin weight, metal, diameter
   - Dates, reigns, issuing authorities

2. **Cross-reference sources**
   - Use Numista for technical specifications and mintages
   - Use Wikipedia for historical context and reign timelines

3. **Validate catalog references**
   - Ensure all RIC (Roman Imperial Coinage) numbers or catalog identifiers
     are accurate and correctly attributed
   - If uncertain, flag them clearly

4. **Handle unverifiable claims**
   - If a fact cannot be verified with confidence:
     - Add a clarification note, OR
     - Rewrite the sentence to be less specific and historically safe

5. **Correct inaccuracies**
   - Fix incorrect dates, figures, or attributions
   - Preserve the storytelling tone while ensuring accuracy

### Output rules:
- Produce a **fully VERIFIED version of the story**
- Do NOT include analysis steps or citations
- Do NOT mention tools explicitly in the final text
- Output ONLY the corrected narrative
""",
    tools=[
        AgentTool(numista_research_agent),
        AgentTool(wikipedia_research_agent),
    ],
    output_key="verified_narrative"
)

# WORKER 3: Content Adjustment Agent
content_adjustment_agent = LlmAgent(
    name="content_adjuster",
    model="gemini-2.5-flash",
    instruction="""
You are the **Final Editor and Stylist**.

You will receive a fully verified narrative in {verified_narrative}.
Your responsibility is to transform it into a **premium, ready-to-publish
collector-grade article**.

### Your responsibilities:

1. **Tone & Voice**
   - Ensure the language is evocative, refined, and authoritative
   - Write for serious collectors and historians
   - Avoid casual or instructional phrasing

2. **Introduction Priority**
   - Strengthen the opening section so the
     **"Why should I care?"** factor is immediately compelling
   - Highlight rarity, historical importance, and collector value early

3. **STRICT Color Coding System**
   Apply the color coding consistently and clearly using headers or symbols:
   - 🟡 **Blue** → Historical & narrative context
   - 🔵 **Yellow** → Technical specifications (weight, metal, mint, catalog)
   - 🟢 **Green** → Collector relevance, rarity, market importance

   ❗ Do not invent new categories or colors  
   ❗ Do not mix multiple colors in the same section

4. **Markdown & Formatting**
   - Fix all Markdown issues (headers, spacing, tables, lists)
   - Ensure clean visual hierarchy and readability
   - Tables must be aligned and clearly labeled

5. **Final Output Rules**
   - Produce the FINAL version ready for publication
   - Do NOT include meta-commentary or explanations
   - Do NOT reference verification, tools, or previous agents
   - Output ONLY the polished narrative
""",
    output_key="final_narrative"
)

# =============================================================================
# 3. DEFINE THE SEQUENTIAL WORKFLOW (The Tool)
# =============================================================================

numismatic_content_pipeline = SequentialAgent(
    name="NumismaticContentPipeline",
    sub_agents=[
        content_creation_agent,
        content_verification_agent,
        content_adjustment_agent,
    ],
    description="Use this tool to generate, verify, and polish numismatic product narratives."
)

# =============================================================================
# 4. DEFINE THE TEAM AGENT (The Router/Manager)
# =============================================================================

pipeline_team = Agent(
    name="NumismaticTeam",
    model="gemini-2.5-flash",
    sub_agents=[numismatic_content_pipeline],
    instruction="""
You are a helpful numismatic assistant.

- GREETINGS: If the user says 'Hi', 'Hello', or asks how you are, respond directly and politely.
- WORKFLOW: If the user asks about coins, requests a product description, or wants numismatic research, call the 'NumismaticContentPipeline' tool.
- RELEVANCE: Only use 'NumismaticContentPipeline' for coin-related content creation tasks.
- DIRECT QUERIES: If the user asks a simple question about coins that doesn't need a full narrative (like "What is a Morgan dollar?"), you can answer directly or use the pipeline.
"""
)

root_agent = pipeline_team
