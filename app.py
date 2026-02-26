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
from reportlab.lib.colors import HexColor
warnings.filterwarnings('ignore')

# ============================================================================
# PDF EXPORT IMPORTS
# ============================================================================
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from PIL import Image as PILImage

# ============================================================================
# НАСТРОЙКА СТРАНИЦЫ
# ============================================================================

st.set_page_config(
    page_title="Publication Clustering",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# РАСШИРЕННАЯ ПАЛИТРА ТЕМ (10 ВАРИАНТОВ)
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

# Выбираем случайную палитру при запуске
if 'color_palette' not in st.session_state:
    st.session_state['color_palette'] = random.choice(COLOR_PALETTES)

colors = st.session_state['color_palette']

# Научный стиль для matplotlib (НЕЗАВИСИМЫЙ от интерфейсной палитры)
plt.style.use('default')
plt.rcParams.update({
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
})

# ============================================================================
# КАСТОМНЫЕ СТИЛИ
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
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# КОНФИГУРАЦИЯ OPENALEX API
# ============================================================================

OPENALEX_BASE_URL = "https://api.openalex.org"
MAILTO = "your-email@example.com"  # Замените на ваш email
POLITE_POOL_HEADER = {'User-Agent': f'Publication-Clustering (mailto:{MAILTO})'}

# Настройки rate limit
RATE_LIMIT_PER_SECOND = 8
CURSOR_PAGE_SIZE = 200
MAX_RETRIES = 3
INITIAL_DELAY = 1
MAX_DELAY = 60

# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def clean_text(text: str) -> str:
    """Очистка текста от HTML тегов и лишних символов"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def parse_query_terms(term: str) -> str:
    """
    Парсит поисковый термин для OpenAlex API.
    Поддерживает:
    - Простые слова
    - Фразы в кавычках
    - Логические операторы: AND, OR, NOT
    - Wildcard (*) для поиска по корню слова
    """
    term = term.strip()
    
    # Обработка wildcard (звездочка)
    if '*' in term:
        # Если это просто wildcard термин типа "electroly*"
        if term.endswith('*') and not (' ' in term or 'OR' in term.upper() or '"' in term):
            # Для OpenAlex wildcard не поддерживается напрямую, поэтому создаем OR запрос
            # с常见 вариантами окончаний
            base = term[:-1]  # убираем звездочку
            # Типичные окончания для научных терминов
            suffixes = ['', 'e', 'es', 'ed', 'ing', 'ion', 'ions', 'ic', 'ical', 'ly', 'sis', 'tic', 'al', 'ize', 'izer']
            variants = [f'"{base}{suffix}"' if ' ' in base+suffix else f'{base}{suffix}' for suffix in suffixes]
            # Убираем пустые варианты и объединяем через OR
            variants = [v for v in variants if v.strip('"')]
            return ' OR '.join(variants)
    
    # Если это фраза в кавычках, оставляем как есть
    if term.startswith('"') and term.endswith('"'):
        return term
    
    # Если есть оператор OR (регистронезависимый)
    if ' OR ' in term.upper():
        # Разбиваем по OR, обрабатываем каждую часть
        parts = re.split(r'\s+OR\s+', term, flags=re.IGNORECASE)
        processed_parts = []
        for part in parts:
            part = part.strip()
            if ' ' in part and not (part.startswith('"') and part.endswith('"')):
                # Если в части есть пробелы, оборачиваем в кавычки
                processed_parts.append(f'"{part}"')
            else:
                processed_parts.append(part)
        return ' OR '.join(processed_parts)
    
    # Если есть пробелы, но не OR, значит это фраза - оборачиваем в кавычки
    if ' ' in term:
        return f'"{term}"'
    
    return term

def create_metric_card(title: str, value, icon: str = "📊"):
    """Создает компактную карточку с метрикой"""
    st.markdown(f"""
    <div class="metric-card">
        <h4>{icon} {title}</h4>
        <div class="value">{value:,}</div>
    </div>
    """, unsafe_allow_html=True)

def create_result_card(work: dict, index: int, topic: str):
    """Создает карточку результата"""
    citation_count = work.get('cited_by_count', 0)
    
    # Определяем цвет баджа цитирования
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

def navigation_buttons(show_back: bool = True, show_new: bool = True, back_to_step1: bool = False):
    """Отображает кнопки навигации"""
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if show_back and st.session_state.step > 1:
            target_step = 1 if back_to_step1 else st.session_state.step - 1
            button_text = "← Back to Step 1" if back_to_step1 else "← Back"
            if st.button(button_text, key="back_btn", use_container_width=True):
                st.session_state.step = target_step
                st.rerun()
    
    with col2:
        if show_new:
            if st.button("🔄 New Search", key="new_btn", use_container_width=True):
                # Очищаем сессию, НО сохраняем введенные термины
                level1_input = st.session_state.get('level1_input', '')
                level2_input = st.session_state.get('level2_input', '')
                level3_input = st.session_state.get('level3_input', [])
                years_input = st.session_state.get('years_input', [])
                
                for key in ['step', 'results', 'topic_counts', 'level1_count', 'level2_count']:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # Восстанавливаем введенные термины
                st.session_state['level1_input'] = level1_input
                st.session_state['level2_input'] = level2_input
                st.session_state['level3_input'] = level3_input
                st.session_state['years_input'] = years_input
                st.session_state.step = 1
                st.rerun()

# ============================================================================
# ФУНКЦИИ ДЛЯ ПОСТРОЕНИЯ ЗАПРОСОВ
# ============================================================================

def build_search_filter(level1_term: str, level2_term: Optional[str] = None,
                       years: Optional[List[int]] = None) -> Dict[str, str]:
    """Строит фильтры для OpenAlex API на основе первых двух уровней"""
    filters = {}
    
    # Формируем поисковый запрос
    search_parts = []
    
    # Уровень 1 - основной термин
    if level1_term:
        search_parts.append(f"({parse_query_terms(level1_term)})")
    
    # Уровень 2 - дополнительный термин (опционально)
    if level2_term:
        search_parts.append(f"({parse_query_terms(level2_term)})")
    
    # Объединяем все части с AND
    if search_parts:
        filters['default.search'] = ' AND '.join(search_parts)
    
    # Фильтр по годам
    if years:
        if len(years) == 1:
            filters['publication_year'] = str(years[0])
        else:
            filters['publication_year'] = f"{min(years)}-{max(years)}"
    
    return filters

def build_level3_filter(level3_term: str, base_filters: Dict[str, str]) -> str:
    """Строит фильтр для термина третьего уровня с учетом всех фильтров"""
    filter_parts = []
    
    if 'publication_year' in base_filters:
        filter_parts.append(f"publication_year:{base_filters['publication_year']}")
    
    search_parts = []
    if 'default.search' in base_filters:
        search_parts.append(f"({base_filters['default.search']})")
    
    if level3_term:
        search_parts.append(f"({parse_query_terms(level3_term)})")
    
    if search_parts:
        filter_parts.append(f"default.search:{' AND '.join(search_parts)}")
    
    return ','.join(filter_parts)

def build_count_filter(base_filters: Dict[str, str]) -> str:
    """Строит фильтр только из первых двух уровней"""
    filter_parts = []
    
    if 'publication_year' in base_filters:
        filter_parts.append(f"publication_year:{base_filters['publication_year']}")
    
    if 'default.search' in base_filters:
        filter_parts.append(f"default.search:{base_filters['default.search']}")
    
    return ','.join(filter_parts)

# ============================================================================
# ФУНКЦИИ ДЛЯ ЗАПРОСОВ К OPENALEX
# ============================================================================

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=INITIAL_DELAY, max=MAX_DELAY),
    retry=retry_if_exception_type((requests.exceptions.RequestException,))
)
@sleep_and_retry
@limits(calls=RATE_LIMIT_PER_SECOND, period=1)
def make_openalex_request(url: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """Выполняет запрос к OpenAlex API с учетом rate limiting"""
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
    """Получает общее количество статей по запросу"""
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

def get_topic_counts(level1_term: str, level2_term: Optional[str],
                    level3_terms: List[str], years: Optional[List[int]],
                    progress_callback=None) -> Dict[str, int]:
    """Получает количество статей по каждому термину третьего уровня"""
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
    """Получает топ-N наиболее релевантных работ по термину"""
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
    """Обогащает данные работы дополнительными полями"""
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
    
    # Авторы
    authorships = work.get('authorships', [])
    authors = []
    for authorship in authorships[:5]:
        if authorship and 'author' in authorship:
            author_name = authorship['author'].get('display_name', '')
            if author_name:
                authors.append(author_name)
    enriched['authors'] = authors
    
    # Журнал
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

def get_yearly_distribution(level1_term: str, level2_term: Optional[str], 
                           level3_term: str, years: Optional[List[int]]) -> Dict[int, int]:
    """
    Получает реальное распределение по годам для конкретной подтемы
    """
    base_filters = build_search_filter(level1_term, level2_term)
    filter_str = build_level3_filter(level3_term, base_filters)
    
    yearly_counts = {}
    
    for year in years:
        # Для каждого года создаем фильтр с конкретным годом
        year_filter = f"{filter_str},publication_year:{year}"
        
        params = {
            'filter': year_filter,
            'per-page': 1
        }
        
        data = make_openalex_request(f"{OPENALEX_BASE_URL}/works", params)
        
        if data and 'meta' in data:
            yearly_counts[year] = data['meta'].get('count', 0)
        else:
            yearly_counts[year] = 0
        
        time.sleep(0.1)  # Небольшая задержка между запросами
    
    return yearly_counts

# ============================================================================
# ФУНКЦИИ ДЛЯ ВИЗУАЛИЗАЦИИ (НАУЧНЫЙ СТИЛЬ)
# ============================================================================

def create_scientific_bar_chart(data: Dict[str, int], level2_count: int, title: str):
    """Создает научную столбчатую диаграмму с помощью matplotlib"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Фильтруем нулевые значения
    non_zero = {k: v for k, v in data.items() if v > 0}
    if not non_zero:
        return None
    
    topics = list(non_zero.keys())
    counts = list(non_zero.values())
    percentages = [(c / level2_count * 100) if level2_count > 0 else 0 for c in counts]
    
    # Сортируем по убыванию
    sorted_idx = np.argsort(counts)[::-1]
    topics = [topics[i] for i in sorted_idx]
    counts = [counts[i] for i in sorted_idx]
    percentages = [percentages[i] for i in sorted_idx]
    
    # Цвета в научном стиле (оттенки серого)
    colors1 = plt.cm.Greys(np.linspace(0.3, 0.7, len(topics)))
    colors2 = plt.cm.Greys(np.linspace(0.3, 0.7, len(topics)))
    
    # График количества
    bars1 = ax1.barh(range(len(topics)), counts, color=colors1, edgecolor='black', linewidth=0.5)
    ax1.set_yticks(range(len(topics)))
    ax1.set_yticklabels(topics, fontsize=9)
    ax1.set_xlabel('Number of Publications', fontsize=10, fontweight='bold')
    ax1.set_title('A) Publication Counts', fontsize=11, fontweight='bold', pad=10)
    ax1.tick_params(axis='both', which='major', labelsize=9)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    # Добавляем значения на бары
    for i, (bar, count) in enumerate(zip(bars1, counts)):
        ax1.text(count + max(counts)*0.01, bar.get_y() + bar.get_height()/2, 
                f'{count}', va='center', fontsize=8)
    
    # График процентов
    bars2 = ax2.barh(range(len(topics)), percentages, color=colors2, edgecolor='black', linewidth=0.5)
    ax2.set_yticks(range(len(topics)))
    ax2.set_yticklabels([])  # Убираем метки, так как они уже есть на первом графике
    ax2.set_xlabel('Percentage of Total (%)', fontsize=10, fontweight='bold')
    ax2.set_title('B) Percentage Distribution', fontsize=11, fontweight='bold', pad=10)
    ax2.tick_params(axis='both', which='major', labelsize=9)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    # Добавляем проценты на бары
    for i, (bar, pct) in enumerate(zip(bars2, percentages)):
        ax2.text(pct + max(percentages)*0.01, bar.get_y() + bar.get_height()/2, 
                f'{pct:.1f}%', va='center', fontsize=8)
    
    plt.suptitle(title, fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    return fig

def create_yearly_distribution_chart(yearly_data: Dict[int, int], title: str):
    """Создает график распределения по годам на основе реальных данных"""
    if not yearly_data:
        return None
    
    years_sorted = sorted(yearly_data.keys())
    counts = [yearly_data[y] for y in years_sorted]
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    bars = ax.bar(years_sorted, counts, color='#4C72B0', edgecolor='black', linewidth=0.5)
    ax.set_xlabel('Publication Year', fontsize=10, fontweight='bold')
    ax.set_ylabel('Number of Publications', fontsize=10, fontweight='bold')
    ax.set_title(title, fontsize=11, fontweight='bold', pad=10)
    ax.tick_params(axis='both', which='major', labelsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Добавляем значения на бары
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    return fig

def create_citation_distribution_chart(works: List[Dict], title: str):
    """Создает график распределения цитирований"""
    citations = [w.get('cited_by_count', 0) for w in works]
    if not citations:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Создаем гистограмму
    n, bins, patches = ax.hist(citations, bins=20, color='#55A868', 
                               edgecolor='black', linewidth=0.5, alpha=0.7)
    
    ax.set_xlabel('Number of Citations', fontsize=10, fontweight='bold')
    ax.set_ylabel('Number of Papers', fontsize=10, fontweight='bold')
    ax.set_title(title, fontsize=11, fontweight='bold', pad=10)
    ax.tick_params(axis='both', which='major', labelsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Добавляем статистику
    mean_cit = np.mean(citations)
    median_cit = np.median(citations)
    ax.axvline(mean_cit, color='red', linestyle='--', linewidth=1, label=f'Mean: {mean_cit:.1f}')
    ax.axvline(median_cit, color='blue', linestyle='--', linewidth=1, label=f'Median: {median_cit:.1f}')
    ax.legend(fontsize=8, frameon=True, edgecolor='black')
    
    plt.tight_layout()
    return fig

def create_combined_yearly_charts(topic_yearly_data: Dict[str, Dict[int, int]], 
                                  level2_term: Optional[str] = None):
    """
    Создает комбинированный график с годовыми распределениями для всех подтем
    на основе РЕАЛЬНЫХ данных
    """
    if not topic_yearly_data:
        return None
    
    # Создаем фигуру с тремя подграфиками
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Определяем все доступные годы из первого набора данных
    all_years = set()
    for data in topic_yearly_data.values():
        all_years.update(data.keys())
    years = sorted(all_years)
    
    # Подграфик 1: Со смещением (stacked)
    ax = axes[0]
    bottom = np.zeros(len(years))
    colors_stack = plt.cm.Set3(np.linspace(0, 1, len(topic_yearly_data)))
    
    for idx, (topic, data) in enumerate(topic_yearly_data.items()):
        counts = [data.get(year, 0) for year in years]
        ax.bar(years, counts, bottom=bottom, label=topic, 
               color=colors_stack[idx], edgecolor='black', linewidth=0.5, alpha=0.7)
        bottom += counts
    
    ax.set_xlabel('Publication Year', fontsize=10, fontweight='bold')
    ax.set_ylabel('Number of Publications', fontsize=10, fontweight='bold')
    ax.set_title('A) Stacked Yearly Distribution', fontsize=11, fontweight='bold', pad=10)
    ax.tick_params(axis='both', which='major', labelsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(fontsize=8, frameon=True, edgecolor='black')
    
    # Подграфик 2: Нормализованный (по максимальному значению каждой темы)
    ax = axes[1]
    
    for topic, data in topic_yearly_data.items():
        counts = np.array([data.get(year, 0) for year in years])
        if counts.max() > 0:
            normalized = counts / counts.max()
            ax.plot(years, normalized, marker='o', linewidth=1.5, markersize=4, label=topic)
    
    ax.set_xlabel('Publication Year', fontsize=10, fontweight='bold')
    ax.set_ylabel('Normalized Intensity (max=1)', fontsize=10, fontweight='bold')
    ax.set_title('B) Normalized by Maximum', fontsize=11, fontweight='bold', pad=10)
    ax.tick_params(axis='both', which='major', labelsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylim(0, 1.1)
    ax.legend(fontsize=8, frameon=True, edgecolor='black')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Подграфик 3: Логарифмическая шкала (абсолютные значения)
    ax = axes[2]
    
    # Находим глобальный максимум для настройки оси Y
    all_counts = []
    for data in topic_yearly_data.values():
        all_counts.extend(data.values())
    max_count = max(all_counts) if all_counts else 1
    
    for topic, data in topic_yearly_data.items():
        counts = [data.get(year, 0) for year in years]
        if max(counts) > 0:
            # Используем абсолютные значения, но для log(0) ставим 0.1 (ниже минимального видимого значения)
            counts_log = [c if c > 0 else 0.1 for c in counts]
            ax.semilogy(years, counts_log, marker='s', linewidth=1.5, markersize=4, label=topic)
    
    ax.set_xlabel('Publication Year', fontsize=10, fontweight='bold')
    ax.set_ylabel('Number of Publications (log scale)', fontsize=10, fontweight='bold')
    ax.set_title('C) Logarithmic Scale (absolute values)', fontsize=11, fontweight='bold', pad=10)
    ax.tick_params(axis='both', which='major', labelsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Настраиваем логарифмическую шкалу Y
    y_min = 0.5  # Чуть ниже 1 для показа 0 значений
    y_max = max_count * 2  # Немного выше максимума для запаса
    ax.set_ylim(y_min, y_max)
    
    # Добавляем основные линии сетки для логарифмической шкалы
    ax.grid(True, alpha=0.3, linestyle='--', which='both')
    
    # Добавляем легенду
    ax.legend(fontsize=8, frameon=True, edgecolor='black', loc='best')
    
    plt.suptitle(f'Comparative Yearly Distribution Analysis' + (f' (with {level2_term})' if level2_term else ''), 
                 fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    return fig

def create_tree_visualization(topic_counts: Dict[str, int], level1_term: str, level2_term: Optional[str] = None):
    """
    Создает древовидную визуализацию в научном стиле
    """
    topics = [t for t, count in topic_counts.items() if count > 0]
    if not topics:
        return None
    
    # Сортируем темы по убыванию
    topics_sorted = sorted(topics, key=lambda x: topic_counts[x], reverse=True)
    counts = [topic_counts[t] for t in topics_sorted]
    max_count = max(counts) if counts else 1
    
    # Создаем фигуру с научным оформлением
    fig, ax = plt.subplots(figsize=(14, 10), facecolor='white')
    ax.set_facecolor('white')
    
    # Параметры дерева
    tree_height = 8
    trunk_width = 1.5
    
    # Рисуем ствол (прямоугольник)
    trunk = plt.Rectangle((-trunk_width/2, 0), trunk_width, tree_height, 
                          facecolor='#8B4513', edgecolor='black', linewidth=1, alpha=0.8)
    ax.add_patch(trunk)
    
    # Добавляем текстуру коры (линии)
    for y in np.linspace(0.5, tree_height-0.5, 15):
        ax.plot([-trunk_width/2, trunk_width/2], [y, y], 
                color='#5D3A1A', linewidth=0.5, alpha=0.5)
    
    # Позиции для веток
    branch_positions = np.linspace(tree_height * 0.3, tree_height * 0.9, len(topics_sorted))
    
    # Цвета для листьев/плодов (научная цветовая схема)
    leaf_colors = plt.cm.YlGn(np.linspace(0.3, 0.9, len(topics_sorted)))
    
    for i, (topic, count, y_pos, color) in enumerate(zip(topics_sorted, counts, branch_positions, leaf_colors)):
        # Нормализованная толщина ветки (от 0.2 до 0.8)
        branch_width = 0.2 + 0.6 * (count / max_count)
        
        # Длина ветки пропорциональна количеству
        branch_length = 2 + 3 * (count / max_count)
        
        # Рисуем ветку (с изгибом для реалистичности)
        x_start = trunk_width/2
        x_end = x_start + branch_length
        y_start = y_pos
        
        # Создаем изогнутую ветку с помощью кривой Безье
        # Контрольные точки для изгиба вверх
        control_x = x_start + branch_length * 0.4
        control_y = y_start + 0.5
        control_x2 = x_start + branch_length * 0.7
        control_y2 = y_start - 0.2
        
        # Рисуем ветку
        t = np.linspace(0, 1, 50)
        # Кубическая кривая Безье
        x = (1-t)**3 * x_start + 3*(1-t)**2*t * control_x + 3*(1-t)*t**2 * control_x2 + t**3 * x_end
        y = (1-t)**3 * y_start + 3*(1-t)**2*t * control_y + 3*(1-t)*t**2 * control_y2 + t**3 * y_start
        ax.plot(x, y, color='#8B4513', linewidth=branch_width*2, alpha=0.9)
        
        # Добавляем маленькие веточки
        num_twigs = max(2, int(count / max_count * 5))
        for j in range(num_twigs):
            t_twig = 0.3 + 0.6 * j / num_twigs
            x_twig = (1-t_twig)**3 * x_start + 3*(1-t_twig)**2*t_twig * control_x + 3*(1-t_twig)*t_twig**2 * control_x2 + t_twig**3 * x_end
            y_twig = (1-t_twig)**3 * y_start + 3*(1-t_twig)**2*t_twig * control_y + 3*(1-t_twig)*t_twig**2 * control_y2 + t_twig**3 * y_start
            
            # Маленькая веточка вверх или вниз
            angle = np.random.uniform(-30, 30) * np.pi/180
            twig_length = 0.5
            x_twig_end = x_twig + twig_length * np.cos(angle)
            y_twig_end = y_twig + twig_length * np.sin(angle)
            ax.plot([x_twig, x_twig_end], [y_twig, y_twig_end], 
                   color='#A0522D', linewidth=1, alpha=0.6)
        
        # Добавляем листья/плоды (размер пропорционален количеству)
        leaf_size = 50 + 200 * (count / max_count)
        
        # Позиция для листьев - на конце ветки
        leaf_x = x_end
        leaf_y = y_start
        
        # Рисуем несколько листьев/плодов
        for k in range(3):
            offset_x = np.random.uniform(-0.3, 0.3)
            offset_y = np.random.uniform(-0.3, 0.3)
            ax.scatter(leaf_x + offset_x, leaf_y + offset_y, 
                      s=leaf_size * (0.7 + 0.3*k/3), 
                      c=[color], 
                      edgecolor='black', linewidth=0.5, alpha=0.8, zorder=5)
        
        # Добавляем метку с количеством
        label_x = leaf_x + 0.8
        label_y = leaf_y
        ax.annotate(f'{topic}\n({count:,})', 
                   xy=(leaf_x, leaf_y), xytext=(label_x, label_y),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.2',
                                 color='black', lw=0.5),
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                           edgecolor='black', alpha=0.9),
                   fontsize=9, ha='left', va='center')
    
    # Добавляем корни
    root_y = -1
    for i in range(3):
        root_x = -trunk_width/2 + i * trunk_width/2
        root_length = 1 + np.random.random()
        ax.plot([root_x, root_x - 1], [root_y, root_y - 1], 
                color='#8B4513', linewidth=1.5, alpha=0.7)
        ax.plot([root_x, root_x + 1], [root_y, root_y - 1], 
                color='#8B4513', linewidth=1.5, alpha=0.7)
    
    # Добавляем метку корня/ствола
    root_label = level1_term
    if level2_term:
        root_label += f'\n+ {level2_term}'
    ax.text(0, tree_height/2, root_label, 
           ha='center', va='center', fontsize=12, fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                    edgecolor='black', alpha=0.9))
    
    # Настройки графика
    ax.set_xlim(-3, 12)
    ax.set_ylim(-3, tree_height + 1)
    ax.set_aspect('equal')
    ax.axis('off')
    
    plt.title('Hierarchical Tree Diagram of Research Topics', 
              fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    
    return fig

# ============================================================================
# ФУНКЦИИ ДЛЯ ЭКСПОРТА
# ============================================================================

def export_to_csv(works_by_topic: Dict[str, List[Dict]]) -> bytes:
    """Экспортирует результаты в CSV"""
    all_rows = []
    for topic, works in works_by_topic.items():
        for work in works:
            enriched = enrich_work_data(work)
            enriched['sub_topic'] = topic
            all_rows.append(enriched)
    
    df = pd.DataFrame(all_rows)
    return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

def export_to_excel(works_by_topic: Dict[str, List[Dict]]) -> bytes:
    """Экспортирует результаты в Excel"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Общий лист
        all_rows = []
        for topic, works in works_by_topic.items():
            for work in works:
                enriched = enrich_work_data(work)
                enriched['sub_topic'] = topic
                all_rows.append(enriched)
        
        if all_rows:
            df_all = pd.DataFrame(all_rows)
            df_all.to_excel(writer, sheet_name='All Papers', index=False)
        
        # Отдельные листы для каждой подтемы
        for topic, works in works_by_topic.items():
            if works:
                df_topic = pd.DataFrame([enrich_work_data(w) for w in works])
                sheet_name = re.sub(r'[^\w\s-]', '', topic)[:31]
                df_topic.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Форматирование
        workbook = writer.book
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': colors['primary'],
            'font_color': 'white',
            'border': 1
        })
        
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            if sheet_name == 'All Papers':
                df = df_all
            else:
                df = next((pd.DataFrame([enrich_work_data(w) for w in works]) 
                          for t, works in works_by_topic.items() 
                          if re.sub(r'[^\w\s-]', '', t)[:31] == sheet_name), None)
            
            if df is not None:
                for col_num, col_name in enumerate(df.columns):
                    worksheet.write(0, col_num, col_name, header_format)
                    max_len = max(
                        df[col_name].astype(str).map(len).max() if not df[col_name].empty else 0,
                        len(str(col_name))
                    ) + 2
                    worksheet.set_column(col_num, col_num, min(max_len, 50))
    
    return output.getvalue()

def export_to_pdf(works_by_topic: Dict[str, List[Dict]], topic_counts: Dict[str, int],
                  level1_term: str, level2_term: Optional[str], years: List[int]) -> bytes:
    """Экспортирует результаты в PDF с научным оформлением"""
    
    # Вспомогательная функция для очистки текста
    def clean_text_for_pdf(text):
        if not text:
            return ""
        # Заменяем HTML сущности и теги
        text = re.sub(r'<[^>]+>', '', str(text))
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return text
    
    buffer = io.BytesIO()
    
    # Используем A4 для большего пространства
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        topMargin=1*cm,
        bottomMargin=1*cm,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm
    )
    
    styles = getSampleStyleSheet()
    
    # ========== СОЗДАНИЕ КАСТОМНЫХ СТИЛЕЙ ==========
    
    # Стиль для заголовка
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Стиль для подзаголовка
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    # Стиль для информации о теме
    topic_style = ParagraphStyle(
        'CustomTopic',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#16A085'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Стиль для мета-информации
    meta_style = ParagraphStyle(
        'CustomMeta',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#7F8C8D'),
        spaceAfter=3,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    # Стиль для названия темы в результатах
    topic_header_style = ParagraphStyle(
        'TopicHeader',
        parent=styles['Heading4'],
        fontSize=13,
        textColor=colors.HexColor('#2980B9'),
        spaceAfter=8,
        spaceBefore=12,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    # Стиль для названия статьи
    paper_title_style = ParagraphStyle(
        'CustomPaperTitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=4,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    # Стиль для авторов
    authors_style = ParagraphStyle(
        'CustomAuthors',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=2,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    # Стиль для деталей статьи
    details_style = ParagraphStyle(
        'CustomDetails',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#7F8C8D'),
        spaceAfter=2,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    # Стиль для метрик
    metrics_style = ParagraphStyle(
        'CustomMetrics',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#27AE60'),
        spaceAfter=0,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    # Стиль для разделителя
    separator_style = ParagraphStyle(
        'CustomSeparator',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#BDC3C7'),
        spaceAfter=10,
        spaceBefore=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    # Стиль для ссылок
    link_style = ParagraphStyle(
        'CustomLink',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.blue,
        spaceAfter=2,
        alignment=TA_LEFT,
        fontName='Helvetica',
        underline=True
    )
    
    # Стиль для нижнего колонтитула
    footer_style = ParagraphStyle(
        'CustomFooter',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#95A5A6'),
        spaceBefore=15,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    story = []
    
    # ========== ТИТУЛЬНАЯ СТРАНИЦА ==========
    
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("Publication Clustering Analysis Report", title_style))
    story.append(Spacer(1, 1*cm))
    
    # Информация о запросе
    query_text = f"Level 1: {clean_text_for_pdf(level1_term)}"
    if level2_term:
        query_text += f"<br/>Level 2: {clean_text_for_pdf(level2_term)}"
    story.append(Paragraph(query_text, subtitle_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Информация о годах
    year_text = f"Publication Years: {min(years)} - {max(years)}"
    story.append(Paragraph(year_text, meta_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Дата генерации
    current_date = datetime.now().strftime('%B %d, %Y at %H:%M')
    story.append(Paragraph(f"Generated on {current_date}", meta_style))
    story.append(Spacer(1, 2*cm))
    
    # Копирайт
    story.append(Paragraph("© Publication Clustering", footer_style))
    
    story.append(PageBreak())
    
    # ========== СТАТИСТИКА ==========
    
    story.append(Paragraph("EXECUTIVE SUMMARY", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Собираем статистику
    total_level1 = st.session_state.get('level1_count', 0)
    total_level2 = st.session_state.get('level2_count', 0)
    total_papers_found = sum(len(works) for works in works_by_topic.values())
    topics_with_results = sum(1 for v in works_by_topic.values() if v)
    
    # Создаем таблицу статистики
    stats_data = [
        ["Metric", "Value"],
        ["Level 1 Papers", f"{total_level1:,}"],
        ["After Level 2 Filter", f"{total_level2:,}"],
        ["Top Papers Found", f"{total_papers_found:,}"],
        ["Topics with Results", f"{topics_with_results}"],
        ["Total Sub-topics", f"{len(topic_counts)}"],
        ["Year Range", f"{min(years)} - {max(years)}"]
    ]
    
    stats_table = Table(stats_data, colWidths=[doc.width/2.5, doc.width/3])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D5DBDB')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F4F4')]),
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 1*cm))
    
    # Распределение по подтемам
    story.append(Paragraph("Topic Distribution", subtitle_style))
    story.append(Spacer(1, 0.3*cm))
    
    topic_data = [["Topic", "Papers", "Percentage"]] + [
        [t, f"{c:,}", f"{(c/total_level2*100):.1f}%" if total_level2 > 0 else "0%"]
        for t, c in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True) if c > 0
    ]
    
    if len(topic_data) > 1:
        topic_table = Table(topic_data, colWidths=[doc.width/2, doc.width/5, doc.width/5])
        topic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ECC71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D5DBDB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F4F4')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(topic_table)
    
    story.append(PageBreak())
    
    # ========== ДЕТАЛЬНЫЙ ОТЧЕТ ПО ПОДТЕМАМ ==========
    
    story.append(Paragraph("DETAILED ANALYSIS BY SUB-TOPIC", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Обрабатываем каждую подтему
    for topic, works in works_by_topic.items():
        if not works:
            continue
        
        total_for_topic = topic_counts.get(topic, 0)
        
        # Заголовок темы
        story.append(Paragraph(f"Topic: {clean_text_for_pdf(topic)}", topic_header_style))
        story.append(Paragraph(f"Total papers: {total_for_topic:,} | Showing top {len(works)} most relevant", 
                             meta_style))
        story.append(Spacer(1, 0.2*cm))
        
        # Показываем первые 10 статей по каждой теме
        for i, work in enumerate(works[:10], 1):
            # Заголовок статьи
            title = clean_text_for_pdf(work.get('title', 'No title available'))
            story.append(Paragraph(f"{i}. {title}", paper_title_style))
            
            # Авторы
            authors = work.get('authors', [])
            if authors:
                authors_text = ', '.join(authors[:3])
                if len(authors) > 3:
                    authors_text += f' et al. ({len(authors)} authors)'
                story.append(Paragraph(f"<b>Authors:</b> {clean_text_for_pdf(authors_text)}", authors_style))
            
            # Основные метрики
            citations = work.get('cited_by_count', 0)
            year = work.get('publication_year', 'N/A')
            relevance = work.get('relevance_score', 0)
            journal = clean_text_for_pdf(work.get('journal', 'N/A')[:40])
            
            metrics_text = f"""
            <b>Citations:</b> {citations} | 
            <b>Year:</b> {year} | 
            <b>Relevance Score:</b> {relevance:.2f} | 
            <b>Journal:</b> {journal} | 
            <b>Open Access:</b> {'Yes' if work.get('is_oa') else 'No'}
            """
            story.append(Paragraph(metrics_text, metrics_style))
            
            # DOI и ссылка
            doi = work.get('doi', '')
            doi_url = work.get('doi_url', '')
            
            if doi:
                if doi_url:
                    story.append(Paragraph(f"<b>DOI:</b> {clean_text_for_pdf(doi)}", details_style))
                    story.append(Paragraph(f"<b>Link:</b> {doi_url}", link_style))
                else:
                    story.append(Paragraph(f"<b>DOI:</b> {clean_text_for_pdf(doi)}", details_style))
            
            # Разделитель между статьями
            if i < min(10, len(works)):
                story.append(Spacer(1, 0.2*cm))
                story.append(Paragraph("─" * 40, separator_style))
                story.append(Spacer(1, 0.2*cm))
        
        # Разделитель между темами
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("=" * 60, separator_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Добавляем разрыв страницы если нужно
        if list(works_by_topic.keys())[-1] != topic:
            story.append(PageBreak())
    
    # ========== ЗАКЛЮЧЕНИЕ ==========
    
    story.append(PageBreak())
    story.append(Paragraph("CONCLUSION", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Анализ распределения
    dominant_topic = max(topic_counts.items(), key=lambda x: x[1]) if topic_counts else (None, 0)
    if dominant_topic[0]:
        story.append(Paragraph(
            f"The dominant sub-topic is <b>{clean_text_for_pdf(dominant_topic[0])}</b> with {dominant_topic[1]:,} papers "
            f"({(dominant_topic[1]/total_level2*100):.1f}% of the filtered results).",
            ParagraphStyle('Conclusion', parent=styles['Normal'], fontSize=10, spaceAfter=6)
        ))
    
    # Рекомендации
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Recommendations for further research:</b>", 
                          ParagraphStyle('RecHeader', parent=styles['Normal'], fontSize=11, spaceAfter=4)))
    
    recommendations = [
        "• Explore the dominant sub-topics for comprehensive literature review",
        "• Investigate emerging topics with recent publication spikes",
        "• Consider cross-disciplinary connections between sub-topics",
        "• Analyze highly-cited papers for foundational knowledge",
        "• Review recent Open Access papers for cutting-edge research"
    ]
    
    for rec in recommendations:
        story.append(Paragraph(rec, details_style))
    
    # Нижний колонтитул
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("© Publication Clustering - Generated by Publication Clustering Tool", footer_style))
    story.append(Paragraph(f"Report ID: {hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}", 
                         ParagraphStyle('ReportID', parent=styles['Normal'], fontSize=7,
                                      textColor=colors.HexColor('#BDC3C7'), alignment=TA_CENTER)))
    
    # ========== ГЕНЕРАЦИЯ PDF ==========
    
    doc.build(story)
    
    return buffer.getvalue()

# ============================================================================
# ОСНОВНОЙ ИНТЕРФЕЙС
# ============================================================================

def main():
    """Главная функция приложения"""
    
    # Заголовок
    st.markdown(f'<h1 class="main-header">Publication Clustering</h1>', unsafe_allow_html=True)
    st.markdown(f"""
    <p style="font-size: 1rem; color: {colors['text']}; margin-bottom: 1.5rem;">
    Multi-level literature search with topic clustering and network visualization
    </p>
    """, unsafe_allow_html=True)
    
    # Отображаем информацию о текущей теме
    st.markdown(f"""
    <div style="text-align: right; font-size: 0.8rem; color: {colors['primary']}; margin-bottom: 0.5rem;">
        Theme: {colors['name']}
    </div>
    """, unsafe_allow_html=True)
    
    # Инициализация состояния сессии
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
        st.session_state['level1_input'] = ''
    if 'level2_input' not in st.session_state:
        st.session_state['level2_input'] = ''
    if 'level3_input' not in st.session_state:
        st.session_state['level3_input'] = []
    if 'years_input' not in st.session_state:
        st.session_state['years_input'] = []
    
    # ========================================================================
    # ШАГ 1: ВВОД ТЕРМИНОВ
    # ========================================================================
    
    if st.session_state.step == 1:
        st.markdown(f"""
        <div class="step-card">
            <h3 style="margin: 0; font-size: 1.3rem;">📥 Step 1: Enter Search Terms</h3>
            <p style="margin: 5px 0; font-size: 0.9rem;">Define your multi-level search query</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Расширенная инструкция
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
            • Use <b>*</b> for wildcard search (e.g., "electroly*" matches electrolyte, electrolysis, electrolyzer)<br>
            • Multiple words without operators are treated as exact phrase
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Level 1 (required):**")
            level1 = st.text_input(
                "Main domain (broad research area)",
                value=st.session_state['level1_input'] or '"metal-organic frameworks" OR MOF',
                key="level1",
                label_visibility="collapsed",
                placeholder="e.g., \"machine learning\" OR \"artificial intelligence\""
            )
            
            st.markdown("**Level 2 (optional):**")
            level2 = st.text_input(
                "Refinement term (narrows down Level 1)",
                value=st.session_state['level2_input'] or "",
                key="level2",
                label_visibility="collapsed",
                placeholder="e.g., \"neural networks\" OR deep learning"
            )
        
        with col2:
            st.markdown("**Level 3 terms (one per line - these will become your clusters):**")
            level3_default = "\n".join(st.session_state['level3_input']) if st.session_state['level3_input'] else "MIL\nZIF\nIRMOF\nUiO\nHKUST"
            level3_text = st.text_area(
                "Sub-topics for classification",
                value=level3_default,
                height=120,
                key="level3",
                label_visibility="collapsed",
                placeholder="Enter each sub-topic on a new line"
            )
        
        # Фильтр по годам
        st.markdown("---")
        st.markdown("**📅 Publication Years:**")
        
        current_year = datetime.now().year
        
        # Опции для выбора типа фильтра годов
        year_option = st.radio(
            "Year filter type",
            ["Range", "Single year", "Multiple years"],
            horizontal=True,
            key="year_type",
            index=0  # Range по умолчанию первый
        )
        
        if year_option == "Range":
            default_range = st.session_state['years_input'] if st.session_state['years_input'] else [2000, current_year]
            if isinstance(default_range, list) and len(default_range) > 1:
                default_min, default_max = min(default_range), max(default_range)
            else:
                default_min, default_max = 2000, current_year
            
            year_range = st.slider(
                "Select range", 
                2000, current_year, 
                (default_min, default_max)
            )
            years = list(range(year_range[0], year_range[1] + 1))
        elif year_option == "Single year":
            default_year = st.session_state['years_input'][0] if st.session_state['years_input'] else current_year
            year = st.slider("Select year", 2000, current_year, default_year)
            years = [year]
        else:  # Multiple years
            default_years = st.session_state['years_input'] if st.session_state['years_input'] else [current_year-2, current_year-1, current_year]
            years = st.multiselect(
                "Select years",
                list(range(current_year, 1999, -1)),
                default=default_years
            )
        
        # Тестовая кнопка для проверки запроса
        with st.expander("🔧 Test Query Before Full Analysis"):
            if st.button("Test Current Query", use_container_width=True):
                with st.spinner("Testing query..."):
                    temp_count = get_total_count(level1.strip(), level2.strip() or None, years)
                    if temp_count > 0:
                        st.success(f"✅ Found {temp_count:,} papers matching your Level 1+2 criteria")
                    else:
                        st.warning("""
                        ⚠️ No results found! Try:
                        - Using fewer or more general terms
                        - Checking your spelling
                        - Expanding the year range
                        - Using quotes for exact phrases
                        - Using wildcard (*) for word variations
                        """)
        
        # Кнопка запуска
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔍 Start Analysis", type="primary", use_container_width=True):
                if not level1.strip():
                    st.error("❌ Please enter Level 1 term")
                elif not level3_text.strip():
                    st.error("❌ Please enter at least one Level 3 term")
                else:
                    # Сохраняем в сессию через словарь
                    st.session_state['level1_input'] = level1.strip()
                    st.session_state['level2_input'] = level2.strip() or None
                    st.session_state['level3_input'] = [t.strip() for t in level3_text.split('\n') if t.strip()]
                    st.session_state['years_input'] = years
                    st.session_state['step'] = 2
                    st.rerun()
    
    # ========================================================================
    # ШАГ 2: АНАЛИЗ
    # ========================================================================
    
    elif st.session_state.step == 2:
        st.markdown(f"""
        <div class="step-card">
            <h3 style="margin: 0; font-size: 1.3rem;">🔍 Step 2: Analysis in Progress</h3>
            <p style="margin: 5px 0; font-size: 0.9rem;">Fetching data from OpenAlex...</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Показываем параметры запроса
        st.markdown(f"""
        <div class="filter-stats">
            <strong>Query Parameters:</strong><br>
            Level 1: {st.session_state.level1_input}<br>
            Level 2: {st.session_state.level2_input or '(not specified)'}<br>
            Level 3: {', '.join(st.session_state.level3_input)}<br>
            Years: {', '.join(map(str, st.session_state.years_input))}
        </div>
        """, unsafe_allow_html=True)
        
        # Кнопка возврата
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("← Back to Step 1", key="back_from_step2"):
                st.session_state.step = 1
                st.rerun()
        
        # Прогресс
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(value, message):
            progress_bar.progress(value)
            status_text.text(message)
        
        try:
            # Шаг 1: Level 1 count
            update_progress(0.1, "Getting Level 1 count...")
            st.session_state['level1_count'] = get_total_count(
                st.session_state['level1_input'], None, st.session_state['years_input']
            )
            
            # Шаг 2: Level 2 count (if applicable)
            if st.session_state['level2_input']:
                update_progress(0.2, "Getting Level 2 count...")
                st.session_state['level2_count'] = get_total_count(
                    st.session_state['level1_input'], st.session_state['level2_input'], st.session_state['years_input']
                )
            else:
                st.session_state['level2_count'] = st.session_state['level1_count']
            
            # Шаг 3: Level 3 counts
            update_progress(0.3, "Analyzing Level 3 terms...")
            st.session_state['topic_counts'] = get_topic_counts(
                st.session_state['level1_input'],
                st.session_state['level2_input'],
                st.session_state['level3_input'],
                st.session_state['years_input'],
                lambda p, m: update_progress(0.3 + p*0.2, m)
            )
            
            # Шаг 4: Fetch top works for each level 3 term
            update_progress(0.5, "Fetching top papers...")
            st.session_state['results'] = {}
            
            for i, term in enumerate(st.session_state['level3_input']):
                if st.session_state['topic_counts'][term] == 0:
                    st.session_state['results'][term] = []
                    continue
                
                update_progress(
                    0.5 + (i / len(st.session_state['level3_input'])) * 0.4,
                    f"Fetching papers for: {term}"
                )
                
                works = fetch_top_works(
                    st.session_state['level1_input'],
                    st.session_state['level2_input'],
                    term,
                    st.session_state['years_input'],
                    100,
                    lambda p, m: None
                )
                st.session_state['results'][term] = works
            
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
    # ШАГ 3: РЕЗУЛЬТАТЫ
    # ========================================================================
    
    elif st.session_state.step == 3:
        st.markdown(f"""
        <div class="step-card">
            <h3 style="margin: 0; font-size: 1.3rem;">📊 Step 3: Results</h3>
            <p style="margin: 5px 0; font-size: 0.9rem;">Analysis complete - review the findings</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Навигационные кнопки - back to step 1
        navigation_buttons(show_back=True, show_new=True, back_to_step1=True)
        
        # Статистика
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            create_metric_card("Level 1 Papers", st.session_state.level1_count, "📄")
        
        with col2:
            create_metric_card("After Level 2", st.session_state.level2_count, "🔍")
        
        with col3:
            total_found = sum(len(works) for works in st.session_state.results.values())
            create_metric_card("Top Papers Found", total_found, "🎯")
        
        with col4:
            topics_with_results = sum(1 for v in st.session_state.results.values() if v)
            create_metric_card("Topics with results", topics_with_results, "✅")
        
        st.markdown("---")
        
        # Показываем соотношение найденных статей
        st.markdown(f"""
        <div class="info-message">
            <strong>📊 Topic Distribution Analysis:</strong><br>
            Total papers matching Level 1+2 filters: {st.session_state.level2_count}<br>
            Sum of papers in all sub-topics: {sum(st.session_state.topic_counts.values())}<br>
            <i>Note: Papers containing multiple sub-topic keywords are counted in each category, 
            so the sum may exceed the total.</i>
        </div>
        """, unsafe_allow_html=True)
        
        # Вкладки для разных представлений
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Topic Distribution", "🌳 Tree Diagram", "📋 Papers by Topic", "📥 Export"])
        
        with tab1:
            # График сравнения подтем
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
            
            # Получаем реальные данные по годам для каждой подтемы
            topic_yearly_data = {}
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, term in enumerate(st.session_state.topic_counts.keys()):
                if st.session_state.topic_counts[term] > 0:
                    status_text.text(f"Fetching yearly distribution for: {term}")
                    progress_bar.progress((idx + 1) / len(st.session_state.topic_counts))
                    
                    yearly_data = get_yearly_distribution(
                        st.session_state.level1_input,
                        st.session_state.level2_input,
                        term,
                        st.session_state.years_input
                    )
                    topic_yearly_data[term] = yearly_data
                    time.sleep(0.2)  # Небольшая задержка между запросами
            
            progress_bar.empty()
            status_text.empty()
            
            # Комбинированный график годовых распределений на основе РЕАЛЬНЫХ данных
            if topic_yearly_data:
                st.markdown('<div class="scientific-plot">', unsafe_allow_html=True)
                st.markdown("<h4>Comparative Yearly Distribution Analysis</h4>", unsafe_allow_html=True)
                
                fig_combined = create_combined_yearly_charts(
                    topic_yearly_data,
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
                    • <b>Log scale</b> shows absolute values on logarithmic scale, enabling comparison of vastly different scales
                </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Графики для каждой подтемы с РЕАЛЬНЫМИ данными
            for term in st.session_state.topic_counts.keys():
                total_count = st.session_state.topic_counts.get(term, 0)
                top_works = st.session_state.results.get(term, [])
                
                if total_count > 0 and term in topic_yearly_data:
                    st.markdown(f'<div class="scientific-plot">', unsafe_allow_html=True)
                    st.markdown(f"<h4>Analysis for: {term} (showing distribution of total {total_count} papers)</h4>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig1 = create_yearly_distribution_chart(
                            topic_yearly_data[term], 
                            f"{term}: Publications by Year (all papers)"
                        )
                        if fig1:
                            st.pyplot(fig1)
                            plt.close(fig1)
                    
                    with col2:
                        if top_works:
                            fig2 = create_citation_distribution_chart(
                                top_works, 
                                f"{term}: Citation Distribution (based on top {len(top_works)} papers)"
                            )
                            if fig2:
                                st.pyplot(fig2)
                                plt.close(fig2)
                        else:
                            st.info(f"No citation data available for {term}")
                    
                    st.markdown(f'<p style="font-size:0.8rem; color:#666; text-align:right;">Year distribution based on all {total_count} papers, citation distribution based on top {len(top_works)} most relevant papers</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            # Улучшенная древовидная диаграмма (только Tree Diagram)
            st.markdown('<div class="scientific-plot">', unsafe_allow_html=True)
            st.markdown("<h4>Hierarchical Tree Diagram</h4>", unsafe_allow_html=True)
            
            if any(count > 0 for count in st.session_state.topic_counts.values()):
                st.markdown("**Scientific Tree Visualization** - Hierarchical structure with branch thickness proportional to publication count")
                
                fig_tree = create_tree_visualization(
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
                    • <b>Trunk</b> represents the main research area (Level 1 + Level 2)<br>
                    • <b>Branch thickness</b> is proportional to publications in each sub-topic<br>
                    • <b>Leaf/fruit size</b> shows relative contribution<br>
                    • <b>Branch curvature</b> adds natural, organic feel to the visualization<br>
                    • This diagram visualizes the hierarchical relationship between main topic and sub-fields
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No data available for tree visualization")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab3:
            # Показываем статьи по каждой подтеме
            for term, works in st.session_state.results.items():
                if works:
                    with st.expander(f"📚 {term} - {len(works)} papers"):
                        for i, work in enumerate(works[:10], 1):
                            enriched = enrich_work_data(work)
                            create_result_card(enriched, i, term)
                            
                            if i < len(works[:10]):
                                st.markdown("---")
        
        with tab4:
            st.markdown("### 📥 Export Results")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # CSV экспорт
                csv_data = export_to_csv(st.session_state.results)
                st.download_button(
                    label="📊 Download CSV",
                    data=csv_data,
                    file_name=f"publication_clusters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Excel экспорт
                excel_data = export_to_excel(st.session_state.results)
                st.download_button(
                    label="📈 Download Excel",
                    data=excel_data,
                    file_name=f"publication_clusters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col3:
                # PDF экспорт
                pdf_data = export_to_pdf(
                    st.session_state.results,
                    st.session_state.topic_counts,
                    st.session_state.level1_input,
                    st.session_state.level2_input,
                    st.session_state.years_input
                )
                st.download_button(
                    label="📑 Download PDF Report",
                    data=pdf_data,
                    file_name=f"publication_clusters_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    
    # Футер
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #888; font-size: 0.8rem; margin-top: 1rem;">
        <p>© Publication Clustering | Theme: {colors['name']}</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

