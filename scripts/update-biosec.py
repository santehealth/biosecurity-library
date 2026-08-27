#!/usr/bin/env python3
import os
import re
from datetime import datetime
from anthropic import Anthropic

client = Anthropic()

def read_html():
    """Read the current biosecurity-library.html"""
    try:
        with open('biosecurity-library.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print("Error: biosecurity-library.html not found")
        return None

def update_timestamp(html):
    """Update the LAST UPDATED timestamp in the HTML"""
    today = datetime.now().strftime('%b %d, %Y').upper()
    pattern = r'<span>LAST UPDATED: <b>[^<]+</b></span>'
    replacement = f'<span>LAST UPDATED: <b>{today}</b></span>'
    return re.sub(pattern, replacement, html)

def get_biosecurity_signals():
    """Use Claude to search for high-signal biosecurity articles"""
    
    conversation_history = []
    
    # Initial prompt asking Claude to search for signals
    initial_message = """You are a biosecurity signal curator. Search for and summarize 6-8 new high-signal articles from the past week across these domains:

1. Live outbreaks (WHO, UNDP)
2. AI x biosecurity (OpenAI, Anthropic, NTI, Council on Strategic Risks)
3. Pandemic infrastructure (far-UVC, ventilation, ILS/cat bonds)
4. Funding & grants (Gates, NSF SBIR, Blueprint)
5. Policy & national security (US biodefense)
6. Climate x epidemic (El Niño, ENSO)
7. Mass gatherings (Copa 2026)

For EACH article, provide:
- Title (15-25 words, concise)
- URL (must be valid and clickable)
- Source (author/domain/date)
- Description (40-60 words, plain text no HTML)
- Category (one of: outbreaks, policy, markets, climate, gatherings, heat, econ, aixbio, infra, funding, careers, ideas, events)

Format as JSON array like:
[
  {
    "title": "Title here",
    "url": "https://...",
    "source": "source.com · Date",
    "description": "Description here",
    "category": "policy"
  }
]

Return ONLY the JSON array, no other text."""

    conversation_history.append({
        "role": "user",
        "content": initial_message
    })
    
    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=2000,
        system="You are a biosecurity curator helping maintain a signal library. Search for and return high-signal articles in JSON format only.",
        messages=conversation_history
    )
    
    assistant_message = response.content[0].text
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })
    
    # Ask Claude to validate and refine the JSON
    conversation_history.append({
        "role": "user",
        "content": "Please verify all URLs are valid (200 status), correct any formatting issues, and return only valid JSON."
    })
    
    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=2000,
        system="You are a biosecurity curator helping maintain a signal library. Return only valid JSON.",
        messages=conversation_history
    )
    
    final_output = response.content[0].text
    
    # Clean up markdown code blocks if present
    final_output = final_output.replace("```json", "").replace("```", "").strip()
    
    return final_output

def add_signals_to_html(html, signals_json):
    """Add new signals to the HTML"""
    import json
    
    try:
        signals = json.loads(signals_json)
    except json.JSONDecodeError as e:
        print(f"Error parsing signals JSON: {e}")
        print(f"Raw output: {signals_json}")
        return html
    
    # Map categories to section IDs
    category_map = {
        "outbreaks": "outbreaks",
        "policy": "policy",
        "markets": "markets",
        "climate": "climate",
        "gatherings": "gatherings",
        "heat": "heat",
        "econ": "econ",
        "aixbio": "aixbio",
        "infra": "infra",
        "funding": "funding",
        "careers": "careers",
        "ideas": "ideas",
        "events": "events"
    }
    
    for signal in signals:
        category = signal.get("category", "ideas")
        section_id = category_map.get(category, "ideas")
        
        # Build the entry HTML
        entry_html = f'''        <a class="entry" href="{signal['url']}" target="_blank" rel="noopener">
          <span class="title">{signal['title']}</span>
          <span class="source">{signal['source']}</span>
          <p class="desc">{signal['description']}</p>
        </a>
'''
        
        # Find the entries div for this section and add the new entry
        pattern = f'(<section class="category" id="{section_id}">[^<]*?<div class="entries">)'
        replacement = f'\\1\n{entry_html}'
        html = re.sub(pattern, replacement, html, count=1, flags=re.DOTALL)
    
    return html

def main():
    print("🔍 Fetching biosecurity signals...")
    
    # Read current HTML
    html = read_html()
    if not html:
        return
    
    # Get new signals from Claude
    signals_json = get_biosecurity_signals()
    print(f"📄 Retrieved signals:\n{signals_json}")
    
    # Add signals to HTML
    html = add_signals_to_html(html, signals_json)
    
    # Update timestamp
    html = update_timestamp(html)
    
    # Save updated HTML
    with open('biosecurity-library.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ Biosecurity library updated successfully")

if __name__ == "__main__":
    main()
