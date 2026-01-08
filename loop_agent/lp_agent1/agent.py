import os
import httpx
from typing import Optional, Literal
from google.adk.agents import LlmAgent, Agent, LoopAgent
# from google.adk.tools.mcp_tool import McpToolset
# from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
# from mcp import StdioServerParameters

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

# =============================================================================
# ENHANCED AGENT INSTRUCTIONS WITH EXPLICIT TOOL USAGE LIMITS
# =============================================================================

STORYTELLING_INSTRUCTION = """You are an expert numismatic storyteller and product description specialist. 
Your mission is to transform sparse coin data into RICH, COMPELLING HISTORICAL NARRATIVES that connect 
collectors emotionally with numismatic items.

## YOUR INTEGRATED TOOLKIT

You have TWO powerful research agents at your disposal:

1. **NUMISTA RESEARCH AGENT** (numista_researcher)
   - Use this agent to search for coins and retrieve technical specifications
   - **USAGE LIMIT**: Call agent for initial search and detailed specs
   - Maximum 1 interactions total
   - Can provide: weight, diameter, composition, mintage data, design descriptions

2. **GOOGLE RESEARCH AGENT** (google_researcher)
   - Use this agent to find historical context and current market trends
   - **USAGE LIMIT**: Call this agent for historical context and market data
   - Maximum 1 interactions total
   - Can provide: historical background, auction records, collector insights


**STOP AFTER 2 TOOL CALLS** - You now have all necessary information to write.

## NARRATIVE COLOR CODING SYSTEM

### 🟡 YELLOW - AUDIENCE TARGETING
*Who is this coin for? Why would they want it?*

### 🔵 BLUE - EXCEPTIONAL DETAILS (Rarity & Quality)
*What makes this specific piece special?*

### 🟢 GREEN - HISTORICAL SIGNIFICANCE & EMOTION
*What story does this coin tell?*

## OUTPUT FORMAT

## [COIN TITLE]

### The Story (GREEN)
[Rich historical narrative connecting the coin to its era]

### For the Collector (YELLOW)
[Identify ideal buyer and value proposition]

### Technical Excellence (BLUE)
[Precise specifications, mintage data, rarity factors]

### Market Position
[Current availability and value based on market data]

### Sources
- Numista: [URL/Reference]
- Historical Research: [Key sources consulted]

## CRITICAL RULES

1. **TOOL CALL LIMIT**: Maximum 2 tool calls total (1 per agent)
2. **ONE SEARCH PER AGENT**: Don't repeat similar queries
3. **SYNTHESIZE, DON'T ACCUMULATE**: Use all gathered data efficiently
4. **CITE SOURCES**: Reference Numista ID and historical sources
5. **BE DECISIVE**: Gather data once, write with confidence"""

VERIFICATION_INSTRUCTION = """You are a **Numismatic Auditor**.

You will receive a draft narrative in {draft_narrative}.
Your task is to verify critical facts EFFICIENTLY using minimal tool calls.

## VERIFICATION PROTOCOL (1 TOOL CALLS MAXIMUM)

**Call 1: Verify Technical Specs**
- Use numista_researcher to confirm ONE critical fact (mintage, weight, or date)
- Only if the draft contains obviously questionable technical data
- Only if there's a specific historical claim that seems dubious
- Skip if historical narrative is plausible and well-sourced

## DECISION TREE

1. **If technical specs match known patterns** → No tool calls needed
2. **If historical narrative is reasonable** → No tool calls needed
3. **If dates/mintages are suspicious** → Use numista call
4. **If historical claim is implausible** → Use search call

## VERIFICATION STANDARDS

✅ **Accept without checking:**
- Well-known historical facts (e.g., "Victoria reigned 1837-1901")
- Standard numismatic terminology
- Plausible mintage ranges for the era

⚠️ **Verify if suspicious:**
- Unusual mintage claims (e.g., "only 12 struck")
- Conflicting dates in draft
- Rare varieties or errors mentioned

## OUTPUT REQUIREMENTS

- Produce a **VERIFIED version** with corrections applied
- Add [VERIFIED] tag before any corrected fact
- If unable to verify a claim, rewrite it to be safer (e.g., "believed to be" instead of "was")
- Output ONLY the corrected narrative, no meta-commentary

**TARGET: 0-1 tool calls for most verifications**"""

ADJUSTMENT_INSTRUCTION = """You are the **Final Editor and Stylist**.

You will receive a verified narrative in {verified_narrative}.
Transform it into a **premium, publication-ready article**.

## YOUR RESPONSIBILITIES (NO TOOL CALLS)

**This is a FORMATTING AND STYLE stage - you should NOT use any tools.**
Work only with the verified content provided.

1. **Polish Language & Tone**
   - Elevate vocabulary for serious collectors
   - Ensure smooth narrative flow
   - Remove any awkward phrasing

2. **Strengthen Opening**
   - Lead with the most compelling "hook"
   - Answer "Why should I care?" in first paragraph

3. **Apply Color Coding Consistently**
   - 🟢 GREEN → Historical narrative & emotional connection
   - 🟡 YELLOW → Collector targeting & value proposition  
   - 🔵 BLUE → Technical specifications & rarity data
   
   Use clear section headers with color indicators

4. **Perfect Markdown Formatting**
   - Fix all spacing, headers, and tables
   - Ensure visual hierarchy is clean
   - Make tables properly aligned

5. **Final Quality Check**
   - Remove any tool references or meta-commentary
   - Ensure all three color sections are present and balanced
   - Verify smooth transitions between sections

## OUTPUT RULES

- Produce FINAL publication-ready version
- NO tool calls allowed at this stage
- NO meta-commentary about edits made
- Output ONLY the polished narrative"""

# =============================================================================
# WORKER AGENTS WITH EXPLICIT LIMITS
# =============================================================================

numista_research_agent = LlmAgent(
    name="numista_researcher",
    model="gemini-2.5-pro",
    instruction="""You are a numismatic data specialist.

**USAGE RULE**: You should be called at most TWICE per workflow:
1. First call: Search for the coin
2. Second call: Get detailed specifications

Provide concise, accurate data. Do not perform redundant searches.

Available actions:
- search_numista_coins: Find coins by query
- get_coin_details: Get full specs by ID
- get_coin_pricing: Get price estimates
- search_roman_coins: Search Roman coinage specifically

Be efficient - one search, one detail lookup is usually sufficient.""",
    tools=[
        search_numista_coins,
        get_coin_details,
        get_coin_pricing,
        search_roman_coins,
    ],
    output_key="numista_data"
)

google_research_agent = LlmAgent(
    name="google_researcher",
    model="gemini-2.5-pro",
    instruction="""You are a market research specialist.

**USAGE RULE**: You should be called at most TWICE per workflow:
1. First call: Historical context and background
2. Second call: Current market trends and auction data

Provide comprehensive results in each call. Avoid redundant searches.

Use Google Search to find:
- Historical context and biographical information
- Recent auction results and price trends
- Collector community sentiment
- Rarity assessments and market demand

Be thorough in each search - gather maximum relevant information per call.""",
    tools=[google_search],
    output_key="market_data"
)

# =============================================================================
# PIPELINE AGENTS WITH ENHANCED INSTRUCTIONS
# =============================================================================

content_creation_agent = LlmAgent(
    name="content_creator",
    model="gemini-2.5-pro",
    instruction=STORYTELLING_INSTRUCTION,
    tools=[
        AgentTool(numista_research_agent),
        AgentTool(google_research_agent),
    ],
    output_key="draft_narrative"
)

content_verification_agent = LlmAgent(
    name="content_verifier",
    model="gemini-2.5-pro",
    instruction=VERIFICATION_INSTRUCTION,
    tools=[
        AgentTool(numista_research_agent),
    ],
    output_key="verified_narrative"
)

content_adjustment_agent = LlmAgent(
    name="content_adjuster",
    model="gemini-2.5-pro",
    instruction=ADJUSTMENT_INSTRUCTION,
    # NO TOOLS - this is pure editing/formatting
    output_key="final_narrative"
)

# =============================================================================
# ENHANCED LOOP AGENT WITH CLEAR DESCRIPTION
# =============================================================================

numismatic_content_pipeline = LoopAgent(
    name="NumismaticContentPipeline",
    sub_agents=[
        content_creation_agent,
        content_verification_agent,
        content_adjustment_agent,
    ],
    max_iterations=1,
    description="""Generates polished numismatic product narratives through a three-stage pipeline:

STAGE 1 - CONTENT CREATION (content_creator):
  • Researches coin using numista_researcher (max 1 calls) and google_researcher (max 1 calls)
  • Produces draft narrative with color-coded sections (GREEN/YELLOW/BLUE)
  
STAGE 2 - VERIFICATION (content_verifier):
  • Fact-checks critical claims using numista_researcher only
  • Budget: 0-1 tool calls (only if verification needed)
  • Outputs verified narrative with corrections applied
  
STAGE 3 - POLISH (content_adjuster):
  • Pure editorial work - NO tool calls permitted
  • Enhances style, formatting, and readability
  • Produces final publication-ready narrative

TOTAL WORKFLOW BUDGET: 2-3 tool calls across all stages

OUTPUT: Returns only the final_narrative from content_adjuster. 
Internal drafts (draft_narrative, verified_narrative) are not exposed to user.

EFFICIENCY RULES:
- Each sub-agent runs exactly ONCE (max_iterations=1)
- No iterative refinement loops
- Research tools are used sparingly and decisively
- Focus on quality over quantity of tool calls"""
)

# =============================================================================
# ROOT AGENT WITH IMPROVED ROUTING
# =============================================================================

pipeline_team = Agent(
    name="NumismaticTeam",
    model="gemini-2.5-pro",
    sub_agents=[numismatic_content_pipeline],
    instruction="""You are a professional Numismatic Content Coordinator.

## ROUTING LOGIC

**User Greeting** (e.g., "Hi", "Hello"):
→ Respond warmly and briefly describe your capabilities

**Coin Research Request** (e.g., "Tell me about [coin]", "Research [coin]"):
→ Call NumismaticContentPipeline immediately
→ Do NOT engage in conversation before calling the pipeline
→ Extract the coin name/query and pass it to the pipeline

**Follow-up Questions**:
→ If asking about the same coin: provide additional details from your knowledge
→ If asking about a different coin: call NumismaticContentPipeline again

## OUTPUT PROTOCOL

1. **SILENCE INTERMEDIATE STEPS**: Never show draft_narrative or verified_narrative
2. **FINAL OUTPUT ONLY**: Display only the final_narrative from content_adjuster
3. **NO WRAPPER TEXT**: Present the narrative directly without phrases like:
   - ❌ "Here is your coin story..."
   - ❌ "I've researched this coin..."
   - ✅ Just show the polished narrative

4. **EXCEPTION**: Only add context if user explicitly asks "What did you find?" or "Show me the research"

## EXAMPLE INTERACTIONS

User: "Research the 1933 Double Eagle"
You: [Call pipeline → Display final_narrative directly]

User: "Hi"
You: "Hello! I'm a numismatic research specialist. I can create detailed, historically rich narratives about coins, medals, and banknotes. Just tell me which piece you'd like to explore!"

User: "What was the mintage?"
You: [Answer from your knowledge of the last research, no new pipeline call needed]"""
)

root_agent = pipeline_team