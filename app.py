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

# PDF экспорт
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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

# ============================================================================
# НАУЧНЫЙ СТИЛЬ ДЛЯ ГРАФИКОВ (НЕ ЗАВИСИТ ОТ ИНТЕРФЕЙСА)
# ============================================================================

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

def expand_wildcard(term: str) -> str:
    """
    Расширяет wildcard запросы вида electro* в OR комбинацию
    """
    if '*' not in term:
        return term
    
    # Словарь часто используемых расширений для научных терминов
    expansions = {
        'electroly*': 'electrolyte OR electrolysis OR electrolyzer OR electrolytic OR electrolytical',
        'cataly*': 'catalyst OR catalysis OR catalytic OR catalyzed',
        'polymer*': 'polymer OR polymers OR polymeric OR polymerization',
        'synthes*': 'synthesis OR synthetic OR synthesized OR synthesizing',
        'spectro*': 'spectroscopy OR spectrometric OR spectrophotometry OR spectra',
        'chromato*': 'chromatography OR chromatographic OR chromatogram',
        'thermo*': 'thermodynamics OR thermodynamic OR thermal OR thermochemical',
        'photo*': 'photo OR photos OR photochemical OR photocatalytic OR photoelectric',
        'electro*': 'electro OR electrochemical OR electrochemistry OR electrode OR electrolyte',
        'nano*': 'nano OR nanoparticles OR nanomaterial OR nanostructure OR nanotechnology',
        'bio*': 'bio OR biological OR biochemistry OR biomedical OR biotechnology',
        'chem*': 'chemistry OR chemical OR chemometrics',
        'phys*': 'physics OR physical OR physicochemical',
        'analy*': 'analysis OR analytical OR analyze OR analyzing',
        'mater*': 'material OR materials OR material science',
        'organ*': 'organic OR organometallic OR organism',
        'inorg*': 'inorganic OR inorganics',
        'metal*': 'metal OR metals OR metallic OR metallurgy',
        'crystal*': 'crystal OR crystals OR crystalline OR crystallization',
        'molec*': 'molecular OR molecule OR molecules',
        'atom*': 'atomic OR atom OR atoms',
        'quant*': 'quantum OR quantitative',
        'comput*': 'computational OR computer OR computing OR computation',
        'simul*': 'simulation OR simulate OR simulated',
        'model*': 'model OR modeling OR models',
        'experim*': 'experimental OR experiment OR experiments',
        'theor*': 'theoretical OR theory',
        'appli*': 'application OR applications OR applied',
        'techni*': 'technique OR techniques OR technical',
        'method*': 'method OR methods OR methodology',
        'process*': 'process OR processes OR processing',
        'react*': 'reaction OR reactions OR reactive OR reactivity',
        'kinet*': 'kinetics OR kinetic',
        'mechan*': 'mechanism OR mechanisms OR mechanistic',
        'struct*': 'structure OR structures OR structural',
        'proper*': 'property OR properties',
        'charac*': 'characterization OR characterize OR characteristic',
        'funct*': 'functional OR function OR functionality',
        'surface*': 'surface OR surfaces OR interfacial',
        'interfac*': 'interface OR interfaces OR interfacial',
        'adsorp*': 'adsorption OR adsorbent OR adsorbed',
        'absorp*': 'absorption OR absorbent OR absorbed',
        'diffus*': 'diffusion OR diffusive',
        'transp*': 'transport OR transportation',
        'conduc*': 'conductivity OR conduction OR conductive',
        'resist*': 'resistance OR resistive',
        'capac*': 'capacitance OR capacitor OR capacitive',
        'imped*': 'impedance OR impedimetric',
        'voltam*': 'voltammetry OR voltammetric',
        'ampero*': 'amperometry OR amperometric',
        'potent*': 'potentiometry OR potentiometric OR potential',
        'sensor*': 'sensor OR sensors OR sensing',
        'detect*': 'detection OR detector OR detecting',
        'measure*': 'measurement OR measuring OR measure',
        'calibr*': 'calibration OR calibrated',
        'valid*': 'validation OR validate OR valid',
        'optim*': 'optimization OR optimize OR optimal',
        'design*': 'design OR designing',
        'develop*': 'development OR developing OR developed',
        'fabric*': 'fabrication OR fabricate OR fabricated',
        'prepar*': 'preparation OR prepare OR prepared',
        'synthe*': 'synthesis OR synthesize OR synthesized',
        'produc*': 'production OR produce OR produced',
        'sourc*': 'source OR sources',
        'energy*': 'energy OR energies',
        'power*': 'power OR powered',
        'fuel*': 'fuel OR fuels',
        'batter*': 'battery OR batteries',
        'cell*': 'cell OR cells',
        'device*': 'device OR devices',
        'system*': 'system OR systems',
        'array*': 'array OR arrays',
        'network*': 'network OR networks',
        'compos*': 'composite OR composites',
        'hybrid*': 'hybrid OR hybrids',
        'alloy*': 'alloy OR alloys',
        'oxide*': 'oxide OR oxides',
        'sulfi*': 'sulfide OR sulfides',
        'nitri*': 'nitride OR nitrides',
        'carbi*': 'carbide OR carbides',
        'phosph*': 'phosphate OR phosphide OR phosphorus',
        'halid*': 'halide OR halides',
        'chl*': 'chloride OR chlorine OR chloro',
        'fluor*': 'fluoride OR fluorine OR fluoro',
        'brom*': 'bromide OR bromine OR bromo',
        'iod*': 'iodide OR iodine OR iodo'
    }
    
    # Проверяем точное совпадение с известными расширениями
    if term.lower() in expansions:
        return expansions[term.lower()]
    
    # Если нет точного совпадения, возвращаем исходный термин
    # OpenAlex поддерживает wildcard поиск через *
    return term

def parse_query_terms(term: str) -> str:
    """
    Парсит поисковый термин для OpenAlex API.
    Поддерживает:
    - Простые слова
    - Фразы в кавычках
    - Логические операторы: AND, OR, NOT
    - Wildcard запросы (electroly*)
    """
    term = term.strip()
    
    # Проверяем на wildcard
    if '*' in term:
        term = expand_wildcard(term)
    
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

def navigation_buttons(show_back: bool = True, show_new: bool = True):
    """Отображает кнопки навигации"""
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if show_back and st.session_state.step > 1:
            if st.button("← Back", key="back_btn", use_container_width=True):
                st.session_state.step -= 1
                st.rerun()
    
    with col2:
        if show_new:
            if st.button("🔄 New Search", key="new_btn", use_container_width=True):
                # Очищаем сессию
                for key in ['step', 'results', 'topic_counts', 'level1_count', 'level2_count',
                           'level1_input', 'level2_input', 'level3_input', 'years_input']:
                    if key in st.session_state:
                        del st.session_state[key]
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
        parsed = parse_query_terms(level1_term)
        search_parts.append(parsed)
    
    # Уровень 2 - дополнительный термин (опционально)
    if level2_term:
        parsed = parse_query_terms(level2_term)
        search_parts.append(parsed)
    
    # Объединяем все части с AND
    if search_parts:
        # Используем default.search вместо title_and_abstract.search для лучших результатов
        filters['default.search'] = ' AND '.join(search_parts)
    
    # Фильтр по годам
    if years:
        if len(years) == 1:
            filters['publication_year'] = str(years[0])
        else:
            # Для диапазона используем формат from:to
            filters['publication_year'] = f"{min(years)}-{max(years)}"
    
    return filters

def build_level3_filter(level3_term: str, base_filters: Dict[str, str]) -> str:
    """Строит фильтр для термина третьего уровня с учетом всех фильтров"""
    filter_parts = []
    
    if 'publication_year' in base_filters:
        filter_parts.append(f"publication_year:{base_filters['publication_year']}")
    
    # Собираем поисковые части
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

def fetch_yearly_distribution(level1_term: str, level2_term: Optional[str],
                             level3_term: str, years: Optional[List[int]]) -> Dict[int, int]:
    """
    Получает распределение по годам для конкретного термина третьего уровня
    Используется для синхронизации данных между разными графиками
    """
    base_filters = build_search_filter(level1_term, level2_term, years=years)
    filter_str = build_level3_filter(level3_term, base_filters)
    
    yearly_counts = {}
    
    # Для каждого года из запрошенного диапазона получаем количество
    for year in years:
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
    
    # Цвета в научном стиле (оттенки серого для печати)
    colors1 = plt.cm.Greys(np.linspace(0.3, 0.7, len(topics)))
    colors2 = plt.cm.Greys(np.linspace(0.4, 0.8, len(topics)))
    
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
    
    bars = ax.bar(years_sorted, counts, color='#666666', edgecolor='black', linewidth=0.5)
    ax.set_xlabel('Publication Year', fontsize=10, fontweight='bold')
    ax.set_ylabel('Number of Publications', fontsize=10, fontweight='bold')
    ax.set_title(title, fontsize=11, fontweight='bold', pad=10)
    ax.tick_params(axis='both', which='major', labelsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Добавляем значения на бары
    for bar in bars:
        height = bar.get_height()
        if height > 0:  # Показываем только для ненулевых значений
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    return fig

def create_citation_distribution_chart(works: List[Dict], title: str):
    """Создает график распределения цитирований"""
    citations = [w.get('cited_by_count', 0) for w in works if w.get('cited_by_count', 0) is not None]
    if not citations:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Создаем гистограмму
    n, bins, patches = ax.hist(citations, bins=20, color='#666666', 
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
                                  years_input: List[int], 
                                  level2_term: Optional[str] = None):
    """
    Создает комбинированный график с годовыми распределениями для всех подтем
    Использует реальные данные, полученные через fetch_yearly_distribution
    """
    # Создаем фигуру с тремя подграфиками
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Определяем все доступные годы
    years = sorted(set(years_input))
    topics = [t for t in topic_yearly_data.keys()]
    
    # Подграфик 1: Со смещением (stacked)
    ax = axes[0]
    bottom = np.zeros(len(years))
    
    # Используем оттенки серого для печати
    gray_colors = [plt.cm.Greys(0.3 + i*0.1) for i in range(len(topics))]
    
    for idx, topic in enumerate(topics):
        counts = [topic_yearly_data[topic].get(year, 0) for year in years]
        ax.bar(years, counts, bottom=bottom, label=topic, 
               color=gray_colors[idx], edgecolor='black', linewidth=0.5)
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
    
    for idx, topic in enumerate(topics):
        counts = np.array([topic_yearly_data[topic].get(year, 0) for year in years])
        if counts.max() > 0:
            normalized = counts / counts.max()
            ax.plot(years, normalized, marker='o', linewidth=1.5, markersize=4, 
                   color=gray_colors[idx], label=topic)
    
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
    for topic in topics:
        counts = [topic_yearly_data[topic].get(year, 0) for year in years]
        all_counts.extend(counts)
    max_count = max(all_counts) if all_counts else 1
    
    for idx, topic in enumerate(topics):
        counts = [topic_yearly_data[topic].get(year, 0) for year in years]
        if max(counts) > 0:
            # Используем абсолютные значения, но для log(0) ставим 0.1 (ниже минимального видимого значения)
            counts_log = [c if c > 0 else 0.1 for c in counts]
            ax.semilogy(years, counts_log, marker='s', linewidth=1.5, markersize=4, 
                       color=gray_colors[idx], label=topic)
    
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
    Создает древовидную визуализацию в научном стиле с толщиной веток, 
    пропорциональной количеству публикаций
    """
    topics = [t for t, count in topic_counts.items() if count > 0]
    if not topics:
        return None
    
    # Сортируем темы по убыванию
    topics_sorted = sorted(topics, key=lambda x: topic_counts[x], reverse=True)
    counts = [topic_counts[t] for t in topics_sorted]
    max_count = max(counts) if counts else 1
    total_count = sum(counts)
    
    # Создаем фигуру с научным стилем
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Настройки для научного стиля
    ax.set_facecolor('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Рисуем корневую систему
    # Главный ствол - более реалистичный
    from matplotlib.patches import Polygon
    
    # Координаты для ствола (трапеция для реалистичности)
    trunk_width = 0.15 + 0.1 * (total_count / 10000)  # Ширина зависит от общего количества
    trunk_points = [
        [-trunk_width/2, 0],
        [trunk_width/2, 0],
        [trunk_width/3, 1],
        [-trunk_width/3, 1]
    ]
    trunk = Polygon(trunk_points, closed=True, facecolor='#555555', edgecolor='black', linewidth=1, alpha=0.8)
    ax.add_patch(trunk)
    
    # Добавляем текстуру коры (линии)
    for y in np.linspace(0.1, 0.9, 8):
        ax.plot([-trunk_width/4, trunk_width/4], [y, y], color='black', linewidth=0.3, alpha=0.3)
    
    # Добавляем метку корня
    root_label = level1_term
    if level2_term:
        root_label += f"\n+ {level2_term}"
    ax.text(0, 0.5, root_label, ha='center', va='center', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor='white', edgecolor='black', linewidth=1))
    
    # Рисуем ветви для каждой подтемы
    n_topics = len(topics_sorted)
    
    # Распределяем ветви по кругу для более реалистичного вида
    angles = np.linspace(-np.pi/3, np.pi/3, n_topics)
    
    for i, (topic, count) in enumerate(zip(topics_sorted, counts)):
        # Нормализованная толщина ветки (от 1 до 6)
        branch_width = 1 + 5 * (count / max_count)
        
        # Угол ветки
        angle = angles[i]
        
        # Длина ветки (пропорциональна количеству)
        branch_length = 0.8 + 0.4 * (count / max_count)
        
        # Начальная точка на стволе
        x0 = 0.2 * np.sin(angle)
        y0 = 0.7
        
        # Точка изгиба
        x_mid = x0 + branch_length * 0.3 * np.cos(angle)
        y_mid = y0 + branch_length * 0.4
        
        # Конечная точка
        x_end = x0 + branch_length * np.cos(angle)
        y_end = y0 + branch_length * 0.8
        
        # Рисуем ветку с градиентом толщины
        from matplotlib.collections import LineCollection
        from matplotlib.path import Path
        
        # Создаем изогнутую ветку
        t = np.linspace(0, 1, 20)
        x_branch = x0 + branch_length * t * np.cos(angle) + 0.1 * np.sin(t * np.pi)
        y_branch = y0 + branch_length * t * 0.8
        
        # Толщина ветки уменьшается к концу
        widths = np.linspace(branch_width, branch_width * 0.4, len(x_branch))
        
        # Рисуем ветку как набор сегментов с переменной толщиной
        points = np.array([x_branch, y_branch]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        
        lc = LineCollection(segments, linewidths=widths[:-1], color='#666666', alpha=0.8)
        ax.add_collection(lc)
        
        # Добавляем листочки/плоды (кружки, размер пропорционален количеству)
        leaf_size = 50 + 200 * (count / max_count)
        
        # Используем разные маркеры для разных тем
        markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
        marker = markers[i % len(markers)]
        
        ax.scatter(x_end, y_end, s=leaf_size, c='white', marker=marker,
                  edgecolor='black', linewidth=1.5, alpha=0.9, zorder=5)
        
        # Добавляем вторую точку для объема
        ax.scatter(x_end, y_end, s=leaf_size*0.3, c='#333333', marker=marker,
                  edgecolor='none', alpha=0.5, zorder=6)
        
        # Добавляем метку с количеством
        ax.text(x_end + 0.15, y_end, f"{topic}\n(n={count:,})", 
                va='center', fontsize=9, 
                bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='black', linewidth=0.8))
        
        # Добавляем небольшие дополнительные веточки для больших тем
        if count > max_count * 0.3:
            for j in range(2):
                small_angle = angle + 0.1 * (-1)**j
                small_x = x_end - 0.05
                small_y = y_end - 0.05
                small_x_end = small_x + 0.2 * np.cos(small_angle)
                small_y_end = small_y + 0.1
                ax.plot([small_x, small_x_end], [small_y, small_y_end], 
                       color='#666666', linewidth=1, alpha=0.4)
                ax.scatter(small_x_end, small_y_end, s=10, c='white', 
                          edgecolor='black', linewidth=0.5, alpha=0.6)
    
    # Добавляем масштабный бар
    scale_bar_y = -0.1
    ax.plot([-0.5, 0.5], [scale_bar_y, scale_bar_y], 'k-', linewidth=1)
    ax.text(0, scale_bar_y - 0.05, f'Scale: 1.0 (relative units)', 
            ha='center', va='top', fontsize=8, style='italic')
    
    # Настройки графика
    ax.set_xlim(-1.2, 2.0)
    ax.set_ylim(-0.2, 2.0)
    ax.set_aspect('equal')
    
    plt.title('Topic Tree: Hierarchical Structure\n(Branch thickness ∝ publication count)', 
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

def generate_pdf(data: Dict[str, List[Dict]], topic_counts: Dict[str, int], 
                 level1_term: str, level2_term: Optional[str], 
                 level3_terms: List[str], years_input: List[int]) -> bytes:
    """Генерация PDF файла с результатами анализа"""
    
    # Вспомогательная функция для очистки текста
    def clean_text(text):
        if not text:
            return ""
        # Заменяем HTML сущности и теги
        text = re.sub(r'<[^>]+>', '', text)  # Удаляем HTML теги
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
    
    # Стиль для названия статьи
    paper_title_style = ParagraphStyle(
        'CustomPaperTitle',
        parent=styles['Heading4'],
        fontSize=11,
        textColor=colors.HexColor('#2980B9'),
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
        fontSize=9,
        textColor=colors.blue,
        spaceAfter=2,
        alignment=TA_LEFT,
        fontName='Helvetica',
        underline=True
    )
    
    story = []
    
    # ========== ЗАГОЛОВОЧНАЯ СТРАНИЦА ==========
    
    story.append(Spacer(1, 1*cm))
    
    # Заголовок
    story.append(Paragraph("Publication Clustering Report", title_style))
    story.append(Paragraph("Multi-Level Literature Analysis", subtitle_style))
    story.append(Spacer(1, 0.8*cm))
    
    # Информация о запросе
    query_info = f"Level 1: {level1_term}"
    if level2_term:
        query_info += f"<br/>Level 2: {level2_term}"
    query_info += f"<br/>Level 3 terms: {', '.join(level3_terms)}"
    query_info += f"<br/>Years: {min(years_input)}-{max(years_input)}"
    
    story.append(Paragraph(query_info, topic_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Мета-информация
    current_date = datetime.now().strftime('%B %d, %Y at %H:%M')
    story.append(Paragraph(f"Generated on {current_date}", meta_style))
    
    # Статистика
    total_papers = sum(topic_counts.values())
    topics_with_results = sum(1 for v in data.values() if v)
    top_papers_found = sum(len(works) for works in data.values())
    
    stats_text = f"""
    Total papers matching criteria: {total_papers:,} | 
    Topics with results: {topics_with_results} | 
    Top papers analyzed: {top_papers_found}
    """
    story.append(Paragraph(stats_text, meta_style))
    
    story.append(Spacer(1, 1.5*cm))
    
    # Копирайт информация
    story.append(Paragraph("© Publication Clustering", footer_style))
    
    # Разделитель страниц
    story.append(PageBreak())
    
    # ========== ТАБЛИЦА СОДЕРЖАНИЯ ==========
    story.append(Paragraph("TABLE OF CONTENTS", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Создаем оглавление
    toc_items = [
        "1. Topic Distribution Summary",
        "2. Detailed Topic Analysis",
        "3. Papers by Topic"
    ]
    
    for item in toc_items:
        story.append(Paragraph(f"• {item}", details_style))
    
    story.append(PageBreak())
    
    # ========== РАСПРЕДЕЛЕНИЕ ПО ТЕМАМ ==========
    story.append(Paragraph("1. TOPIC DISTRIBUTION SUMMARY", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Таблица с распределением
    table_data = [["Topic", "Number of Papers", "Percentage"]]
    total = sum(topic_counts.values())
    
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            percentage = (count / total * 100) if total > 0 else 0
            table_data.append([clean_text(topic), str(count), f"{percentage:.1f}%"])
    
    if len(table_data) > 1:
        topic_table = Table(table_data, colWidths=[doc.width*0.5, doc.width*0.2, doc.width*0.2])
        topic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
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
        story.append(topic_table)
    
    story.append(PageBreak())
    
    # ========== ДЕТАЛЬНЫЙ АНАЛИЗ ПО ТЕМАМ ==========
    story.append(Paragraph("2. DETAILED TOPIC ANALYSIS", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0 and topic in data and data[topic]:
            story.append(Paragraph(f"Topic: {clean_text(topic)}", subtitle_style))
            story.append(Paragraph(f"Total papers: {count:,}", meta_style))
            story.append(Paragraph(f"Top papers analyzed: {len(data[topic])}", meta_style))
            
            # Статистика по цитированиям для этой темы
            citations = [w.get('cited_by_count', 0) for w in data[topic]]
            if citations:
                avg_cit = np.mean(citations)
                median_cit = np.median(citations)
                story.append(Paragraph(f"Average citations: {avg_cit:.1f}", details_style))
                story.append(Paragraph(f"Median citations: {median_cit:.1f}", details_style))
            
            story.append(Spacer(1, 0.3*cm))
            
            # Разделитель между темами
            story.append(Paragraph("─" * 50, separator_style))
    
    story.append(PageBreak())
    
    # ========== СТАТЬИ ПО ТЕМАМ ==========
    story.append(Paragraph("3. PAPERS BY TOPIC", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    for topic, works in data.items():
        if works:
            story.append(Paragraph(f"Topic: {clean_text(topic)}", subtitle_style))
            story.append(Spacer(1, 0.2*cm))
            
            for i, work in enumerate(works[:20], 1):  # Ограничиваем 20 статьями на тему
                # Заголовок статьи
                title = clean_text(work.get('title', 'No title available'))
                story.append(Paragraph(f"{i}. {title}", paper_title_style))
                
                # Авторы
                authors = work.get('authors', [])
                if authors:
                    authors_text = ', '.join(authors[:3])
                    if len(authors) > 3:
                        authors_text += f' et al. ({len(authors)} authors)'
                    story.append(Paragraph(f"<b>Authors:</b> {clean_text(authors_text)}", authors_style))
                
                # Основные метрики
                citations = work.get('cited_by_count', 0)
                year = work.get('publication_year', 'N/A')
                relevance = work.get('relevance_score', 0)
                journal = clean_text(work.get('journal', 'N/A')[:40])
                
                metrics_text = f"""
                <b>Citations:</b> {citations} | 
                <b>Year:</b> {year} | 
                <b>Relevance Score:</b> {relevance:.2f} | 
                <b>Journal:</b> {journal} | 
                <b>Open Access:</b> {'Yes' if work.get('is_oa') else 'No'}
                """
                story.append(Paragraph(metrics_text, metrics_style))
                
                # DOI и ссылка
                doi_url = work.get('doi_url', '')
                if doi_url:
                    story.append(Paragraph(f"<b>Link:</b> {doi_url}", link_style))
                
                # Разделитель между статьями
                if i < min(20, len(works)):
                    story.append(Spacer(1, 0.2*cm))
                    story.append(Paragraph("─" * 30, separator_style))
                    story.append(Spacer(1, 0.2*cm))
            
            # Разделитель между темами
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph("=" * 50, separator_style))
            story.append(Spacer(1, 0.5*cm))
    
    # ========== ЗАКЛЮЧЕНИЕ ==========
    story.append(PageBreak())
    story.append(Paragraph("CONCLUSION", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Рекомендации на основе анализа
    conclusions = [
        f"This report analyzed {sum(len(works) for works in data.values())} top papers across {len([t for t, c in topic_counts.items() if c > 0])} sub-topics.",
        f"The most productive sub-topic is: {max(topic_counts.items(), key=lambda x: x[1])[0] if topic_counts else 'N/A'}",
        "Consider exploring papers with high relevance scores for literature reviews.",
        "Papers with low citation counts may represent emerging research directions."
    ]
    
    for conclusion in conclusions:
        story.append(Paragraph(f"• {clean_text(conclusion)}", details_style))
    
    story.append(Spacer(1, 1*cm))
    
    # Заключительные замечания
    story.append(Paragraph("FINAL NOTES", subtitle_style))
    final_notes = [
        "This report was generated automatically by Publication Clustering.",
        "All data is sourced from OpenAlex API and is subject to their terms of use.",
        "For the most current data, please visit the original sources via the provided DOIs.",
        "Citation counts are as of the report generation date and may change over time."
    ]
    
    for note in final_notes:
        story.append(Paragraph(f"• {clean_text(note)}", details_style))
    
    # Нижний колонтитул на последней странице
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("© Publication Clustering", footer_style))
    story.append(Paragraph(f"Report ID: {hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}", 
                         ParagraphStyle(
                             'ReportID',
                             parent=styles['Normal'],
                             fontSize=7,
                             textColor=colors.HexColor('#BDC3C7'),
                             alignment=TA_CENTER
                         )))
    
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
    
    # Загружаем сохраненные значения или устанавливаем значения по умолчанию
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
            • Use <b>*</b> for wildcard (e.g., "electroly*" matches electrolyte, electrolysis, electrolyzer)<br>
            • Multiple words without OR are treated as a phrase automatically
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Level 1 (required):**")
            level1 = st.text_input(
                "Main domain (broad research area)",
                value=st.session_state['level1_input'] if st.session_state['level1_input'] else '"metal-organic frameworks" OR MOF',
                key="level1",
                label_visibility="collapsed",
                placeholder="e.g., \"machine learning\" OR \"artificial intelligence\""
            )
            
            st.markdown("**Level 2 (optional):**")
            level2 = st.text_input(
                "Refinement term (narrows down Level 1)",
                value=st.session_state['level2_input'] if st.session_state['level2_input'] else "",
                key="level2",
                label_visibility="collapsed",
                placeholder="e.g., \"neural networks\" OR deep learning"
            )
        
        with col2:
            st.markdown("**Level 3 terms (one per line - these will become your clusters):**")
            default_level3 = '\n'.join(st.session_state['level3_input']) if st.session_state['level3_input'] else "MIL\nZIF\nIRMOF\nUiO\nHKUST"
            level3_text = st.text_area(
                "Sub-topics for classification",
                value=default_level3,
                height=120,
                key="level3",
                label_visibility="collapsed",
                placeholder="Enter each sub-topic on a new line"
            )
        
        # Фильтр по годам
        st.markdown("---")
        st.markdown("**📅 Publication Years:**")
        
        current_year = datetime.now().year
        
        # Опции годов с Range по умолчанию на первом месте
        year_option = st.radio(
            "Year filter type",
            ["Range", "Single year", "Multiple years"],
            horizontal=True,
            key="year_type",
            index=0  # Range по умолчанию
        )
        
        if year_option == "Range":
            # Полный диапазон от 2000 до 2026
            default_range = (2000, 2026)
            year_range = st.slider("Select range", 2000, 2026, default_range)
            years = list(range(year_range[0], year_range[1] + 1))
        elif year_option == "Single year":
            years = [st.slider("Select year", 2000, current_year, current_year)]
        else:  # Multiple years
            years = st.multiselect(
                "Select years",
                list(range(current_year, 2000, -1)),
                default=[current_year-2, current_year-1, current_year]
            )
        
        # Тестовая кнопка для проверки запроса
        with st.expander("🔧 Test Query Before Full Analysis"):
            if st.button("Test Current Query", key="test_query"):
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
                        - Using wildcards (*) for word variations
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
                    # Сохраняем в сессию
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
        
        # Кнопка возврата на Step 1
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
            
            # Шаг 4: Fetch yearly distribution data for each level 3 term
            update_progress(0.5, "Fetching yearly distribution data...")
            st.session_state['yearly_data'] = {}
            
            for i, term in enumerate(st.session_state['level3_input']):
                if st.session_state['topic_counts'][term] == 0:
                    st.session_state['yearly_data'][term] = {}
                    continue
                
                update_progress(
                    0.5 + (i / len(st.session_state['level3_input'])) * 0.2,
                    f"Fetching yearly data for: {term}"
                )
                
                yearly_data = fetch_yearly_distribution(
                    st.session_state['level1_input'],
                    st.session_state['level2_input'],
                    term,
                    st.session_state['years_input']
                )
                st.session_state['yearly_data'][term] = yearly_data
            
            # Шаг 5: Fetch top works for each level 3 term
            update_progress(0.7, "Fetching top papers...")
            st.session_state['results'] = {}
            
            for i, term in enumerate(st.session_state['level3_input']):
                if st.session_state['topic_counts'][term] == 0:
                    st.session_state['results'][term] = []
                    continue
                
                update_progress(
                    0.7 + (i / len(st.session_state['level3_input'])) * 0.3,
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
        
        # Навигационные кнопки
        nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 2])
        
        with nav_col1:
            if st.button("← Back to Step 1", key="back_from_step3"):
                st.session_state.step = 1
                st.rerun()
        
        with nav_col2:
            if st.button("🔄 New Search", key="new_from_step3"):
                # Очищаем сессию
                for key in ['step', 'results', 'topic_counts', 'level1_count', 'level2_count',
                           'level1_input', 'level2_input', 'level3_input', 'years_input', 'yearly_data']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.session_state.step = 1
                st.rerun()
        
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
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Topic Distribution", "🌳 Cluster Graph", "📋 Papers by Topic", "📥 Export"])
        
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
            
            # Комбинированный график годовых распределений с реальными данными
            if hasattr(st.session_state, 'yearly_data') and st.session_state.yearly_data:
                st.markdown('<div class="scientific-plot">', unsafe_allow_html=True)
                st.markdown("<h4>Comparative Yearly Distribution Analysis</h4>", unsafe_allow_html=True)
                
                fig_combined = create_combined_yearly_charts(
                    st.session_state.yearly_data,
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
                    • <b>Log scale</b> shows absolute values on logarithmic scale - 10,000 papers appear as 10⁴, enabling comparison of vastly different scales
                </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Графики для каждой подтемы с реальными данными по годам
            for term in st.session_state.topic_counts.keys():
                total_count = st.session_state.topic_counts.get(term, 0)
                top_works = st.session_state.results.get(term, [])
                
                if total_count > 0:
                    st.markdown(f'<div class="scientific-plot">', unsafe_allow_html=True)
                    st.markdown(f"<h4>Analysis for: {term} (distribution of all {total_count} papers)</h4>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Используем реальные данные по годам из yearly_data
                        if hasattr(st.session_state, 'yearly_data') and term in st.session_state.yearly_data:
                            fig1 = create_yearly_distribution_chart(
                                st.session_state.yearly_data[term], 
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
            # Улучшенная древовидная визуализация
            st.markdown('<div class="scientific-plot">', unsafe_allow_html=True)
            st.markdown("<h4>Topic Relationship Tree</h4>", unsafe_allow_html=True)
            
            if any(count > 0 for count in st.session_state.topic_counts.values()):
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
                    • Trunk thickness represents the overall field size<br>
                    • Branch thickness is proportional to publications in each sub-topic<br>
                    • Node size and marker style show relative contribution<br>
                    • Numbers (n) indicate exact publication counts<br>
                    • Visualizes the hierarchical relationship between main topic and sub-fields in a scientific style
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
                pdf_data = generate_pdf(
                    st.session_state.results,
                    st.session_state.topic_counts,
                    st.session_state.level1_input,
                    st.session_state.level2_input,
                    st.session_state.level3_input,
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
