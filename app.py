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
import re
import time
import json
from datetime import datetime, timedelta
from collections import Counter
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
# НАСТРОЙКА СТРАНИЦЫ
# ============================================================================

st.set_page_config(
    page_title="OpenAlex Multi-level Search",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Научный стиль для matplotlib
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
# КАСТОМНЫЕ СТИЛИ (как в CTA Recommender)
# ============================================================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.8rem;
    }
    
    .step-card {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border-radius: 12px;
        padding: 18px;
        border-left: 4px solid #667eea;
        margin-bottom: 15px;
        box-shadow: 0 3px 5px rgba(0, 0, 0, 0.04);
    }
    
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.06);
        border: 1px solid #e0e0e0;
        height: 100%;
        min-height: 90px;
    }
    
    .metric-card h4 {
        font-size: 0.85rem;
        margin: 0 0 8px 0;
        color: #666;
    }
    
    .metric-card .value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #333;
        line-height: 1.2;
    }
    
    .result-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
        border-left: 3px solid #4CAF50;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
    }
    
    .info-message {
        background: linear-gradient(135deg, #2196F315 0%, #0D47A115 100%);
        border-radius: 8px;
        padding: 12px;
        border-left: 3px solid #2196F3;
        font-size: 0.9rem;
        margin: 10px 0;
    }
    
    .warning-message {
        background: linear-gradient(135deg, #FF980015 0%, #EF6C0015 100%);
        border-radius: 8px;
        padding: 12px;
        border-left: 3px solid #FF9800;
        font-size: 0.9rem;
        margin: 10px 0;
    }
    
    .filter-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #dee2e6;
    }
    
    .filter-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #495057;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid #667eea;
    }
    
    .filter-stats {
        background: white;
        border-radius: 8px;
        padding: 12px;
        border: 1px solid #ced4da;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .year-checkbox-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin-bottom: 15px;
    }
    
    .year-checkbox-item {
        background: white;
        border-radius: 6px;
        padding: 10px;
        border: 1px solid #dee2e6;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .year-checkbox-item:hover {
        border-color: #667eea;
        background-color: #f8f9ff;
    }
    
    .year-checkbox-item.selected {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border-color: #667eea;
        color: #667eea;
        font-weight: 600;
    }
    
    .scientific-plot {
        background: white;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #dee2e6;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    .scientific-plot h4 {
        color: #2C3E50;
        font-weight: 600;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 2px solid #667eea;
    }
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
POLITE_POOL_HEADER = {'User-Agent': f'MultiLevel-Search (mailto:{MAILTO})'}

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
    - Простые слова: MOF
    - Фразы в кавычках: "metal-organic frameworks"
    - Логические операторы: AND, OR, NOT
    """
    term = term.strip()
    
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
    
    # Если есть пробелы, но не OR, значит AND (по умолчанию)
    if ' ' in term:
        words = term.split()
        return ' AND '.join(words)
    
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
                <span style="font-weight: 600; color: #667eea; margin-right: 8px;">{topic} #{index}</span>
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
            <a href="{doi_url}" target="_blank" style="color: #2196F3; text-decoration: none; font-size: 0.85rem;">
                🔗 View Article
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
        filters['title_and_abstract.search'] = ' AND '.join(search_parts)
    
    # Фильтр по годам
    if years:
        if len(years) == 1:
            filters['publication_year'] = str(years[0])
        else:
            if len(years) == 2 and years[1] > years[0] + 1:
                filters['publication_year'] = f"{years[0]}-{years[1]}"
            else:
                filters['publication_year'] = '|'.join(map(str, years))
    
    return filters

def build_level3_filter(level3_term: str, base_filters: Dict[str, str]) -> str:
    """Строит фильтр для термина третьего уровня с учетом всех фильтров"""
    filter_parts = []
    
    if 'publication_year' in base_filters:
        filter_parts.append(f"publication_year:{base_filters['publication_year']}")
    
    search_parts = []
    if 'title_and_abstract.search' in base_filters:
        search_parts.append(f"({base_filters['title_and_abstract.search']})")
    
    if level3_term:
        search_parts.append(f"({parse_query_terms(level3_term)})")
    
    if search_parts:
        filter_parts.append(f"title_and_abstract.search:{' AND '.join(search_parts)}")
    
    return ','.join(filter_parts)

def build_count_filter(base_filters: Dict[str, str]) -> str:
    """Строит фильтр только из первых двух уровней"""
    filter_parts = []
    
    if 'publication_year' in base_filters:
        filter_parts.append(f"publication_year:{base_filters['publication_year']}")
    
    if 'title_and_abstract.search' in base_filters:
        filter_parts.append(f"title_and_abstract.search:{base_filters['title_and_abstract.search']}")
    
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
    
    # Цвета
    colors1 = plt.cm.Blues(np.linspace(0.4, 0.8, len(topics)))
    colors2 = plt.cm.Purples(np.linspace(0.4, 0.8, len(topics)))
    
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

def create_yearly_distribution_chart(works: List[Dict], title: str):
    """Создает график распределения по годам"""
    years = [w.get('publication_year') for w in works if w.get('publication_year')]
    if not years:
        return None
    
    year_counts = Counter(years)
    years_sorted = sorted(year_counts.keys())
    counts = [year_counts[y] for y in years_sorted]
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    bars = ax.bar(years_sorted, counts, color='#667eea', edgecolor='black', linewidth=0.5)
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
    n, bins, patches = ax.hist(citations, bins=20, color='#764ba2', 
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
            'bg_color': '#667eea',
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

# ============================================================================
# ОСНОВНОЙ ИНТЕРФЕЙС
# ============================================================================

def main():
    """Главная функция приложения"""
    
    # Заголовок
    st.markdown('<h1 class="main-header">🔬 OpenAlex Multi-level Search</h1>', unsafe_allow_html=True)
    st.markdown("""
    <p style="font-size: 1rem; color: #666; margin-bottom: 1.5rem;">
    Search scientific literature with multi-level filtering and OR support
    </p>
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
    
    # ========================================================================
    # ШАГ 1: ВВОД ТЕРМИНОВ
    # ========================================================================
    
    if st.session_state.step == 1:
        st.markdown("""
        <div class="step-card">
            <h3 style="margin: 0; font-size: 1.3rem;">📥 Step 1: Enter Search Terms</h3>
            <p style="margin: 5px 0; font-size: 0.9rem;">Define your multi-level search query</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Информация о синтаксисе
        st.markdown("""
        <div class="info-message">
            <strong>💡 Search Syntax:</strong><br>
            • Use <b>OR</b> for logical OR (e.g., "MOF OR COF")<br>
            • Use quotes for exact phrases (e.g., "metal-organic frameworks")<br>
            • Multiple words without OR are treated as AND
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Level 1 (required):**")
            level1 = st.text_input(
                "Main term",
                value='"metal-organic frameworks" OR MOF',
                key="level1",
                label_visibility="collapsed"
            )
            
            st.markdown("**Level 2 (optional):**")
            level2 = st.text_input(
                "Secondary term",
                value="",
                key="level2",
                label_visibility="collapsed",
                placeholder="e.g., \"gas storage\" OR adsorption"
            )
        
        with col2:
            st.markdown("**Level 3 terms (one per line):**")
            level3_text = st.text_area(
                "Sub-topics",
                value="MIL\nZIF\nIRMOF\nUiO\nHKUST",
                height=120,
                key="level3",
                label_visibility="collapsed"
            )
        
        # Фильтр по годам
        st.markdown("---")
        st.markdown("**📅 Publication Years:**")
        
        current_year = datetime.now().year
        year_option = st.radio(
            "Year filter type",
            ["Single year", "Range", "Multiple years"],
            horizontal=True,
            key="year_type"
        )
        
        if year_option == "Single year":
            years = [st.slider("Select year", 2000, current_year, current_year)]
        elif year_option == "Range":
            year_range = st.slider("Select range", 2000, current_year, (current_year-5, current_year))
            years = list(range(year_range[0], year_range[1] + 1))
        else:
            years = st.multiselect(
                "Select years",
                list(range(current_year, 2000, -1)),
                default=[current_year-2, current_year-1, current_year]
            )
        
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
                    st.session_state['level1'] = level1.strip()
                    st.session_state['level2'] = level2.strip() or None
                    st.session_state['level3'] = [t.strip() for t in level3_text.split('\n') if t.strip()]
                    st.session_state['years'] = years
                    st.session_state['step'] = 2
                    st.rerun()
    
    # ========================================================================
    # ШАГ 2: АНАЛИЗ
    # ========================================================================
    
    elif st.session_state.step == 2:
        st.markdown("""
        <div class="step-card">
            <h3 style="margin: 0; font-size: 1.3rem;">🔍 Step 2: Analysis in Progress</h3>
            <p style="margin: 5px 0; font-size: 0.9rem;">Fetching data from OpenAlex...</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Показываем параметры запроса
        st.markdown(f"""
        <div class="filter-stats">
            <strong>Query Parameters:</strong><br>
            Level 1: {st.session_state.level1}<br>
            Level 2: {st.session_state.level2 or '(not specified)'}<br>
            Level 3: {', '.join(st.session_state.level3)}<br>
            Years: {', '.join(map(str, st.session_state.years))}
        </div>
        """, unsafe_allow_html=True)
        
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
                st.session_state['level1'], None, st.session_state['years']
            )
            
            # Шаг 2: Level 2 count (if applicable)
            if st.session_state['level2']:
                update_progress(0.2, "Getting Level 2 count...")
                st.session_state['level2_count'] = get_total_count(
                    st.session_state['level1'], st.session_state['level2'], st.session_state['years']
                )
            else:
                st.session_state['level2_count'] = st.session_state['level1_count']
            
            # Шаг 3: Level 3 counts
            update_progress(0.3, "Analyzing Level 3 terms...")
            st.session_state['topic_counts'] = get_topic_counts(
                st.session_state['level1'],
                st.session_state['level2'],
                st.session_state['level3'],
                st.session_state['years'],
                lambda p, m: update_progress(0.3 + p*0.2, m)
            )
            
            # Шаг 4: Fetch top works for each level 3 term
            update_progress(0.5, "Fetching top papers...")
            st.session_state['results'] = {}
            
            for i, term in enumerate(st.session_state['level3']):
                if st.session_state['topic_counts'][term] == 0:
                    st.session_state['results'][term] = []
                    continue
                
                update_progress(
                    0.5 + (i / len(st.session_state['level3'])) * 0.4,
                    f"Fetching papers for: {term}"
                )
                
                works = fetch_top_works(
                    st.session_state['level1'],
                    st.session_state['level2'],
                    term,
                    st.session_state['years'],
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
        st.markdown("""
        <div class="step-card">
            <h3 style="margin: 0; font-size: 1.3rem;">📊 Step 3: Results</h3>
            <p style="margin: 5px 0; font-size: 0.9rem;">Analysis complete - review the findings</p>
        </div>
        """, unsafe_allow_html=True)
        
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
        
        # Проверка на пересечение тем
        total_percentage = sum(st.session_state.topic_counts.values()) / st.session_state.level2_count * 100
        if total_percentage > 105:  # Допускаем небольшую погрешность
            st.markdown("""
            <div class="warning-message">
                <strong>⚠️ Note:</strong> Some papers may be counted in multiple sub-topics
                (e.g., a paper containing multiple keywords in title/abstract)
            </div>
            """, unsafe_allow_html=True)
        
        # Вкладки для разных представлений
        tab1, tab2, tab3 = st.tabs(["📈 Visualizations", "📋 Papers by Topic", "📥 Export"])
        
        with tab1:
            # График сравнения подтем
            if st.session_state.topic_counts:
                st.markdown('<div class="scientific-plot">', unsafe_allow_html=True)
                st.markdown("<h4>Sub-topic Distribution</h4>", unsafe_allow_html=True)
                
                fig = create_scientific_bar_chart(
                    st.session_state.topic_counts,
                    st.session_state.level2_count,
                    f"Publications by Sub-topic ({', '.join(map(str, st.session_state.years[:3]))})"
                )
                if fig:
                    st.pyplot(fig)
                    plt.close(fig)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Графики для каждой подтемы
            for term, works in st.session_state.results.items():
                if works:
                    st.markdown(f'<div class="scientific-plot">', unsafe_allow_html=True)
                    st.markdown(f"<h4>Analysis for: {term}</h4>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig1 = create_yearly_distribution_chart(works, f"{term}: Publications by Year")
                        if fig1:
                            st.pyplot(fig1)
                            plt.close(fig1)
                    
                    with col2:
                        fig2 = create_citation_distribution_chart(works, f"{term}: Citation Distribution")
                        if fig2:
                            st.pyplot(fig2)
                            plt.close(fig2)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            # Показываем статьи по каждой подтеме
            for term, works in st.session_state.results.items():
                if works:
                    with st.expander(f"📚 {term} - {len(works)} papers"):
                        for i, work in enumerate(works[:10], 1):
                            enriched = enrich_work_data(work)
                            create_result_card(enriched, i, term)
                            
                            if i < len(works[:10]):
                                st.markdown("---")
        
        with tab3:
            st.markdown("### 📥 Export Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # CSV экспорт
                csv_data = export_to_csv(st.session_state.results)
                st.download_button(
                    label="📊 Download CSV",
                    data=csv_data,
                    file_name=f"openalex_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Excel экспорт
                excel_data = export_to_excel(st.session_state.results)
                st.download_button(
                    label="📈 Download Excel",
                    data=excel_data,
                    file_name=f"openalex_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        # Кнопка нового поиска
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 New Search", use_container_width=True):
                # Очищаем сессию
                for key in ['step', 'results', 'topic_counts', 'level1_count', 'level2_count',
                           'level1', 'level2', 'level3', 'years']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.session_state.step = 1
                st.rerun()
    
    # Футер
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888; font-size: 0.8rem; margin-top: 1rem;">
        <p>© OpenAlex Multi-level Search | Data from OpenAlex API</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()





