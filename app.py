import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
import re
import time
import json
import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional, Set, Any
import hashlib
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ratelimit import limits, sleep_and_retry
import logging
import io
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# PDF IMPORTS - FIXED
# ============================================================================
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as reportlab_colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    st.warning("reportlab not installed. PDF export will be disabled. Install with: pip install reportlab")

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Publication Clustering",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# EXTENDED COLOR PALETTES (10 VARIANTS)
# ============================================================================

COLOR_PALETTES = [
    {
        'name': 'Ocean Blues',
        'primary': '#0066cc',
        'secondary': '#00a8cc',
        'gradient_start': '#0066cc',
        'gradient_end': '#00a8cc',
        'accent1': '#004d66',
        'accent2': '#66c2ff',
        'background': '#f0f8ff',
        'card_bg': '#ffffff',
        'text': '#003333',
        'border': '#b3e0ff'
    },
    {
        'name': 'Forest Green',
        'primary': '#2e7d32',
        'secondary': '#81c784',
        'gradient_start': '#1b5e20',
        'gradient_end': '#4caf50',
        'accent1': '#0d3d0d',
        'accent2': '#a5d6a7',
        'background': '#f1f8e9',
        'card_bg': '#ffffff',
        'text': '#1b3b1b',
        'border': '#c8e6c9'
    },
    {
        'name': 'Sunset Orange',
        'primary': '#e65100',
        'secondary': '#ffb74d',
        'gradient_start': '#bf360c',
        'gradient_end': '#ff9800',
        'accent1': '#8d2f00',
        'accent2': '#ffe082',
        'background': '#fff3e0',
        'card_bg': '#ffffff',
        'text': '#4a2c00',
        'border': '#ffe0b2'
    },
    {
        'name': 'Royal Purple',
        'primary': '#6a1b9a',
        'secondary': '#ba68c8',
        'gradient_start': '#4a148c',
        'gradient_end': '#9c27b0',
        'accent1': '#311b92',
        'accent2': '#ce93d8',
        'background': '#f3e5f5',
        'card_bg': '#ffffff',
        'text': '#2a0f3a',
        'border': '#e1bee7'
    },
    {
        'name': 'Ruby Red',
        'primary': '#b71c1c',
        'secondary': '#ef5350',
        'gradient_start': '#8b0000',
        'gradient_end': '#d32f2f',
        'accent1': '#5a0000',
        'accent2': '#ffcdd2',
        'background': '#ffebee',
        'card_bg': '#ffffff',
        'text': '#3b0000',
        'border': '#ffcdd2'
    },
    {
        'name': 'Amber Gold',
        'primary': '#ff8f00',
        'secondary': '#ffb300',
        'gradient_start': '#ff6f00',
        'gradient_end': '#ffa000',
        'accent1': '#b26500',
        'accent2': '#ffe082',
        'background': '#fff8e1',
        'card_bg': '#ffffff',
        'text': '#5c3f00',
        'border': '#ffecb3'
    },
    {
        'name': 'Teal Marine',
        'primary': '#00796b',
        'secondary': '#4db6ac',
        'gradient_start': '#004d40',
        'gradient_end': '#009688',
        'accent1': '#00332e',
        'accent2': '#b2dfdb',
        'background': '#e0f2f1',
        'card_bg': '#ffffff',
        'text': '#00332e',
        'border': '#b2dfdb'
    },
    {
        'name': 'Lavender Mist',
        'primary': '#7e57c2',
        'secondary': '#b085f5',
        'gradient_start': '#512da8',
        'gradient_end': '#9575cd',
        'accent1': '#311b92',
        'accent2': '#d1c4e9',
        'background': '#ede7f6',
        'card_bg': '#ffffff',
        'text': '#1e0f3a',
        'border': '#d1c4e9'
    },
    {
        'name': 'Crimson Rose',
        'primary': '#c2185b',
        'secondary': '#f06292',
        'gradient_start': '#880e4f',
        'gradient_end': '#e91e63',
        'accent1': '#560027',
        'accent2': '#f8bbd0',
        'background': '#fce4ec',
        'card_bg': '#ffffff',
        'text': '#33001a',
        'border': '#f8bbd0'
    },
    {
        'name': 'Slate Gray',
        'primary': '#546e7a',
        'secondary': '#90a4ae',
        'gradient_start': '#29434e',
        'gradient_end': '#607d8b',
        'accent1': '#1c313a',
        'accent2': '#cfd8dc',
        'background': '#eceff1',
        'card_bg': '#ffffff',
        'text': '#1c313a',
        'border': '#cfd8dc'
    }
]

# Select random palette at startup
if 'color_palette' not in st.session_state:
    st.session_state['color_palette'] = random.choice(COLOR_PALETTES)

colors = st.session_state['color_palette']

# ============================================================================
# SCIENTIFIC STYLE FOR PLOTS (INDEPENDENT FROM UI)
# ============================================================================

SCIENTIFIC_STYLE = {
    # Font sizes and weights
    'font.size': 10,
    'font.family': 'serif',
    'axes.labelsize': 11,
    'axes.labelweight': 'bold',
    'axes.titlesize': 12,
    'axes.titleweight': 'bold',
    
    # Axes appearance
    'axes.facecolor': 'white',
    'axes.edgecolor': 'black',
    'axes.linewidth': 1.0,
    'axes.grid': False,
    
    # Tick parameters
    'xtick.color': 'black',
    'ytick.color': 'black',
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'xtick.major.size': 4,
    'xtick.minor.size': 2,
    'ytick.major.size': 4,
    'ytick.minor.size': 2,
    'xtick.major.width': 0.8,
    'ytick.major.width': 0.8,
    
    # Legend
    'legend.fontsize': 10,
    'legend.frameon': True,
    'legend.framealpha': 0.9,
    'legend.edgecolor': 'black',
    'legend.fancybox': False,
    
    # Figure
    'figure.dpi': 600,
    'savefig.dpi': 600,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
    'figure.facecolor': 'white',
    
    # Lines
    'lines.linewidth': 1.5,
    'lines.markersize': 6,
    'errorbar.capsize': 3,
}

# Apply scientific style
plt.style.use('default')
plt.rcParams.update(SCIENTIFIC_STYLE)

# ============================================================================
# CUSTOM STYLES
# ============================================================================

st.markdown(f"""
<style>
    .main-header {{
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, {colors['gradient_start']} 0%, {colors['gradient_end']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.8rem;
    }}
    
    .step-card {{
        background: linear-gradient(135deg, {colors['gradient_start']}15 0%, {colors['gradient_end']}15 100%);
        border-radius: 12px;
        padding: 18px;
        border-left: 4px solid {colors['primary']};
        margin-bottom: 15px;
        box-shadow: 0 3px 5px rgba(0, 0, 0, 0.04);
    }}
    
    .metric-card {{
        background: {colors['card_bg']};
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.06);
        border: 1px solid {colors['border']};
        height: 100%;
        min-height: 90px;
    }}
    
    .metric-card h4 {{
        font-size: 0.85rem;
        margin: 0 0 8px 0;
        color: {colors['accent1']};
    }}
    
    .metric-card .value {{
        font-size: 1.6rem;
        font-weight: 700;
        color: {colors['text']};
        line-height: 1.2;
    }}
    
    .result-card {{
        background: {colors['card_bg']};
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
        border-left: 3px solid {colors['primary']};
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
    }}
    
    .info-message {{
        background: linear-gradient(135deg, {colors['primary']}15 0%, {colors['secondary']}15 100%);
        border-radius: 8px;
        padding: 12px;
        border-left: 3px solid {colors['primary']};
        font-size: 0.9rem;
        margin: 10px 0;
    }}
    
    .warning-message {{
        background: linear-gradient(135deg, #FF980015 0%, #EF6C0015 100%);
        border-radius: 8px;
        padding: 12px;
        border-left: 3px solid #FF9800;
        font-size: 0.9rem;
        margin: 10px 0;
    }}
    
    .filter-section {{
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #dee2e6;
    }}
    
    .filter-header {{
        font-size: 1.1rem;
        font-weight: 600;
        color: {colors['accent1']};
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid {colors['primary']};
    }}
    
    .filter-stats {{
        background: {colors['card_bg']};
        border-radius: 8px;
        padding: 12px;
        border: 1px solid {colors['border']};
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }}
    
    .year-checkbox-container {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin-bottom: 15px;
    }}
    
    .year-checkbox-item {{
        background: white;
        border-radius: 6px;
        padding: 10px;
        border: 1px solid #dee2e6;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
    }}
    
    .year-checkbox-item:hover {{
        border-color: {colors['primary']};
        background-color: {colors['background']};
    }}
    
    .year-checkbox-item.selected {{
        background: linear-gradient(135deg, {colors['primary']}15 0%, {colors['secondary']}15 100%);
        border-color: {colors['primary']};
        color: {colors['primary']};
        font-weight: 600;
    }}
    
    .scientific-plot {{
        background: white;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid {colors['border']};
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }}
    
    .scientific-plot h4 {{
        color: {colors['accent1']};
        font-weight: 600;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 2px solid {colors['primary']};
    }}
    
    .back-button {{
        background-color: {colors['background']};
        color: {colors['primary']};
        border: 2px solid {colors['primary']};
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    
    .back-button:hover {{
        background-color: {colors['primary']};
        color: white;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# OPENALEX API CONFIGURATION
# ============================================================================

OPENALEX_BASE_URL = "https://api.openalex.org"
MAILTO = "your-email@example.com"
POLITE_POOL_HEADER = {'User-Agent': f'Publication-Clustering (mailto:{MAILTO})'}

# Rate limit settings
RATE_LIMIT_PER_SECOND = 8
CURSOR_PAGE_SIZE = 200
MAX_RETRIES = 3
INITIAL_DELAY = 1
MAX_DELAY = 60

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def clean_text(text: str) -> str:
    """Clean text from HTML tags and extra characters"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def expand_wildcard(term: str) -> str:
    """
    Convert wildcard queries (e.g., "electroly*") to OR query for OpenAlex.
    electroly* -> (electrolyte OR electrolysis OR electrolyzer OR electrolytic OR electrolytical)
    """
    if '*' not in term:
        return term
    
    # Common expansions for typical roots
    expansions = {
        'electroly*': ['electrolyte', 'electrolysis', 'electrolyzer', 'electrolytic', 'electrolytical'],
        'cataly*': ['catalyst', 'catalysis', 'catalytic', 'catalyze', 'catalyser'],
        'polymer*': ['polymer', 'polymeric', 'polymerization', 'polymerisation', 'polymerase'],
        'nanomater*': ['nanomaterial', 'nanomaterials', 'nanostructured', 'nanoparticle'],
        'biomolec*': ['biomolecule', 'biomolecular', 'biomolecules'],
        'spectroscop*': ['spectroscopy', 'spectroscopic', 'spectroscope'],
        'chromatogra*': ['chromatography', 'chromatographic', 'chromatogram'],
        'thermodynam*': ['thermodynamics', 'thermodynamic', 'thermodynamical'],
        'quantum*': ['quantum', 'quantized', 'quantization'],
        'molecular*': ['molecular', 'molecule', 'molecules'],
    }
    
    # Check known patterns
    for pattern, expansions_list in expansions.items():
        if term.lower() == pattern.lower():
            return '(' + ' OR '.join(expansions_list) + ')'
    
    # For unknown patterns - general rule
    # Remove asterisk and look for common endings
    base = term.rstrip('*')
    common_endings = ['', 's', 'es', 'ing', 'ed', 'tion', 'tions', 'al', 'ic', 'ize', 'ise', 'izer', 'iser', 'lysis', 'lytic']
    expanded_terms = [base + ending for ending in common_endings if base + ending]
    
    if len(expanded_terms) > 1:
        return '(' + ' OR '.join(expanded_terms) + ')'
    
    return term

def parse_query_terms(term: str) -> str:
    """
    Parse search term for OpenAlex API.
    Enhanced version with proper phrase and wildcard handling.
    Supports:
    - Simple words
    - Phrases in quotes
    - Logical operators: AND, OR, NOT
    - Wildcard (*) queries
    """
    term = term.strip()
    
    # Check for wildcard
    if '*' in term and not (term.startswith('"') and term.endswith('"')):
        return expand_wildcard(term)
    
    # If it's a quoted phrase, leave as is
    if term.startswith('"') and term.endswith('"'):
        return term
    
    # If there's OR operator (case insensitive)
    if ' OR ' in term.upper():
        # Split by OR, process each part
        parts = re.split(r'\s+OR\s+', term, flags=re.IGNORECASE)
        processed_parts = []
        for part in parts:
            part = part.strip()
            if ' ' in part and not (part.startswith('"') and part.endswith('"')):
                # If part has spaces, wrap in quotes
                processed_parts.append(f'"{part}"')
            else:
                processed_parts.append(part)
        return ' OR '.join(processed_parts)
    
    # If there are spaces but no OR, it's a phrase - use quotes
    if ' ' in term:
        return f'"{term}"'
    
    return term

def create_metric_card(title: str, value, icon: str = "📊"):
    """Create compact metric card with formatted numbers"""
    # Format large numbers with commas
    if isinstance(value, (int, float)):
        formatted_value = f"{value:,}"
    else:
        formatted_value = str(value)
    
    st.markdown(f"""
    <div class="metric-card">
        <h4>{icon} {title}</h4>
        <div class="value">{formatted_value}</div>
    </div>
    """, unsafe_allow_html=True)

def create_result_card(work: dict, index: int, topic: str):
    """Create result card"""
    citation_count = work.get('cited_by_count', 0)
    
    # Determine citation badge color
    if citation_count == 0:
        badge_color = "#4CAF50"
        badge_text = "0 citations"
    elif citation_count <= 3:
        badge_color = "#4CAF50"
        badge_text = f"{citation_count} citation{'s' if citation_count > 1 else ''}"
    elif citation_count <= 10:
        badge_color = "#FF9800"
        badge_text = f"{citation_count} citations"
    else:
        badge_color = "#f44336"
        badge_text = f"{citation_count} citations"
    
    oa_badge = '🔓' if work.get('is_oa') else '🔒'
    doi_url = work.get('doi_url', '')
    title = work.get('title', 'No title')
    authors = ', '.join(work.get('authors', [])[:2])
    if len(work.get('authors', [])) > 2:
        authors += ' et al.'
    
    st.markdown(f"""
    <div class="result-card">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <div>
                <span style="font-weight: 600; color: {colors['primary']}; margin-right: 8px;">{topic} #{index}</span>
                <span style="background: {badge_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;">
                    {badge_text}
                </span>
                <span style="background: #e3f2fd; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; margin-left: 5px;">
                    Score: {work.get('relevance_score', 0):.2f}
                </span>
            </div>
            <span style="color: #666; font-size: 0.8rem;">{work.get('publication_year', '')}</span>
        </div>
        <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 5px; line-height: 1.3;">{title}</div>
        <div style="color: #555; font-size: 0.85rem; margin-bottom: 5px;">👤 {authors}</div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
            <span>{oa_badge} {work.get('journal', '')[:30]}</span>
            <a href="{doi_url}" target="_blank" style="color: {colors['primary']}; text-decoration: none; font-size: 0.85rem;">
                🔗 View Article
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

def navigation_buttons(show_back: bool = True, show_new: bool = True):
    """Display navigation buttons"""
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if show_back and st.session_state.step > 1:
            if st.button("← Back", key="back_btn", use_container_width=True):
                st.session_state.step -= 1
                st.rerun()
    
    with col2:
        if show_new:
            if st.button("🔄 New Search", key="new_btn", use_container_width=True):
                # Clear session but keep terms for Step 1
                level1 = st.session_state.get('level1_input', '')
                level2 = st.session_state.get('level2_input', '')
                level3 = st.session_state.get('level3_input', [])
                years = st.session_state.get('years_input', [])
                
                for key in ['step', 'results', 'topic_counts', 'level1_count', 'level2_count', 'consistent_data']:
                    if key in st.session_state:
                        del st.session_state[key]
                
                st.session_state.step = 1
                st.session_state['level1_input'] = level1
                st.session_state['level2_input'] = level2
                st.session_state['level3_input'] = level3
                st.session_state['years_input'] = years
                st.rerun()

# ============================================================================
# QUERY BUILDING FUNCTIONS
# ============================================================================

def build_search_filter(level1_term: str, level2_term: Optional[str] = None,
                       years: Optional[List[int]] = None) -> Dict[str, str]:
    """Build filters for OpenAlex API based on first two levels"""
    filters = {}
    
    # Build search query
    search_parts = []
    
    # Level 1 - main term
    if level1_term:
        parsed = parse_query_terms(level1_term)
        search_parts.append(parsed)
    
    # Level 2 - additional term (optional)
    if level2_term:
        parsed = parse_query_terms(level2_term)
        search_parts.append(parsed)
    
    # Combine all parts with AND
    if search_parts:
        # Use default.search instead of title_and_abstract.search for better results
        filters['default.search'] = ' AND '.join(search_parts)
    
    # Year filter
    if years:
        if len(years) == 1:
            filters['publication_year'] = str(years[0])
        else:
            # For range use format from:to
            filters['publication_year'] = f"{min(years)}-{max(years)}"
    
    return filters

def build_level3_filter(level3_term: str, base_filters: Dict[str, str]) -> str:
    """Build filter for level 3 term including all filters"""
    filter_parts = []
    
    if 'publication_year' in base_filters:
        filter_parts.append(f"publication_year:{base_filters['publication_year']}")
    
    # Collect search parts
    search_parts = []
    if 'default.search' in base_filters:
        search_parts.append(f"({base_filters['default.search']})")
    
    if level3_term:
        parsed = parse_query_terms(level3_term)
        search_parts.append(f"({parsed})")
    
    if search_parts:
        filter_parts.append(f"default.search:{' AND '.join(search_parts)}")
    
    return ','.join(filter_parts)

def build_count_filter(base_filters: Dict[str, str]) -> str:
    """Build filter only from first two levels"""
    filter_parts = []
    
    if 'publication_year' in base_filters:
        filter_parts.append(f"publication_year:{base_filters['publication_year']}")
    
    if 'default.search' in base_filters:
        filter_parts.append(f"default.search:{base_filters['default.search']}")
    
    return ','.join(filter_parts)

# ============================================================================
# OPENALEX API REQUEST FUNCTIONS
# ============================================================================

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=INITIAL_DELAY, max=MAX_DELAY),
    retry=retry_if_exception_type((requests.exceptions.RequestException,))
)
@sleep_and_retry
@limits(calls=RATE_LIMIT_PER_SECOND, period=1)
def make_openalex_request(url: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """Make request to OpenAlex API with rate limiting"""
    if params is None:
        params = {}
    
    params['mailto'] = MAILTO
    
    try:
        response = requests.get(
            url,
            params=params,
            headers=POLITE_POOL_HEADER,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 5))
            logger.warning(f"Rate limited. Waiting {retry_after} seconds")
            time.sleep(retry_after)
            raise requests.exceptions.RequestException("Rate limited")
        else:
            logger.error(f"Error {response.status_code}: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        logger.warning("Request timeout")
        raise
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        raise

def get_total_count(level1_term: str, level2_term: Optional[str] = None,
                   years: Optional[List[int]] = None) -> int:
    """Get total count of papers matching query"""
    filters = build_search_filter(level1_term, level2_term, years=years)
    filter_str = build_count_filter(filters)
    
    if not filter_str:
        return 0
    
    params = {
        'filter': filter_str,
        'per-page': 1
    }
    
    data = make_openalex_request(f"{OPENALEX_BASE_URL}/works", params)
    
    if data and 'meta' in data:
        return data['meta'].get('count', 0)
    
    return 0

def test_query(level1_term: str, level2_term: Optional[str] = None, years: Optional[List[int]] = None):
    """Test query and show how it will be sent to OpenAlex"""
    filters = build_search_filter(level1_term, level2_term, years)
    filter_str = build_count_filter(filters)
    
    st.write("**Debug Information:**")
    st.write(f"Original Level 1: {level1_term}")
    st.write(f"Parsed Level 1: {parse_query_terms(level1_term)}")
    if level2_term:
        st.write(f"Original Level 2: {level2_term}")
        st.write(f"Parsed Level 2: {parse_query_terms(level2_term)}")
    st.write(f"Filter string: {filter_str}")
    st.write(f"Full URL: https://api.openalex.org/works?filter={filter_str}&per-page=1")
    
    # Test request
    count = get_total_count(level1_term, level2_term, years)
    st.write(f"**Result count: {count:,}**")
    return count

def get_topic_counts(level1_term: str, level2_term: Optional[str],
                    level3_terms: List[str], years: Optional[List[int]],
                    progress_callback=None) -> Dict[str, int]:
    """Get paper counts for each level 3 term"""
    base_filters = build_search_filter(level1_term, level2_term, years=years)
    counts = {}
    
    for i, term in enumerate(level3_terms):
        if progress_callback:
            progress_callback(i / len(level3_terms), f"Analyzing: {term}")
        
        filter_str = build_level3_filter(term, base_filters)
        
        params = {
            'filter': filter_str,
            'per-page': 1
        }
        
        data = make_openalex_request(f"{OPENALEX_BASE_URL}/works", params)
        
        if data and 'meta' in data:
            counts[term] = data['meta'].get('count', 0)
        else:
            counts[term] = 0
        
        time.sleep(0.2)
    
    return counts

def fetch_top_works(level1_term: str, level2_term: Optional[str],
                   level3_term: str, years: Optional[List[int]],
                   limit: int = 100, progress_callback=None) -> List[Dict]:
    """Fetch top N most relevant works for a term"""
    base_filters = build_search_filter(level1_term, level2_term, years=years)
    filter_str = build_level3_filter(level3_term, base_filters)
    
    all_works = []
    cursor = "*"
    page = 0
    
    while len(all_works) < limit and cursor:
        page += 1
        if progress_callback:
            progress_callback(
                min(len(all_works) / limit, 0.99),
                f"Fetching {level3_term}: page {page}"
            )
        
        params = {
            'filter': filter_str,
            'per-page': min(CURSOR_PAGE_SIZE, limit - len(all_works)),
            'cursor': cursor,
            'sort': 'relevance_score:desc'
        }
        
        data = make_openalex_request(f"{OPENALEX_BASE_URL}/works", params)
        
        if not data or 'results' not in data:
            break
        
        works = data['results']
        if not works:
            break
        
        all_works.extend(works)
        cursor = data.get('meta', {}).get('next_cursor')
        time.sleep(0.1)
    
    return all_works[:limit]

def enrich_work_data(work: Dict) -> Dict:
    """Enrich work data with additional fields"""
    if not work:
        return {}
    
    doi_raw = work.get('doi')
    doi_clean = ''
    if doi_raw:
        doi_clean = str(doi_raw).replace('https://doi.org/', '')
    
    enriched = {
        'id': work.get('id', ''),
        'doi': doi_clean,
        'title': clean_text(work.get('title', '')),
        'publication_date': work.get('publication_date', ''),
        'publication_year': work.get('publication_year', 0),
        'cited_by_count': work.get('cited_by_count', 0),
        'type': work.get('type', ''),
        'doi_url': f"https://doi.org/{doi_clean}" if doi_clean else '',
        'relevance_score': work.get('relevance_score', 0)
    }
    
    # Authors
    authorships = work.get('authorships', [])
    authors = []
    for authorship in authorships[:5]:
        if authorship and 'author' in authorship:
            author_name = authorship['author'].get('display_name', '')
            if author_name:
                authors.append(author_name)
    enriched['authors'] = authors
    
    # Journal
    primary_location = work.get('primary_location')
    if primary_location and 'source' in primary_location:
        source = primary_location['source']
        enriched['journal'] = source.get('display_name', '') if source else ''
    else:
        enriched['journal'] = ''
    
    # Open Access
    open_access = work.get('open_access', {})
    enriched['is_oa'] = open_access.get('is_oa', False)
    
    return enriched

def get_yearly_distribution_group_by(level1_term: str, level2_term: Optional[str], 
                                    level3_term: str, years: List[int]) -> Dict[int, int]:
    """
    Get yearly distribution for a specific sub-topic using group_by (single request)
    This ensures perfect consistency between total count and yearly sum
    """
    base_filters = build_search_filter(level1_term, level2_term)
    filter_str = build_level3_filter(level3_term, base_filters)
    
    params = {
        'filter': filter_str,
        'group-by': 'publication_year',
        'per-page': 200
    }
    
    data = make_openalex_request(f"{OPENALEX_BASE_URL}/works", params)
    
    # Initialize all years with 0
    yearly_counts = {year: 0 for year in years}
    
    if data and 'group_by' in data:
        for group in data['group_by']:
            try:
                year = int(group['key'])
                if year in years:
                    yearly_counts[year] = group['count']
            except (ValueError, TypeError):
                continue
    
    return yearly_counts

# ============================================================================
# NEW FUNCTIONS FOR ENHANCED CITATION ANALYSIS
# ============================================================================

def get_citation_distribution_group_by(level1_term: str, level2_term: Optional[str],
                                      level3_term: str, years: List[int]) -> Dict[str, int]:
    """
    Get citation distribution using group_by with filters for citation ranges.
    Makes 4 separate API requests to get exact counts for each citation category.
    """
    base_filters = build_search_filter(level1_term, level2_term)
    
    # Define citation ranges
    citation_ranges = {
        '0': 'cited_by_count:0',
        '1-3': 'cited_by_count:1-3',
        '4-10': 'cited_by_count:4-10',
        '11-50': 'cited_by_count:11-50',
        '51-100': 'cited_by_count:51-100',
        '100+': 'cited_by_count:>100'
    }
    
    distribution = {}
    
    for range_name, range_filter in citation_ranges.items():
        # Combine base filter with citation range filter
        combined_filter = f"{range_filter}"
        if base_filters:
            filter_parts = []
            if 'publication_year' in base_filters:
                filter_parts.append(f"publication_year:{base_filters['publication_year']}")
            if 'default.search' in base_filters:
                filter_parts.append(f"default.search:{base_filters['default.search']}")
            if level3_term:
                parsed = parse_query_terms(level3_term)
                filter_parts.append(f"default.search:({parsed})")
            
            if filter_parts:
                combined_filter = f"{range_filter},{','.join(filter_parts)}"
        
        params = {
            'filter': combined_filter,
            'per-page': 1
        }
        
        data = make_openalex_request(f"{OPENALEX_BASE_URL}/works", params)
        
        if data and 'meta' in data:
            distribution[range_name] = data['meta'].get('count', 0)
        else:
            distribution[range_name] = 0
        
        time.sleep(0.1)  # Small delay to be polite to API
    
    return distribution

def calculate_gini_coefficient(citations: List[int]) -> float:
    """
    Calculate Gini coefficient for citation distribution.
    Gini = 0 (perfect equality) to 1 (perfect inequality)
    """
    if citations is None or len(citations) == 0:
        return 0.0
    
    citations = np.array(citations)
    if len(citations) == 0 or np.sum(citations) == 0:
        return 0.0
    
    # Sort citations in ascending order
    citations = np.sort(citations)
    n = len(citations)
    
    # Calculate Gini coefficient using the formula:
    # G = (2 * Σ(i * x_i)) / (n * Σx) - (n + 1)/n
    indices = np.arange(1, n + 1)
    numerator = 2 * np.sum(indices * citations)
    denominator = n * np.sum(citations)
    
    if denominator == 0:
        return 0.0
    
    gini = (numerator / denominator) - (n + 1) / n
    return float(gini)

def calculate_cagr(start_count: int, end_count: int, num_years: int) -> float:
    """
    Calculate Compound Annual Growth Rate
    CAGR = (End/Start)^(1/num_years) - 1
    """
    if start_count == 0 or num_years == 0:
        return 0.0
    
    cagr = (end_count / start_count) ** (1 / num_years) - 1
    return float(cagr * 100)  # Return as percentage

def calculate_citation_velocity(citations: int, years_since_publication: int) -> float:
    """
    Calculate citation velocity (citations per year since publication)
    """
    if years_since_publication == 0:
        return 0.0
    return citations / years_since_publication

def get_consistent_topic_data(level1_term: str, level2_term: Optional[str],
                            level3_terms: List[str], years: List[int],
                            max_papers_to_fetch: int = 100,
                            progress_callback=None) -> Dict[str, Dict]:
    """
    Get consistent data for all topics using hybrid approach:
    - group_by for yearly distributions (single request per topic)
    - group_by for citation distributions (4 requests per topic)
    - topic_counts from the same group_by data (sum of yearly)
    - fetch top papers for detailed view (limited)
    
    This ensures all visualizations use the SAME source data
    """
    consistent_data = {}
    total_terms = len(level3_terms)
    
    for idx, term in enumerate(level3_terms):
        if progress_callback:
            progress_callback(
                idx / total_terms,
                f"Analyzing: {term}"
            )
        
        # Step 1: Get yearly distribution using group_by (1 request)
        yearly_dist = get_yearly_distribution_group_by(
            level1_term, level2_term, term, years
        )
        
        # Step 2: Get citation distribution using group_by (4 requests)
        citation_dist = get_citation_distribution_group_by(
            level1_term, level2_term, term, years
        )
        
        # Step 3: Calculate total from yearly data (ensures consistency)
        total_papers = sum(yearly_dist.values())
        
        # Step 4: Fetch top works for detailed view
        top_works = []
        if total_papers > 0:
            top_works = fetch_top_works(
                level1_term, level2_term, term, years,
                limit=max_papers_to_fetch
            )
        
        # Step 5: Calculate enhanced citation stats from top works
        citation_stats = {}
        if top_works:
            citations = [w.get('cited_by_count', 0) for w in top_works]
            
            # Calculate current year for citation velocity
            current_year = datetime.now().year
            
            # Calculate citation velocities
            velocities = []
            for work in top_works:
                pub_year = work.get('publication_year', current_year)
                years_since = max(1, current_year - pub_year)
                velocity = calculate_citation_velocity(
                    work.get('cited_by_count', 0), 
                    years_since
                )
                velocities.append(velocity)
            
            # Calculate Gini coefficient
            gini = calculate_gini_coefficient(citations)
            
            citation_stats = {
                'mean': float(np.mean(citations)),
                'median': float(np.median(citations)),
                'max': int(max(citations)),
                'gini': gini,
                'total_citations': int(sum(citations)),
                'mean_velocity': float(np.mean(velocities)),
                'median_velocity': float(np.median(velocities)),
                'distribution': {
                    '0': int(sum(1 for c in citations if c == 0)),
                    '1-3': int(sum(1 for c in citations if 1 <= c <= 3)),
                    '4-10': int(sum(1 for c in citations if 4 <= c <= 10)),
                    '11-50': int(sum(1 for c in citations if 11 <= c <= 50)),
                    '51-100': int(sum(1 for c in citations if 51 <= c <= 100)),
                    '100+': int(sum(1 for c in citations if c > 100))
                },
                'highly_cited_50': int(sum(1 for c in citations if c > 50)),
                'highly_cited_100': int(sum(1 for c in citations if c > 100))
            }
        
        # Step 6: Calculate CAGR for last 5 years if enough data
        cagr_data = {}
        if len(years) >= 5:
            recent_years = sorted(years)[-5:]
            if len(recent_years) >= 2:
                start_year = recent_years[0]
                end_year = recent_years[-1]
                start_count = yearly_dist.get(start_year, 0)
                end_count = yearly_dist.get(end_year, 0)
                cagr_data = {
                    'period': f"{start_year}-{end_year}",
                    'cagr': calculate_cagr(start_count, end_count, len(recent_years) - 1),
                    'start_count': start_count,
                    'end_count': end_count
                }
        
        # Step 7: Find peak year
        peak_year = None
        peak_count = 0
        for year, count in yearly_dist.items():
            if count > peak_count:
                peak_count = count
                peak_year = year
        
        consistent_data[term] = {
            'total': total_papers,
            'yearly': yearly_dist,  # Exact data from group_by
            'citation_distribution': citation_dist,  # Exact counts from group_by
            'top_works': top_works,
            'citation_stats': citation_stats,
            'cagr': cagr_data,
            'peak_year': peak_year,
            'peak_count': peak_count
        }
        
        # Small delay to be polite to API
        time.sleep(0.1)
    
    return consistent_data

# ============================================================================
# ENHANCED VISUALIZATION FUNCTIONS
# ============================================================================

def create_lorenz_curve(all_works_by_topic: Dict[str, List[Dict]], title: str = "Citation Inequality (Lorenz Curve)"):
    """
    Create Lorenz curve showing citation inequality across all topics combined
    """
    # Collect all citations from all topics
    all_citations = []
    for topic, works in all_works_by_topic.items():
        for work in works:
            all_citations.append(work.get('cited_by_count', 0))
    
    if not all_citations:
        return None
    
    # Sort citations
    all_citations = np.sort(all_citations)
    n = len(all_citations)
    
    # Calculate cumulative shares
    cum_citations = np.cumsum(all_citations)
    total_citations = cum_citations[-1] if cum_citations[-1] > 0 else 1
    
    # Population shares (x-axis)
    population_share = np.arange(1, n + 1) / n
    
    # Citation shares (y-axis)
    citation_share = cum_citations / total_citations
    
    # Calculate Gini coefficient for all papers combined
    gini_all = calculate_gini_coefficient(all_citations)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Apply scientific style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_linewidth(1.0)
    ax.spines['left'].set_linewidth(1.0)
    ax.tick_params(axis='both', which='major', labelsize=9)
    
    # Plot Lorenz curve
    ax.plot(population_share, citation_share, 'b-', linewidth=2, label=f'Lorenz curve (Gini = {gini_all:.3f})')
    
    # Plot equality line
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Perfect equality')
    
    # Fill area between curves
    ax.fill_between(population_share, population_share, citation_share, alpha=0.2, color='gray')
    
    ax.set_xlabel('Cumulative share of papers (from least to most cited)', fontsize=10, fontweight='bold')
    ax.set_ylabel('Cumulative share of citations', fontsize=10, fontweight='bold')
    ax.set_title(title, fontsize=11, fontweight='bold', pad=10)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(fontsize=9, frameon=True, edgecolor='black')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Add text box with interpretation
    if gini_all > 0.6:
        interpretation = "Very high inequality (Matthew effect)"
    elif gini_all > 0.4:
        interpretation = "High inequality"
    elif gini_all > 0.2:
        interpretation = "Moderate inequality"
    else:
        interpretation = "Low inequality"
    
    ax.text(0.05, 0.95, f"Interpretation: {interpretation}\nTotal papers: {n:,}\nTotal citations: {total_citations:,}", 
            transform=ax.transAxes, fontsize=8, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    return fig

def create_top_journals_chart(all_works_by_topic: Dict[str, List[Dict]], top_n: int = 10):
    """
    Create chart showing top journals by number of publications and their average citations
    """
    # Collect journal data
    journal_data = defaultdict(lambda: {'count': 0, 'citations': [], 'topics': set()})
    
    for topic, works in all_works_by_topic.items():
        for work in works:
            enriched = enrich_work_data(work)
            journal = enriched.get('journal', 'Unknown Journal')
            if journal and journal != 'Unknown Journal':
                journal_data[journal]['count'] += 1
                journal_data[journal]['citations'].append(enriched.get('cited_by_count', 0))
                journal_data[journal]['topics'].add(topic)
    
    if not journal_data:
        return None
    
    # Sort by publication count and get top N
    top_journals = sorted(journal_data.items(), key=lambda x: x[1]['count'], reverse=True)[:top_n]
    
    # Prepare data for plotting
    journals = [j[0] for j in top_journals]
    counts = [j[1]['count'] for j in top_journals]
    avg_citations = [np.mean(j[1]['citations']) if j[1]['citations'] else 0 for j in top_journals]
    topic_counts = [len(j[1]['topics']) for j in top_journals]
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Apply scientific style
    for ax in [ax1, ax2]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_linewidth(1.0)
        ax.spines['left'].set_linewidth(1.0)
        ax.tick_params(axis='both', which='major', labelsize=9)
    
    # Plot 1: Publication counts
    y_pos = np.arange(len(journals))
    bars1 = ax1.barh(y_pos, counts, color='gray', edgecolor='black', linewidth=0.5)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(journals, fontsize=8)
    ax1.set_xlabel('Number of Publications', fontsize=10, fontweight='bold')
    ax1.set_title('A) Top Journals by Publication Count', fontsize=11, fontweight='bold', pad=10)
    
    # Add values to bars
    for i, (bar, count, topics) in enumerate(zip(bars1, counts, topic_counts)):
        ax1.text(count + max(counts)*0.01, bar.get_y() + bar.get_height()/2, 
                f'{count} ({topics} topics)', va='center', fontsize=7)
    
    # Plot 2: Average citations
    bars2 = ax2.barh(y_pos, avg_citations, color='lightgray', edgecolor='black', linewidth=0.5)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([])  # Remove labels
    ax2.set_xlabel('Average Citations per Paper', fontsize=10, fontweight='bold')
    ax2.set_title('B) Average Citations by Journal', fontsize=11, fontweight='bold', pad=10)
    
    # Add values to bars
    for i, (bar, avg_cit) in enumerate(zip(bars2, avg_citations)):
        ax2.text(avg_cit + max(avg_citations)*0.01, bar.get_y() + bar.get_height()/2, 
                f'{avg_cit:.1f}', va='center', fontsize=8)
    
    plt.suptitle(f'Top {top_n} Journals Analysis', fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    return fig

def create_citation_velocity_chart(consistent_data: Dict[str, Dict], current_year: int = None):
    """
    Create chart showing citation velocity (citations per year) for each topic
    """
    if current_year is None:
        current_year = datetime.now().year
    
    topics = []
    velocities = []
    errors = []
    
    for topic, data in consistent_data.items():
        if data['citation_stats'] and 'mean_velocity' in data['citation_stats']:
            topics.append(topic)
            velocities.append(data['citation_stats']['mean_velocity'])
            # Use standard deviation or quartiles for error bars if available
            # For now, use a simple estimate
            errors.append(data['citation_stats'].get('mean_velocity', 0) * 0.2)
    
    if not topics:
        return None
    
    # Sort by velocity
    sorted_data = sorted(zip(topics, velocities, errors), key=lambda x: x[1], reverse=True)
    topics = [x[0] for x in sorted_data]
    velocities = [x[1] for x in sorted_data]
    errors = [x[2] for x in sorted_data]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Apply scientific style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_linewidth(1.0)
    ax.spines['left'].set_linewidth(1.0)
    ax.tick_params(axis='both', which='major', labelsize=9)
    
    # Create bar chart with error bars
    x_pos = np.arange(len(topics))
    bars = ax.bar(x_pos, velocities, yerr=errors, capsize=5, 
                  color='gray', edgecolor='black', linewidth=0.5, 
                  error_kw={'ecolor': 'black', 'linewidth': 1})
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(topics, rotation=45, ha='right', fontsize=9)
    ax.set_xlabel('Research Topic', fontsize=10, fontweight='bold')
    ax.set_ylabel('Mean Citations per Year', fontsize=10, fontweight='bold')
    ax.set_title('Citation Velocity by Topic\n(Higher values indicate "hotter" research areas)', 
                 fontsize=11, fontweight='bold', pad=10)
    
    # Add values on bars
    for i, (bar, vel) in enumerate(zip(bars, velocities)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(velocities)*0.02,
                f'{vel:.2f}', ha='center', va='bottom', fontsize=8)
    
    # Add reference line for average
    avg_velocity = np.mean(velocities)
    ax.axhline(avg_velocity, color='red', linestyle='--', linewidth=1, 
               label=f'Average: {avg_velocity:.2f}')
    ax.legend(fontsize=8, frameon=True, edgecolor='black')
    
    plt.tight_layout()
    return fig

def create_highly_cited_share_chart(consistent_data: Dict[str, Dict], threshold: int = 50):
    """
    Create chart showing share of highly-cited papers (>threshold citations) by topic
    """
    topics = []
    shares = []
    counts = []
    
    for topic, data in consistent_data.items():
        if data['citation_stats']:
            total_papers = len(data['top_works'])
            if total_papers > 0:
                highly_cited = data['citation_stats'].get(f'highly_cited_{threshold}', 0)
                share = (highly_cited / total_papers) * 100
                topics.append(topic)
                shares.append(share)
                counts.append(highly_cited)
    
    if not topics:
        return None
    
    # Sort by share
    sorted_data = sorted(zip(topics, shares, counts), key=lambda x: x[1], reverse=True)
    topics = [x[0] for x in sorted_data]
    shares = [x[1] for x in sorted_data]
    counts = [x[2] for x in sorted_data]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Apply scientific style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_linewidth(1.0)
    ax.spines['left'].set_linewidth(1.0)
    ax.tick_params(axis='both', which='major', labelsize=9)
    
    # Create horizontal bar chart
    y_pos = np.arange(len(topics))
    bars = ax.barh(y_pos, shares, color='gray', edgecolor='black', linewidth=0.5)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(topics, fontsize=9)
    ax.set_xlabel(f'Percentage of Papers with >{threshold} Citations (%)', fontsize=10, fontweight='bold')
    ax.set_ylabel('Research Topic', fontsize=10, fontweight='bold')
    ax.set_title(f'Share of Highly-Cited Papers (>{threshold} citations) by Topic', 
                 fontsize=11, fontweight='bold', pad=10)
    
    # Add values to bars
    for i, (bar, share, count) in enumerate(zip(bars, shares, counts)):
        ax.text(share + max(shares)*0.01, bar.get_y() + bar.get_height()/2,
                f'{share:.1f}% ({count})', va='center', fontsize=8)
    
    plt.tight_layout()
    return fig

def create_relevance_vs_citations_scatter(consistent_data: Dict[str, Dict]):
    """
    Create scatter plot of relevance score vs citation count for all papers
    """
    all_data = []
    for topic, data in consistent_data.items():
        for work in data['top_works']:
            enriched = enrich_work_data(work)
            all_data.append({
                'topic': topic,
                'relevance': enriched.get('relevance_score', 0),
                'citations': enriched.get('cited_by_count', 0),
                'title': enriched.get('title', '')[:50]
            })
    
    if not all_data:
        return None
    
    df = pd.DataFrame(all_data)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Apply scientific style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_linewidth(1.0)
    ax.spines['left'].set_linewidth(1.0)
    ax.tick_params(axis='both', which='major', labelsize=9)
    
    # Create scatter plot with different colors for topics
    topics = df['topic'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(topics)))
    
    for topic, color in zip(topics, colors):
        topic_data = df[df['topic'] == topic]
        ax.scatter(topic_data['relevance'], topic_data['citations'], 
                  alpha=0.6, s=30, label=topic, color=color, edgecolor='black', linewidth=0.3)
    
    # Add trend line
    z = np.polyfit(df['relevance'], df['citations'], 1)
    p = np.poly1d(z)
    ax.plot(df['relevance'], p(df['relevance']), "r--", alpha=0.8, linewidth=1, 
            label=f'Trend (r² = {np.corrcoef(df["relevance"], df["citations"])[0,1]**2:.3f})')
    
    ax.set_xlabel('OpenAlex Relevance Score', fontsize=10, fontweight='bold')
    ax.set_ylabel('Number of Citations', fontsize=10, fontweight='bold')
    ax.set_title('Relevance Score vs Citation Count\n(Does relevance predict impact?)', 
                 fontsize=11, fontweight='bold', pad=10)
    ax.legend(fontsize=8, frameon=True, edgecolor='black', loc='upper left')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Use log scale for citations if range is large
    if df['citations'].max() > 100:
        ax.set_yscale('log')
        ax.set_ylabel('Number of Citations (log scale)', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    return fig

def create_cagr_chart(consistent_data: Dict[str, Dict], years: List[int]):
    """
    Create chart showing Compound Annual Growth Rate for each topic
    """
    topics = []
    cagrs = []
    periods = []
    start_counts = []
    end_counts = []
    
    for topic, data in consistent_data.items():
        if data.get('cagr') and data['cagr']:
            topics.append(topic)
            cagrs.append(data['cagr']['cagr'])
            periods.append(data['cagr']['period'])
            start_counts.append(data['cagr']['start_count'])
            end_counts.append(data['cagr']['end_count'])
    
    if not topics:
        return None
    
    # Sort by CAGR
    sorted_data = sorted(zip(topics, cagrs, periods, start_counts, end_counts), 
                        key=lambda x: x[1], reverse=True)
    topics = [x[0] for x in sorted_data]
    cagrs = [x[1] for x in sorted_data]
    periods = [x[2] for x in sorted_data]
    start_counts = [x[3] for x in sorted_data]
    end_counts = [x[4] for x in sorted_data]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Apply scientific style
    for ax in [ax1, ax2]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_linewidth(1.0)
        ax.spines['left'].set_linewidth(1.0)
        ax.tick_params(axis='both', which='major', labelsize=9)
    
    # Plot 1: CAGR values
    y_pos = np.arange(len(topics))
    bars1 = ax1.barh(y_pos, cagrs, color='gray', edgecolor='black', linewidth=0.5)
    
    # Color positive/negative differently
    for i, (bar, cagr) in enumerate(zip(bars1, cagrs)):
        if cagr < 0:
            bar.set_color('lightcoral')
        elif cagr > 10:
            bar.set_color('darkgreen')
    
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(topics, fontsize=9)
    ax1.set_xlabel('Compound Annual Growth Rate (%)', fontsize=10, fontweight='bold')
    ax1.set_title(f'A) Growth Rate ({periods[0]})', fontsize=11, fontweight='bold', pad=10)
    
    # Add zero line
    ax1.axvline(0, color='black', linewidth=0.8, linestyle='-')
    
    # Add values to bars
    for i, (bar, cagr, start, end) in enumerate(zip(bars1, cagrs, start_counts, end_counts)):
        ax1.text(cagr + (max(cagrs)*0.02 if cagr >= 0 else -max(cagrs)*0.1), 
                bar.get_y() + bar.get_height()/2,
                f'{cagr:.1f}% ({start}→{end})', va='center', fontsize=7,
                ha='left' if cagr >= 0 else 'right')
    
    # Plot 2: Growth visualization (start vs end)
    width = 0.35
    x = np.arange(len(topics))
    
    ax2.bar(x - width/2, start_counts, width, label='Start', 
            color='lightgray', edgecolor='black', linewidth=0.5)
    ax2.bar(x + width/2, end_counts, width, label='End', 
            color='gray', edgecolor='black', linewidth=0.5)
    
    ax2.set_xticks(x)
    ax2.set_xticklabels(topics, rotation=45, ha='right', fontsize=8)
    ax2.set_xlabel('Research Topic', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Number of Publications', fontsize=10, fontweight='bold')
    ax2.set_title('B) Publication Count: Start vs End of Period', fontsize=11, fontweight='bold', pad=10)
    ax2.legend(fontsize=8, frameon=True, edgecolor='black')
    
    plt.suptitle('Publication Growth Analysis (CAGR)', fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    return fig

def create_peak_year_analysis(consistent_data: Dict[str, Dict]):
    """
    Create chart showing peak publication year for each topic
    """
    topics = []
    peak_years = []
    peak_counts = []
    current_counts = []  # Count in most recent year
    
    # Get most recent year from data
    all_years = []
    for data in consistent_data.values():
        all_years.extend(data['yearly'].keys())
    if not all_years:
        return None
    latest_year = max(all_years)
    
    for topic, data in consistent_data.items():
        if data['peak_year'] is not None:
            topics.append(topic)
            peak_years.append(data['peak_year'])
            peak_counts.append(data['peak_count'])
            current_counts.append(data['yearly'].get(latest_year, 0))
    
    if not topics:
        return None
    
    # Sort by peak year
    sorted_data = sorted(zip(topics, peak_years, peak_counts, current_counts), 
                        key=lambda x: x[1])
    topics = [x[0] for x in sorted_data]
    peak_years = [x[1] for x in sorted_data]
    peak_counts = [x[2] for x in sorted_data]
    current_counts = [x[3] for x in sorted_data]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Apply scientific style
    for ax in [ax1, ax2]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_linewidth(1.0)
        ax.spines['left'].set_linewidth(1.0)
        ax.tick_params(axis='both', which='major', labelsize=9)
    
    # Plot 1: Peak years
    y_pos = np.arange(len(topics))
    colors = []
    for year in peak_years:
        if year < latest_year - 3:
            colors.append('lightcoral')  # Past peak
        elif year > latest_year - 2:
            colors.append('lightgreen')  # Still growing
        else:
            colors.append('lightyellow')  # Plateau
    
    bars1 = ax1.barh(y_pos, peak_years, color=colors, edgecolor='black', linewidth=0.5)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(topics, fontsize=9)
    ax1.set_xlabel('Peak Publication Year', fontsize=10, fontweight='bold')
    ax1.set_title('A) Peak Year of Publication Activity', fontsize=11, fontweight='bold', pad=10)
    
    # Add vertical line for current year
    ax1.axvline(latest_year, color='red', linestyle='--', linewidth=1, label=f'Current ({latest_year})')
    
    # Add values
    for i, (bar, year, count) in enumerate(zip(bars1, peak_years, peak_counts)):
        ax1.text(year + 0.5, bar.get_y() + bar.get_height()/2,
                f'{year} ({count} papers)', va='center', fontsize=8)
    
    ax1.legend(fontsize=8, frameon=True, edgecolor='black')
    
    # Plot 2: Peak vs Current
    width = 0.35
    x = np.arange(len(topics))
    
    ax2.bar(x - width/2, peak_counts, width, label='Peak', 
            color='lightgray', edgecolor='black', linewidth=0.5)
    ax2.bar(x + width/2, current_counts, width, label=f'Current ({latest_year})', 
            color='gray', edgecolor='black', linewidth=0.5)
    
    ax2.set_xticks(x)
    ax2.set_xticklabels(topics, rotation=45, ha='right', fontsize=8)
    ax2.set_xlabel('Research Topic', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Number of Publications', fontsize=10, fontweight='bold')
    ax2.set_title('B) Peak vs Current Publication Counts', fontsize=11, fontweight='bold', pad=10)
    ax2.legend(fontsize=8, frameon=True, edgecolor='black')
    
    # Add trend indicators
    for i, (peak, current) in enumerate(zip(peak_counts, current_counts)):
        if current > peak * 0.9:
            status = "⚡ Active"
        elif current > peak * 0.5:
            status = "📉 Declining"
        else:
            status = "💤 Past peak"
        ax2.text(i, max(peak, current) * 1.05, status, ha='center', fontsize=7)
    
    plt.suptitle('Publication Peak Analysis', fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    return fig

def create_open_access_share_chart(consistent_data: Dict[str, Dict], years: List[int]):
    """
    Create chart showing Open Access share by topic and over time
    """
    # Prepare data by topic
    topic_oa_data = {}
    
    for topic, data in consistent_data.items():
        if data['top_works']:
            oa_count = sum(1 for w in data['top_works'] if enrich_work_data(w).get('is_oa', False))
            oa_share = (oa_count / len(data['top_works'])) * 100
            topic_oa_data[topic] = {
                'share': oa_share,
                'count': oa_count,
                'total': len(data['top_works'])
            }
    
    if not topic_oa_data:
        return None
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Apply scientific style
    for ax in [ax1, ax2]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_linewidth(1.0)
        ax.spines['left'].set_linewidth(1.0)
        ax.tick_params(axis='both', which='major', labelsize=9)
    
    # Plot 1: OA share by topic
    topics = list(topic_oa_data.keys())
    shares = [topic_oa_data[t]['share'] for t in topics]
    counts = [topic_oa_data[t]['count'] for t in topics]
    totals = [topic_oa_data[t]['total'] for t in topics]
    
    # Sort by share
    sorted_data = sorted(zip(topics, shares, counts, totals), key=lambda x: x[1], reverse=True)
    topics = [x[0] for x in sorted_data]
    shares = [x[1] for x in sorted_data]
    counts = [x[2] for x in sorted_data]
    totals = [x[3] for x in sorted_data]
    
    y_pos = np.arange(len(topics))
    bars1 = ax1.barh(y_pos, shares, color='gray', edgecolor='black', linewidth=0.5)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(topics, fontsize=9)
    ax1.set_xlabel('Open Access Share (%)', fontsize=10, fontweight='bold')
    ax1.set_title('A) Open Access Share by Topic', fontsize=11, fontweight='bold', pad=10)
    
    # Add values to bars
    for i, (bar, share, count, total) in enumerate(zip(bars1, shares, counts, totals)):
        ax1.text(share + 2, bar.get_y() + bar.get_height()/2,
                f'{share:.1f}% ({count}/{total})', va='center', fontsize=8)
    
    # Plot 2: OA trend over years (aggregate across all topics)
    # Collect yearly OA data
    yearly_oa = defaultdict(lambda: {'total': 0, 'oa': 0})
    
    for topic, data in consistent_data.items():
        for work in data['top_works']:
            enriched = enrich_work_data(work)
            year = enriched.get('publication_year')
            if year in years:
                yearly_oa[year]['total'] += 1
                if enriched.get('is_oa', False):
                    yearly_oa[year]['oa'] += 1
    
    # Sort years
    sorted_years = sorted([y for y in yearly_oa.keys() if yearly_oa[y]['total'] > 0])
    if not sorted_years:
        ax2.text(0.5, 0.5, 'Insufficient data for trend analysis', 
                ha='center', va='center', transform=ax2.transAxes)
    else:
        oa_shares = [(yearly_oa[y]['oa'] / yearly_oa[y]['total']) * 100 for y in sorted_years]
        total_papers = [yearly_oa[y]['total'] for y in sorted_years]
        
        # Create line chart with markers
        ax2.plot(sorted_years, oa_shares, 'o-', color='gray', linewidth=2, markersize=6,
                markerfacecolor='white', markeredgecolor='black', markeredgewidth=1)
        
        # Add bubble size representing total papers
        for year, share, total in zip(sorted_years, oa_shares, total_papers):
            ax2.annotate(f'n={total}', (year, share), 
                        xytext=(0, 10), textcoords='offset points',
                        ha='center', fontsize=7)
        
        ax2.set_xlabel('Publication Year', fontsize=10, fontweight='bold')
        ax2.set_ylabel('Open Access Share (%)', fontsize=10, fontweight='bold')
        ax2.set_title('B) Open Access Trend Over Time', fontsize=11, fontweight='bold', pad=10)
        ax2.set_xticks(sorted_years)
        ax2.set_xticklabels([str(y) for y in sorted_years], rotation=45, ha='right')
        ax2.grid(True, alpha=0.3, linestyle='--')
    
    plt.suptitle('Open Access Analysis', fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    return fig

def create_scientific_bar_chart(data: Dict[str, int], level2_count: int, title: str):
    """Create scientific bar chart with matplotlib"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Apply scientific style
    for ax in [ax1, ax2]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_linewidth(1.0)
        ax.spines['left'].set_linewidth(1.0)
        ax.tick_params(axis='both', which='major', labelsize=9)
    
    # Filter zero values
    non_zero = {k: v for k, v in data.items() if v > 0}
    if not non_zero:
        return None
    
    topics = list(non_zero.keys())
    counts = list(non_zero.values())
    percentages = [(c / level2_count * 100) if level2_count > 0 else 0 for c in counts]
    
    # Sort descending
    sorted_idx = np.argsort(counts)[::-1]
    topics = [topics[i] for i in sorted_idx]
    counts = [counts[i] for i in sorted_idx]
    percentages = [percentages[i] for i in sorted_idx]
    
    # Grayscale colors for scientific style
    colors1 = plt.cm.Greys(np.linspace(0.3, 0.7, len(topics)))
    colors2 = plt.cm.Greys(np.linspace(0.4, 0.8, len(topics)))
    
    # Count plot
    bars1 = ax1.barh(range(len(topics)), counts, color=colors1, edgecolor='black', linewidth=0.5)
    ax1.set_yticks(range(len(topics)))
    ax1.set_yticklabels(topics, fontsize=9)
    ax1.set_xlabel('Number of Publications', fontsize=10, fontweight='bold')
    ax1.set_title('A) Publication Counts', fontsize=11, fontweight='bold', pad=10)
    
    # Add values to bars
    for i, (bar, count) in enumerate(zip(bars1, counts)):
        ax1.text(count + max(counts)*0.01, bar.get_y() + bar.get_height()/2, 
                f'{count:,}', va='center', fontsize=8)
    
    # Percentage plot
    bars2 = ax2.barh(range(len(topics)), percentages, color=colors2, edgecolor='black', linewidth=0.5)
    ax2.set_yticks(range(len(topics)))
    ax2.set_yticklabels([])  # Remove labels as they're on first plot
    ax2.set_xlabel('Percentage of Total (%)', fontsize=10, fontweight='bold')
    ax2.set_title('B) Percentage Distribution', fontsize=11, fontweight='bold', pad=10)
    
    # Add percentages to bars
    for i, (bar, pct) in enumerate(zip(bars2, percentages)):
        ax2.text(pct + max(percentages)*0.01, bar.get_y() + bar.get_height()/2, 
                f'{pct:.1f}%', va='center', fontsize=8)
    
    plt.suptitle(title, fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    return fig

def create_yearly_distribution_chart(yearly_data: Dict[int, int], title: str):
    """
    Create yearly distribution chart based on provided data
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Apply scientific style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_linewidth(1.0)
    ax.spines['left'].set_linewidth(1.0)
    ax.tick_params(axis='both', which='major', labelsize=9)
    
    # Ensure keys are integers and sort
    years_sorted = sorted([int(y) for y in yearly_data.keys()])
    counts = [yearly_data[y] for y in years_sorted]
    
    # Create bar chart with proper years
    bars = ax.bar(years_sorted, counts, color='gray', edgecolor='black', linewidth=0.5, width=0.8)
    
    # Set integer labels on X axis
    ax.set_xticks(years_sorted)
    ax.set_xticklabels([str(y) for y in years_sorted], rotation=45, ha='right')
    
    ax.set_xlabel('Publication Year', fontsize=10, fontweight='bold')
    ax.set_ylabel('Number of Publications', fontsize=10, fontweight='bold')
    ax.set_title(title, fontsize=11, fontweight='bold', pad=10)
    
    # Add values to bars if not too many
    if len(years_sorted) <= 15:
        for bar in bars:
            height = bar.get_height()
            if height > 0:  # Only show positive values
                ax.text(bar.get_x() + bar.get_width()/2., height + max(counts)*0.01,
                       f'{int(height):,}', ha='center', va='bottom', fontsize=8)
    
    # Add total count
    total = sum(counts)
    ax.text(0.98, 0.98, f'Total: {total:,}', transform=ax.transAxes, 
            ha='right', va='top', fontsize=9, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    return fig

def create_citation_distribution_chart(works_or_stats, title: str, is_stats: bool = False, is_full_distribution: bool = False):
    """
    Create citation distribution chart
    Enhanced to handle both top_works stats and full distribution from group_by
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Apply scientific style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_linewidth(1.0)
    ax.spines['left'].set_linewidth(1.0)
    ax.tick_params(axis='both', which='major', labelsize=9)
    
    if is_full_distribution:
        # For full citation distribution from group_by
        dist = works_or_stats  # This is the citation_distribution dict
        categories = list(dist.keys())
        counts = list(dist.values())
        total = sum(counts)
        
        # Calculate percentages
        percentages = [(c / total * 100) if total > 0 else 0 for c in counts]
        
        # Create bar chart
        bars = ax.bar(categories, counts, color='gray', edgecolor='black', linewidth=0.5)
        ax.set_xlabel('Citation Categories', fontsize=10, fontweight='bold')
        ax.set_ylabel('Number of Papers', fontsize=10, fontweight='bold')
        
        # Add values and percentages on bars
        for bar, count, pct in zip(bars, counts, percentages):
            if count > 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                       f'{count:,}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=7)
        
        # Add total
        ax.text(0.98, 0.98, f'Total: {total:,} papers', transform=ax.transAxes,
                ha='right', va='top', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
    elif is_stats:
        # For citation stats from top_works (backward compatibility)
        dist = works_or_stats.get('distribution', {})
        categories = list(dist.keys())
        counts = list(dist.values())
        
        bars = ax.bar(categories, counts, color='gray', edgecolor='black', linewidth=0.5)
        ax.set_xlabel('Citation Categories', fontsize=10, fontweight='bold')
        ax.set_ylabel('Number of Papers', fontsize=10, fontweight='bold')
        
        # Add values on bars
        for bar, count in zip(bars, counts):
            if count > 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                       f'{count:,}', ha='center', va='bottom', fontsize=8)
        
        # Add note about sample
        total = sum(counts)
        ax.text(0.98, 0.98, f'Sample: {total} papers', transform=ax.transAxes,
                ha='right', va='top', fontsize=8, fontstyle='italic',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
    else:
        # For raw works list
        citations = [w.get('cited_by_count', 0) for w in works_or_stats]
        if not citations:
            return None
        
        # Create histogram
        n, bins, patches = ax.hist(citations, bins=20, color='gray', 
                                   edgecolor='black', linewidth=0.5, alpha=0.7)
        
        ax.set_xlabel('Number of Citations', fontsize=10, fontweight='bold')
        ax.set_ylabel('Number of Papers', fontsize=10, fontweight='bold')
        
        # Add statistics
        mean_cit = np.mean(citations)
        median_cit = np.median(citations)
        ax.axvline(mean_cit, color='black', linestyle='--', linewidth=1, 
                  label=f'Mean: {mean_cit:.1f}')
        ax.axvline(median_cit, color='gray', linestyle=':', linewidth=1, 
                  label=f'Median: {median_cit:.1f}')
        ax.legend(fontsize=8, frameon=True, edgecolor='black')
        
        # Add sample size
        ax.text(0.98, 0.98, f'Sample: {len(citations)} papers', transform=ax.transAxes,
                ha='right', va='top', fontsize=8, fontstyle='italic',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.set_title(title, fontsize=11, fontweight='bold', pad=10)
    plt.tight_layout()
    return fig

def create_combined_yearly_charts(consistent_data: Dict[str, Dict], 
                                 years_input: List[int], 
                                 level2_term: Optional[str] = None):
    """
    Create combined chart with yearly distributions for all sub-topics
    Uses CONSISTENT data from group_by
    """
    # Create figure with three subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Apply scientific style
    for ax in axes:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_linewidth(1.0)
        ax.spines['left'].set_linewidth(1.0)
        ax.tick_params(axis='both', which='major', labelsize=9)
    
    # Determine all available years - sort and convert to integers
    years = sorted([int(y) for y in set(years_input)])
    topics = [t for t, data in consistent_data.items() if data['total'] > 0]
    
    if not topics or not years:
        plt.close(fig)
        return None
    
    # Subplot 1: Stacked
    ax = axes[0]
    bottom = np.zeros(len(years))
    
    # Use grayscale for scientific style
    gray_colors = plt.cm.Greys(np.linspace(0.3, 0.7, len(topics)))
    
    # Create list to store yearly totals for validation
    yearly_totals = np.zeros(len(years))
    
    for idx, topic in enumerate(topics):
        # Get REAL data from consistent_data
        topic_yearly = consistent_data[topic]['yearly']
        counts = [topic_yearly.get(year, 0) for year in years]
        
        ax.bar(years, counts, bottom=bottom, label=topic, 
               color=gray_colors[idx], edgecolor='black', linewidth=0.5, width=0.8)
        bottom += counts
        yearly_totals += counts
    
    # Set integer labels on X axis
    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years], rotation=45, ha='right')
    
    ax.set_xlabel('Publication Year', fontsize=10, fontweight='bold')
    ax.set_ylabel('Number of Publications', fontsize=10, fontweight='bold')
    ax.set_title('A) Stacked Yearly Distribution', fontsize=11, fontweight='bold', pad=10)
    ax.legend(fontsize=8, frameon=True, edgecolor='black')
    
    # Add total count above plot
    total_papers = int(sum(yearly_totals))
    ax.text(0.5, 0.98, f'Total: {total_papers:,} papers', 
            transform=ax.transAxes, ha='center', va='top', 
            fontsize=9, fontweight='bold', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Subplot 2: Normalized (by maximum of each topic)
    ax = axes[1]
    
    for idx, topic in enumerate(topics):
        topic_yearly = consistent_data[topic]['yearly']
        counts = np.array([topic_yearly.get(year, 0) for year in years])
        if counts.max() > 0:
            normalized = counts / counts.max()
            ax.plot(years, normalized, marker='o', linewidth=1.5, markersize=4, 
                   label=topic, color=gray_colors[idx])
    
    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years], rotation=45, ha='right')
    
    ax.set_xlabel('Publication Year', fontsize=10, fontweight='bold')
    ax.set_ylabel('Normalized Intensity (max=1)', fontsize=10, fontweight='bold')
    ax.set_title('B) Normalized by Maximum', fontsize=11, fontweight='bold', pad=10)
    ax.set_ylim(0, 1.1)
    ax.legend(fontsize=8, frameon=True, edgecolor='black')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Subplot 3: Logarithmic scale (absolute values)
    ax = axes[2]
    
    # Find global maximum for Y axis tuning
    all_counts = []
    for topic in topics:
        topic_yearly = consistent_data[topic]['yearly']
        counts = [topic_yearly.get(year, 0) for year in years]
        all_counts.extend(counts)
    max_count = max(all_counts) if all_counts else 1
    
    for idx, topic in enumerate(topics):
        topic_yearly = consistent_data[topic]['yearly']
        counts = [topic_yearly.get(year, 0) for year in years]
        if max(counts) > 0:
            # For log scale, replace 0 with 0.1 (below minimum)
            counts_log = [c if c > 0 else 0.1 for c in counts]
            ax.semilogy(years, counts_log, marker='s', linewidth=1.5, markersize=4, 
                       label=topic, color=gray_colors[idx])
    
    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years], rotation=45, ha='right')
    
    ax.set_xlabel('Publication Year', fontsize=10, fontweight='bold')
    ax.set_ylabel('Number of Publications (log scale)', fontsize=10, fontweight='bold')
    ax.set_title('C) Logarithmic Scale (absolute values)', fontsize=11, fontweight='bold', pad=10)
    
    # Configure logarithmic Y scale
    y_min = 0.5
    y_max = max_count * 2
    ax.set_ylim(y_min, y_max)
    
    # Add grid lines for log scale
    ax.grid(True, alpha=0.3, linestyle='--', which='both')
    ax.legend(fontsize=8, frameon=True, edgecolor='black', loc='best')
    
    plt.suptitle(f'Comparative Yearly Distribution Analysis' + (f' (with {level2_term})' if level2_term else ''), 
                 fontsize=12, fontweight='bold', y=1.05)
    plt.tight_layout()
    
    return fig

def create_scientific_tree_visualization(topic_counts: Dict[str, int], level1_term: str, level2_term: Optional[str] = None):
    """
    Create scientific tree visualization
    """
    topics = [t for t, count in topic_counts.items() if count > 0]
    if not topics:
        return None
    
    # Sort topics descending
    topics_sorted = sorted(topics, key=lambda x: topic_counts[x], reverse=True)
    counts = [topic_counts[t] for t in topics_sorted]
    max_count = max(counts) if counts else 1
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Apply scientific style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='both', which='both', bottom=False, top=False, left=False, right=False,
                  labelbottom=False, labelleft=False)
    
    # Node positions
    n_topics = len(topics_sorted)
    
    # Root node
    root_x, root_y = 0.5, 0.9
    
    # Leaf positions (distribute along an arc)
    leaf_x = []
    leaf_y = []
    
    if n_topics == 1:
        leaf_x = [0.5]
        leaf_y = [0.3]
    else:
        # Distribute along arc
        angles = np.linspace(np.pi/4, 3*np.pi/4, n_topics)
        leaf_x = 0.5 + 0.35 * np.cos(angles)
        leaf_y = 0.3 + 0.15 * np.sin(angles)
    
    # Draw connections (branches)
    for i in range(n_topics):
        # Line thickness proportional to publication count
        line_width = 1 + 3 * (counts[i] / max_count)
        
        # Draw branch with slight curve
        x_vals = [root_x, root_x - 0.1 + 0.2 * i / n_topics, leaf_x[i]]
        y_vals = [root_y, root_y - 0.3, leaf_y[i]]
        
        ax.plot(x_vals, y_vals, 'k-', linewidth=line_width, alpha=0.7, solid_capstyle='round')
    
    # Draw root node
    root_size = 300 + 100 * (sum(counts) / max_count) if max_count > 0 else 300
    ax.scatter([root_x], [root_y], s=root_size, c='white', edgecolor='black', 
               linewidth=1.5, zorder=10)
    
    # Add root node text
    root_label = f"{level1_term}"
    if level2_term:
        root_label += f"\n+ {level2_term}"
    ax.annotate(root_label, (root_x, root_y), ha='center', va='center', 
                fontsize=10, fontweight='bold', zorder=11)
    
    # Draw leaf nodes
    for i in range(n_topics):
        # Node size proportional to publication count
        node_size = 200 + 300 * (counts[i] / max_count)
        
        ax.scatter([leaf_x[i]], [leaf_y[i]], s=node_size, c='white', edgecolor='black', 
                   linewidth=1.0, zorder=10)
        
        # Add label
        ax.annotate(f"{topics_sorted[i]}\n({counts[i]:,})", 
                   (leaf_x[i], leaf_y[i]), ha='center', va='center', 
                   fontsize=8, zorder=11)
    
    # Add title
    ax.set_title('Hierarchical Topic Structure\nBranch thickness proportional to publication count', 
                fontsize=12, fontweight='bold', pad=20)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    
    return fig

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_to_csv(works_by_topic: Dict[str, List[Dict]]) -> bytes:
    """Export results to CSV"""
    all_rows = []
    for topic, works in works_by_topic.items():
        for work in works:
            enriched = enrich_work_data(work)
            enriched['sub_topic'] = topic
            all_rows.append(enriched)
    
    df = pd.DataFrame(all_rows)
    return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

def export_to_excel(works_by_topic: Dict[str, List[Dict]]) -> bytes:
    """Export results to Excel with papers sorted from newest to oldest"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Main sheet - собираем все статьи
        all_rows = []
        for topic, works in works_by_topic.items():
            for work in works:
                enriched = enrich_work_data(work)
                enriched['sub_topic'] = topic
                all_rows.append(enriched)
        
        if all_rows:
            df_all = pd.DataFrame(all_rows)
            
            # СОРТИРОВКА: от новых к старым
            # Сначала по году (убывание), затем по дате (убывание)
            df_all = df_all.sort_values(
                by=['publication_year', 'publication_date'], 
                ascending=[False, False]  # False = descending (новые сверху)
            )
            
            df_all.to_excel(writer, sheet_name='All Papers', index=False)
        
        # Separate sheets for each sub-topic (тоже с сортировкой)
        for topic, works in works_by_topic.items():
            if works:
                # Собираем данные для конкретной темы
                topic_rows = []
                for work in works:
                    enriched = enrich_work_data(work)
                    topic_rows.append(enriched)
                
                df_topic = pd.DataFrame(topic_rows)
                
                # СОРТИРОВКА для каждой темы
                df_topic = df_topic.sort_values(
                    by=['publication_year', 'publication_date'], 
                    ascending=[False, False]
                )
                
                sheet_name = re.sub(r'[^\w\s-]', '', topic)[:31]
                df_topic.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Formatting (оставляем как есть)
        workbook = writer.book
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': st.session_state['color_palette']['primary'],
            'font_color': 'white',
            'border': 1
        })
        
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            if sheet_name == 'All Papers':
                df = df_all
            else:
                # Находим соответствующий DataFrame для текущего листа
                df = None
                for t, works in works_by_topic.items():
                    if re.sub(r'[^\w\s-]', '', t)[:31] == sheet_name:
                        # Создаем DataFrame с сортировкой
                        temp_rows = []
                        for work in works:
                            temp_rows.append(enrich_work_data(work))
                        df = pd.DataFrame(temp_rows)
                        df = df.sort_values(
                            by=['publication_year', 'publication_date'], 
                            ascending=[False, False]
                        )
                        break
            
            if df is not None:
                for col_num, col_name in enumerate(df.columns):
                    worksheet.write(0, col_num, col_name, header_format)
                    max_len = max(
                        df[col_name].astype(str).map(len).max() if not df[col_name].empty else 0,
                        len(str(col_name))
                    ) + 2
                    worksheet.set_column(col_num, col_num, min(max_len, 50))
    
    return output.getvalue()

def generate_pdf_report(works_by_topic: Dict[str, List[Dict]], level1_term: str, level2_term: Optional[str] = None, years: Optional[List[int]] = None) -> Optional[bytes]:
    """Generate PDF report with analysis results"""
    if not PDF_AVAILABLE:
        return None
    
    buffer = io.BytesIO()
    
    # Document setup
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm
    )
    
    styles = getSampleStyleSheet()
    
    # ========== CREATE CUSTOM STYLES ==========
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=reportlab_colors.HexColor('#2C3E50'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=reportlab_colors.HexColor('#34495E'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    topic_style = ParagraphStyle(
        'CustomTopic',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=reportlab_colors.HexColor('#16A085'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    meta_style = ParagraphStyle(
        'CustomMeta',
        parent=styles['Normal'],
        fontSize=10,
        textColor=reportlab_colors.HexColor('#7F8C8D'),
        spaceAfter=3,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    paper_title_style = ParagraphStyle(
        'CustomPaperTitle',
        parent=styles['Heading4'],
        fontSize=11,
        textColor=reportlab_colors.HexColor('#2980B9'),
        spaceAfter=4,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    authors_style = ParagraphStyle(
        'CustomAuthors',
        parent=styles['Normal'],
        fontSize=9,
        textColor=reportlab_colors.HexColor('#2C3E50'),
        spaceAfter=2,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    details_style = ParagraphStyle(
        'CustomDetails',
        parent=styles['Normal'],
        fontSize=8,
        textColor=reportlab_colors.HexColor('#7F8C8D'),
        spaceAfter=2,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    metrics_style = ParagraphStyle(
        'CustomMetrics',
        parent=styles['Normal'],
        fontSize=9,
        textColor=reportlab_colors.HexColor('#27AE60'),
        spaceAfter=0,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    footer_style = ParagraphStyle(
        'CustomFooter',
        parent=styles['Normal'],
        fontSize=8,
        textColor=reportlab_colors.HexColor('#95A5A6'),
        spaceBefore=15,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    separator_style = ParagraphStyle(
        'CustomSeparator',
        parent=styles['Normal'],
        fontSize=8,
        textColor=reportlab_colors.HexColor('#BDC3C7'),
        spaceAfter=10,
        spaceBefore=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    story = []
    
    # ========== TITLE PAGE ==========
    
    story.append(Spacer(1, 1*cm))
    
    # Title
    story.append(Paragraph("Publication Clustering Report", title_style))
    story.append(Paragraph("Multi-level Literature Analysis", subtitle_style))
    story.append(Spacer(1, 0.8*cm))
    
    # Query information
    topic_name = level1_term
    if level2_term:
        topic_name += f" + {level2_term}"
    story.append(Paragraph(f"RESEARCH TOPIC:", topic_style))
    story.append(Paragraph(topic_name, subtitle_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Meta information
    current_date = datetime.now().strftime('%B %d, %Y at %H:%M')
    story.append(Paragraph(f"Generated on {current_date}", meta_style))
    
    total_papers = sum(len(works) for works in works_by_topic.values())
    story.append(Paragraph(f"Total papers analyzed: {total_papers:,}", meta_style))
    
    if years:
        year_range = f"{min(years)}-{max(years)}"
        story.append(Paragraph(f"Publication years: {year_range}", meta_style))
    
    story.append(Spacer(1, 1.5*cm))
    
    # Copyright
    story.append(Paragraph("© Publication Clustering Tool", footer_style))
    story.append(Paragraph("Powered by OpenAlex API", footer_style))
    
    # Page break
    story.append(PageBreak())
    
    # ========== TABLE OF CONTENTS ==========
    
    story.append(Paragraph("TABLE OF CONTENTS", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    toc_items = [
        "1. Topic Distribution Summary",
        "2. Detailed Paper Analysis",
        "3. Statistical Summary"
    ]
    
    for item in toc_items:
        story.append(Paragraph(item, details_style))
    
    story.append(PageBreak())
    
    # ========== TOPIC DISTRIBUTION ==========
    
    story.append(Paragraph("1. TOPIC DISTRIBUTION SUMMARY", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Topic distribution table
    topic_data = [["Topic", "Papers Found", "Percentage"]]
    total_all = sum(len(works) for works in works_by_topic.values())
    
    for topic, works in works_by_topic.items():
        if works:
            count = len(works)
            percentage = (count / total_all * 100) if total_all > 0 else 0
            topic_data.append([topic, f"{count:,}", f"{percentage:.1f}%"])
    
    if len(topic_data) > 1:
        topic_table = Table(topic_data, colWidths=[doc.width/2, doc.width/4, doc.width/4])
        topic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), reportlab_colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), reportlab_colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), reportlab_colors.HexColor('#F8F9FA')),
            ('GRID', (0, 0), (-1, -1), 0.5, reportlab_colors.HexColor('#D5DBDB')),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(topic_table)
    
    story.append(PageBreak())
    
    # ========== DETAILED ANALYSIS ==========
    
    story.append(Paragraph("2. DETAILED PAPER ANALYSIS", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    for topic, works in works_by_topic.items():
        if works:
            story.append(Paragraph(f"Topic: {topic}", topic_style))
            story.append(Spacer(1, 0.3*cm))
            
            for i, work in enumerate(works, 1):  # Show ALL papers, not just 20
                enriched = enrich_work_data(work)
                
                # Title
                title = clean_text(enriched.get('title', 'No title'))
                story.append(Paragraph(f"{i}. {title}", paper_title_style))
                
                # Authors
                authors = enriched.get('authors', [])
                if authors:
                    authors_text = ', '.join(authors[:3])
                    if len(authors) > 3:
                        authors_text += f' et al. ({len(authors)} authors)'
                    story.append(Paragraph(f"Authors: {authors_text}", authors_style))
                
                # Metrics
                metrics = f"Citations: {enriched.get('cited_by_count', 0):,} | Year: {enriched.get('publication_year', 'N/A')} | OA: {'Yes' if enriched.get('is_oa') else 'No'}"
                story.append(Paragraph(metrics, metrics_style))
                
                # DOI
                doi = enriched.get('doi', '')
                if doi:
                    # Format DOI URL
                    if doi.startswith('10.'):
                        doi_url = f"https://doi.org/{doi}"
                    elif doi.startswith('https://doi.org/'):
                        doi_url = doi
                    else:
                        doi_url = f"https://doi.org/{doi}"
                    
                    # Create clickable link
                    doi_link = f'<link href="{doi_url}"><font color="blue"><u>{doi}</u></font></link>'
                    story.append(Paragraph(f"DOI: {doi_link}", details_style))
                
                # Separator
                story.append(Spacer(1, 0.2*cm))
                story.append(Paragraph("─" * 30, separator_style))
                story.append(Spacer(1, 0.2*cm))
            
            story.append(PageBreak())
    
    # ========== STATISTICAL SUMMARY ==========
    
    story.append(Paragraph("3. STATISTICAL SUMMARY", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Collect statistics
    all_citations = []
    all_years = []
    all_scores = []
    
    for works in works_by_topic.values():
        for work in works:
            enriched = enrich_work_data(work)
            all_citations.append(enriched.get('cited_by_count', 0))
            if enriched.get('publication_year'):
                all_years.append(enriched.get('publication_year'))
            all_scores.append(enriched.get('relevance_score', 0))
    
    if all_citations:
        stats_data = [
            ["Metric", "Value"],
            ["Total Papers", f"{len(all_citations):,}"],
            ["Average Citations", f"{np.mean(all_citations):.2f}"],
            ["Median Citations", f"{np.median(all_citations):.2f}"],
            ["Max Citations", f"{max(all_citations):,}"],
            ["Papers with 0 citations", f"{sum(1 for c in all_citations if c == 0):,}"],
            ["Open Access Papers", f"{sum(1 for w in works_by_topic.values() for work in w if enrich_work_data(work).get('is_oa')):,}"],
            ["Average Relevance Score", f"{np.mean(all_scores):.2f}"],
        ]
        
        if all_years:
            stats_data.append(["Earliest Year", min(all_years)])
            stats_data.append(["Latest Year", max(all_years)])
        
        stats_table = Table(stats_data, colWidths=[doc.width/2, doc.width/3])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), reportlab_colors.HexColor('#27AE60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), reportlab_colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), reportlab_colors.HexColor('#F8F9FA')),
            ('GRID', (0, 0), (-1, -1), 0.5, reportlab_colors.HexColor('#D5DBDB')),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(stats_table)
    
    # ========== CONCLUSION ==========
    
    story.append(PageBreak())
    story.append(Paragraph("CONCLUSION", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    conclusions = [
        f"This report analyzed {total_papers:,} papers across {len([t for t, w in works_by_topic.items() if w])} topics.",
        "The analysis provides insights into the distribution and impact of research in these areas.",
        "Papers with low citation counts may represent emerging research directions.",
        "For the most current data, please visit the original sources via the provided DOIs."
    ]
    
    for conclusion in conclusions:
        story.append(Paragraph(f"• {conclusion}", details_style))
    
    # Footer
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("© Publication Clustering Tool - Generated Automatically", footer_style))
    story.append(Paragraph(f"Report ID: {hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}", footer_style))
    
    # ========== GENERATE PDF ==========
    
    doc.build(story)
    return buffer.getvalue()

# ============================================================================
# MAIN INTERFACE
# ============================================================================

def main():
    """Main application function"""
    
    # Header
    st.markdown(f'<h1 class="main-header">Publication Clustering</h1>', unsafe_allow_html=True)
    st.markdown(f"""
    <p style="font-size: 1rem; color: {colors['text']}; margin-bottom: 1.5rem;">
    Multi-level literature search with topic clustering and network visualization
    </p>
    """, unsafe_allow_html=True)
    
    # Display current theme info
    st.markdown(f"""
    <div style="text-align: right; font-size: 0.8rem; color: {colors['primary']}; margin-bottom: 0.5rem;">
        Theme: {colors['name']}
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'step' not in st.session_state:
        st.session_state['step'] = 1
    if 'results' not in st.session_state:
        st.session_state['results'] = {}
    if 'topic_counts' not in st.session_state:
        st.session_state['topic_counts'] = {}
    if 'level1_count' not in st.session_state:
        st.session_state['level1_count'] = 0
    if 'level2_count' not in st.session_state:
        st.session_state['level2_count'] = 0
    if 'level1_input' not in st.session_state:
        st.session_state['level1_input'] = '"metal-organic frameworks" OR MOF'
    if 'level2_input' not in st.session_state:
        st.session_state['level2_input'] = ''
    if 'level3_input' not in st.session_state:
        st.session_state['level3_input'] = ['MIL', 'ZIF', 'IRMOF', 'UiO', 'HKUST']
    if 'years_input' not in st.session_state:
        st.session_state['years_input'] = list(range(2000, 2026))
    if 'consistent_data' not in st.session_state:
        st.session_state['consistent_data'] = {}
    
    # ========================================================================
    # STEP 1: TERM INPUT
    # ========================================================================
    
    if st.session_state.step == 1:
        st.markdown(f"""
        <div class="step-card">
            <h3 style="margin: 0; font-size: 1.3rem;">📥 Step 1: Enter Search Terms</h3>
            <p style="margin: 5px 0; font-size: 0.9rem;">Define your multi-level search query</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced instructions
        st.markdown(f"""
        <div class="info-message">
            <strong>📚 How the multi-level search works:</strong><br><br>
            • <b>Level 1 (Main domain)</b> - broad research area that defines the overall scope<br>
            • <b>Level 2 (Optional refinement)</b> - narrows down the search within Level 1<br>
            • <b>Level 3 terms (Classification topics)</b> - these are the specific sub-topics that will be used for <b>clustering and classification</b>. 
            The system will count papers matching each Level 3 term within the context of Level 1+2, and then fetch the most relevant papers for detailed analysis.
            <br><br>
            <i>Example: If Level 1 is "metal-organic frameworks" and Level 3 terms are "MIL", "ZIF", "UiO" - 
            the system will create separate clusters for each MOF family and analyze their publication patterns.</i>
        </div>
        
        <div class="info-message" style="margin-top: 10px;">
            <strong>💡 Search Syntax Tips:</strong><br>
            • Use <b>OR</b> for logical OR (e.g., "MOF OR COF")<br>
            • Use quotes for exact phrases (e.g., "metal-organic frameworks")<br>
            • Use <b>*</b> for wildcard (e.g., "electroly*" matches electrolyte, electrolysis, electrolyzer)<br>
            • Multiple words without OR are treated as a phrase automatically
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Level 1 (required):**")
            level1 = st.text_input(
                "Main domain (broad research area)",
                value=st.session_state['level1_input'],
                key="level1_input_widget",
                label_visibility="collapsed",
                placeholder="e.g., \"machine learning\" OR \"artificial intelligence\""
            )
            
            st.markdown("**Level 2 (optional):**")
            level2 = st.text_input(
                "Refinement term (narrows down Level 1)",
                value=st.session_state['level2_input'] if st.session_state['level2_input'] else '',
                key="level2_input_widget",
                label_visibility="collapsed",
                placeholder="e.g., \"neural networks\" OR deep learning"
            )
        
        with col2:
            st.markdown("**Level 3 terms (one per line - these will become your clusters):**")
            level3_text = st.text_area(
                "Sub-topics for classification",
                value='\n'.join(st.session_state['level3_input']),
                height=120,
                key="level3_input_widget",
                label_visibility="collapsed",
                placeholder="Enter each sub-topic on a new line"
            )
        
        # Year filter
        st.markdown("---")
        st.markdown("**📅 Publication Years:**")
        
        current_year = datetime.now().year
        
        # Change order: Range first
        year_option = st.radio(
            "Year filter type",
            ["Range", "Single year", "Multiple years"],
            horizontal=True,
            key="year_type",
            index=0  # Range by default
        )
        
        if year_option == "Single year":
            years = [st.slider("Select year", 2000, current_year, current_year)]
        elif year_option == "Range":
            default_range = (2000, current_year)
            year_range = st.slider("Select range", 2000, current_year, default_range)
            years = list(range(year_range[0], year_range[1] + 1))
        else:  # Multiple years
            default_years = [current_year-2, current_year-1, current_year]
            years = st.multiselect(
                "Select years",
                list(range(current_year, 2000-1, -1)),
                default=default_years
            )
        
        # Test query
        with st.expander("🔧 Test Query Before Full Analysis"):
            if st.button("Test Current Query"):
                with st.spinner("Testing query..."):
                    # FIXED: Added proper None checking for level2
                    level2_for_test = level2.strip() if level2 and level2.strip() else None
                    temp_count = get_total_count(level1.strip(), level2_for_test, years)
                    
                    if temp_count > 0:
                        st.success(f"✅ Found {temp_count:,} papers matching your Level 1+2 criteria")
                        
                        # Additional information
                        parsed_level2 = parse_query_terms(level2.strip()) if level2 and level2.strip() else '(not specified)'
                        st.markdown(f"""
                        <div class="info-message">
                            <strong>Query Analysis:</strong><br>
                            • Parsed Level 1: {parse_query_terms(level1.strip())}<br>
                            • Parsed Level 2: {parsed_level2}<br>
                            • Years: {min(years)}-{max(years)}<br>
                            • Total papers: {temp_count:,}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("""
                        ❌ No results found! Try:
                        - Using fewer or more general terms
                        - Checking your spelling
                        - Expanding the year range
                        - Using quotes for exact phrases
                        - Using wildcard (*) for word variations
                        """)
        
        # Start button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔍 Start Analysis", type="primary", use_container_width=True):
                if not level1 or not level1.strip():
                    st.error("❌ Please enter Level 1 term")
                elif not level3_text or not level3_text.strip():
                    st.error("❌ Please enter at least one Level 3 term")
                else:
                    # Save to session with proper None handling
                    st.session_state['level1_input'] = level1.strip()
                    st.session_state['level2_input'] = level2.strip() if level2 and level2.strip() else None
                    st.session_state['level3_input'] = [t.strip() for t in level3_text.split('\n') if t.strip()]
                    st.session_state['years_input'] = years
                    st.session_state['step'] = 2
                    st.rerun()
    
    # ========================================================================
    # STEP 2: ANALYSIS
    # ========================================================================
    
    elif st.session_state.step == 2:
        st.markdown(f"""
        <div class="step-card">
            <h3 style="margin: 0; font-size: 1.3rem;">🔍 Step 2: Analysis in Progress</h3>
            <p style="margin: 5px 0; font-size: 0.9rem;">Fetching data from OpenAlex...</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show query parameters
        st.markdown(f"""
        <div class="filter-stats">
            <strong>Query Parameters:</strong><br>
            Level 1: {st.session_state.level1_input}<br>
            Level 2: {st.session_state.level2_input or '(not specified)'}<br>
            Level 3: {', '.join(st.session_state.level3_input)}<br>
            Years: {min(st.session_state.years_input)}-{max(st.session_state.years_input)}
        </div>
        """, unsafe_allow_html=True)
        
        # Back button
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("← Back to Step 1", key="back_from_step2"):
                st.session_state.step = 1
                st.rerun()
        
        # Progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(value, message):
            progress_bar.progress(value)
            status_text.text(message)
        
        try:
            # Step 1: Level 1 count
            update_progress(0.1, "Getting Level 1 count...")
            st.session_state['level1_count'] = get_total_count(
                st.session_state['level1_input'], None, st.session_state['years_input']
            )
            
            # Step 2: Level 2 count (if applicable)
            if st.session_state['level2_input']:
                update_progress(0.2, "Getting Level 2 count...")
                st.session_state['level2_count'] = get_total_count(
                    st.session_state['level1_input'], st.session_state['level2_input'], st.session_state['years_input']
                )
            else:
                st.session_state['level2_count'] = st.session_state['level1_count']
            
            # Step 3: Get CONSISTENT data using hybrid approach with enhanced citation distribution
            update_progress(0.3, "Analyzing Level 3 terms with group_by...")
            st.session_state['consistent_data'] = get_consistent_topic_data(
                st.session_state['level1_input'],
                st.session_state['level2_input'],
                st.session_state['level3_input'],
                st.session_state['years_input'],
                max_papers_to_fetch=100,
                progress_callback=lambda p, m: update_progress(0.3 + p*0.6, m)
            )
            
            # Step 4: Extract topic_counts and results from consistent_data for backward compatibility
            st.session_state['topic_counts'] = {
                term: data['total'] 
                for term, data in st.session_state['consistent_data'].items()
            }
            
            st.session_state['results'] = {
                term: data['top_works'] 
                for term, data in st.session_state['consistent_data'].items()
            }
            
            update_progress(1.0, "✅ Analysis complete!")
            time.sleep(0.5)
            
            st.session_state['step'] = 3
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error during analysis: {str(e)}")
            if st.button("← Back to Step 1"):
                st.session_state['step'] = 1
                st.rerun()
    
    # ========================================================================
    # STEP 3: RESULTS
    # ========================================================================
    
    elif st.session_state.step == 3:
        st.markdown(f"""
        <div class="step-card">
            <h3 style="margin: 0; font-size: 1.3rem;">📊 Step 3: Results</h3>
            <p style="margin: 5px 0; font-size: 0.9rem;">Analysis complete - review the findings</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Use consistent_data for all visualizations
        consistent_data = st.session_state.get('consistent_data', {})
        
        # Navigation buttons
        nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 2])
        
        with nav_col1:
            if st.button("← Back to Step 1", key="back_from_step3"):
                st.session_state.step = 1
                st.rerun()
        
        with nav_col2:
            if st.button("🔄 New Search", key="new_from_step3"):
                # Clear session but keep terms for Step 1
                level1 = st.session_state.get('level1_input', '')
                level2 = st.session_state.get('level2_input', '')
                level3 = st.session_state.get('level3_input', [])
                years = st.session_state.get('years_input', [])
                
                for key in ['step', 'results', 'topic_counts', 'level1_count', 'level2_count', 'consistent_data']:
                    if key in st.session_state:
                        del st.session_state[key]
                
                st.session_state.step = 1
                st.session_state['level1_input'] = level1
                st.session_state['level2_input'] = level2
                st.session_state['level3_input'] = level3
                st.session_state['years_input'] = years
                st.rerun()
        
        # Show data consistency info
        st.markdown(f"""
        <div class="info-message">
            <strong>✅ Data Consistency Note:</strong><br>
            All charts use the SAME source data from group_by queries.<br>
            • Topic totals are calculated from yearly distributions<br>
            • Yearly distributions sum exactly to topic totals<br>
            • Citation distributions are now calculated for ALL papers using group_by (4 requests per topic)<br>
            • Additional analytics (Gini, CAGR, peak year, OA share) are calculated from the available data
        </div>
        """, unsafe_allow_html=True)
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            create_metric_card("Level 1 Papers", st.session_state.level1_count, "📄")
        
        with col2:
            create_metric_card("After Level 2", st.session_state.level2_count, "🔍")
        
        with col3:
            total_found = sum(len(works) for works in st.session_state.results.values())
            create_metric_card("Top Papers Found", total_found, "🎯")
        
        with col4:
            topics_with_results = sum(1 for data in consistent_data.values() if data['total'] > 0)
            create_metric_card("Topics with results", topics_with_results, "✅")
        
        st.markdown("---")
        
        # Topic distribution info
        st.markdown(f"""
        <div class="info-message">
            <strong>📊 Topic Distribution Analysis:</strong><br>
            Total papers matching Level 1+2 filters: {st.session_state.level2_count:,}<br>
            Sum of papers in all sub-topics: {sum(st.session_state.topic_counts.values()):,}<br>
            <i>Note: Papers containing multiple sub-topic keywords are counted in each category, 
            so the sum may exceed the total.</i>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs for different views - ENHANCED WITH NEW ANALYTICS
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Topic Distribution", 
            "🌳 Cluster Graph", 
            "📊 Advanced Analytics",
            "📋 Papers by Topic", 
            "📥 Export"
        ])
        
        with tab1:
            # Topic distribution chart
            if st.session_state.topic_counts:
                st.markdown('<div class="scientific-plot">', unsafe_allow_html=True)
                st.markdown("<h4>Sub-topic Distribution</h4>", unsafe_allow_html=True)
                
                fig = create_scientific_bar_chart(
                    st.session_state.topic_counts,
                    st.session_state.level2_count,
                    f"Publications by Sub-topic ({min(st.session_state.years_input)}-{max(st.session_state.years_input)})"
                )
                if fig:
                    st.pyplot(fig)
                    plt.close(fig)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Combined yearly charts using CONSISTENT data
            if consistent_data:
                st.markdown('<div class="scientific-plot">', unsafe_allow_html=True)
                st.markdown("<h4>Comparative Yearly Distribution Analysis</h4>", unsafe_allow_html=True)
                
                fig_combined = create_combined_yearly_charts(
                    consistent_data,
                    st.session_state.years_input,
                    st.session_state.level2_input
                )
                if fig_combined:
                    st.pyplot(fig_combined)
                    plt.close(fig_combined)
                
                st.markdown("""
                <div class="info-message">
                    <strong>📌 Interpretation:</strong><br>
                    • <b>Stacked chart</b> shows absolute contributions over time<br>
                    • <b>Normalized chart</b> reveals relative trends (each topic normalized to its maximum)<br>
                    • <b>Log scale</b> shows absolute values on logarithmic scale - enabling comparison of vastly different scales
                </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Individual topic charts using CONSISTENT data with enhanced citation distribution
            for term, data in consistent_data.items():
                total_count = data['total']
                yearly_data = data['yearly']
                citation_distribution = data.get('citation_distribution', {})  # NEW: full distribution
                top_works = data['top_works']
                citation_stats = data['citation_stats']
                
                if total_count > 0:
                    st.markdown(f'<div class="scientific-plot">', unsafe_allow_html=True)
                    st.markdown(f"<h4>Analysis for: {term} (showing distribution of all {total_count:,} papers)</h4>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig1 = create_yearly_distribution_chart(yearly_data, f"{term}: Publications by Year (all papers)")
                        if fig1:
                            st.pyplot(fig1)
                            plt.close(fig1)
                    
                    with col2:
                        # NEW: Use full citation distribution from group_by
                        if citation_distribution:
                            fig2 = create_citation_distribution_chart(
                                citation_distribution, 
                                f"{term}: Citation Distribution (ALL {total_count:,} papers)", 
                                is_full_distribution=True
                            )
                            if fig2:
                                st.pyplot(fig2)
                                plt.close(fig2)
                        elif citation_stats:
                            # Fallback to top_works stats
                            fig2 = create_citation_distribution_chart(
                                citation_stats, 
                                f"{term}: Citation Distribution (based on top {len(top_works)} papers)", 
                                is_stats=True
                            )
                            if fig2:
                                st.pyplot(fig2)
                                plt.close(fig2)
                        else:
                            st.info(f"No citation data available for {term}")
                    
                    # Display Gini coefficient if available
                    if citation_stats and 'gini' in citation_stats:
                        gini = citation_stats['gini']
                        st.markdown(f"""
                        <div style="background: #f0f0f0; padding: 10px; border-radius: 5px; margin-top: 10px;">
                            <strong>Gini coefficient: {gini:.3f}</strong> - 
                            {'Very high inequality (Matthew effect)' if gini > 0.6 else 
                             'High inequality' if gini > 0.4 else 
                             'Moderate inequality' if gini > 0.2 else 
                             'Low inequality'}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown(f'<p style="font-size:0.8rem; color:#666; text-align:right;">Year distribution based on all {total_count:,} papers, citation distribution based on ALL papers via group_by queries</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            # Enhanced tree visualization
            st.markdown('<div class="scientific-plot">', unsafe_allow_html=True)
            st.markdown("<h4>Topic Hierarchy Visualization</h4>", unsafe_allow_html=True)
            
            if any(count > 0 for count in st.session_state.topic_counts.values()):
                fig_tree = create_scientific_tree_visualization(
                    st.session_state.topic_counts,
                    st.session_state.level1_input,
                    st.session_state.level2_input
                )
                if fig_tree:
                    st.pyplot(fig_tree)
                    plt.close(fig_tree)
                
                st.markdown("""
                <div class="info-message">
                    <strong>🌳 Tree Diagram Interpretation:</strong><br>
                    • Root node represents the main research area (Level 1 + Level 2)<br>
                    • Leaf nodes represent sub-topics (Level 3 terms)<br>
                    • Branch thickness is proportional to number of publications in each sub-topic<br>
                    • Node size reflects relative publication count<br>
                    • This visualization shows the hierarchical relationship between main topic and sub-fields
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No data available for cluster visualization")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab3:
            # NEW TAB: Advanced Analytics
            st.markdown('<div class="scientific-plot">', unsafe_allow_html=True)
            st.markdown("<h4>📊 Advanced Citation and Growth Analytics</h4>", unsafe_allow_html=True)
            
            # Create a 2x2 grid for advanced charts
            col1, col2 = st.columns(2)
            
            with col1:
                # 1. Lorenz Curve (Citation Inequality)
                st.markdown("**1. Citation Inequality (Lorenz Curve)**")
                fig_lorenz = create_lorenz_curve(
                    st.session_state.results,
                    "Citation Distribution Across All Topics"
                )
                if fig_lorenz:
                    st.pyplot(fig_lorenz)
                    plt.close(fig_lorenz)
                else:
                    st.info("Insufficient data for Lorenz curve")
            
            with col2:
                # 2. Top Journals
                st.markdown("**2. Top Journals Analysis**")
                fig_journals = create_top_journals_chart(st.session_state.results)
                if fig_journals:
                    st.pyplot(fig_journals)
                    plt.close(fig_journals)
                else:
                    st.info("Insufficient journal data")
            
            col3, col4 = st.columns(2)
            
            with col3:
                # 3. Citation Velocity
                st.markdown("**3. Citation Velocity (Citations per Year)**")
                fig_velocity = create_citation_velocity_chart(consistent_data)
                if fig_velocity:
                    st.pyplot(fig_velocity)
                    plt.close(fig_velocity)
                    
                    # Add interpretation
                    st.markdown("""
                    <div style="font-size:0.8rem; color:#666; padding:5px;">
                        <i>Higher values indicate "hotter" research areas that accumulate citations faster</i>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("Insufficient data for velocity analysis")
            
            with col4:
                # 4. Highly Cited Papers Share
                st.markdown("**4. Share of Highly-Cited Papers (>50 citations)**")
                fig_highly_cited = create_highly_cited_share_chart(consistent_data, threshold=50)
                if fig_highly_cited:
                    st.pyplot(fig_highly_cited)
                    plt.close(fig_highly_cited)
                else:
                    st.info("Insufficient data for highly-cited analysis")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Second row of advanced charts
            st.markdown('<div class="scientific-plot">', unsafe_allow_html=True)
            st.markdown("<h4>📈 Growth and Trend Analysis</h4>", unsafe_allow_html=True)
            
            col5, col6 = st.columns(2)
            
            with col5:
                # 5. Relevance vs Citations Scatter
                st.markdown("**5. Relevance Score vs Citation Impact**")
                fig_scatter = create_relevance_vs_citations_scatter(consistent_data)
                if fig_scatter:
                    st.pyplot(fig_scatter)
                    plt.close(fig_scatter)
                else:
                    st.info("Insufficient data for scatter plot")
            
            with col6:
                # 6. CAGR Analysis
                st.markdown("**6. Publication Growth Rate (CAGR)**")
                fig_cagr = create_cagr_chart(consistent_data, st.session_state.years_input)
                if fig_cagr:
                    st.pyplot(fig_cagr)
                    plt.close(fig_cagr)
                else:
                    st.info("Insufficient data for CAGR analysis")
            
            col7, col8 = st.columns(2)
            
            with col7:
                # 7. Peak Year Analysis
                st.markdown("**7. Peak Publication Year Analysis**")
                fig_peak = create_peak_year_analysis(consistent_data)
                if fig_peak:
                    st.pyplot(fig_peak)
                    plt.close(fig_peak)
                else:
                    st.info("Insufficient data for peak year analysis")
            
            with col8:
                # 8. Open Access Share
                st.markdown("**8. Open Access Analysis**")
                fig_oa = create_open_access_share_chart(consistent_data, st.session_state.years_input)
                if fig_oa:
                    st.pyplot(fig_oa)
                    plt.close(fig_oa)
                else:
                    st.info("Insufficient data for OA analysis")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab4:
            # Show papers by topic (was tab3)
            for term, works in st.session_state.results.items():
                if works:
                    with st.expander(f"📚 {term} - {len(works)} papers"):
                        for i, work in enumerate(works[:10], 1):
                            enriched = enrich_work_data(work)
                            create_result_card(enriched, i, term)
                            
                            if i < len(works[:10]):
                                st.markdown("---")
        
        with tab5:
            # Export (was tab4)
            st.markdown("### 📥 Export Results")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # CSV export
                csv_data = export_to_csv(st.session_state.results)
                st.download_button(
                    label="📊 Download CSV",
                    data=csv_data,
                    file_name=f"publication_clusters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Excel export
                excel_data = export_to_excel(st.session_state.results)
                st.download_button(
                    label="📈 Download Excel",
                    data=excel_data,
                    file_name=f"publication_clusters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col3:
                # PDF export
                if PDF_AVAILABLE:
                    pdf_data = generate_pdf_report(
                        st.session_state.results,
                        st.session_state.level1_input,
                        st.session_state.level2_input,
                        st.session_state.years_input
                    )
                    if pdf_data:
                        st.download_button(
                            label="📄 Download PDF Report",
                            data=pdf_data,
                            file_name=f"publication_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    else:
                        st.button("📄 PDF Report", disabled=True, use_container_width=True)
                else:
                    st.warning("PDF export requires reportlab. Install with: pip install reportlab")
                    st.button("📄 PDF Report", disabled=True, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #888; font-size: 0.8rem; margin-top: 1rem;">
        <p>© Publication Clustering | Theme: {colors['name']}</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()


