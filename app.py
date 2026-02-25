import streamlit as st
import requests
import pandas as pd
import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from datetime import datetime, timedelta
import json
import asyncio
import aiohttp
import time
import sqlite3
import os
from pathlib import Path
import hashlib
import joblib
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ratelimit import limits, sleep_and_retry
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from typing import List, Dict, Tuple, Optional, Set, Any, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import io
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Image
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Image
import xlsxwriter
from PIL import Image as PILImage
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки приложения
st.set_page_config(
    page_title="CTA Article Recommender Pro",
    page_icon="logo.jpg",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Кастомные стили (более компактные)
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
    
    .compact-button {
        padding: 8px 16px !important;
        font-size: 0.9rem !important;
        margin: 5px 0 !important;
        border-radius: 6px !important;
    }
    
    .compact-textarea {
        font-size: 0.9rem !important;
        line-height: 1.4 !important;
    }
    
    .compact-select {
        font-size: 0.9rem !important;
    }
    
    .compact-slider {
        margin: 5px 0 !important;
    }
    
    .back-button {
        position: absolute;
        top: 10px;
        left: 10px;
        z-index: 100;
    }
    
    .progress-container {
        background: #f5f5f5;
        border-radius: 8px;
        height: 6px;
        margin: 20px 0;
        overflow: hidden;
    }
    
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 8px;
        transition: width 0.5s ease;
    }
    
    .step-indicator {
        display: flex;
        justify-content: space-between;
        margin: 15px 0;
        font-size: 0.85rem;
        color: #666;
    }
    
    .step-indicator .active {
        color: #667eea;
        font-weight: 600;
    }
    
    .filter-chip {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        margin: 2px;
        background: #e3f2fd;
        border-radius: 16px;
        font-size: 0.8rem;
        color: #1565c0;
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
    
    .topic-card {
        background: white;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        border: 1px solid #e0e0e0;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .topic-card:hover {
        border-color: #667eea;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
    }
    
    .topic-card.selected {
        background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%);
        border-color: #667eea;
        border-left: 4px solid #667eea;
    }
    
    .dataframe th {
        padding: 8px 12px !important;
        font-size: 0.85rem !important;
    }
    
    .dataframe td {
        padding: 6px 12px !important;
        font-size: 0.85rem !important;
    }
    
    .download-buttons {
        display: flex;
        gap: 10px;
        margin: 15px 0;
    }
    
    .download-button {
        flex: 1;
    }
    
    /* Новые стили для фильтров */
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
    
    .citation-checkbox-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    
    .citation-checkbox-item {
        flex: 1;
        text-align: center;
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
    
    /* Новые стили для кластеризации и классификации */
    .cluster-node {
        background: linear-gradient(135deg, #6a11cb15 0%, #2575fc15 100%);
        border-radius: 8px;
        padding: 10px;
        margin: 5px;
        border-left: 3px solid #6a11cb;
        font-size: 0.9rem;
    }
    
    .category-badge {
        display: inline-block;
        padding: 4px 10px;
        margin: 2px;
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
        color: white;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .classification-panel {
        background: #fafafa;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #e0e0e0;
        margin-top: 20px;
    }
    
    .category-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .category-card.blue { border-left-color: #3498db; }
    .category-card.green { border-left-color: #2ecc71; }
    .category-card.orange { border-left-color: #e67e22; }
    .category-card.purple { border-left-color: #9b59b6; }
    .category-card.red { border-left-color: #e74c3c; }
    .category-card.teal { border-left-color: #1abc9c; }
    
    .hierarchy-view {
        font-family: monospace;
        font-size: 0.9rem;
        line-height: 1.8;
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    
    .hierarchy-line {
        color: #6c757d;
    }
    
    .hierarchy-node {
        color: #2c3e50;
        font-weight: 500;
    }
    
    .hierarchy-count {
        background: #667eea;
        color: white;
        padding: 2px 6px;
        border-radius: 12px;
        font-size: 0.75rem;
        margin-left: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Конфигурация OpenAlex API
OPENALEX_BASE_URL = "https://api.openalex.org"
MAILTO = "your-email@example.com"  # Замените на ваш email
POLITE_POOL_HEADER = {'User-Agent': f'CTA-App (mailto:{MAILTO})'}

# Настройки rate limit
RATE_LIMIT_PER_SECOND = 8
BATCH_SIZE = 50
CURSOR_PAGE_SIZE = 200
MAX_WORKERS_ASYNC = 3
MAX_RETRIES = 3
INITIAL_DELAY = 1
MAX_DELAY = 60

# Настройки кэширования
CACHE_DIR = Path("./cache")
CACHE_DB = CACHE_DIR / "openalex_cache.db"
CACHE_EXPIRY_DAYS = 30

# Инициализация кэш директории
CACHE_DIR.mkdir(exist_ok=True)

# Инициализация стоп-слов
nltk.download('stopwords', quiet=True)
COMMON_WORDS = {
    'study', 'studies', 'research', 'paper', 'article', 'review', 'analysis', 'analyses',
    'investigation', 'investigations', 'effect', 'effects', 'property', 'properties',
    'performance', 'behavior', 'behaviour', 'characterization', 'characterisation',
    'synthesis', 'development', 'preparation', 'fabrication', 'application', 'applications',
    'method', 'methods', 'approach', 'approaches', 'result', 'results', 'discussion',
    'conclusion', 'conclusions', 'introduction', 'experimental', 'experiment', 'experiments',
    'measurement', 'measurements', 'observation', 'observations', 'technique', 'techniques',
    'technology', 'technologies', 'material', 'materials', 'system', 'systems',
    'process', 'processes', 'structure', 'structures', 'model', 'models',
    'based', 'using', 'used', 'use', 'high', 'low', 'temperature', 'temperatures',
    'pressure', 'different', 'various', 'several', 'important', 'significant',
    'novel', 'new', 'recent', 'current', 'potential', 'possible', 'first',
    'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth',
    'tenth', 'good', 'better', 'best', 'poor', 'higher', 'lower', 'strong',
    'weak', 'large', 'small', 'great', 'major', 'minor', 'main', 'primary',
    'secondary', 'critical', 'essential', 'general', 'specific', 'special',
    'particular', 'similar', 'different', 'various', 'several', 'multiple',
    'numerous', 'common', 'unusual', 'typical', 'atypical', 'standard',
    'advanced', 'basic', 'fundamental', 'theoretical', 'practical', 'experimental',
    'computational', 'numerical', 'analytical', 'theoretical', 'practical'
}

ALL_STOPWORDS = set(stopwords.words('english')).union(COMMON_WORDS)

# ============================================================================
# НОВЫЙ КЛАСС ДЛЯ ПОСТРОЕНИЯ ЗАПРОСОВ OPENALEX
# ============================================================================

class OpenAlexQueryBuilder:
    """
    Строит сложные запросы для OpenAlex с поддержкой вложенных логических операций
    и многоуровневой фильтрации.
    """
    
    def __init__(self):
        self.base_url = OPENALEX_BASE_URL
        self.filters = []
        self.search_fields = ["title", "abstract"]  # По умолчанию ищем в заголовках и абстрактах
        self.years_filter = None
        self.citation_filter = None
        self.concept_filter = None
        self.author_filter = None
        self.journal_filter = None
        
    def parse_logical_term(self, term: str) -> Dict[str, Any]:
        """
        Парсит термин с логическими операторами AND/OR.
        
        Примеры:
        "SOFC" -> {"type": "simple", "term": "SOFC"}
        "(SOFC and PCFC)" -> {"type": "and", "terms": ["SOFC", "PCFC"]}
        "(SOFC or PCFC)" -> {"type": "or", "terms": ["SOFC", "PCFC"]}
        "(SOFC and (PCFC or SOFC-H))" -> {"type": "and", "terms": ["SOFC", {"type": "or", "terms": ["PCFC", "SOFC-H"]}]}
        """
        term = term.strip()
        
        # Проверяем, есть ли скобки
        if term.startswith('(') and term.endswith(')'):
            # Убираем внешние скобки
            inner = term[1:-1].strip()
            
            # Ищем операторы вне вложенных скобок
            depth = 0
            and_positions = []
            or_positions = []
            
            for i, char in enumerate(inner):
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                elif depth == 0:
                    # Проверяем операторы
                    if inner[i:i+3].lower() == 'and' and (i == 0 or not inner[i-1].isalnum()):
                        and_positions.append(i)
                    elif inner[i:i+2].lower() == 'or' and (i == 0 or not inner[i-1].isalnum()):
                        or_positions.append(i)
            
            # Определяем основной оператор
            if and_positions and (not or_positions or min(and_positions) < min(or_positions)):
                # Разделяем по AND
                terms = []
                last_pos = 0
                for pos in and_positions:
                    part = inner[last_pos:pos].strip()
                    if part:
                        terms.append(self.parse_logical_term(part))
                    last_pos = pos + 3
                last_part = inner[last_pos:].strip()
                if last_part:
                    terms.append(self.parse_logical_term(last_part))
                return {"type": "and", "terms": terms}
            
            elif or_positions:
                # Разделяем по OR
                terms = []
                last_pos = 0
                for pos in or_positions:
                    part = inner[last_pos:pos].strip()
                    if part:
                        terms.append(self.parse_logical_term(part))
                    last_pos = pos + 2
                last_part = inner[last_pos:].strip()
                if last_part:
                    terms.append(self.parse_logical_term(last_part))
                return {"type": "or", "terms": terms}
            
            else:
                # Просто термин в скобках
                return self.parse_logical_term(inner)
        
        else:
            # Простой термин
            # Проверяем, не содержит ли он операторы без скобок
            if ' and ' in term.lower():
                parts = re.split(r'\s+and\s+', term, flags=re.IGNORECASE)
                return {"type": "and", "terms": [self.parse_logical_term(p) for p in parts]}
            elif ' or ' in term.lower():
                parts = re.split(r'\s+or\s+', term, flags=re.IGNORECASE)
                return {"type": "or", "terms": [self.parse_logical_term(p) for p in parts]}
            else:
                return {"type": "simple", "term": term}
    
    def build_search_filter(self, parsed_term: Dict[str, Any], level: int) -> str:
        """
        Строит фильтр поиска для OpenAlex на основе распарсенного терма.
        """
        if parsed_term["type"] == "simple":
            # Для простого терма используем поиск по заголовку и абстракту
            term = parsed_term["term"]
            # Экранируем специальные символы
            term = term.replace('"', '\\"')
            return f"title_and_abstract.search:\"{term}\""
        
        elif parsed_term["type"] == "and":
            # Для AND объединяем через пробел (по умолчанию AND в поиске)
            sub_filters = [self.build_search_filter(t, level) for t in parsed_term["terms"]]
            # Извлекаем значения search из фильтров
            search_terms = []
            for f in sub_filters:
                if f.startswith("title_and_abstract.search:"):
                    term = f.replace("title_and_abstract.search:", "").strip('"')
                    search_terms.append(term)
            
            if search_terms:
                return f"title_and_abstract.search:\"{' '.join(search_terms)}\""
            else:
                return ",".join(sub_filters)
        
        elif parsed_term["type"] == "or":
            # Для OR используем |
            sub_filters = [self.build_search_filter(t, level) for t in parsed_term["terms"]]
            search_terms = []
            for f in sub_filters:
                if f.startswith("title_and_abstract.search:"):
                    term = f.replace("title_and_abstract.search:", "").strip('"')
                    search_terms.append(term)
            
            if search_terms:
                return f"title_and_abstract.search:\"{'|'.join(search_terms)}\""
            else:
                return "|".join(sub_filters)
        
        return ""
    
    def add_level_filter(self, term: str, level: int):
        """
        Добавляет фильтр для определенного уровня иерархии.
        """
        parsed = self.parse_logical_term(term)
        search_filter = self.build_search_filter(parsed, level)
        
        self.filters.append({
            "level": level,
            "original_term": term,
            "parsed_term": parsed,
            "search_filter": search_filter
        })
        
        logger.info(f"Added level {level} filter: {term} -> {search_filter}")
    
    def parse_years(self, years_input: str) -> Optional[str]:
        """
        Парсит строку годов и возвращает OpenAlex year filter.
        
        Примеры:
        "2000,2021" -> "publication_year:2000|2021"
        "2020-2026" -> "publication_year:2020-2026"
        "2021,2023-2025" -> "publication_year:2021|2023-2025"
        """
        if not years_input or years_input.strip() == "":
            return None
        
        parts = years_input.split(',')
        year_filters = []
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # Диапазон годов
                try:
                    start, end = part.split('-')
                    start = int(start.strip())
                    end = int(end.strip())
                    
                    if start <= end and 1900 <= start <= 2100 and 1900 <= end <= 2100:
                        year_filters.append(f"{start}-{end}")
                    else:
                        logger.warning(f"Invalid year range: {part}")
                except ValueError:
                    logger.warning(f"Could not parse year range: {part}")
            else:
                # Одиночный год
                try:
                    year = int(part.strip())
                    if 1900 <= year <= 2100:
                        year_filters.append(str(year))
                    else:
                        logger.warning(f"Year out of range: {year}")
                except ValueError:
                    logger.warning(f"Could not parse year: {part}")
        
        if year_filters:
            self.years_filter = f"publication_year:{'|'.join(year_filters)}"
            return self.years_filter
        
        return None
    
    def parse_citations(self, citations_input: str) -> Optional[str]:
        """
        Парсит строку цитирований.
        
        Примеры:
        "0-10" -> "cited_by_count:0-10"
        "5,10-20" -> "cited_by_count:5|10-20"
        """
        if not citations_input or citations_input.strip() == "":
            return None
        
        parts = citations_input.split(',')
        citation_filters = []
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                try:
                    start, end = part.split('-')
                    start = int(start.strip())
                    end = int(end.strip())
                    
                    if start <= end and 0 <= start and 0 <= end:
                        citation_filters.append(f"{start}-{end}")
                except ValueError:
                    logger.warning(f"Could not parse citation range: {part}")
            else:
                try:
                    count = int(part.strip())
                    if count >= 0:
                        citation_filters.append(str(count))
                except ValueError:
                    logger.warning(f"Could not parse citation count: {part}")
        
        if citation_filters:
            self.citation_filter = f"cited_by_count:{'|'.join(citation_filters)}"
            return self.citation_filter
        
        return None
    
    def build_query(self, level: Optional[int] = None) -> str:
        """
        Собирает все фильтры до указанного уровня в один запрос.
        Если level не указан, использует все уровни.
        """
        filter_parts = []
        
        # Добавляем фильтры уровней
        for f in self.filters:
            if level is None or f["level"] <= level:
                if f["search_filter"]:
                    filter_parts.append(f["search_filter"])
        
        # Добавляем фильтр по годам
        if self.years_filter:
            filter_parts.append(self.years_filter)
        
        # Добавляем фильтр по цитированиям
        if self.citation_filter:
            filter_parts.append(self.citation_filter)
        
        # Добавляем другие фильтры
        if self.concept_filter:
            filter_parts.append(self.concept_filter)
        if self.author_filter:
            filter_parts.append(self.author_filter)
        if self.journal_filter:
            filter_parts.append(self.journal_filter)
        
        if filter_parts:
            return ",".join(filter_parts)
        
        return ""
    
    def get_query_description(self, level: Optional[int] = None) -> str:
        """
        Возвращает человекочитаемое описание запроса.
        """
        lines = ["Query filters:"]
        
        for f in self.filters:
            if level is None or f["level"] <= level:
                lines.append(f"  Level {f['level']}: {f['original_term']}")
        
        if self.years_filter:
            lines.append(f"  Years: {self.years_filter}")
        if self.citation_filter:
            lines.append(f"  Citations: {self.citation_filter}")
        
        return "\n".join(lines)


# ============================================================================
# НОВЫЙ КЛАСС ДЛЯ ИЕРАРХИЧЕСКОЙ КЛАСТЕРИЗАЦИИ
# ============================================================================

class HierarchicalClusterNode:
    """Узел иерархического дерева кластеризации."""
    
    def __init__(self, name: str, level: int, filter_term: str, parent=None):
        self.name = name
        self.level = level
        self.filter_term = filter_term
        self.parent = parent
        self.children = []
        self.works = []  # Список работ в этом узле
        self.work_count = 0
        self.dois = []  # DOI для конечных узлов
        self.metadata = {}  # Дополнительные метаданные
        
    def add_child(self, child_node):
        """Добавляет дочерний узел."""
        child_node.parent = self
        self.children.append(child_node)
        
    def add_work(self, work: dict):
        """Добавляет работу в узел."""
        self.works.append(work)
        self.work_count += 1
        
        # Добавляем DOI в список
        doi = work.get('doi', '')
        if doi:
            doi_clean = doi.replace('https://doi.org/', '')
            if doi_clean not in self.dois:
                self.dois.append(doi_clean)
        
    def get_all_works(self) -> List[dict]:
        """Возвращает все работы из узла и его потомков."""
        all_works = self.works.copy()
        
        for child in self.children:
            all_works.extend(child.get_all_works())
        
        return all_works
    
    def get_leaf_nodes(self) -> List['HierarchicalClusterNode']:
        """Возвращает все листовые узлы."""
        if not self.children:
            return [self]
        
        leaves = []
        for child in self.children:
            leaves.extend(child.get_leaf_nodes())
        
        return leaves
    
    def get_depth(self) -> int:
        """Возвращает глубину поддерева."""
        if not self.children:
            return 1
        
        return 1 + max(child.get_depth() for child in self.children)
    
    def get_node_stats(self) -> Dict[str, Any]:
        """Возвращает статистику по узлу."""
        return {
            "name": self.name,
            "level": self.level,
            "filter_term": self.filter_term,
            "work_count": self.work_count,
            "child_count": len(self.children),
            "doi_count": len(self.dois),
            "has_children": len(self.children) > 0
        }
    
    def to_dict(self) -> Dict:
        """Преобразует узел в словарь для сериализации."""
        return {
            "name": self.name,
            "level": self.level,
            "filter_term": self.filter_term,
            "work_count": self.work_count,
            "dois": self.dois[:10],  # Ограничиваем для больших деревьев
            "children": [child.to_dict() for child in self.children],
            "metadata": self.metadata
        }


class HierarchicalClusterer:
    """
    Создает иерархическую структуру на основе последовательных фильтров.
    """
    
    def __init__(self, query_builder: OpenAlexQueryBuilder = None):
        self.query_builder = query_builder or OpenAlexQueryBuilder()
        self.root = None
        self.nodes_by_level = {}  # level -> list of nodes
        self.all_works_cache = {}  # cache для предотвращения повторных запросов
        self.work_cache = {}  # кэш работ по DOI
        
    def build_tree(self, filters: List[str], years_filter: str = None, 
                  max_works_per_level: int = 5000) -> HierarchicalClusterNode:
        """
        Строит дерево на основе последовательности фильтров.
        
        Args:
            filters: Список фильтров для каждого уровня
            years_filter: Фильтр по годам
            max_works_per_level: Максимальное количество работ на уровень
        
        Returns:
            Корневой узел дерева
        """
        # Создаем корневой узел
        self.root = HierarchicalClusterNode(
            name="Root",
            level=0,
            filter_term=""
        )
        
        self.nodes_by_level = {0: [self.root]}
        
        # Применяем фильтры последовательно
        current_works = None
        
        for level, filter_term in enumerate(filters, 1):
            logger.info(f"Building level {level} with filter: {filter_term}")
            
            # Добавляем фильтр в builder
            self.query_builder.add_level_filter(filter_term, level)
            
            # Получаем работы для этого уровня
            level_works = self._fetch_works_for_level(level, max_works_per_level)
            
            # Создаем узлы для этого уровня
            level_nodes = self._create_level_nodes(level, filter_term, level_works)
            
            # Связываем с предыдущим уровнем
            self._link_with_parents(level, level_nodes, current_works)
            
            self.nodes_by_level[level] = level_nodes
            current_works = level_works
            
            logger.info(f"Level {level}: created {len(level_nodes)} nodes with {len(level_works)} works")
        
        return self.root
    
    def _fetch_works_for_level(self, level: int, max_works: int) -> List[dict]:
        """
        Загружает работы для указанного уровня с использованием кэша.
        """
        # Строим запрос для этого уровня
        query = self.query_builder.build_query(level)
        
        # Проверяем кэш
        cache_key = f"level_{level}_{hashlib.md5(query.encode()).hexdigest()}"
        
        if cache_key in self.all_works_cache:
            logger.info(f"Using cached works for level {level}")
            return self.all_works_cache[cache_key]
        
        # Загружаем из OpenAlex
        works = self._fetch_from_openalex(query, max_works)
        
        # Сохраняем в кэш
        self.all_works_cache[cache_key] = works
        
        return works
    
    def _fetch_from_openalex(self, query: str, max_works: int) -> List[dict]:
        """
        Загружает работы из OpenAlex API.
        """
        all_works = []
        cursor = "*"
        
        with st.spinner(f"Loading works with filter: {query[:50]}..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                while len(all_works) < max_works:
                    params = {
                        "filter": query,
                        "per-page": CURSOR_PAGE_SIZE,
                        "cursor": cursor,
                        "mailto": MAILTO,
                        "sort": "publication_date:desc"
                    }
                    
                    url = f"{OPENALEX_BASE_URL}/works"
                    response = requests.get(url, params=params, headers=POLITE_POOL_HEADER, timeout=60)
                    
                    if response.status_code != 200:
                        logger.error(f"Error fetching works: {response.status_code}")
                        break
                    
                    data = response.json()
                    works = data.get('results', [])
                    
                    if not works:
                        break
                    
                    all_works.extend(works)
                    
                    # Обновляем прогресс
                    progress = min(len(all_works) / max_works, 1.0)
                    progress_bar.progress(progress)
                    status_text.text(f"Loaded {len(all_works)} works...")
                    
                    # Получаем следующий курсор
                    next_cursor = data.get('meta', {}).get('next_cursor')
                    if not next_cursor:
                        break
                    
                    cursor = next_cursor
                    
                    # Небольшая задержка
                    time.sleep(0.1)
                
                progress_bar.empty()
                status_text.empty()
                
            except Exception as e:
                logger.error(f"Error in _fetch_from_openalex: {str(e)}")
                progress_bar.empty()
                status_text.empty()
        
        return all_works[:max_works]
    
    def _create_level_nodes(self, level: int, filter_term: str, 
                           works: List[dict]) -> List[HierarchicalClusterNode]:
        """
        Создает узлы для указанного уровня на основе работ.
        """
        # Группируем работы по какому-либо признаку
        # Например, по основным концепциям или ключевым словам
        nodes = []
        
        # Извлекаем ключевые слова из работ
        keywords_counter = Counter()
        for work in works:
            title = work.get('title', '')
            abstract = work.get('abstract', '')
            text = f"{title} {abstract}".lower()
            
            # Извлекаем ключевые слова
            words = re.findall(r'\b[a-z]{4,}\b', text)
            keywords_counter.update(words)
        
        # Берем топ-10 ключевых слов для создания подузлов
        top_keywords = [kw for kw, _ in keywords_counter.most_common(10)]
        
        for keyword in top_keywords[:5]:  # Ограничиваем количество подузлов
            node = HierarchicalClusterNode(
                name=keyword,
                level=level,
                filter_term=f"{filter_term} + {keyword}"
            )
            
            # Добавляем работы, содержащие это ключевое слово
            for work in works:
                title = work.get('title', '').lower()
                abstract = work.get('abstract', '').lower()
                
                if keyword in title or keyword in abstract:
                    node.add_work(work)
            
            if node.work_count > 0:
                nodes.append(node)
        
        # Если не удалось создать узлы по ключевым словам, создаем один узел
        if not nodes:
            node = HierarchicalClusterNode(
                name=filter_term[:30],
                level=level,
                filter_term=filter_term
            )
            
            for work in works:
                node.add_work(work)
            
            nodes.append(node)
        
        return nodes
    
    def _link_with_parents(self, level: int, current_nodes: List[HierarchicalClusterNode],
                           parent_works: List[dict]):
        """
        Связывает текущие узлы с родительскими на основе parent_works.
        """
        if level == 1:
            # Первый уровень связываем с корнем
            for node in current_nodes:
                self.root.add_child(node)
            return
        
        parent_nodes = self.nodes_by_level.get(level - 1, [])
        
        # Для каждого текущего узла ищем подходящего родителя
        for node in current_nodes:
            # Ищем родителя, который содержит работы этого узла
            for parent in parent_nodes:
                # Проверяем пересечение работ
                node_dois = {w.get('doi', '') for w in node.works if w.get('doi')}
                parent_dois = {w.get('doi', '') for w in parent.works if w.get('doi')}
                
                if node_dois.intersection(parent_dois):
                    parent.add_child(node)
                    break
            else:
                # Если не нашли родителя, прикрепляем к первому
                if parent_nodes:
                    parent_nodes[0].add_child(node)
    
    def get_dendrogram_data(self) -> Dict[str, Any]:
        """
        Возвращает данные для построения дендрограммы в формате, совместимом с Vega-Lite.
        """
        if not self.root:
            return {"nodes": [], "links": []}
        
        nodes = []
        links = []
        
        # Обходим дерево и собираем узлы и связи
        def traverse(node: HierarchicalClusterNode, node_id: str = "root"):
            node_data = {
                "id": node_id,
                "name": node.name,
                "level": node.level,
                "size": node.work_count,
                "doi_count": len(node.dois),
                "has_children": len(node.children) > 0
            }
            nodes.append(node_data)
            
            for i, child in enumerate(node.children):
                child_id = f"{node_id}_{i}"
                links.append({
                    "source": node_id,
                    "target": child_id,
                    "value": child.work_count
                })
                traverse(child, child_id)
        
        traverse(self.root)
        
        return {
            "type": "tree",
            "method": "tidy",
            "size": [{"signal": "width"}, {"signal": "height"}],
            "nodes": nodes,
            "links": links
        }
    
    def get_cluster_statistics(self) -> pd.DataFrame:
        """
        Возвращает статистику по кластерам в виде DataFrame.
        """
        if not self.root:
            return pd.DataFrame()
        
        stats_data = []
        
        def collect_stats(node: HierarchicalClusterNode):
            stats_data.append({
                "Level": node.level,
                "Cluster": node.name,
                "Filter": node.filter_term,
                "Papers": node.work_count,
                "DOIs": len(node.dois),
                "Children": len(node.children)
            })
            
            for child in node.children:
                collect_stats(child)
        
        collect_stats(self.root)
        
        return pd.DataFrame(stats_data)


# ============================================================================
# НОВЫЙ КЛАСС ДЛЯ КЛАССИФИКАЦИИ ПО КАТЕГОРИЯМ
# ============================================================================

class CategoryClassifier:
    """
    Классифицирует найденные работы по предопределенным категориям.
    """
    
    def __init__(self):
        self.categories = {}  # {category_name: category_config}
        self.classification_results = {}
        self.category_colors = [
            "#3498db", "#2ecc71", "#e67e22", "#9b59b6", 
            "#e74c3c", "#1abc9c", "#f39c12", "#d35400",
            "#c0392b", "#16a085", "#27ae60", "#2980b9",
            "#8e44ad", "#2c3e50", "#7f8c8d", "#95a5a6"
        ]
        
    def add_category(self, name: str, terms: List[str], logic: str = "OR", 
                     description: str = "", color: str = None):
        """
        Добавляет категорию для классификации.
        
        Args:
            name: Название категории
            terms: Список поисковых терминов
            logic: Логика объединения терминов ("OR" или "AND")
            description: Описание категории
            color: Цвет для визуализации (если None, будет выбран автоматически)
        """
        # Нормализуем термины
        normalized_terms = [term.strip().lower() for term in terms if term.strip()]
        
        if not normalized_terms:
            logger.warning(f"No valid terms for category {name}")
            return
        
        # Выбираем цвет, если не указан
        if color is None:
            color_idx = len(self.categories) % len(self.category_colors)
            color = self.category_colors[color_idx]
        
        self.categories[name] = {
            "name": name,
            "terms": normalized_terms,
            "logic": logic.upper(),
            "description": description,
            "color": color,
            "query_builder": self._build_category_query(normalized_terms, logic)
        }
        
        logger.info(f"Added category: {name} with {len(normalized_terms)} terms ({logic})")
    
    def _build_category_query(self, terms: List[str], logic: str) -> str:
        """
        Строит поисковый запрос для категории.
        """
        if logic == "AND":
            # Для AND объединяем через пробел
            return f"title_and_abstract.search:\"{' '.join(terms)}\""
        else:
            # Для OR используем |
            return f"title_and_abstract.search:\"{'|'.join(terms)}\""
    
    def classify_works(self, works: List[dict]) -> Dict[str, List[dict]]:
        """
        Распределяет работы по категориям.
        
        Returns:
            Словарь {category_name: список работ}
        """
        if not self.categories:
            logger.warning("No categories defined for classification")
            return {}
        
        # Инициализируем результаты
        classification = {name: [] for name in self.categories.keys()}
        classification["Unclassified"] = []
        
        # Для каждой работы проверяем все категории
        for work in works:
            title = work.get('title', '').lower()
            abstract = work.get('abstract', '').lower()
            text = f"{title} {abstract}"
            
            matched_categories = []
            
            for cat_name, cat_config in self.categories.items():
                terms = cat_config["terms"]
                logic = cat_config["logic"]
                
                if logic == "AND":
                    # Все термины должны присутствовать
                    if all(term in text for term in terms):
                        matched_categories.append(cat_name)
                else:  # OR
                    # Хотя бы один термин должен присутствовать
                    if any(term in text for term in terms):
                        matched_categories.append(cat_name)
            
            # Если работа попала в несколько категорий, добавляем во все
            if matched_categories:
                for cat_name in matched_categories:
                    classification[cat_name].append(work)
            else:
                classification["Unclassified"].append(work)
        
        self.classification_results = classification
        return classification
    
    def get_statistics(self, classification: Dict[str, List[dict]] = None) -> pd.DataFrame:
        """
        Возвращает статистику по категориям.
        """
        if classification is None:
            classification = self.classification_results
        
        if not classification:
            return pd.DataFrame()
        
        stats_data = []
        total_works = sum(len(works) for works in classification.values())
        
        for cat_name, works in classification.items():
            if cat_name == "Unclassified":
                continue
            
            # Собираем статистику
            works_count = len(works)
            percentage = (works_count / total_works * 100) if total_works > 0 else 0
            
            # Статистика по цитированиям
            citations = [w.get('cited_by_count', 0) for w in works]
            avg_citations = np.mean(citations) if citations else 0
            max_citations = max(citations) if citations else 0
            
            # Статистика по годам
            years = [w.get('publication_year', 0) for w in works if w.get('publication_year')]
            recent_count = sum(1 for y in years if y >= datetime.now().year - 2)
            
            # Open Access статистика
            oa_count = sum(1 for w in works if w.get('is_oa'))
            
            # Авторы
            all_authors = []
            for w in works:
                all_authors.extend(w.get('authors', []))
            unique_authors = len(set(all_authors))
            
            stats_data.append({
                "Category": cat_name,
                "Papers": works_count,
                "Percentage": f"{percentage:.1f}%",
                "Avg Citations": f"{avg_citations:.1f}",
                "Max Citations": max_citations,
                "Recent Papers (≤2y)": recent_count,
                "Open Access": oa_count,
                "Unique Authors": unique_authors,
                "Color": self.categories.get(cat_name, {}).get("color", "#95a5a6")
            })
        
        # Добавляем статистику для неклассифицированных
        if "Unclassified" in classification:
            unclassified_works = classification["Unclassified"]
            if unclassified_works:
                stats_data.append({
                    "Category": "Unclassified",
                    "Papers": len(unclassified_works),
                    "Percentage": f"{(len(unclassified_works) / total_works * 100):.1f}%" if total_works > 0 else "0%",
                    "Avg Citations": f"{np.mean([w.get('cited_by_count', 0) for w in unclassified_works]):.1f}",
                    "Max Citations": max([w.get('cited_by_count', 0) for w in unclassified_works]) if unclassified_works else 0,
                    "Recent Papers (≤2y)": sum(1 for w in unclassified_works if w.get('publication_year', 0) >= datetime.now().year - 2),
                    "Open Access": sum(1 for w in unclassified_works if w.get('is_oa')),
                    "Unique Authors": len(set([a for w in unclassified_works for a in w.get('authors', [])])),
                    "Color": "#95a5a6"
                })
        
        return pd.DataFrame(stats_data)
    
    def get_category_details(self, category_name: str) -> Dict[str, Any]:
        """
        Возвращает детальную информацию по категории.
        """
        if category_name not in self.classification_results:
            return {}
        
        works = self.classification_results[category_name]
        
        if not works:
            return {}
        
        # Группировка по годам
        years_distribution = {}
        for work in works:
            year = work.get('publication_year')
            if year:
                years_distribution[year] = years_distribution.get(year, 0) + 1
        
        # Топ журналы
        journals = Counter()
        for work in works:
            journal = work.get('journal_name')
            if journal:
                journals[journal] += 1
        
        # Топ авторы
        authors = Counter()
        for work in works:
            for author in work.get('authors', []):
                authors[author] += 1
        
        # Топ ключевые слова из заголовков
        keywords = Counter()
        for work in works:
            title = work.get('title', '')
            words = re.findall(r'\b[a-zA-Z]{4,}\b', title.lower())
            keywords.update(words)
        
        return {
            "category_name": category_name,
            "total_works": len(works),
            "years_distribution": dict(sorted(years_distribution.items())),
            "top_journals": journals.most_common(10),
            "top_authors": authors.most_common(10),
            "top_keywords": keywords.most_common(20),
            "sample_dois": [w.get('doi') for w in works[:10] if w.get('doi')]
        }
    
    def export_classification(self, format: str = "json") -> Union[str, bytes]:
        """
        Экспортирует результаты классификации.
        """
        if format == "json":
            data = {
                "categories": self.categories,
                "results": {
                    cat: [{"doi": w.get('doi'), "title": w.get('title')} 
                          for w in works[:100]]  # Ограничиваем для больших данных
                    for cat, works in self.classification_results.items()
                },
                "statistics": self.get_statistics().to_dict('records')
            }
            return json.dumps(data, indent=2)
        
        elif format == "csv":
            # Создаем плоскую таблицу
            rows = []
            for cat, works in self.classification_results.items():
                for work in works[:100]:  # Ограничиваем
                    rows.append({
                        "Category": cat,
                        "DOI": work.get('doi'),
                        "Title": work.get('title'),
                        "Year": work.get('publication_year'),
                        "Citations": work.get('cited_by_count'),
                        "Authors": ", ".join(work.get('authors', [])[:3])
                    })
            
            df = pd.DataFrame(rows)
            return df.to_csv(index=False, encoding='utf-8-sig')
        
        return ""


# ============================================================================
# НОВЫЙ МОДУЛЬ ДЛЯ ВИЗУАЛИЗАЦИИ
# ============================================================================

class VisualizationModule:
    """
    Создает различные типы визуализаций для кластеризации и классификации.
    """
    
    @staticmethod
    def create_dendrogram(clusterer: HierarchicalClusterer) -> go.Figure:
        """
        Создает дендрограмму на основе иерархического кластера.
        """
        if not clusterer or not clusterer.root:
            return go.Figure()
        
        # Получаем данные для дендрограммы
        tree_data = clusterer.get_dendrogram_data()
        
        # Создаем граф для позиционирования
        G = nx.DiGraph()
        
        # Добавляем узлы и связи
        for node in tree_data["nodes"]:
            G.add_node(node["id"], **node)
        
        for link in tree_data["links"]:
            G.add_edge(link["source"], link["target"], weight=link["value"])
        
        # Используем иерархическое расположение
        pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
        
        # Создаем фигуру
        fig = go.Figure()
        
        # Добавляем связи
        edge_x = []
        edge_y = []
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        ))
        
        # Добавляем узлы
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        node_color = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            node_data = G.nodes[node]
            node_text.append(
                f"<b>{node_data.get('name', 'Node')}</b><br>"
                f"Level: {node_data.get('level', 0)}<br>"
                f"Papers: {node_data.get('size', 0)}<br>"
                f"DOIs: {node_data.get('doi_count', 0)}"
            )
            
            # Размер узла зависит от количества работ
            size = max(10, min(50, node_data.get('size', 0) / 10))
            node_size.append(size)
            
            # Цвет зависит от уровня
            level = node_data.get('level', 0)
            colors = ['#2c3e50', '#3498db', '#2ecc71', '#e67e22', '#9b59b6', '#e74c3c']
            node_color.append(colors[level % len(colors)])
        
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=[G.nodes[n].get('name', '')[:20] for n in G.nodes()],
            textposition="top center",
            hovertext=node_text,
            hoverinfo='text',
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(color='white', width=1)
            )
        ))
        
        fig.update_layout(
            title="Hierarchical Cluster Dendrogram",
            showlegend=False,
            hovermode='closest',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=600,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    
    @staticmethod
    def create_category_pie_chart(stats_df: pd.DataFrame) -> go.Figure:
        """
        Создает круговую диаграмму распределения по категориям.
        """
        if stats_df.empty:
            return go.Figure()
        
        # Фильтруем только категории с >0 papers
        filtered_df = stats_df[stats_df["Papers"] > 0].copy()
        
        fig = go.Figure(data=[go.Pie(
            labels=filtered_df["Category"],
            values=filtered_df["Papers"],
            hole=0.3,
            marker=dict(
                colors=filtered_df["Color"].tolist() if "Color" in filtered_df.columns else None,
                line=dict(color='white', width=2)
            ),
            textinfo='label+percent',
            textposition='auto',
            hovertemplate="<b>%{label}</b><br>" +
                         "Papers: %{value}<br>" +
                         "Percentage: %{percent}<br>" +
                         "<extra></extra>"
        )])
        
        fig.update_layout(
            title="Paper Distribution by Category",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    
    @staticmethod
    def create_category_bar_chart(stats_df: pd.DataFrame) -> go.Figure:
        """
        Создает столбчатую диаграмму по категориям.
        """
        if stats_df.empty:
            return go.Figure()
        
        # Фильтруем только категории с >0 papers
        filtered_df = stats_df[stats_df["Papers"] > 0].copy()
        
        fig = go.Figure()
        
        # Добавляем столбцы для количества работ
        fig.add_trace(go.Bar(
            name="Papers",
            x=filtered_df["Category"],
            y=filtered_df["Papers"],
            marker_color=filtered_df["Color"].tolist() if "Color" in filtered_df.columns else None,
            text=filtered_df["Papers"],
            textposition='auto',
            hovertemplate="<b>%{x}</b><br>" +
                         "Papers: %{y}<br>" +
                         "Avg Citations: %{customdata[0]}<br>" +
                         "Open Access: %{customdata[1]}<br>" +
                         "<extra></extra>",
            customdata=filtered_df[["Avg Citations", "Open Access"]].values
        ))
        
        fig.update_layout(
            title="Paper Count by Category",
            xaxis_title="Category",
            yaxis_title="Number of Papers",
            height=400,
            margin=dict(l=40, r=20, t=40, b=80),
            xaxis=dict(tickangle=-45)
        )
        
        return fig
    
    @staticmethod
    def create_timeline_chart(classification: Dict[str, List[dict]]) -> go.Figure:
        """
        Создает временную шкалу публикаций по категориям.
        """
        if not classification:
            return go.Figure()
        
        fig = go.Figure()
        
        # Собираем данные по годам для каждой категории
        for cat_name, works in classification.items():
            if cat_name == "Unclassified" or not works:
                continue
            
            years = [w.get('publication_year') for w in works if w.get('publication_year')]
            if not years:
                continue
            
            # Группируем по годам
            year_counts = {}
            for year in years:
                year_counts[year] = year_counts.get(year, 0) + 1
            
            years_sorted = sorted(year_counts.keys())
            counts = [year_counts[y] for y in years_sorted]
            
            fig.add_trace(go.Scatter(
                name=cat_name,
                x=years_sorted,
                y=counts,
                mode='lines+markers',
                stackgroup='one' if len(classification) > 1 else None,
                line=dict(width=2),
                hovertemplate="<b>%{legendtext}</b><br>" +
                             "Year: %{x}<br>" +
                             "Papers: %{y}<br>" +
                             "<extra></extra>"
            ))
        
        fig.update_layout(
            title="Publication Timeline by Category",
            xaxis_title="Year",
            yaxis_title="Number of Papers",
            height=400,
            margin=dict(l=40, r=20, t=40, b=40),
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_citation_boxplot(classification: Dict[str, List[dict]]) -> go.Figure:
        """
        Создает box plot распределения цитирований по категориям.
        """
        if not classification:
            return go.Figure()
        
        fig = go.Figure()
        
        for cat_name, works in classification.items():
            if cat_name == "Unclassified" or not works:
                continue
            
            citations = [w.get('cited_by_count', 0) for w in works]
            
            fig.add_trace(go.Box(
                name=cat_name,
                y=citations,
                boxmean='sd',
                hovertemplate="<b>%{x}</b><br>" +
                             "Median: %{median}<br>" +
                             "Q1: %{q1}<br>" +
                             "Q3: %{q3}<br>" +
                             "<extra></extra>"
            ))
        
        fig.update_layout(
            title="Citation Distribution by Category",
            yaxis_title="Number of Citations",
            height=400,
            margin=dict(l=40, r=20, t=40, b=80),
            xaxis=dict(tickangle=-45)
        )
        
        return fig
    
    @staticmethod
    def create_heatmap(clusterer: HierarchicalClusterer) -> go.Figure:
        """
        Создает тепловую карту пересечений категорий.
        """
        if not clusterer or not clusterer.root:
            return go.Figure()
        
        # Собираем все листовые узлы
        leaf_nodes = clusterer.root.get_leaf_nodes()
        
        if len(leaf_nodes) < 2:
            return go.Figure()
        
        # Создаем матрицу пересечений
        n_nodes = len(leaf_nodes)
        intersection_matrix = np.zeros((n_nodes, n_nodes))
        
        node_names = [node.name[:20] for node in leaf_nodes]
        
        # Вычисляем пересечения по DOI
        for i in range(n_nodes):
            for j in range(n_nodes):
                if i != j:
                    doi_i = set(leaf_nodes[i].dois)
                    doi_j = set(leaf_nodes[j].dois)
                    intersection = len(doi_i.intersection(doi_j))
                    union = len(doi_i.union(doi_j))
                    
                    if union > 0:
                        intersection_matrix[i][j] = intersection / union
        
        fig = go.Figure(data=go.Heatmap(
            z=intersection_matrix,
            x=node_names,
            y=node_names,
            colorscale='Viridis',
            hoverongaps=False,
            hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>" +
                         "Similarity: %{z:.2f}<br>" +
                         "<extra></extra>"
        ))
        
        fig.update_layout(
            title="Cluster Intersection Heatmap",
            height=500,
            margin=dict(l=100, r=20, t=40, b=100),
            xaxis=dict(tickangle=-45)
        )
        
        return fig
    
    @staticmethod
    def create_wordcloud(category_name: str, works: List[dict]) -> plt.Figure:
        """
        Создает облако слов для категории.
        """
        if not works:
            return plt.Figure()
        
        # Собираем текст из заголовков
        text = " ".join([w.get('title', '') for w in works if w.get('title')])
        
        # Создаем облако слов
        wordcloud = WordCloud(
            width=800, height=400,
            background_color='white',
            max_words=100,
            colormap='viridis'
        ).generate(text.lower())
        
        # Создаем фигуру matplotlib
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title(f'Word Cloud - {category_name}', fontsize=16)
        
        return fig
    
    @staticmethod
    def create_hierarchy_view(clusterer: HierarchicalClusterer) -> str:
        """
        Создает текстовое представление иерархии.
        """
        if not clusterer or not clusterer.root:
            return "No hierarchy data"
        
        lines = []
        
        def traverse(node: HierarchicalClusterNode, prefix: str = "", is_last: bool = True):
            # Добавляем текущий узел
            marker = "└── " if is_last else "├── "
            count_info = f" [{node.work_count} papers, {len(node.dois)} DOIs]"
            lines.append(f"{prefix}{marker}{node.name}{count_info}")
            
            # Обновляем префикс для детей
            new_prefix = prefix + ("    " if is_last else "│   ")
            
            # Обрабатываем детей
            for i, child in enumerate(node.children):
                is_child_last = (i == len(node.children) - 1)
                traverse(child, new_prefix, is_child_last)
        
        traverse(clusterer.root)
        
        return "\n".join(lines)


# ============================================================================
# НОВЫЙ ИНТЕРФЕЙС ДЛЯ КЛАСТЕРИЗАЦИИ И КЛАССИФИКАЦИИ
# ============================================================================

def hierarchical_clustering_interface():
    """
    Интерфейс для настройки иерархической кластеризации.
    """
    st.markdown("""
    <div class="filter-section">
        <div class="filter-header">🌳 Hierarchical Clustering Setup</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Инициализация состояния
    if 'cluster_levels' not in st.session_state:
        st.session_state.cluster_levels = 3
    
    if 'cluster_filters' not in st.session_state:
        st.session_state.cluster_filters = [""] * 4
    
    if 'years_filter' not in st.session_state:
        st.session_state.years_filter = ""
    
    # Количество уровней
    st.session_state.cluster_levels = st.number_input(
        "Number of hierarchical levels (1-4)",
        min_value=1, max_value=4, value=st.session_state.cluster_levels,
        help="Define how many levels of filtering to apply"
    )
    
    # Ввод фильтров для каждого уровня
    st.markdown("### 🔍 Level Filters")
    st.markdown("""
    <div class="info-message">
        <small>Use parentheses for complex queries. Examples:<br>
        • Simple: "SOFC"<br>
        • AND: "(SOFC and PCFC)"<br>
        • OR: "(SOFC or PCFC)"<br>
        • Nested: "(SOFC and (PCFC or SOFC-H))"</small>
    </div>
    """, unsafe_allow_html=True)
    
    for level in range(1, st.session_state.cluster_levels + 1):
        st.session_state.cluster_filters[level-1] = st.text_input(
            f"Level {level} filter",
            value=st.session_state.cluster_filters[level-1],
            placeholder=f"e.g., SOFC or (SOFC and PCFC)",
            key=f"cluster_filter_{level}"
        )
    
    # Фильтр по годам
    st.markdown("### 📅 Year Filter")
    st.markdown("""
    <div class="info-message">
        <small>Examples:<br>
        • Single year: "2020"<br>
        • Range: "2020-2025"<br>
        • Multiple: "2020,2022,2024"<br>
        • Mixed: "2020,2022-2025"</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.session_state.years_filter = st.text_input(
        "Publication years",
        value=st.session_state.years_filter,
        placeholder="e.g., 2020-2025",
        key="years_filter_input"
    )
    
    # Дополнительные настройки
    with st.expander("⚙️ Advanced Settings"):
        st.session_state.max_works_per_level = st.number_input(
            "Max works per level",
            min_value=100, max_value=10000, value=2000,
            help="Maximum number of papers to fetch per level"
        )
        
        st.session_state.include_abstracts = st.checkbox(
            "Search in abstracts", value=True,
            help="Include abstracts in text analysis"
        )
        
        st.session_state.use_concepts = st.checkbox(
            "Use OpenAlex concepts", value=False,
            help="Use concept-based clustering instead of keywords"
        )
    
    # Кнопка запуска кластеризации
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🌳 Build Hierarchical Tree", type="primary", use_container_width=True):
            # Проверяем, что есть хотя бы один фильтр
            valid_filters = [f for f in st.session_state.cluster_filters[:st.session_state.cluster_levels] if f.strip()]
            
            if not valid_filters:
                st.error("Please enter at least one filter term")
                return
            
            # Создаем query builder
            query_builder = OpenAlexQueryBuilder()
            
            # Добавляем фильтры
            for level, filter_term in enumerate(valid_filters, 1):
                query_builder.add_level_filter(filter_term, level)
            
            # Добавляем фильтр по годам
            if st.session_state.years_filter:
                query_builder.parse_years(st.session_state.years_filter)
            
            # Сохраняем в сессию
            st.session_state.query_builder = query_builder
            st.session_state.active_filters = valid_filters
            
            # Переходим к результатам кластеризации
            st.session_state.current_step = 6  # Новый шаг для кластеризации
            st.rerun()


def classification_interface():
    """
    Интерфейс для настройки классификации после фильтрации.
    """
    st.markdown("""
    <div class="filter-section">
        <div class="filter-header">📊 Classification Setup</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Инициализация состояния
    if 'num_categories' not in st.session_state:
        st.session_state.num_categories = 4
    
    if 'categories_config' not in st.session_state:
        st.session_state.categories_config = []
    
    # Количество категорий
    st.session_state.num_categories = st.number_input(
        "Number of categories",
        min_value=1, max_value=10, value=st.session_state.num_categories,
        help="Define how many categories for classification"
    )
    
    # Динамическое создание категорий
    st.session_state.categories_config = []
    
    for i in range(st.session_state.num_categories):
        with st.expander(f"Category {i+1}", expanded=i==0):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                name = st.text_input(
                    "Category name",
                    key=f"cat_name_{i}",
                    placeholder="e.g., Co-free"
                )
            
            with col2:
                color = st.color_picker(
                    "Color",
                    value=["#3498db", "#2ecc71", "#e67e22", "#9b59b6", 
                           "#e74c3c", "#1abc9c", "#f39c12", "#d35400",
                           "#c0392b", "#16a085"][i % 10],
                    key=f"cat_color_{i}"
                )
            
            logic = st.radio(
                "Logic between terms",
                ["OR", "AND"],
                horizontal=True,
                key=f"cat_logic_{i}"
            )
            
            terms = st.text_area(
                "Search terms (one per line)",
                key=f"cat_terms_{i}`",
                height=80,
                placeholder="cobalt-free\nwithout cobalt\nCo-free"
            )
            
            description = st.text_input(
                "Description (optional)",
                key=f"cat_desc_{i}",
                placeholder=f"Papers about {name if name else 'this topic'}"
            )
            
            if name and terms:
                st.session_state.categories_config.append({
                    "name": name,
                    "color": color,
                    "logic": logic,
                    "terms": [t.strip() for t in terms.split('\n') if t.strip()],
                    "description": description
                })
    
    # Кнопка запуска классификации
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📊 Run Classification", type="primary", use_container_width=True):
            if not st.session_state.categories_config:
                st.error("Please configure at least one category")
                return
            
            # Получаем работы для классификации
            if 'clusterer' in st.session_state:
                # Используем работы из кластеризации
                works = st.session_state.clusterer.root.get_all_works() if st.session_state.clusterer.root else []
            elif 'filtered_works' in st.session_state:
                # Используем отфильтрованные работы
                works = st.session_state.filtered_works
            else:
                st.error("No works available for classification. Please run clustering first.")
                return
            
            if not works:
                st.error("No works found to classify")
                return
            
            # Создаем классификатор
            classifier = CategoryClassifier()
            
            for cat_config in st.session_state.categories_config:
                classifier.add_category(
                    name=cat_config["name"],
                    terms=cat_config["terms"],
                    logic=cat_config["logic"],
                    description=cat_config.get("description", ""),
                    color=cat_config.get("color")
                )
            
            # Выполняем классификацию
            with st.spinner("Classifying papers..."):
                classification = classifier.classify_works(works)
            
            # Сохраняем результаты
            st.session_state.classifier = classifier
            st.session_state.classification = classification
            
            # Переходим к результатам классификации
            st.session_state.current_step = 7  # Новый шаг для классификации
            st.rerun()


def step_clustering_results():
    """
    Шаг 6: Результаты кластеризации.
    """
    create_back_button()
    
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">🌳 Step 6: Hierarchical Clustering Results</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Visualization of the hierarchical tree structure.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'query_builder' not in st.session_state or 'active_filters' not in st.session_state:
        st.error("No clustering data available. Please go back to Step 6.")
        return
    
    # Создаем кластеризатор, если его еще нет
    if 'clusterer' not in st.session_state:
        with st.spinner("Building hierarchical tree..."):
            clusterer = HierarchicalClusterer(st.session_state.query_builder)
            
            # Строим дерево
            root = clusterer.build_tree(
                filters=st.session_state.active_filters,
                years_filter=st.session_state.years_filter,
                max_works_per_level=st.session_state.get('max_works_per_level', 2000)
            )
            
            st.session_state.clusterer = clusterer
    
    clusterer = st.session_state.clusterer
    
    # Статистика
    st.markdown("### 📊 Cluster Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_works = len(clusterer.root.get_all_works()) if clusterer.root else 0
        create_metric_card_compact("Total Papers", f"{total_works:,}", "📄")
    with col2:
        total_nodes = sum(len(nodes) for nodes in clusterer.nodes_by_level.values())
        create_metric_card_compact("Total Clusters", total_nodes, "🌳")
    with col3:
        max_depth = clusterer.root.get_depth() if clusterer.root else 0
        create_metric_card_compact("Max Depth", max_depth, "📏")
    with col4:
        leaf_nodes = len(clusterer.root.get_leaf_nodes()) if clusterer.root else 0
        create_metric_card_compact("Leaf Nodes", leaf_nodes, "🍃")
    
    # Таблица статистики
    stats_df = clusterer.get_cluster_statistics()
    if not stats_df.empty:
        st.dataframe(stats_df, use_container_width=True, height=200)
    
    # Визуализации
    tab1, tab2, tab3, tab4 = st.tabs(["🌳 Dendrogram", "📊 Heatmap", "📈 Hierarchy View", "📋 Details"])
    
    with tab1:
        st.markdown("### Dendrogram Visualization")
        fig = VisualizationModule.create_dendrogram(clusterer)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <div class="info-message">
            <small>• Node size represents number of papers<br>
            • Color indicates hierarchy level<br>
            • Hover over nodes for details<br>
            • Click on nodes to expand/collapse</small>
        </div>
        """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Cluster Intersection Heatmap")
        fig = VisualizationModule.create_heatmap(clusterer)
        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough clusters for heatmap visualization (need at least 2)")
    
    with tab3:
        st.markdown("### Text Hierarchy View")
        hierarchy_text = VisualizationModule.create_hierarchy_view(clusterer)
        st.text_area("Hierarchy", hierarchy_text, height=400, disabled=True)
        
        # Кнопка копирования
        if st.button("📋 Copy to Clipboard"):
            st.write(hierarchy_text)
            st.success("Copied to clipboard!")
    
    with tab4:
        st.markdown("### Detailed Cluster Information")
        
        # Выбор кластера для детального просмотра
        if clusterer.root:
            # Собираем все узлы
            all_nodes = []
            
            def collect_nodes(node):
                all_nodes.append(node)
                for child in node.children:
                    collect_nodes(child)
            
            collect_nodes(clusterer.root)
            
            # Создаем список для выбора
            node_options = {f"{node.name} (Level {node.level}, {node.work_count} papers)": node 
                          for node in all_nodes}
            
            selected_node_name = st.selectbox(
                "Select cluster to view details",
                options=list(node_options.keys())
            )
            
            if selected_node_name:
                selected_node = node_options[selected_node_name]
                
                # Отображаем информацию о кластере
                st.markdown(f"""
                <div class="cluster-node">
                    <h4>{selected_node.name}</h4>
                    <p><strong>Level:</strong> {selected_node.level}</p>
                    <p><strong>Filter:</strong> {selected_node.filter_term}</p>
                    <p><strong>Papers:</strong> {selected_node.work_count}</p>
                    <p><strong>DOIs:</strong> {len(selected_node.dois)}</p>
                    <p><strong>Children:</strong> {len(selected_node.children)}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Показываем примеры DOI
                if selected_node.dois:
                    st.markdown("**Sample DOIs:**")
                    for doi in selected_node.dois[:10]:
                        st.markdown(f"- [{doi}](https://doi.org/{doi})")
                    
                    if len(selected_node.dois) > 10:
                        st.markdown(f"*... and {len(selected_node.dois) - 10} more*")
    
    # Кнопка перехода к классификации
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📊 Proceed to Classification", type="primary", use_container_width=True):
            st.session_state.current_step = 7
            st.rerun()


def step_classification_results():
    """
    Шаг 7: Результаты классификации.
    """
    create_back_button()
    
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📊 Step 7: Classification Results</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Papers categorized by your defined categories.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'classifier' not in st.session_state or 'classification' not in st.session_state:
        st.error("No classification data available. Please run classification first.")
        
        # Кнопка для запуска классификации
        if st.button("📊 Go to Classification Setup"):
            st.session_state.current_step = 6
            st.rerun()
        return
    
    classifier = st.session_state.classifier
    classification = st.session_state.classification
    
    # Статистика
    stats_df = classifier.get_statistics(classification)
    
    if stats_df.empty:
        st.warning("No classification statistics available")
        return
    
    # Общая статистика
    total_papers = sum(len(works) for works in classification.values())
    
    st.markdown(f"""
    <div class="filter-stats">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>📊 Classification Summary</strong><br>
                <span style="font-size: 0.9rem; color: #666;">
                    {len([c for c in classification.keys() if c != "Unclassified"])} categories defined
                </span>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 1.5rem; font-weight: 700; color: #667eea;">{total_papers:,}</span><br>
                <span style="font-size: 0.8rem; color: #666;">total papers classified</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Визуализации в табах
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", "🥧 Pie Chart", "📈 Timeline", "📦 Box Plot", "🔍 Details"
    ])
    
    with tab1:
        st.markdown("### Category Statistics")
        st.dataframe(stats_df, use_container_width=True)
        
        # Столбчатая диаграмма
        fig = VisualizationModule.create_category_bar_chart(stats_df)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("### Distribution Pie Chart")
        fig = VisualizationModule.create_category_pie_chart(stats_df)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### Publication Timeline")
        fig = VisualizationModule.create_timeline_chart(classification)
        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough timeline data")
    
    with tab4:
        st.markdown("### Citation Distribution")
        fig = VisualizationModule.create_citation_boxplot(classification)
        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough citation data")
    
    with tab5:
        st.markdown("### Detailed Category View")
        
        # Выбор категории для детального просмотра
        category_options = list(classification.keys())
        selected_category = st.selectbox("Select category", category_options)
        
        if selected_category:
            works = classification[selected_category]
            
            if works:
                st.markdown(f"""
                <div class="category-card {' '.join(selected_category.lower().split()[:1])}">
                    <h4>{selected_category}</h4>
                    <p><strong>Papers:</strong> {len(works)}</p>
                    <p><strong>Percentage:</strong> {(len(works) / total_papers * 100):.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Детальная информация
                details = classifier.get_category_details(selected_category)
                
                if details:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Top Journals:**")
                        for journal, count in details.get('top_journals', [])[:5]:
                            st.markdown(f"- {journal}: {count}")
                    
                    with col2:
                        st.markdown("**Top Authors:**")
                        for author, count in details.get('top_authors', [])[:5]:
                            st.markdown(f"- {author}: {count}")
                    
                    st.markdown("**Sample Papers:**")
                    for i, doi in enumerate(details.get('sample_dois', [])[:5]):
                        if doi:
                            st.markdown(f"{i+1}. [{doi}](https://doi.org/{doi})")
                    
                    # Word cloud (если есть matplotlib)
                    try:
                        fig = VisualizationModule.create_wordcloud(selected_category, works)
                        st.pyplot(fig)
                    except:
                        pass
    
    # Экспорт результатов
    st.markdown("### 📥 Export Classification")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        json_data = classifier.export_classification("json")
        st.download_button(
            label="📊 JSON",
            data=json_data,
            file_name=f"classification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        csv_data = classifier.export_classification("csv")
        st.download_button(
            label="📈 CSV",
            data=csv_data,
            file_name=f"classification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        # Подготовка данных для Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)
            
            for cat_name, works in classification.items():
                if works:
                    cat_df = pd.DataFrame([{
                        'DOI': w.get('doi'),
                        'Title': w.get('title'),
                        'Year': w.get('publication_year'),
                        'Citations': w.get('cited_by_count'),
                        'Authors': ', '.join(w.get('authors', [])[:3]),
                        'Journal': w.get('journal_name')
                    } for w in works[:100]])  # Ограничиваем для больших категорий
                    
                    cat_df.to_excel(writer, sheet_name=cat_name[:30], index=False)
        
        st.download_button(
            label="📗 Excel",
            data=output.getvalue(),
            file_name=f"classification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # Кнопка нового анализа
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Start New Analysis", use_container_width=True):
            # Очищаем все данные сессии
            keys_to_clear = [
                'clusterer', 'classifier', 'classification', 'query_builder',
                'active_filters', 'cluster_filters', 'years_filter',
                'categories_config', 'num_categories', 'cluster_levels',
                'max_works_per_level', 'filtered_works', 'filtered_total_count'
            ]
            
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.session_state.current_step = 1
            st.rerun()


# ============================================================================
# КЭШИРОВАНИЕ НА УРОВНЕ SQLite
# ============================================================================

def init_cache_db():
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS works_cache (
            doi TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topic_works_cache (
            topic_id TEXT,
            cursor_key TEXT,
            data TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            PRIMARY KEY (topic_id, cursor_key)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics_cache (
            topic_id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cluster_cache (
            cache_key TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_works_expires ON works_cache(expires_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_topic_works_expires ON topic_works_cache(expires_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_topics_expires ON topics_cache(expires_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cluster_expires ON cluster_cache(expires_at)')
    
    conn.commit()
    conn.close()

def get_cache_key(prefix: str, key: str) -> str:
    return hashlib.md5(f"{prefix}:{key}".encode()).hexdigest()

@st.cache_resource
def get_db_connection():
    init_cache_db()
    return sqlite3.connect(CACHE_DB, check_same_thread=False)

def cache_work(doi: str, data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    expires_at = datetime.now() + timedelta(days=CACHE_EXPIRY_DAYS)
    
    cursor.execute('''
        INSERT OR REPLACE INTO works_cache (doi, data, expires_at)
        VALUES (?, ?, ?)
    ''', (doi, json.dumps(data), expires_at))
    
    conn.commit()

def get_cached_work(doi: str) -> Optional[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT data FROM works_cache 
        WHERE doi = ? AND (expires_at IS NULL OR expires_at > ?)
    ''', (doi, datetime.now()))
    
    result = cursor.fetchone()
    if result:
        return json.loads(result[0])
    return None

def cache_topic_works(topic_id: str, cursor_key: str, data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    expires_at = datetime.now() + timedelta(days=7)
    
    cursor.execute('''
        INSERT OR REPLACE INTO topic_works_cache (topic_id, cursor_key, data, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (topic_id, cursor_key, json.dumps(data), expires_at))
    
    conn.commit()

def get_cached_topic_works(topic_id: str, cursor_key: str) -> Optional[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT data FROM topic_works_cache 
        WHERE topic_id = ? AND cursor_key = ? 
        AND (expires_at IS NULL OR expires_at > ?)
    ''', (topic_id, cursor_key, datetime.now()))
    
    result = cursor.fetchone()
    if result:
        return json.loads(result[0])
    return None

def cache_topic_stats(topic_id: str, data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    expires_at = datetime.now() + timedelta(days=30)
    
    cursor.execute('''
        INSERT OR REPLACE INTO topics_cache (topic_id, data, expires_at)
        VALUES (?, ?, ?)
    ''', (topic_id, json.dumps(data), expires_at))
    
    conn.commit()

def get_cached_topic_stats(topic_id: str) -> Optional[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT data FROM topics_cache 
        WHERE topic_id = ? AND (expires_at IS NULL OR expires_at > ?)
    ''', (topic_id, datetime.now()))
    
    result = cursor.fetchone()
    if result:
        return json.loads(result[0])
    return None

def cache_cluster_data(cache_key: str, data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    expires_at = datetime.now() + timedelta(days=7)
    
    cursor.execute('''
        INSERT OR REPLACE INTO cluster_cache (cache_key, data, expires_at)
        VALUES (?, ?, ?)
    ''', (cache_key, json.dumps(data), expires_at))
    
    conn.commit()

def get_cached_cluster_data(cache_key: str) -> Optional[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT data FROM cluster_cache 
        WHERE cache_key = ? AND (expires_at IS NULL OR expires_at > ?)
    ''', (cache_key, datetime.now()))
    
    result = cursor.fetchone()
    if result:
        return json.loads(result[0])
    return None

def clear_old_cache():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Преобразуем datetime в строку в ISO формате для SQLite
    now_str = datetime.now().isoformat(' ', 'seconds')
    
    cursor.execute('DELETE FROM works_cache WHERE expires_at <= ?', (now_str,))
    cursor.execute('DELETE FROM topic_works_cache WHERE expires_at <= ?', (now_str,))
    cursor.execute('DELETE FROM topics_cache WHERE expires_at <= ?', (now_str,))
    cursor.execute('DELETE FROM cluster_cache WHERE expires_at <= ?', (now_str,))
    
    conn.commit()

# ============================================================================
# НОВЫЕ ФУНКЦИИ ДЛЯ ПАРСИНГА ДИАПАЗОНОВ ЦИТИРОВАНИЙ
# ============================================================================

def parse_citation_ranges(range_str: str) -> List[Tuple[int, int]]:
    """
    Парсит строку диапазонов цитирований в список кортежей.
    
    Примеры:
    "0" -> [(0, 0)]
    "0-3" -> [(0, 3)]
    "1,3-5" -> [(1, 1), (3, 5)]
    "0-1,3-4" -> [(0, 1), (3, 4)]
    "0,1,2,3" -> [(0, 0), (1, 1), (2, 2), (3, 3)]
    """
    ranges = []
    
    if not range_str or range_str.strip() == "":
        return [(0, 10)]  # По умолчанию
    
    # Разделяем по запятым
    parts = range_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # Диапазон
            try:
                start, end = part.split('-')
                start = int(start.strip())
                end = int(end.strip())
                
                # Проверяем что end >= start и оба в пределах 0-10
                if start <= end and 0 <= start <= 10 and 0 <= end <= 10:
                    ranges.append((start, end))
                else:
                    logger.warning(f"Invalid range: {part}. Using default.")
                    ranges.append((0, 10))
            except ValueError:
                logger.warning(f"Could not parse range: {part}. Using default.")
                ranges.append((0, 10))
        else:
            # Одиночное значение
            try:
                value = int(part.strip())
                if 0 <= value <= 10:
                    ranges.append((value, value))
                else:
                    logger.warning(f"Value out of range: {value}. Using default.")
                    ranges.append((0, 10))
            except ValueError:
                logger.warning(f"Could not parse value: {part}. Using default.")
                ranges.append((0, 10))
    
    # Удаляем дубликаты и сортируем
    unique_ranges = list(set(ranges))
    unique_ranges.sort(key=lambda x: x[0])
    
    return unique_ranges if unique_ranges else [(0, 10)]

def format_citation_ranges(ranges: List[Tuple[int, int]]) -> str:
    """
    Форматирует список диапазонов в читаемую строку.
    """
    if not ranges:
        return "0-10"
    
    parts = []
    for start, end in ranges:
        if start == end:
            parts.append(str(start))
        else:
            parts.append(f"{start}-{end}")
    
    return ", ".join(parts)

# ============================================================================
# НОВЫЕ ФУНКЦИИ ДЛЯ ОБНОВЛЕННОГО АНАЛИЗА С ФИЛЬТРАЦИЕЙ НА СТОРОНЕ API
# ============================================================================

def build_openalex_filter(topic_id: str, selected_years: List[int], 
                         selected_citations: List[Tuple[int, int]]) -> str:
    """
    Строит фильтр для OpenAlex API на основе выбранных параметров.
    
    Args:
        topic_id: Идентификатор темы (например, "T10366")
        selected_years: Список выбранных годов [2022, 2023, 2024]
        selected_citations: Список диапазонов цитирований [(0,0), (1,2), ...]
    
    Returns:
        Строка фильтра для OpenAlex API
    """
    filter_parts = [f"topics.id:{topic_id}"]
    
    # Добавляем фильтр по годам
    if selected_years:
        years_str = "|".join(map(str, selected_years))
        filter_parts.append(f"publication_year:{years_str}")
    
    # Добавляем фильтр по цитированиям
    if selected_citations:
        cites_str_parts = []
        for start, end in selected_citations:
            if start == end:
                cites_str_parts.append(str(start))
            else:
                cites_str_parts.append(f"{start}-{end}")
        
        if cites_str_parts:
            cites_str = "|".join(cites_str_parts)
            filter_parts.append(f"cited_by_count:{cites_str}")
    
    return ",".join(filter_parts)

def get_topic_total_works_count(topic_id: str) -> int:
    """
    Получает общее количество работ по теме из OpenAlex.
    
    Args:
        topic_id: Идентификатор темы
    
    Returns:
        Общее количество работ по теме
    """
    # Проверяем кэш
    cache_key = f"topic_total_{topic_id}"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT data FROM topics_cache 
        WHERE topic_id = ? AND (expires_at IS NULL OR expires_at > ?)
    ''', (cache_key, datetime.now()))
    
    result = cursor.fetchone()
    if result:
        return int(json.loads(result[0]))
    
    # Если нет в кэше, запрашиваем из API
    try:
        url = f"{OPENALEX_BASE_URL}/topics/{topic_id}"
        response = requests.get(url, headers=POLITE_POOL_HEADER, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            works_count = data.get('works_count', 0)
            
            # Сохраняем в кэш
            expires_at = datetime.now() + timedelta(days=7)
            cursor.execute('''
                INSERT OR REPLACE INTO topics_cache (topic_id, data, expires_at)
                VALUES (?, ?, ?)
            ''', (cache_key, str(works_count), expires_at))
            conn.commit()
            
            return works_count
        else:
            logger.error(f"Error fetching topic stats: {response.status_code}")
            return 0
    except Exception as e:
        logger.error(f"Error in get_topic_total_works_count: {str(e)}")
        return 0

def fetch_filtered_works_by_topic(
    topic_id: str,
    years_filter: List[int],
    citations_filter: List[Tuple[int, int]],
    max_results: Optional[int] = None,
    progress_callback=None
) -> Tuple[List[dict], int]:
    """
    Загружает работы по теме с фильтрацией на стороне API.
    
    Args:
        topic_id: Идентификатор темы
        years_filter: Список годов для фильтрации
        citations_filter: Список диапазонов цитирований
        max_results: Максимальное количество результатов (None = все)
        progress_callback: Функция обратного вызова для прогресса
    
    Returns:
        Кортеж (список работ, общее количество после фильтров)
    """
    # Строим фильтр для API
    filter_str = build_openalex_filter(topic_id, years_filter, citations_filter)
    
    # Ключ кэша на основе фильтров
    cache_key = f"filtered_{topic_id}_{hashlib.md5(filter_str.encode()).hexdigest()[:16]}"
    
    # Проверяем кэш
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT data FROM topic_works_cache 
        WHERE topic_id = ? AND cursor_key = ? 
        AND (expires_at IS NULL OR expires_at > ?)
    ''', (topic_id, cache_key, datetime.now()))
    
    result = cursor.fetchone()
    if result:
        cached_data = json.loads(result[0])
        works_list = cached_data.get('works', [])
        total_count = cached_data.get('total_count', 0)
        
        if max_results and len(works_list) >= max_results:
            logger.info(f"Using cached filtered data for topic {topic_id}")
            return works_list[:max_results] if max_results else works_list, total_count
    
    # Если нет в кэше, загружаем с API
    logger.info(f"Fetching filtered works for topic {topic_id}")
    logger.info(f"Filter: {filter_str}")
    
    all_works = []
    cursor_param = "*"
    page_count = 0
    total_count = 0
    
    try:
        while True:
            if max_results and len(all_works) >= max_results:
                break
                
            page_count += 1
            
            # Формируем URL с фильтрами
            params = {
                "filter": filter_str,
                "per-page": CURSOR_PAGE_SIZE,
                "cursor": cursor_param,
                "mailto": MAILTO
            }
            
            url = f"{OPENALEX_BASE_URL}/works"
            response = requests.get(url, params=params, headers=POLITE_POOL_HEADER, timeout=60)
            
            if response.status_code != 200:
                logger.error(f"Error fetching works: {response.status_code}")
                break
            
            data = response.json()
            
            # Получаем общее количество на первой странице
            if page_count == 1:
                total_count = data.get('meta', {}).get('count', 0)
                logger.info(f"Total works after filters: {total_count}")
                
                if total_count == 0:
                    return [], 0
            
            works = data.get('results', [])
            if not works:
                break
            
            all_works.extend(works)
            
            # Вызываем callback прогресса
            if progress_callback and total_count > 0:
                progress = min(len(all_works) / min(total_count, max_results or total_count), 1.0)
                progress_callback(progress, len(all_works), page_count, total_count)
            
            logger.info(f"Page {page_count}: got {len(works)} works, total: {len(all_works)}/{total_count}")
            
            # Получаем следующий курсор
            next_cursor = data.get('meta', {}).get('next_cursor')
            if not next_cursor:
                break
            
            cursor_param = next_cursor
            
            # Небольшая задержка для соблюдения rate limit
            time.sleep(0.1)
        
        # Сохраняем в кэш
        if all_works:
            cache_data = {
                'works': all_works,
                'total_count': total_count,
                'filter': filter_str,
                'timestamp': datetime.now().isoformat()
            }
            
            expires_at = datetime.now() + timedelta(days=3)
            cursor.execute('''
                INSERT OR REPLACE INTO topic_works_cache (topic_id, cursor_key, data, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (topic_id, cache_key, json.dumps(cache_data), expires_at))
            conn.commit()
        
        # Ограничиваем результаты если нужно
        result_works = all_works[:max_results] if max_results else all_works
        
        return result_works, total_count
        
    except Exception as e:
        logger.error(f"Error in fetch_filtered_works_by_topic: {str(e)}")
        return all_works, total_count

# ============================================================================
# ASYNCIO + AIOHTTP
# ============================================================================

class OpenAlexAsyncClient:
    def __init__(self):
        self.session = None
        self.semaphore = asyncio.Semaphore(MAX_WORKERS_ASYNC)
        self.request_count = 0
        self.start_time = time.time()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers=POLITE_POOL_HEADER,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=INITIAL_DELAY, max=MAX_DELAY),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def make_request(self, url: str) -> Optional[dict]:
        async with self.semaphore:
            elapsed = time.time() - self.start_time
            expected_time = self.request_count / RATE_LIMIT_PER_SECOND
            
            if elapsed < expected_time:
                wait_time = expected_time - elapsed
                await asyncio.sleep(wait_time)
            
            try:
                async with self.session.get(url) as response:
                    self.request_count += 1
                    
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 5))
                        logger.warning(f"Rate limited. Waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=429
                        )
                    
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        logger.warning(f"Resource not found: {url}")
                        return None
                    else:
                        logger.error(f"HTTP {response.status}: {url}")
                        return None
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout: {url}")
                raise
            except Exception as e:
                logger.error(f"Error: {url} - {str(e)}")
                raise
    
    async def fetch_works_by_dois_batch(self, dois: List[str]) -> List[Optional[dict]]:
        if not dois:
            return []
        
        cached_results = []
        uncached_dois = []
        
        for doi in dois:
            cached = get_cached_work(doi)
            if cached:
                cached_results.append(cached)
            else:
                uncached_dois.append(doi)
        
        if not uncached_dois:
            return cached_results
        
        logger.info(f"Fetching {len(uncached_dois)} works via batch API")
        
        doi_filter = "|".join(uncached_dois)
        url = f"{OPENALEX_BASE_URL}/works?filter=doi:{doi_filter}&per-page=200"
        
        try:
            data = await self.make_request(url)
            if data and 'results' in data:
                results = data['results']
                
                for work in results:
                    doi = work.get('doi', '').replace('https://doi.org/', '')
                    if doi:
                        cache_work(doi, work)
                
                doi_to_work = {w.get('doi', '').replace('https://doi.org/', ''): w for w in results}
                batch_results = []
                
                for doi in uncached_dois:
                    if doi in doi_to_work:
                        batch_results.append(doi_to_work[doi])
                    else:
                        try:
                            work_data = await self.fetch_single_work(doi)
                            batch_results.append(work_data)
                        except:
                            batch_results.append(None)
                
                return cached_results + batch_results
            else:
                return cached_results + [None] * len(uncached_dois)
                
        except Exception as e:
            logger.error(f"Batch fetch error: {str(e)}")
            return cached_results + [None] * len(uncached_dois)
    
    async def fetch_single_work(self, doi: str) -> Optional[dict]:
        cached = get_cached_work(doi)
        if cached:
            return cached
        
        url = f"{OPENALEX_BASE_URL}/works/https://doi.org/{doi}"
        data = await self.make_request(url)
        
        if data:
            cache_work(doi, data)
        
        return data
    
    async def fetch_works_by_topic_cursor(self, topic_id: str, max_results: int = 2000, 
                                         progress_callback=None) -> List[dict]:
        all_works = []
        cursor = "*"
        page_count = 0
        
        cache_key = f"{topic_id}_cursor_{cursor}"
        cached = get_cached_topic_works(topic_id, cache_key)
        
        if cached and len(cached) >= max_results:
            logger.info(f"Using cached data for topic {topic_id}")
            return cached[:max_results]
        
        logger.info(f"Fetching works for topic {topic_id} (max: {max_results})")
        
        try:
            while len(all_works) < max_results and cursor:
                page_count += 1
                
                url = (f"{OPENALEX_BASE_URL}/works?"
                      f"filter=topics.id:{topic_id}&"
                      f"per-page={CURSOR_PAGE_SIZE}&"
                      f"cursor={cursor}&"
                      f"sort=publication_date:desc")
                
                data = await self.make_request(url)
                
                if not data or 'results' not in data:
                    break
                
                works = data['results']
                if not works:
                    break
                
                all_works.extend(works)
                
                # Call progress callback
                if progress_callback:
                    progress = min(len(all_works) / max_results, 1.0)
                    progress_callback(progress, len(all_works), page_count)
                
                meta = data.get('meta', {})
                cursor = meta.get('next_cursor')
                
                logger.info(f"Page {page_count}: got {len(works)} works, total: {len(all_works)}")
                
                cache_key = f"{topic_id}_cursor_{cursor or 'end'}"
                cache_topic_works(topic_id, cache_key, all_works)
                
                if not cursor or page_count >= 10:
                    break
                
                await asyncio.sleep(0.5)
            
            result = all_works[:max_results]
            cache_topic_works(topic_id, "final", result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching topic works: {str(e)}")
            return all_works
    
    async def fetch_topic_stats(self, topic_id: str) -> Optional[dict]:
        cached = get_cached_topic_stats(topic_id)
        if cached:
            return cached
        
        url = f"{OPENALEX_BASE_URL}/topics/{topic_id}"
        data = await self.make_request(url)
        
        if data:
            cache_topic_stats(topic_id, data)
        
        return data

# ============================================================================
# СИНХРОННЫЕ ОБЕРТКИ
# ============================================================================

def run_async(coro):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def fetch_works_by_dois_sync(dois: List[str]) -> Tuple[List[dict], int, int]:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    batches = [dois[i:i + BATCH_SIZE] for i in range(0, len(dois), BATCH_SIZE)]
    all_results = []
    successful = 0
    failed = 0
    
    async def process_batches():
        nonlocal all_results, successful, failed
        async with OpenAlexAsyncClient() as client:
            for i, batch in enumerate(batches):
                progress = (i + 1) / len(batches)
                progress_bar.progress(progress)
                status_text.text(f"Batch {i+1}/{len(batches)}: {len(batch)} DOI")
                
                results = await client.fetch_works_by_dois_batch(batch)
                
                for result in results:
                    if result:
                        successful += 1
                        all_results.append({
                            'data': result,
                            'success': True
                        })
                    else:
                        failed += 1
                        all_results.append({
                            'data': None,
                            'success': False
                        })
                
                if i < len(batches) - 1:
                    await asyncio.sleep(1)
    
    run_async(process_batches())
    
    progress_bar.empty()
    status_text.empty()
    
    return all_results, successful, failed

def fetch_works_by_topic_sync(topic_id: str, max_results: int = 2000) -> List[dict]:
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_works = []
    
    def update_progress(progress, count, page):
        progress_bar.progress(progress)
        status_text.text(f"Page {page}: {count}/{max_results} works fetched")
    
    async def fetch():
        async with OpenAlexAsyncClient() as client:
            return await client.fetch_works_by_topic_cursor(
                topic_id, max_results, update_progress
            )
    
    result = run_async(fetch())
    progress_bar.empty()
    status_text.empty()
    return result

def fetch_topic_stats_sync(topic_id: str) -> Optional[dict]:
    async def fetch():
        async with OpenAlexAsyncClient() as client:
            return await client.fetch_topic_stats(topic_id)
    
    return run_async(fetch())

# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def normalize_word(word: str) -> str:
    word_lower = word.lower()
    
    if len(word_lower) < 4:
        return ''
    
    plural_exceptions = {
        'analyses': 'analysis', 'bases': 'base', 'criteria': 'criterion',
        'hypotheses': 'hypothesis', 'phenomena': 'phenomenon',
        'properties': 'property', 'activities': 'activity',
        'efficiencies': 'efficiency', 'performances': 'performance'
    }
    
    if word_lower in plural_exceptions:
        return plural_exceptions[word_lower]
    
    if word_lower.endswith('ies'):
        base = word_lower[:-3] + 'y'
        if len(base) >= 4:
            return base
    elif word_lower.endswith('es'):
        if word_lower.endswith(('ches', 'shes', 'xes', 'zes', 'sses')):
            base = word_lower[:-2]
            if len(base) >= 4:
                return base
    elif word_lower.endswith('s') and not word_lower.endswith(('ss', 'us', 'is', 'ys', 'as')):
        base = word_lower[:-1]
        if len(base) >= 4:
            return base
    
    return word_lower

def extract_keywords_from_title(title: str) -> List[str]:
    if not title:
        return []
    
    words = re.findall(r'\b[a-zA-Z]{4,}\b', title)
    filtered_words = []
    
    for word in words:
        word_lower = word.lower()
        
        if word_lower in ALL_STOPWORDS:
            continue
        
        if re.search(r'\d', word_lower):
            continue
        
        normalized = normalize_word(word_lower)
        if normalized:
            filtered_words.append(normalized)
    
    return filtered_words

def extract_numeric_from_doi(doi: str) -> int:
    """
    Extract numeric suffix from DOI for comparison.
    
    Examples:
        "10.5281/zenodo.17747567" -> 17747567
        "10.1002/anie.202000001" -> 202000001
        "10.1038/nature12345" -> 12345
    
    Args:
        doi: DOI string
    
    Returns:
        Integer value of the numeric suffix, or 0 if no number found
    """
    if not doi:
        return 0
    
    # Try to find the last numeric sequence in the DOI
    # First, split by common separators
    parts = doi.replace('.', '/').replace('-', '/').split('/')
    
    # Look for numeric parts from the end
    for part in reversed(parts):
        if part.isdigit():
            return int(part)
    
    # If no pure numeric parts, try to extract numbers from mixed strings
    numbers = re.findall(r'\d+', doi)
    if numbers:
        # Use the last number found (often version or ID)
        return int(numbers[-1])
    
    return 0

def parse_doi_input(text: str) -> List[str]:
    """
    Extract DOI identifiers from text handling various formats:
    1. https://doi.org/10.1002/fuce.70042
    2. 10.1002/fuce.70042
    3. https://dx.doi.org/10.1002/fuce.70042
    4. doi:10.1002/fuce.70042
    5. DOI:10.1002/fuce.70042
    6. Full citations with doi:10.1002/cphc.201000936
    """
    if not text or not text.strip():
        return []
    
    # More comprehensive DOI pattern that handles various formats
    # Matches DOI after common prefixes and URLs
    doi_patterns = [
        r'(?i)https?://(?:dx\.)?doi\.org/(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)',  # URL format
        r'(?i)(?:doi|DOI)[:\s]+(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)',            # doi: prefix format
        r'\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b'                               # Raw DOI format
    ]
    
    all_dois = []
    
    for pattern in doi_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):  # Some patterns may return groups
                doi = match[0] if match else ''
            else:
                doi = match
            
            if doi:
                # Clean up the DOI - remove any trailing punctuation
                doi = doi.strip()
                # Remove trailing punctuation (.,;:)
                doi = re.sub(r'[.,;:]+$', '', doi)
                # Remove any angle brackets or parentheses
                doi = doi.strip('<>()[]{}')
                all_dois.append(doi)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_dois = []
    for doi in all_dois:
        # Normalize DOI to lowercase for comparison
        doi_lower = doi.lower()
        if doi_lower not in seen:
            seen.add(doi_lower)
            unique_dois.append(doi)
    
    return unique_dois[:300]

def analyze_keywords_parallel(titles: List[str]) -> Counter:
    all_keywords = []
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(extract_keywords_from_title, title) for title in titles]
        for future in as_completed(futures):
            all_keywords.extend(future.result())
    
    return Counter(all_keywords)

def enrich_work_data(work: dict) -> dict:
    if not work:
        return {}
    
    doi_raw = work.get('doi')
    doi_clean = ''
    if doi_raw:
        doi_clean = str(doi_raw).replace('https://doi.org/', '')
    
    enriched = {
        'id': work.get('id', ''),
        'doi': doi_clean,
        'title': work.get('title', ''),
        'publication_date': work.get('publication_date', ''),
        'publication_year': work.get('publication_year', 0),
        'cited_by_count': work.get('cited_by_count', 0),
        'type': work.get('type', ''),
        'abstract': (work.get('abstract') or '')[:1000],
        'doi_url': f"https://doi.org/{doi_clean}" if doi_clean else '',
    }
    
    authorships = work.get('authorships', [])
    authors = []
    institutions = set()
    
    for authorship in authorships:
        if authorship:
            author = authorship.get('author', {})
            if author:
                author_name = author.get('display_name', '')
                if author_name:
                    authors.append(author_name)
            
            for inst in authorship.get('institutions', []):
                if inst:
                    inst_name = inst.get('display_name', '')
                    if inst_name:
                        institutions.add(inst_name)
    
    enriched['authors'] = authors[:5]
    enriched['institutions'] = list(institutions)
    
    primary_location = work.get('primary_location')
    if primary_location:
        source = primary_location.get('source', {})
        enriched['journal_name'] = source.get('display_name', '') if source else ''
        enriched['journal_type'] = (source or {}).get('type', '')
    else:
        enriched['journal_name'] = ''
        enriched['journal_type'] = ''
    
    open_access = work.get('open_access')
    enriched['is_oa'] = open_access.get('is_oa', False) if open_access else False
    
    topics = work.get('topics', [])
    if topics:
        sorted_topics = sorted(topics, key=lambda x: x.get('score', 0) if x else 0, reverse=True)
        primary_topic = sorted_topics[0] if sorted_topics else {}
        enriched['primary_topic'] = primary_topic.get('display_name', '') if primary_topic else ''
        topic_id = primary_topic.get('id', '') if primary_topic else ''
        enriched['topic_id'] = topic_id.split('/')[-1] if topic_id else ''
    else:
        enriched['primary_topic'] = ''
        enriched['topic_id'] = ''
    
    return enriched

# ============================================================================
# НОВЫЙ КЛАСС ДЛЯ УЛУЧШЕННОГО АНАЛИЗА КЛЮЧЕВЫХ СЛОВ
# ============================================================================

class TitleKeywordsAnalyzer:
    def __init__(self):
        # Initialize stopwords and lemmatizer
        try:
            import nltk
            from nltk.corpus import stopwords
            from nltk.stem import WordNetLemmatizer
            
            # Load necessary NLTK resources
            try:
                nltk.download('wordnet', quiet=True)
                nltk.download('omw-eng', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('punkt', quiet=True)
            except:
                pass
            
            self.stop_words = set(stopwords.words('english'))
            self.lemmatizer = WordNetLemmatizer()
            
            # Правила для специальных случаев
            self.irregular_plurals = {
                'analyses': 'analysis', 'axes': 'axis', 'bases': 'basis',
                'crises': 'crisis', 'criteria': 'criterion', 'data': 'datum',
                'diagnoses': 'diagnosis', 'ellipses': 'ellipsis', 'emphases': 'emphasis',
                'genera': 'genus', 'hypotheses': 'hypothesis', 'indices': 'index',
                'media': 'medium', 'memoranda': 'memorandum', 'parentheses': 'parenthesis',
                'phenomena': 'phenomenon', 'prognoses': 'prognosis', 'radii': 'radius',
                'stimuli': 'stimulus', 'syntheses': 'synthesis', 'theses': 'thesis',
                'vertebrae': 'vertebra', 'oxides': 'oxide', 'composites': 'composite',
                'applications': 'application', 'materials': 'material', 'methods': 'method',
                'systems': 'system', 'techniques': 'technique', 'properties': 'property',
                'structures': 'structure', 'devices': 'device', 'processes': 'process',
                'mechanisms': 'mechanism', 'models': 'model', 'approaches': 'approach',
                'frameworks': 'framework', 'strategies': 'strategy', 'solutions': 'solution',
                'technologies': 'technology', 'materials': 'material', 'nanoparticles': 'nanoparticle',
                'nanostructures': 'nanostructure', 'polymers': 'polymer', 'composites': 'composite',
                'ceramics': 'ceramic', 'alloys': 'alloy', 'coatings': 'coating', 'films': 'film',
                'layers': 'layer', 'interfaces': 'interface', 'surfaces': 'surface',
                'catalysts': 'catalyst', 'sensors': 'sensor', 'actuators': 'actuator',
                'transistors': 'transistor', 'diodes': 'diode', 'circuits': 'circuit',
                'networks': 'network', 'algorithms': 'algorithm', 'protocols': 'protocol',
                'databases': 'database', 'architectures': 'architecture', 'platforms': 'platform',
                'environments': 'environment', 'simulations': 'simulation', 'experiments': 'experiment',
                'measurements': 'measurement', 'observations': 'observation', 'analyses': 'analysis',
                'evaluations': 'evaluation', 'assessments': 'assessment', 'comparisons': 'comparison',
                'classifications': 'classification', 'predictions': 'prediction', 'optimizations': 'optimization',
                'characterizations': 'characterization', 'syntheses': 'synthesis', 'fabrications': 'fabrication',
                'preparations': 'preparation', 'treatments': 'treatment', 'modifications': 'modification',
                'enhancements': 'enhancement', 'improvements': 'improvement', 'developments': 'development',
                'innovations': 'innovation', 'discoveries': 'discovery', 'inventions': 'invention',
                'applications': 'application', 'implementations': 'implementation', 'utilizations': 'utilization',
                'integrations': 'integration', 'combinations': 'combination', 'interactions': 'interaction',
                'relationships': 'relationship', 'dependencies': 'dependency', 'correlations': 'correlation',
                'associations': 'association', 'connections': 'connection', 'communications': 'communication',
                'collaborations': 'collaboration', 'cooperations': 'cooperation', 'competitions': 'competition',
                'conflicts': 'conflict', 'challenges': 'challenge', 'problems': 'problem', 'solutions': 'solution',
                'alternatives': 'alternative', 'options': 'option', 'variants': 'variant', 'versions': 'version',
                'editions': 'edition', 'releases': 'release', 'updates': 'update', 'revisions': 'revision',
                'modifications': 'modification', 'adaptations': 'adaptation', 'customizations': 'customization',
                'personalizations': 'personalization', 'localizations': 'localization', 'internationalizations': 'internationalization',
                'standardizations': 'standardization', 'normalizations': 'normalization', 'optimizations': 'optimization',
                'maximizations': 'maximization', 'minimizations': 'minimization', 'reductions': 'reduction',
                'increases': 'increase', 'improvements': 'improvement', 'enhancements': 'enhancement',
                'advancements': 'advancement', 'progresses': 'progress', 'developments': 'development',
                'evolutions': 'evolution', 'revolutions': 'revolution', 'transformations': 'transformation',
                'changes': 'change', 'variations': 'variation', 'fluctuations': 'fluctuation', 'oscillations': 'oscillation',
                'vibrations': 'vibration', 'rotations': 'rotation', 'translations': 'translation', 'movements': 'movement',
                'motions': 'motion', 'dynamics': 'dynamic', 'kinematics': 'kinematic', 'mechanics': 'mechanic',
                'thermodynamics': 'thermodynamic', 'electrodynamics': 'electrodynamic', 'hydrodynamics': 'hydrodynamic',
                'aerodynamics': 'aerodynamic', 'biomechanics': 'biomechanic', 'geomechanics': 'geomechanic',
                'chemomechanics': 'chemomechanic', 'tribology': 'tribology', 'rheology': 'rheology',
                'viscoelasticity': 'viscoelastic', 'plasticity': 'plastic', 'elasticity': 'elastic',
                'viscosity': 'viscous', 'conductivity': 'conductive', 'resistivity': 'resistive',
                'permeability': 'permeable', 'porosity': 'porous', 'density': 'dense', 'hardness': 'hard',
                'stiffness': 'stiff', 'strength': 'strong', 'toughness': 'tough', 'brittleness': 'brittle',
                'ductility': 'ductile', 'malleability': 'malleable', 'flexibility': 'flexible', 'rigidity': 'rigid',
                'stability': 'stable', 'instability': 'unstable', 'reliability': 'reliable', 'durability': 'durable',
                'sustainability': 'sustainable', 'efficiency': 'efficient', 'effectiveness': 'effective',
                'performance': 'perform', 'productivity': 'productive', 'quality': 'qualitative',
                'quantity': 'quantitative', 'accuracy': 'accurate', 'precision': 'precise', 'reliability': 'reliable',
                'validity': 'valid', 'reproducibility': 'reproducible', 'repeatability': 'repeatable',
                'consistency': 'consistent', 'homogeneity': 'homogeneous', 'heterogeneity': 'heterogeneous',
                'isotropy': 'isotropic', 'anisotropy': 'anisotropic', 'symmetry': 'symmetric',
                'asymmetry': 'asymmetric', 'regularity': 'regular', 'irregularity': 'irregular',
                'periodicity': 'periodic', 'aperiodicity': 'aperiodic', 'randomness': 'random',
                'determinism': 'deterministic', 'stochasticity': 'stochastic', 'probability': 'probable',
                'statistics': 'statistic', 'distributions': 'distribution', 'functions': 'function',
                'equations': 'equation', 'formulas': 'formula', 'theorems': 'theorem', 'lemmas': 'lemma',
                'corollaries': 'corollary', 'proofs': 'proof', 'demonstrations': 'demonstration',
                'verifications': 'verification', 'validations': 'validation', 'confirmations': 'confirmation',
                'tests': 'test', 'experiments': 'experiment', 'trials': 'trial', 'studies': 'study',
                'investigations': 'investigation', 'examinations': 'examination', 'inspections': 'inspection',
                'audits': 'audit', 'reviews': 'review', 'surveys': 'survey', 'polls': 'poll',
                'questionnaires': 'questionnaire', 'interviews': 'interview', 'observations': 'observation',
                'measurements': 'measurement', 'calculations': 'calculation', 'computations': 'computation',
                'simulations': 'simulation', 'modelings': 'modeling', 'analyses': 'analysis', 'syntheses': 'synthesis',
                'evaluations': 'evaluation', 'assessments': 'assessment', 'appraisals': 'appraisal',
                'estimations': 'estimation', 'approximations': 'approximation', 'predictions': 'prediction',
                'forecasts': 'forecast', 'projections': 'projection', 'extrapolations': 'extrapolation',
                'interpolations': 'interpolation', 'regressions': 'regression', 'correlations': 'correlation',
                'classifications': 'classification', 'clusters': 'cluster', 'segments': 'segment', 'groups': 'group',
                'categories': 'category', 'types': 'type', 'classes': 'class', 'kinds': 'kind', 'sorts': 'sort',
                'varieties': 'variety', 'forms': 'form', 'shapes': 'shape', 'sizes': 'size', 'dimensions': 'dimension',
                'volumes': 'volume', 'areas': 'area', 'lengths': 'length', 'widths': 'width', 'heights': 'height',
                'depths': 'depth', 'thicknesses': 'thickness', 'diameters': 'diameter', 'radii': 'radius',
                'circumferences': 'circumference', 'perimeters': 'perimeter', 'surfaces': 'surface',
                'interfaces': 'interface', 'boundaries': 'boundary', 'edges': 'edge', 'corners': 'corner',
                'vertices': 'vertex', 'nodes': 'node', 'points': 'point', 'lines': 'line', 'curves': 'curve',
                'planes': 'plane', 'spaces': 'space', 'regions': 'region', 'zones': 'zone', 'sectors': 'sector',
                'segments': 'segment', 'parts': 'part', 'components': 'component', 'elements': 'element',
                'units': 'unit', 'modules': 'module', 'blocks': 'block', 'pieces': 'piece', 'fragments': 'fragment',
                'particles': 'particle', 'atoms': 'atom', 'molecules': 'molecule', 'ions': 'ion', 'electrons': 'electron',
                'protons': 'proton', 'neutrons': 'neutron', 'photons': 'photon', 'quarks': 'quark', 'leptons': 'lepton',
                'bosons': 'boson', 'fermions': 'fermion', 'hadrons': 'hadron', 'mesons': 'meson', 'baryons': 'baryon',
                'nuclei': 'nucleus', 'isotopes': 'isotope', 'elements': 'element', 'compounds': 'compound',
                'mixtures': 'mixture', 'solutions': 'solution', 'suspensions': 'suspension', 'colloids': 'colloid',
                'emulsions': 'emulsion', 'foams': 'foam', 'gels': 'gel', 'solids': 'solid', 'liquids': 'liquid',
                'gases': 'gas', 'plasmas': 'plasma', 'crystals': 'crystal', 'amorphous': 'amorphous', 'polymers': 'polymer',
                'monomers': 'monomer', 'oligomers': 'oligomer', 'copolymers': 'copolymer', 'homopolymers': 'homopolymer',
                'biopolymers': 'biopolymer', 'proteins': 'protein', 'enzymes': 'enzyme', 'antibodies': 'antibody',
                'antigens': 'antigen', 'vaccines': 'vaccine', 'drugs': 'drug', 'medicines': 'medicine',
                'therapies': 'therapy', 'treatments': 'treatment', 'diagnoses': 'diagnosis', 'prognoses': 'prognosis',
                'symptoms': 'symptom', 'diseases': 'disease', 'disorders': 'disorder', 'conditions': 'condition',
                'syndromes': 'syndrome', 'infections': 'infection', 'inflammations': 'inflammation', 'tumors': 'tumor',
                'cancers': 'cancer', 'metastases': 'metastasis', 'remissions': 'remission', 'recurrences': 'recurrence',
                'survivals': 'survival', 'mortality': 'mortal', 'morbidity': 'morbid', 'epidemiology': 'epidemiologic',
                'pathology': 'pathologic', 'physiology': 'physiologic', 'anatomy': 'anatomic', 'histology': 'histologic',
                'cytology': 'cytologic', 'genetics': 'genetic', 'genomics': 'genomic', 'proteomics': 'proteomic',
                'metabolomics': 'metabolomic', 'transcriptomics': 'transcriptomic', 'epigenetics': 'epigenetic',
                'bioinformatics': 'bioinformatic', 'biotechnology': 'biotechnologic', 'nanotechnology': 'nanotechnologic',
                'microtechnology': 'microtechnologic', 'microfabrication': 'microfabricate', 'nanofabrication': 'nanofabricate',
                'lithography': 'lithographic', 'photolithography': 'photolithographic', 'electron-beam': 'electron-beam',
                'ion-beam': 'ion-beam', 'focused-ion-beam': 'focused-ion-beam', 'atomic-force': 'atomic-force',
                'scanning-tunneling': 'scanning-tunneling', 'transmission-electron': 'transmission-electron',
                'scanning-electron': 'scanning-electron', 'optical': 'optical', 'confocal': 'confocal',
                'fluorescence': 'fluorescent', 'phosphorescence': 'phosphorescent', 'luminescence': 'luminescent',
                'chemiluminescence': 'chemiluminescent', 'bioluminescence': 'bioluminescent', 'electroluminescence': 'electroluminescent',
                'photoluminescence': 'photoluminescent', 'cathodoluminescence': 'cathodoluminescent',
                'thermoluminescence': 'thermoluminescent', 'radioluminescence': 'radioluminescent',
                'sonoluminescence': 'sonoluminescent', 'triboluminescence': 'triboluminescent',
                'crystalloluminescence': 'crystalloluminescent', 'electroluminescence': 'electroluminescent',
                'magnetoluminescence': 'magnetoluminescent',
            }
            
            # Суффиксы, которые нужно преобразовать
            self.suffix_replacements = {
                'ies': 'y',
                'es': '',
                's': '',
                'ed': '',
                'ing': '',
                'ly': '',
                'ally': 'al',
                'ically': 'ic',
                'ization': 'ize',
                'isation': 'ise',
                'ment': '',
                'ness': '',
                'ity': '',
                'ty': '',
                'ic': '',
                'ical': '',
                'ive': '',
                'ous': '',
                'ful': '',
                'less': '',
                'est': '',
                'er': '',
                'ors': 'or',
                'ors': 'or',
                'ings': 'ing',
                'ments': 'ment',
            }
            
        except:
            # Fallback if nltk not available
            self.stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            self.lemmatizer = None
            self.irregular_plurals = {}
            self.suffix_replacements = {}
        
        # Scientific stopwords (уже лемматизированные)
        self.scientific_stopwords = {
            'activate', 'adapt', 'advance', 'analyze', 'apply',
            'approach', 'architect', 'artificial', 'assess',
            'base', 'behave', 'capacity', 'characterize',
            'coat', 'compare', 'compute', 'composite',
            'control', 'cycle', 'damage', 'data', 'density', 'design',
            'detect', 'develop', 'device', 'diagnose', 'discover',
            'dynamic', 'economic', 'effect', 'efficacy',
            'efficient', 'energy', 'engineer', 'enhance', 'environment',
            'evaluate', 'experiment', 'explore', 'factor', 'fail',
            'fabricate', 'field', 'film', 'flow', 'framework', 'frequency',
            'function', 'grow', 'high', 'impact', 'improve',
            'induce', 'influence', 'inform', 'innovate', 'intelligent',
            'interact', 'interface', 'investigate', 'know',
            'layer', 'learn', 'magnetic', 'manage', 'material',
            'measure', 'mechanism', 'medical',
            'method', 'model', 'modify', 'modulate',
            'molecule', 'monitor', 'motion', 'nanoparticle',
            'nanostructure', 'network', 'neural', 'new', 'nonlinear',
            'novel', 'numerical', 'optical', 'optimize', 'pattern', 'perform',
            'phenomenon', 'potential', 'power', 'predict', 'prepare', 'process',
            'produce', 'progress', 'property', 'quality', 'regulate', 'relate',
            'reliable', 'remote', 'repair', 'research', 'resist', 'respond',
            'review', 'risk', 'role', 'safe', 'sample', 'scale', 'screen',
            'separate', 'signal', 'simulate', 'specific', 'stable', 'state',
            'store', 'strain', 'strength', 'stress', 'structure', 'study',
            'sustain', 'synergy', 'synthesize', 'system', 'target',
            'technique', 'technology', 'test', 'theoretical', 'therapy',
            'thermal', 'tissue', 'tolerate', 'toxic', 'transform', 'transition',
            'transmit', 'transport', 'type', 'understand', 'use', 'validate',
            'value', 'vary', 'virtual', 'waste', 'wave',
            'application', 'approach', 'assessment', 'behavior', 'capability',
            'characterization', 'comparison', 'concept', 'condition', 'configuration',
            'construction', 'contribution', 'demonstration', 'description', 'detection',
            'determination', 'development', 'effectiveness', 'efficiency', 'evaluation',
            'examination', 'experimentation', 'explanation', 'exploration', 'fabrication',
            'formation', 'implementation', 'improvement', 'indication', 'investigation',
            'management', 'manufacture', 'measurement', 'modification', 'observation',
            'operation', 'optimization', 'performance', 'preparation', 'presentation',
            'production', 'realization', 'recognition', 'regulation', 'representation',
            'simulation', 'solution', 'specification', 'synthesis', 'transformation',
            'treatment', 'utilization', 'validation', 'verification'
        }
    
    def _get_lemma(self, word: str) -> str:
        """Get word lemma considering special rules"""
        if not word or len(word) < 3:
            return word
        
        # Convert to lowercase for processing
        lower_word = word.lower()
        
        # Check irregular plurals FIRST
        if lower_word in self.irregular_plurals:
            return self.irregular_plurals[lower_word]
        
        # Check regular plurals
        # If word ends with 's' or 'es' but not 'ss' or 'us'
        if lower_word.endswith('s') and not (lower_word.endswith('ss') or lower_word.endswith('us')):
            # Try to remove 's' or 'es'
            if lower_word.endswith('es') and len(lower_word) > 2:
                base_word = lower_word[:-2]
                # Check that after removing 'es' word not too short
                if len(base_word) >= 3:
                    return base_word
            elif len(lower_word) > 1:
                base_word = lower_word[:-1]
                # Check that after removing 's' word not too short
                if len(base_word) >= 3:
                    return base_word
        
        # Use lemmatizer if available
        if self.lemmatizer:
            # Try different parts of speech
            for pos in ['n', 'v', 'a', 'r']:  # noun, verb, adjective, adverb
                lemma = self.lemmatizer.lemmatize(lower_word, pos=pos)
                if lemma != lower_word:
                    return lemma
        
        # Apply suffix rules in reverse order (long to short)
        sorted_suffixes = sorted(self.suffix_replacements.keys(), key=len, reverse=True)
        for suffix in sorted_suffixes:
            if lower_word.endswith(suffix) and len(lower_word) > len(suffix) + 2:
                replacement = self.suffix_replacements[suffix]
                base = lower_word[:-len(suffix)] + replacement
                # Check result not too short
                if len(base) >= 3:
                    # Also check base doesn't end with double consonant
                    if len(base) >= 4 and base[-1] == base[-2]:
                        base = base[:-1]
                    return base
        
        return lower_word
    
    def _get_base_form(self, word: str) -> str:
        """Get base word form with aggressive lemmatization"""
        lemma = self._get_lemma(word)
        
        # Additional rules for scientific terms
        if lemma.endswith('isation'):
            return lemma[:-7] + 'ize'
        elif lemma.endswith('ization'):
            return lemma[:-7] + 'ize'
        elif lemma.endswith('ication'):
            return lemma[:-7] + 'y'
        elif lemma.endswith('ation'):
            return lemma[:-5] + 'e'
        elif lemma.endswith('ition'):
            return lemma[:-5] + 'e'
        elif lemma.endswith('ution'):
            return lemma[:-5] + 'e'
        elif lemma.endswith('ment'):
            return lemma[:-4]
        elif lemma.endswith('ness'):
            return lemma[:-4]
        elif lemma.endswith('ity'):
            return lemma[:-3] + 'e'
        elif lemma.endswith('ty'):
            base = lemma[:-2]
            if base.endswith('i'):
                return base[:-1] + 'y'
            return base
        elif lemma.endswith('ic'):
            return lemma[:-2] + 'y'
        elif lemma.endswith('al'):
            return lemma[:-2]
        elif lemma.endswith('ive'):
            return lemma[:-3] + 'e'
        elif lemma.endswith('ous'):
            return lemma[:-3]
        
        return lemma
    
    def preprocess_content_words(self, text: str) -> List[Dict]:
        """Clean and normalize content words, return dictionaries with lemmas and forms"""
        if not text or text in ['Title not found', 'Request timeout', 'Network error', 'Retrieval error']:
            return []

        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s-]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        words = text.split()
        content_words = []

        for word in words:
            # EXCLUDE word "sub"
            if word == 'sub':
                continue
            if '-' in word:
                continue
            if len(word) > 2 and word not in self.stop_words:
                lemma = self._get_base_form(word)
                if lemma not in self.scientific_stopwords:
                    content_words.append({
                        'original': word,
                        'lemma': lemma,
                        'type': 'content'
                    })

        return content_words

    def extract_compound_words(self, text: str) -> List[Dict]:
        """Extract hyphenated compound words"""
        if not text or text in ['Title not found', 'Request timeout', 'Network error', 'Retrieval error']:
            return []

        text = text.lower()
        compound_words = re.findall(r'\b[a-z]{2,}-[a-z]{2,}(?:-[a-z]{2,})*\b', text)

        compounds = []
        for word in compound_words:
            parts = word.split('-')
            if not any(part in self.stop_words for part in parts):
                # For compound words lemmatize each part
                lemmatized_parts = []
                for part in parts:
                    lemma = self._get_base_form(part)
                    lemmatized_parts.append(lemma)
                
                compounds.append({
                    'original': word,
                    'lemma': '-'.join(lemmatized_parts),
                    'type': 'compound'
                })

        return compounds

    def _are_similar_lemmas(self, lemma1: str, lemma2: str) -> bool:
        """Check if lemmas are similar (e.g., singular/plural)"""
        if lemma1 == lemma2:
            return True
        
        # Check if they are forms of the same word
        # Example: "composite" and "composites"
        if lemma1.endswith('s') and lemma1[:-1] == lemma2:
            return True
        if lemma2.endswith('s') and lemma2[:-1] == lemma1:
            return True
        
        # Check if they are forms with different suffixes
        # Example: "characterization" and "characterize"
        common_prefix = self._get_common_prefix(lemma1, lemma2)
        if len(common_prefix) >= 5:  # If common prefix long enough
            # Check length difference
            if abs(len(lemma1) - len(lemma2)) <= 3:
                return True
        
        return False
    
    def _get_common_prefix(self, str1: str, str2: str) -> str:
        """Return common prefix of two strings"""
        min_length = min(len(str1), len(str2))
        common_prefix = []
        
        for i in range(min_length):
            if str1[i] == str2[i]:
                common_prefix.append(str1[i])
            else:
                break
        
        return ''.join(common_prefix)

class EnhancedKeywordAnalyzer:
    def __init__(self):
        self.title_analyzer = TitleKeywordsAnalyzer()
        
        # Веса для разных типов слов
        self.weights = {
            'content': 1.0,
            'compound': 1.5,  # Составные слова важнее
            'scientific': 0.7  # Научные стоп-слова менее важны
        }
    
    def extract_weighted_keywords(self, titles: List[str]) -> Dict[str, float]:
        """Извлечение ключевых слов с весами"""
        weighted_counter = Counter()
        
        for title in titles:
            if not title:
                continue
                
            # Извлекаем все типы слов
            content_words = self.title_analyzer.preprocess_content_words(title)
            compound_words = self.title_analyzer.extract_compound_words(title)
            
            # Учитываем веса
            for word_info in content_words:
                lemma = word_info['lemma']
                if lemma:
                    weighted_counter[lemma] += self.weights['content']
            
            for word_info in compound_words:
                lemma = word_info['lemma']
                if lemma:
                    weighted_counter[lemma] += self.weights['compound']
        
        return weighted_counter

def calculate_enhanced_relevance(work: dict, keywords: Dict[str, float], 
                                 analyzer: TitleKeywordsAnalyzer) -> Tuple[float, List[str]]:
    """Расчет релевантности с учетом семантической близости"""
    
    title = work.get('title', '').lower()
    abstract = work.get('abstract', '').lower()
    
    if not title:
        return 0.0, []
    
    score = 0.0
    matched_keywords = []
    
    # Извлекаем слова из заголовка анализируемой работы
    title_words = analyzer.preprocess_content_words(title)
    compound_words = analyzer.extract_compound_words(title)
    
    title_lemmas = {w['lemma'] for w in title_words}
    compound_lemmas = {w['lemma'] for w in compound_words}
    all_title_lemmas = title_lemmas.union(compound_lemmas)
    
    # Проверяем каждое ключевое слово
    for keyword, weight in keywords.items():
        keyword_lower = keyword.lower()
        keyword_base = analyzer._get_base_form(keyword_lower)
        
        # Проверяем точное совпадение в заголовке
        if keyword_lower in title:
            score += weight * 3.0  # Высокий вес для точного совпадения
            if keyword not in matched_keywords:
                matched_keywords.append(keyword)
        
        # Проверяем точное совпадение в аннотации
        elif abstract and keyword_lower in abstract:
            score += weight * 1.0  # Меньший вес для аннотации
            if f"{keyword}*" not in matched_keywords:
                matched_keywords.append(f"{keyword}*")
        
        else:
            # Проверяем лемматизированные формы в заголовке
            for lemma in all_title_lemmas:
                if analyzer._are_similar_lemmas(keyword_base, lemma):
                    score += weight * 2.0  # Средний вес для семантической близости
                    if f"{keyword}~{lemma}" not in matched_keywords:
                        matched_keywords.append(f"{keyword}~{lemma}")
                    break
    
    # Дополнительные бонусы
    compound_words_list = analyzer.extract_compound_words(title)
    if compound_words_list:
        score += len(compound_words_list) * 0.5
    
    normalized_score = min(score * 2, 10)
    
    return normalized_score, matched_keywords

def passes_filters(work: dict, year_filter: List[int], 
                   citation_ranges: List[Tuple[int, int]]) -> bool:
    """Проверяет работу на соответствие фильтрам"""
    
    cited_by_count = work.get('cited_by_count', 0)
    publication_year = work.get('publication_year', 0)
    
    # Фильтр по годам
    if year_filter and publication_year not in year_filter:
        return False
    
    # Фильтр по цитированиям
    if citation_ranges:
        in_range = False
        for min_cit, max_cit in citation_ranges:
            if min_cit <= cited_by_count <= max_cit:
                in_range = True
                break
        if not in_range:
            return False
    
    return True

def analyze_works_for_topic(
    topic_id: str,
    keywords: List[str],
    max_citations: int = 10,  # ← Этот параметр теперь не используется!
    max_works: int = 2000,
    top_n: int = 100,
    year_filter: List[int] = None,
    citation_ranges: List[Tuple[int, int]] = None
) -> List[dict]:
    """
    Analyze works for a specific topic with filtering of input DOIs and duplicate titles.
    """
    
    with st.spinner(f"Loading up to {max_works} works..."):
        works = fetch_works_by_topic_sync(topic_id, max_works)
    
    if not works:
        return []
    
    current_year = datetime.now().year
    if year_filter is None:
        year_filter = [current_year - 2, current_year - 1, current_year]
    
    if citation_ranges is None:
        citation_ranges = [(0, 10)]
    
    # Get input DOIs from session state to exclude them from recommendations
    input_dois = set()
    if 'dois' in st.session_state:
        # Normalize input DOIs (remove https://doi.org/ prefix for comparison)
        for doi in st.session_state.dois:
            if doi.startswith('https://doi.org/'):
                clean_doi = doi.replace('https://doi.org/', '').lower()
            else:
                clean_doi = doi.lower()
            input_dois.add(clean_doi)
        logger.info(f"Excluding {len(input_dois)} input DOIs from recommendations")
    
    # Инициализация анализаторов
    title_analyzer = TitleKeywordsAnalyzer()
    keyword_analyzer = EnhancedKeywordAnalyzer()
    
    # Преобразуем ключевые слова в взвешенный словарь
    keywords_lower = [kw.lower() for kw in keywords]
    weighted_keywords = keyword_analyzer.extract_weighted_keywords(keywords_lower)
    
    # Добавляем исходные ключевые слова с весом
    for keyword in keywords:
        keyword_lower = keyword.lower()
        keyword_base = title_analyzer._get_base_form(keyword_lower)
        if keyword_base:
            weighted_keywords[keyword_base] = weighted_keywords.get(keyword_base, 0) + 2.0
    
    # Нормализуем веса
    if weighted_keywords:
        max_weight = max(weighted_keywords.values())
        normalized_keywords = {k: v/max_weight for k, v in weighted_keywords.items()}
    else:
        normalized_keywords = {}
    
    # Track duplicate titles to keep only one version (with highest DOI number)
    title_to_work_map = {}
    
    with st.spinner(f"Analyzing {len(works)} works with enhanced algorithm..."):
        analyzed = []
        
        for work in works:
            # ========== ИСПРАВЛЕНИЕ НАЧИНАЕТСЯ ЗДЕСЬ ==========
            # Проверяем работу фильтрами
            if not passes_filters(work, year_filter, citation_ranges):
                continue
            # ========== ИСПРАВЛЕНИЕ ЗАКАНЧИВАЕТСЯ ЗДЕСЬ ==========
            
            title = work.get('title', '')
            
            if not title:  # Skip works without title
                continue
            
            # Extract and clean DOI for comparison
            doi_raw = work.get('doi', '')
            doi_clean = ''
            if doi_raw:
                doi_clean = str(doi_raw).replace('https://doi.org/', '').lower()
            
            # RULE 1: Exclude works that match input DOIs
            if doi_clean and doi_clean in input_dois:
                logger.debug(f"Excluding work with input DOI: {doi_clean}")
                continue
            
            # Calculate enhanced relevance score
            relevance_score, matched_keywords = calculate_enhanced_relevance(
                work, normalized_keywords, title_analyzer
            )
            
            if relevance_score > 0:
                enriched = enrich_work_data(work)
                enriched.update({
                    'relevance_score': relevance_score,
                    'matched_keywords': matched_keywords,
                    'analysis_time': datetime.now().isoformat()
                })
                
                # RULE 2: Handle duplicate titles
                title_normalized = title.strip().lower()
                
                if title_normalized in title_to_work_map:
                    # We have a duplicate title, compare DOIs
                    existing_work = title_to_work_map[title_normalized]
                    existing_doi = existing_work.get('doi', '').lower()
                    current_doi = enriched.get('doi', '').lower()
                    
                    # Extract numeric parts from DOIs for comparison
                    existing_numeric = extract_numeric_from_doi(existing_doi)
                    current_numeric = extract_numeric_from_doi(current_doi)
                    
                    # Keep the work with higher numeric DOI (or higher score if DOIs equal)
                    if current_numeric > existing_numeric:
                        # Replace with current work
                        title_to_work_map[title_normalized] = enriched
                        logger.debug(f"Replacing duplicate title '{title[:50]}...' with higher DOI")
                    elif current_numeric == existing_numeric:
                        # If DOIs are equal, keep the one with higher relevance score
                        if enriched['relevance_score'] > existing_work['relevance_score']:
                            title_to_work_map[title_normalized] = enriched
                            logger.debug(f"Replacing duplicate title '{title[:50]}...' with higher score")
                    # else: keep existing work
                else:
                    # First occurrence of this title
                    title_to_work_map[title_normalized] = enriched
        
        # Convert map back to list
        analyzed = list(title_to_work_map.values())
        
        # Многокритериальная сортировка
        analyzed.sort(key=lambda x: (
            -x['relevance_score'],          # 1. Релевантность
            -x.get('publication_year', 0),  # 2. Новизна
            -x.get('cited_by_count', 0)     # 3. Цитирования (в пределах диапазона)
        ))
        
        # Apply top_n limit
        result = analyzed[:top_n]
        
        # Log summary statistics
        logger.info(f"Found {len(result)} unique works after filtering")
        logger.info(f"Removed {len(works) - len(analyzed)} works due to filters")
        if len(analyzed) > len(result):
            logger.info(f"Limited from {len(analyzed)} to {len(result)} works by top_n parameter")
        
        return result

# ============================================================================
# НОВАЯ ФУНКЦИЯ ДЛЯ УЛУЧШЕННОГО АНАЛИЗА С ФИЛЬТРАЦИЕЙ НА СТОРОНЕ API
# ============================================================================

def analyze_filtered_works_for_topic(
    topic_id: str,
    keywords: List[str],
    selected_years: List[int],
    selected_citations: List[Tuple[int, int]],
    max_works: Optional[int] = None,
    top_n: int = 100
) -> Tuple[List[dict], int]:
    """
    Analyze works for a specific topic with server-side filtering.
    
    Args:
        topic_id: Идентификатор темы
        keywords: Список ключевых слов для анализа
        selected_years: Список выбранных годов
        selected_citations: Список диапазонов цитирований
        max_works: Максимальное количество работ для загрузки (None = все)
        top_n: Количество топ результатов для возврата
    
    Returns:
        Кортеж (список релевантных работ, общее количество работ после фильтров)
    """
    # Get input DOIs from session state to exclude them from recommendations
    input_dois = set()
    if 'dois' in st.session_state:
        # Normalize input DOIs (remove https://doi.org/ prefix for comparison)
        for doi in st.session_state.dois:
            if doi.startswith('https://doi.org/'):
                clean_doi = doi.replace('https://doi.org/', '').lower()
            else:
                clean_doi = doi.lower()
            input_dois.add(clean_doi)
        logger.info(f"Excluding {len(input_dois)} input DOIs from recommendations")
    
    # Загружаем отфильтрованные работы
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_progress(progress, count, page, total):
        progress_bar.progress(progress)
        status_text.text(f"Page {page}: {count}/{total if total > 0 else '?'} works fetched")
    
    works, total_count = fetch_filtered_works_by_topic(
        topic_id=topic_id,
        years_filter=selected_years,
        citations_filter=selected_citations,
        max_results=max_works,
        progress_callback=update_progress
    )
    
    progress_bar.empty()
    status_text.empty()
    
    if not works:
        logger.warning(f"No works found for topic {topic_id} with given filters")
        return [], total_count
    
    logger.info(f"Loaded {len(works)} works (total after filters: {total_count})")
    
    # Инициализация анализаторов
    title_analyzer = TitleKeywordsAnalyzer()
    keyword_analyzer = EnhancedKeywordAnalyzer()
    
    # Преобразуем ключевые слова в взвешенный словарь
    keywords_lower = [kw.lower() for kw in keywords]
    weighted_keywords = keyword_analyzer.extract_weighted_keywords(keywords_lower)
    
    # Добавляем исходные ключевые слова с весом
    for keyword in keywords:
        keyword_lower = keyword.lower()
        keyword_base = title_analyzer._get_base_form(keyword_lower)
        if keyword_base:
            weighted_keywords[keyword_base] = weighted_keywords.get(keyword_base, 0) + 2.0
    
    # Нормализуем веса
    if weighted_keywords:
        max_weight = max(weighted_keywords.values())
        normalized_keywords = {k: v/max_weight for k, v in weighted_keywords.items()}
    else:
        normalized_keywords = {}
    
    # Track duplicate titles to keep only one version (with highest DOI number)
    title_to_work_map = {}
    
    with st.spinner(f"Analyzing {len(works)} works with enhanced algorithm..."):
        analyzed = []
        
        for work in works:
            title = work.get('title', '')
            
            if not title:  # Skip works without title
                continue
            
            # Extract and clean DOI for comparison
            doi_raw = work.get('doi', '')
            doi_clean = ''
            if doi_raw:
                doi_clean = str(doi_raw).replace('https://doi.org/', '').lower()
            
            # RULE 1: Exclude works that match input DOIs
            if doi_clean and doi_clean in input_dois:
                logger.debug(f"Excluding work with input DOI: {doi_clean}")
                continue
            
            # Calculate enhanced relevance score
            relevance_score, matched_keywords = calculate_enhanced_relevance(
                work, normalized_keywords, title_analyzer
            )
            
            if relevance_score > 0:
                enriched = enrich_work_data(work)
                enriched.update({
                    'relevance_score': relevance_score,
                    'matched_keywords': matched_keywords,
                    'analysis_time': datetime.now().isoformat()
                })
                
                # RULE 2: Handle duplicate titles
                title_normalized = title.strip().lower()
                
                if title_normalized in title_to_work_map:
                    # We have a duplicate title, compare DOIs
                    existing_work = title_to_work_map[title_normalized]
                    existing_doi = existing_work.get('doi', '').lower()
                    current_doi = enriched.get('doi', '').lower()
                    
                    # Extract numeric parts from DOIs for comparison
                    existing_numeric = extract_numeric_from_doi(existing_doi)
                    current_numeric = extract_numeric_from_doi(current_doi)
                    
                    # Keep the work with higher numeric DOI (or higher score if DOIs equal)
                    if current_numeric > existing_numeric:
                        # Replace with current work
                        title_to_work_map[title_normalized] = enriched
                        logger.debug(f"Replacing duplicate title '{title[:50]}...' with higher DOI")
                    elif current_numeric == existing_numeric:
                        # If DOIs are equal, keep the one with higher relevance score
                        if enriched['relevance_score'] > existing_work['relevance_score']:
                            title_to_work_map[title_normalized] = enriched
                            logger.debug(f"Replacing duplicate title '{title[:50]}...' with higher score")
                    # else: keep existing work
                else:
                    # First occurrence of this title
                    title_to_work_map[title_normalized] = enriched
        
        # Convert map back to list
        analyzed = list(title_to_work_map.values())
        
        # Многокритериальная сортировка
        analyzed.sort(key=lambda x: (
            -x['relevance_score'],          # 1. Релевантность
            -x.get('publication_year', 0),  # 2. Новизна
            -x.get('cited_by_count', 0)     # 3. Цитирования (в пределах диапазона)
        ))
        
        # Apply top_n limit
        result = analyzed[:top_n]
        
        # Log summary statistics
        logger.info(f"Found {len(result)} unique works after filtering")
        logger.info(f"Removed {len(works) - len(analyzed)} works due to filters")
        if len(analyzed) > len(result):
            logger.info(f"Limited from {len(analyzed)} to {len(result)} works by top_n parameter")
        
        return result, total_count

# ============================================================================
# ФУНКЦИИ ЭКСПОРТА
# ============================================================================

def generate_csv(data: List[dict]) -> str:
    """Генерация CSV файла"""
    df = pd.DataFrame(data)
    return df.to_csv(index=False, encoding='utf-8-sig')

def generate_excel(data: List[dict]) -> bytes:
    """Генерация Excel файла"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='Papers', index=False)
        
        # Добавляем заголовок
        workbook = writer.book
        worksheet = writer.sheets['Papers']
        
        # Форматирование
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#667eea',
            'font_color': 'white',
            'border': 1
        })
        
        # Применяем к заголовкам
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Авто-ширина колонок
        for i, col in enumerate(df.columns):
            column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, min(column_len, 50))
    
    return output.getvalue()

def generate_pdf(data: List[dict], topic_name: str) -> bytes:
    """Генерация PDF файла с улучшенным дизайном и активными гиперссылками"""
    
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
    
    # Стиль для названия статьи (обычный, не ссылка)
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
    
    # Стиль для ключевых слов
    keywords_style = ParagraphStyle(
        'CustomKeywords',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#E74C3C'),
        spaceAfter=2,
        alignment=TA_LEFT,
        fontName='Helvetica-Oblique'
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

    # Добавляем логотип
    try:
        # Пробуем несколько возможных путей
        possible_paths = [
            "logo.png",  # Текущая директория
            "./logo.png",  # Относительный путь
            "app/logo.png",  # Если в поддиректории
            os.path.join(os.path.dirname(__file__), "logo.png"),  # Абсолютный путь
            os.path.join(os.getcwd(), "logo.png")  # Текущая рабочая директория
        ]
        
        logo_path = None
        for path in possible_paths:
            if os.path.exists(path):
                logo_path = path
                break
        
        if logo_path:
            # Проверяем, что файл действительно является изображением
            try:
                # Проверяем с помощью PIL
                pil_img = PILImage.open(logo_path)
                pil_img.verify()  # Проверяем целостность файла
                
                # Используем Image из reportlab
                logo = Image(logo_path, width=160, height=80)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 0.5*cm))
                logger.info(f"Logo loaded successfully from: {logo_path}")
            except Exception as img_error:
                logger.warning(f"Invalid image file at {logo_path}: {img_error}")
                raise ValueError("Invalid image file")
        else:
            logger.warning("Logo file 'logo.png' not found in any expected location")
            raise FileNotFoundError("Logo not found")
            
    except Exception as e:
        logger.error(f"Could not load logo: {e}")
        # Если логотип не загрузился, показываем эмодзи
        story.append(Paragraph("🔬", ParagraphStyle(
            'LogoEmoji',
            parent=styles['Heading1'],
            fontSize=40,
            textColor=colors.HexColor('#667eea'),
            alignment=TA_CENTER
        )))
        story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("CTA Article Recommender Pro", title_style))
    story.append(Paragraph("Fresh Papers Analysis Report", subtitle_style))
    story.append(Spacer(1, 0.8*cm))
    
    # Информация о теме
    story.append(Paragraph(f"RESEARCH TOPIC:", topic_style))
    story.append(Paragraph(f"{topic_name.upper()}", subtitle_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Мета-информация
    current_date = datetime.now().strftime('%B %d, %Y at %H:%M')
    story.append(Paragraph(f"Generated on {current_date}", meta_style))
    story.append(Paragraph(f"Total papers analyzed: {len(data)}", meta_style))
    
    # Расчет статистик
    if data:
        avg_citations = np.mean([w.get('cited_by_count', 0) for w in data])
        oa_count = sum(1 for w in data if w.get('is_oa'))
        recent_count = sum(1 for w in data if w.get('publication_year', 0) >= datetime.now().year - 2)
        
        stats_text = f"""
        Average citations: {avg_citations:.1f} | 
        Open Access papers: {oa_count} | 
        Recent papers (≤2 years): {recent_count}
        """
        story.append(Paragraph(stats_text, meta_style))
    
    story.append(Spacer(1, 1.5*cm))
    
    # Копирайт информация
    story.append(Paragraph("© CTA - Chimica Techno Acta", footer_style))
    story.append(Paragraph("https://chimicatechnoacta.ru", footer_style))
    story.append(Paragraph("Developed by daM©", footer_style))
    
    # Разделитель страниц
    story.append(PageBreak())
    
    # ========== INITIAL DATA ==========
    story.append(Paragraph("INITIAL DATA", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Получаем данные из сессии
    initial_dois = st.session_state.get('dois', [])
    selected_topic = st.session_state.get('selected_topic', 'Not selected')
    selected_years = st.session_state.get('selected_years', [])
    selected_ranges = st.session_state.get('selected_ranges', [(0, 10)])
    
    # Создаем таблицу с основными параметрами
    initial_data = [
        ["Parameter", "Value"],
        ["Total Input DOIs", len(initial_dois)],
        ["Selected Topic", clean_text(selected_topic)],
        ["Publication Years", ", ".join(map(str, selected_years))],
        ["Citation Ranges", format_citation_ranges(selected_ranges)],
        ["Analysis Date", current_date],
        ["Papers Found", len(data)]
    ]
    
    initial_table = Table(initial_data, colWidths=[doc.width/2.5, doc.width*3/5])
    initial_table.setStyle(TableStyle([
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
        ('WORDWRAP', (0, 0), (-1, -1), 'LTR'),
    ]))
    
    story.append(initial_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Отображаем DOI в виде кликабельного списка
    if initial_dois:
        story.append(Paragraph("<b>Input DOIs:</b>", ParagraphStyle(
            'DOIsHeader',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )))
        
        # Функция для создания ссылок из DOI
        def create_doi_link(doi):
            # Проверяем, есть ли уже https://doi.org/ в начале
            if doi.startswith('10.'):
                doi_url = f"https://doi.org/{doi}"
            elif doi.startswith('https://doi.org/'):
                doi_url = doi
            else:
                doi_url = f"https://doi.org/{doi}"
            
            # Экранируем для XML
            doi_url_clean = doi_url.replace('&', '&amp;')
            
            # Создаем строку с ссылкой (используем <a> вместо <link> для лучшей совместимости)
            return f"<a href='{doi_url_clean}' color='blue'>{doi_url}</a>"
        
        max_dois_to_show = min(300, len(initial_dois))
        for i, doi in enumerate(initial_dois[:max_dois_to_show], 1):
            doi_link = create_doi_link(doi)
            story.append(Paragraph(f"{i}. {doi_link}", ParagraphStyle(
                'DOILink',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.blue,
                spaceAfter=2,
                leftIndent=10,
                fontName='Helvetica',
                underline=True
            )))
        
        # Если DOI больше 25, показываем информацию
        if len(initial_dois) > max_dois_to_show:
            story.append(Paragraph(
                f"... and {len(initial_dois) - max_dois_to_show} more DOI entries", 
                ParagraphStyle(
                    'DOIsMore',
                    parent=styles['Normal'],
                    fontSize=8,
                    textColor=colors.gray,
                    spaceAfter=10,
                    leftIndent=10,
                    fontName='Helvetica-Oblique'
                )
            ))
    
    story.append(Spacer(1, 1*cm))
    
    # ========== TABLE OF CONTENTS ==========
    story.append(Paragraph("TABLE OF CONTENTS", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Создаем оглавление
    toc_items = []
    for i in range(min(20, len(data))):  # Ограничиваем 20 записями для читаемости
        title = data[i].get('title', 'Untitled')
        # Удаляем HTML-теги
        title_clean = re.sub(r'<[^>]+>', '', title)
        # Экранируем специальные символы
        title_clean = title_clean.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        toc_items.append(f"{i+1}. {title_clean[:60]}...")
    
    toc_text = "<br/>".join(toc_items[:15])  # Первые 15 в оглавлении
    story.append(Paragraph(toc_text, details_style))
    
    if len(data) > 15:
        story.append(Paragraph(f"... and {len(data)-15} more papers", details_style))
    
    story.append(PageBreak())
    
    # ========== ДЕТАЛЬНЫЙ ОТЧЕТ ПО СТАТЬЯМ ==========
    
    story.append(Paragraph("DETAILED PAPER ANALYSIS", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Вспомогательная функция для очистки текста
    def clean_text(text):
        if not text:
            return ""
        # Заменяем HTML сущности и теги
        text = re.sub(r'<[^>]+>', '', text)  # Удаляем HTML теги
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return text
    
    # Обрабатываем каждую статью
    for i, work in enumerate(data[:50], 1):
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
        journal = clean_text(work.get('journal_name', 'N/A')[:40])
        
        metrics_text = f"""
        <b>Citations:</b> {citations} | 
        <b>Year:</b> {year} | 
        <b>Relevance Score:</b> {relevance}/10 | 
        <b>Journal:</b> {journal} | 
        <b>Open Access:</b> {'Yes' if work.get('is_oa') else 'No'}
        """
        story.append(Paragraph(metrics_text, metrics_style))
        
        # Ключевые слова (если есть)
        if work.get('matched_keywords'):
            keywords = ', '.join(work.get('matched_keywords', [])[:5])
            story.append(Paragraph(f"<b>Matched Keywords:</b> {clean_text(keywords)}", keywords_style))
        
        # DOI и ссылка
        doi = work.get('doi', '')
        doi_url = work.get('doi_url', '')
        
        if doi:
            if doi_url:
                # Добавляем ссылку как отдельный параграф
                story.append(Paragraph(f"<b>DOI:</b> {clean_text(doi)}", details_style))
                story.append(Paragraph(f"<b>Link:</b> {clean_text(doi_url)}", link_style))
            else:
                story.append(Paragraph(f"<b>DOI:</b> {clean_text(doi)}", details_style))
        
        # Разделитель между статьями
        if i < min(30, len(data)):
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph("─" * 50, separator_style))
            story.append(Spacer(1, 0.3*cm))
        else:
            story.append(Spacer(1, 0.3*cm))
    
    # ========== СТАТИСТИЧЕСКАЯ СТРАНИЦА ==========
    
    if len(data) > 10:
        story.append(PageBreak())
        story.append(Paragraph("STATISTICAL SUMMARY", title_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Подготовка данных для статистики
        citations_list = [w.get('cited_by_count', 0) for w in data]
        years_list = [w.get('publication_year', 0) for w in data if w.get('publication_year', 0) > 1900]
        
        if citations_list and years_list:
            # Базовая статистика
            stats_data = [
                ["Metric", "Value"],
                ["Total Papers", len(data)],
                ["Average Citations", f"{np.mean(citations_list):.2f}"],
                ["Median Citations", f"{np.median(citations_list):.2f}"],
                ["Min Citations", min(citations_list)],
                ["Max Citations", max(citations_list)],
                ["Open Access Papers", sum(1 for w in data if w.get('is_oa'))],
                ["Average Year", f"{np.mean(years_list):.1f}"],
                ["Most Recent Year", max(years_list) if years_list else "N/A"],
                ["Average Relevance", f"{np.mean([w.get('relevance_score', 0) for w in data]):.2f}/10"]
            ]
            
            # Создаем таблицу статистики
            stats_table = Table(stats_data, colWidths=[doc.width/2.5, doc.width/3])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
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
            
            # Распределение по годам
            if years_list:
                year_counts = {}
                for year in years_list:
                    year_counts[year] = year_counts.get(year, 0) + 1
                
                sorted_years = sorted(year_counts.items())
                year_data = [["Year", "Number of Papers"]] + [[str(y), str(c)] for y, c in sorted_years[-10:]]  # Последние 10 лет
                
                if len(year_data) > 1:
                    story.append(Paragraph("Publications by Year (last 3 years)", subtitle_style))
                    year_table = Table(year_data, colWidths=[doc.width/4, doc.width/4])
                    year_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ECC71')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D5DBDB')),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F4F4')]),
                    ]))
                    story.append(year_table)
    
    # ========== ЗАКЛЮЧЕНИЕ ==========
    
    story.append(PageBreak())
    story.append(Paragraph("CONCLUSION & RECOMMENDATIONS", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Рекомендации на основе анализа
    conclusions = [
        f"This report analyzed {len(data)} fresh papers in the field of '{topic_name}'.",
        "Papers with low citation counts often represent emerging ideas or niche research areas.",
        "Consider these papers for:",
        "• Literature reviews of emerging topics",
        "• Identifying research gaps",
        "• Finding novel methodologies",
        "• Cross-disciplinary connections"
    ]
    
    for conclusion in conclusions:
        story.append(Paragraph(clean_text(conclusion), ParagraphStyle(
            'Conclusion',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=4,
            leftIndent=20 if conclusion.startswith('•') else 0,
            fontName='Helvetica'
        )))
    
    story.append(Spacer(1, 1*cm))
    
    # Заключительные замечания
    story.append(Paragraph("FINAL NOTES", subtitle_style))
    final_notes = [
        "This report was generated automatically by CTA Article Recommender Pro.",
        "All data is sourced from OpenAlex API and is subject to their terms of use.",
        "For the most current data, please visit the original sources via the provided DOIs.",
        "Citation counts are as of the report generation date and may change over time."
    ]
    
    for note in final_notes:
        story.append(Paragraph(f"• {clean_text(note)}", details_style))
    
    # Нижний колонтитул на последней странице
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("© CTA Article Recommender Pro - https://chimicatechnoacta.ru", footer_style))
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

def generate_txt(data: List[dict], topic_name: str) -> str:
    """Генерация TXT файла с улучшенным форматированием и структурой"""
    
    output = []
    
    # ========== ЗАГОЛОВОК ==========
    output.append("=" * 80)
    output.append("CTA Article Recommender Pro")
    output.append("Under-Cited Papers Analysis Report")
    output.append("=" * 80)
    output.append("")
    
    # ========== ИНФОРМАЦИЯ О ТЕМЕ ==========
    output.append("RESEARCH TOPIC:")
    output.append(f"  {topic_name.upper()}")
    output.append("")
    
    # ========== МЕТА-ИНФОРМАЦИЯ ==========
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    output.append("REPORT INFORMATION:")
    output.append(f"  Generated: {current_date}")
    output.append(f"  Papers analyzed: {len(data)}")
    
    if data:
        avg_citations = np.mean([w.get('cited_by_count', 0) for w in data])
        oa_count = sum(1 for w in data if w.get('is_oa'))
        recent_count = sum(1 for w in data if w.get('publication_year', 0) >= datetime.now().year - 2)
        
        output.append(f"  Average citations: {avg_citations:.2f}")
        output.append(f"  Open Access papers: {oa_count}")
        output.append(f"  Recent papers (≤2 years): {recent_count}")
    
    output.append("")
    output.append("© CTA - Chemical Technology Acta")
    output.append("https://chimicatechnoacta.ru")
    output.append("Developed by daM©")
    output.append("")
    output.append("=" * 80)
    output.append("")

    # ========== INITIAL DATA ==========
    output.append("INITIAL DATA")
    output.append("=" * 40)
    
    # Получаем данные из сессии
    initial_dois = st.session_state.get('dois', [])
    selected_topic = st.session_state.get('selected_topic', 'Not selected')
    selected_years = st.session_state.get('selected_years', [])
    selected_ranges = st.session_state.get('selected_ranges', [(0, 10)])
    
    # Основные параметры
    output.append(f"  Total Input DOIs: {len(initial_dois)}")
    output.append(f"  Selected Topic: {selected_topic}")
    output.append(f"  Publication Years: {', '.join(map(str, selected_years))}")
    output.append(f"  Citation Ranges: {format_citation_ranges(selected_ranges)}")
    output.append(f"  Analysis Date: {current_date}")
    output.append(f"  Papers Found: {len(data)}")
    
    # Список DOI
    if initial_dois:
        output.append("")
        output.append("  Input DOIs:")
        output.append("  " + "-" * 36)
        
        max_dois_to_show = min(300, len(initial_dois))
        for i, doi in enumerate(initial_dois[:max_dois_to_show], 1):
            # Форматируем DOI в полный URL
            if doi.startswith('10.'):
                doi_url = f"https://doi.org/{doi}"
            elif doi.startswith('https://doi.org/'):
                doi_url = doi
            else:
                doi_url = f"https://doi.org/{doi}"
            
            output.append(f"  {i:3d}. {doi_url}")
        
        if len(initial_dois) > max_dois_to_show:
            output.append(f"  ... and {len(initial_dois) - max_dois_to_show} more")
        
        output.append("  " + "-" * 36)
    
    output.append("")
    output.append("=" * 80)
    output.append("")
    
    # ========== ОГЛАВЛЕНИЕ ==========
    output.append("TABLE OF CONTENTS")
    output.append("-" * 40)
    
    # Группируем статьи по релевантности
    high_relevance = [w for w in data if w.get('relevance_score', 0) >= 8]
    medium_relevance = [w for w in data if 5 <= w.get('relevance_score', 0) < 8]
    low_relevance = [w for w in data if w.get('relevance_score', 0) < 5]
    
    output.append(f"  High Relevance (Score ≥ 8): {len(high_relevance)} papers")
    output.append(f"  Medium Relevance (5-7): {len(medium_relevance)} papers")
    output.append(f"  Low Relevance (Score < 5): {len(low_relevance)} papers")
    output.append("")
    
    # Быстрый обзор по годам
    if data:
        years = [w.get('publication_year', 0) for w in data if w.get('publication_year', 0) > 1900]
        if years:
            output.append("PUBLICATION YEAR DISTRIBUTION:")
            year_counts = {}
            for year in years:
                year_counts[year] = year_counts.get(year, 0) + 1
            
            for year in sorted(year_counts.keys(), reverse=True)[:5]:  # Топ 5 последних лет
                output.append(f"  {year}: {year_counts[year]} papers")
            output.append("")
    
    output.append("=" * 80)
    output.append("")
    
    # ========== ДЕТАЛЬНЫЙ АНАЛИЗ СТАТЕЙ ==========
    output.append("DETAILED PAPER ANALYSIS")
    output.append("=" * 80)
    output.append("")
    
    for i, work in enumerate(data, 1):
        # Номер и релевантность
        relevance_score = work.get('relevance_score', 0)
        relevance_stars = "★" * min(int(relevance_score), 5) + "☆" * max(5 - int(relevance_score), 0)
        
        output.append(f"PAPER #{i:03d}")
        output.append(f"Relevance: {relevance_score}/10 {relevance_stars}")
        output.append("-" * 40)
        
        # Заголовок
        title = work.get('title', 'No title available')
        output.append(f"TITLE: {title}")
        
        # Авторы
        authors = work.get('authors', [])
        if authors:
            output.append(f"AUTHORS: {', '.join(authors[:3])}")
            if len(authors) > 3:
                output.append(f"         + {len(authors) - 3} more authors")
        
        # Основные метрики
        citations = work.get('cited_by_count', 0)
        year = work.get('publication_year', 'N/A')
        journal = work.get('journal_name', 'N/A')
        
        output.append("METRICS:")
        output.append(f"  • Citations: {citations}")
        output.append(f"  • Year: {year}")
        output.append(f"  • Journal/Conference: {journal}")
        output.append(f"  • Open Access: {'Yes' if work.get('is_oa') else 'No'}")
        
        # Ключевые слова
        if work.get('matched_keywords'):
            keywords = work.get('matched_keywords', [])
            output.append(f"KEYWORDS: {', '.join(keywords[:5])}")
            if len(keywords) > 5:
                output.append(f"          + {len(keywords) - 5} more keywords")
        
        # DOI и ссылка
        doi = work.get('doi', '')
        doi_url = work.get('doi_url', '')
        
        if doi:
            output.append(f"DOI: {doi}")
            if doi_url:
                output.append(f"LINK: {doi_url}")
        
        # Абстракт (если есть и короткий)
        abstract = work.get('abstract', '')
        if abstract and len(abstract) < 300:
            output.append("ABSTRACT:")
            # Форматируем абстракт с переносами строк
            words = abstract.split()
            lines = []
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= 70:
                    current_line += " " + word if current_line else word
                else:
                    lines.append("  " + current_line)
                    current_line = word
            if current_line:
                lines.append("  " + current_line)
            output.extend(lines)
        
        # Разделитель между статьями
        if i < len(data):
            output.append("")
            output.append("─" * 60)
            output.append("")
    
    output.append("=" * 80)
    output.append("")
    
    # ========== СТАТИСТИЧЕСКАЯ СВОДКА ==========
    if len(data) > 5:
        output.append("STATISTICAL SUMMARY")
        output.append("=" * 80)
        output.append("")
        
        citations_list = [w.get('cited_by_count', 0) for w in data]
        relevance_list = [w.get('relevance_score', 0) for w in data]
        
        if citations_list:
            output.append("CITATION ANALYSIS:")
            output.append(f"  Average: {np.mean(citations_list):.2f}")
            output.append(f"  Median: {np.median(citations_list):.2f}")
            output.append(f"  Minimum: {min(citations_list)}")
            output.append(f"  Maximum: {max(citations_list)}")
            output.append(f"  Standard Deviation: {np.std(citations_list):.2f}")
            output.append("")
            
            # Распределение по количеству цитирований
            output.append("CITATION DISTRIBUTION:")
            ranges = [(0, 0), (1, 2), (3, 5), (6, 10), (11, 20), (21, 50), (51, 100), (101, 1000)]
            for min_cit, max_cit in ranges:
                count = sum(1 for w in data if min_cit <= w.get('cited_by_count', 0) <= max_cit)
                if count > 0:
                    if min_cit == max_cit:
                        range_str = f"Exactly {min_cit}"
                    else:
                        range_str = f"{min_cit}-{max_cit}"
                    percentage = (count / len(data)) * 100
                    output.append(f"  {range_str:12} citations: {count:3d} papers ({percentage:5.1f}%)")
            output.append("")
        
        if relevance_list:
            output.append("RELEVANCE SCORE ANALYSIS:")
            output.append(f"  Average: {np.mean(relevance_list):.2f}/10")
            output.append(f"  Median: {np.median(relevance_list):.2f}/10")
            
            # Распределение по релевантности
            relevance_counts = {score: 0 for score in range(1, 11)}
            for score in relevance_list:
                rounded = min(int(score), 10)
                relevance_counts[rounded] = relevance_counts.get(rounded, 0) + 1
            
            output.append("  Distribution:")
            for score in range(10, 0, -1):
                count = relevance_counts.get(score, 0)
                if count > 0:
                    percentage = (count / len(data)) * 100
                    stars = "★" * min(score, 5) + "☆" * max(5 - score, 0)
                    output.append(f"    Score {score:2d}/10 {stars}: {count:3d} papers ({percentage:5.1f}%)")
            output.append("")
    
    # ========== ТОП РЕКОМЕНДАЦИЙ ==========
    if len(data) > 10:
        output.append("TOP RECOMMENDATIONS")
        output.append("=" * 80)
        output.append("")
        
        # Сортируем по релевантности, затем по годам (новые первыми)
        sorted_data = sorted(data, key=lambda x: (-x.get('relevance_score', 0), 
                                                  -x.get('publication_year', 0)))
        
        output.append("Highest Relevance & Most Recent:")
        for i, work in enumerate(sorted_data[:5], 1):
            title = work.get('title', '')[:70] + "..." if len(work.get('title', '')) > 70 else work.get('title', '')
            output.append(f"  {i}. {title}")
            output.append(f"     Year: {work.get('publication_year', 'N/A')}, "
                         f"Citations: {work.get('cited_by_count', 0)}, "
                         f"Score: {work.get('relevance_score', 0)}/10")
        
        output.append("")
        output.append("Most Cited (among under-cited):")
        # Берем статьи с ненулевыми цитированиями
        cited_papers = [w for w in data if w.get('cited_by_count', 0) > 0]
        if cited_papers:
            most_cited = sorted(cited_papers, key=lambda x: -x.get('cited_by_count', 0))
            for i, work in enumerate(most_cited[:3], 1):
                title = work.get('title', '')[:70] + "..." if len(work.get('title', '')) > 70 else work.get('title', '')
                output.append(f"  {i}. {title}")
                output.append(f"     Citations: {work.get('cited_by_count', 0)}, "
                             f"Year: {work.get('publication_year', 'N/A')}")
        
        output.append("")
        output.append("Newest Publications:")
        recent_papers = sorted(data, key=lambda x: -x.get('publication_year', 0))
        for i, work in enumerate(recent_papers[:3], 1):
            title = work.get('title', '')[:70] + "..." if len(work.get('title', '')) > 70 else work.get('title', '')
            output.append(f"  {i}. {title}")
            output.append(f"     Year: {work.get('publication_year', 'N/A')}, "
                         f"Citations: {work.get('cited_by_count', 0)}")
    
    # ========== ЗАКЛЮЧЕНИЕ ==========
    output.append("=" * 80)
    output.append("CONCLUSION")
    output.append("=" * 80)
    output.append("")
    
    conclusions = [
        f"This analysis identified {len(data)} under-cited papers in '{topic_name}'.",
        "",
        "KEY INSIGHTS:",
        "• These papers may represent emerging research trends",
        "• Low citation counts don't necessarily indicate low quality",
        "• Consider these for literature reviews and gap analysis",
        "• They may contain novel methodologies or cross-disciplinary insights",
        "",
        "RECOMMENDED ACTIONS:",
        "1. Review high-relevance papers for potential citations",
        "2. Use as starting points for systematic reviews",
        "3. Identify research gaps and opportunities",
        "4. Track emerging authors in this field",
        "",
        "REPORT METADATA:",
        f"• Generated by: CTA Article Recommender Pro",
        f"• Report ID: {hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12].upper()}",
        f"• Data source: OpenAlex API",
        f"• Analysis date: {current_date}",
        "",
        "© CTA - Chemical Technology Acta | https://chimicatechnoacta.ru",
        "This report is for research purposes only.",
        "Always verify information with original sources.",
        "",
        "End of Report"
    ]
    
    output.extend(conclusions)
    
    return "\n".join(output)

# ============================================================================
# КОМПОНЕНТЫ ИНТЕРФЕЙСА
# ============================================================================

def create_progress_bar(current_step: int, total_steps: int):
    """Создает прогресс бар мастер-процесса"""
    progress = current_step / total_steps
    
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar" style="width: {progress * 100}%"></div>
    </div>
    <div class="step-indicator">
        <span class="{'active' if current_step >= 1 else ''}">📥 Data Input</span>
        <span class="{'active' if current_step >= 2 else ''}">🔍 Analysis</span>
        <span class="{'active' if current_step >= 3 else ''}">🎯 Topic Selection</span>
        <span class="{'active' if current_step >= 4 else ''}">⚙️ Filters</span>
        <span class="{'active' if current_step >= 5 else ''}">📊 Results</span>
        <span class="{'active' if current_step >= 6 else ''}">🌳 Clustering</span>
        <span class="{'active' if current_step >= 7 else ''}">📋 Classification</span>
    </div>
    """, unsafe_allow_html=True)

def create_back_button():
    """Создает кнопку возврата назад"""
    if st.session_state.current_step > 1:
        if st.button("← Back", key="back_button", use_container_width=False):
            # При возврате на шаг 4 или 5, сбрасываем кэш результатов, чтобы фильтры применились заново
            if st.session_state.current_step in [4, 5]:
                if 'filtered_works' in st.session_state:
                    del st.session_state['filtered_works']
                if 'filtered_total_count' in st.session_state:
                    del st.session_state['filtered_total_count']
                if 'filter_stats' in st.session_state:
                    del st.session_state['filter_stats']
                if 'top_keywords' in st.session_state:
                    del st.session_state['top_keywords']
            
            st.session_state.current_step -= 1
            st.rerun()

def create_metric_card_compact(title: str, value, icon: str = "📊"):
    """Создает компактную карточку с метрикой"""
    st.markdown(f"""
    <div class="metric-card">
        <h4>{icon} {title}</h4>
        <div class="value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def create_result_card_compact(work: dict, index: int):
    """Создает компактную карточку результата"""
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
                <span style="font-weight: 600; color: #667eea; margin-right: 8px;">#{index}</span>
                <span style="background: {badge_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;">
                    {badge_text}
                </span>
                <span style="background: #e3f2fd; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; margin-left: 5px;">
                    Score: {work.get('relevance_score', 0)}
                </span>
            </div>
            <span style="color: #666; font-size: 0.8rem;">{work.get('publication_year', '')}</span>
        </div>
        <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 5px; line-height: 1.3;">{title}</div>
        <div style="color: #555; font-size: 0.85rem; margin-bottom: 5px;">👤 {authors}</div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
            <span>{oa_badge} {work.get('journal_name', '')[:30]}</span>
            <a href="{doi_url}" target="_blank" style="color: #2196F3; text-decoration: none; font-size: 0.85rem;">
                🔗 View Article
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_topic_selection_ui():
    """Интерфейс выбора темы"""
    st.markdown("<h4>🎯 Select Research Topic</h4>", unsafe_allow_html=True)
    
    topics = st.session_state.topic_counter.most_common()
    
    # Показываем первые 8 тем в компактном виде
    cols = st.columns(2)
    for idx, (topic, count) in enumerate(topics[:8]):
        with cols[idx % 2]:
            is_selected = st.session_state.get('selected_topic') == topic
            st.markdown(f"""
            <div class="topic-card {'selected' if is_selected else ''}" 
                 onclick="this.style.background='#667eea10';">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: 600; font-size: 0.9rem;">{topic[:70]}{'...' if len(topic) > 70 else ''}</div>
                    <span style="background: #667eea; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;">
                        {count} papers
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Select", key=f"select_{idx}", 
                        use_container_width=True,
                        type="primary" if is_selected else "secondary"):
                st.session_state.selected_topic = topic
                
                # Находим ID темы из данных
                for work in st.session_state.works_data:
                    if work.get('primary_topic') == topic:
                        topic_id = work.get('topic_id')
                        if topic_id:
                            st.session_state.selected_topic_id = topic_id
                            break
                
                st.rerun()
    
    # Кнопка продолжения
    if 'selected_topic' in st.session_state:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⚙️ Configure Filters", type="primary", use_container_width=True, key="configure_filters"):
                st.session_state.current_step = 4
                st.rerun()

# ============================================================================
# НОВЫЙ ШАГ ДЛЯ ФИЛЬТРАЦИИ
# ============================================================================

def step_filters():
    """Шаг 4: Настройка фильтров"""
    create_back_button()
    
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">⚙️ Step 4: Configure Filters</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Set publication years and citation ranges for analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'selected_topic_id' not in st.session_state:
        st.error("❌ Topic not selected. Please go back to Step 3.")
        return
    
    topic_id = st.session_state.selected_topic_id
    topic_name = st.session_state.get('selected_topic', 'Selected Topic')
    
    # Получаем общее количество работ по теме
    with st.spinner("Getting topic statistics..."):
        total_works = get_topic_total_works_count(topic_id)
    
    if total_works == 0:
        st.error(f"❌ No works found for topic: {topic_name}")
        return
    
    st.markdown(f"""
    <div class="filter-stats">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>📊 Topic Statistics</strong><br>
                <span style="font-size: 0.9rem; color: #666;">{topic_name}</span>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 1.5rem; font-weight: 700; color: #667eea;">{total_works:,}</span><br>
                <span style="font-size: 0.8rem; color: #666;">total works</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Инициализация состояния фильтров
    if 'selected_years' not in st.session_state:
        current_year = datetime.now().year
        st.session_state.selected_years = [current_year - 2, current_year - 1, current_year]
    
    if 'selected_citations' not in st.session_state:
        st.session_state.selected_citations = [(0, 0), (1, 1), (2, 2)]
    
    # Секция фильтра по годам
    st.markdown("<div class='filter-section'>", unsafe_allow_html=True)
    st.markdown("<div class='filter-header'>📅 Publication Years</div>", unsafe_allow_html=True)
    
    current_year = datetime.now().year
    years_options = list(range(current_year - 2, current_year + 1))  # Только последние 3 года
    
    # Отображаем чекбоксы для годов в 3 колонки
    st.markdown("<div class='year-checkbox-container'>", unsafe_allow_html=True)
    
    cols = st.columns(3)
    selected_years = []
    
    for idx, year in enumerate(years_options):
        col_idx = idx % 3
        with cols[col_idx]:
            is_selected = year in st.session_state.selected_years
            if st.checkbox(f"{year}", value=is_selected, key=f"year_{year}"):
                selected_years.append(year)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Если ничего не выбрано, используем значения по умолчанию
    if not selected_years:
        selected_years = years_options
        # Обновляем чекбоксы
        for year in years_options:
            st.session_state[f"year_{year}"] = True
    
    st.session_state.selected_years = selected_years
    st.markdown(f"<div style='font-size: 0.85rem; color: #666; margin-top: 10px;'>Selected years: {', '.join(map(str, selected_years))}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Секция фильтра по цитированиям
    st.markdown("<div class='filter-section'>", unsafe_allow_html=True)
    st.markdown("<div class='filter-header'>📈 Citation Counts</div>", unsafe_allow_html=True)
    
    citation_options = list(range(0, 11))  # 0-10
    
    # Первый ряд: 0-5
    st.markdown("<div class='citation-checkbox-row'>", unsafe_allow_html=True)
    cols1 = st.columns(6)
    selected_citation_values = []
    
    for i in range(6):  # 0-5
        with cols1[i]:
            citation_value = i
            is_selected = any(start <= citation_value <= end for start, end in st.session_state.selected_citations)
            if st.checkbox(f"{citation_value}", value=is_selected, key=f"citation_{citation_value}"):
                selected_citation_values.append(citation_value)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Второй ряд: 6-10 + "Select all"
    st.markdown("<div class='citation-checkbox-row'>", unsafe_allow_html=True)
    cols2 = st.columns(6)
    
    for i in range(5):  # 6-10
        with cols2[i]:
            citation_value = i + 6
            is_selected = any(start <= citation_value <= end for start, end in st.session_state.selected_citations)
            if st.checkbox(f"{citation_value}", value=is_selected, key=f"citation_{citation_value}"):
                selected_citation_values.append(citation_value)
    
    # Колонка для "Select all"
    with cols2[5]:
        # Используем ключ для select all и обрабатываем логику позже
        select_all = st.checkbox("Select all", key="citation_all")
        
        # Если выбран select_all, то выбираем все значения
        if select_all:
            selected_citation_values = list(range(0, 11))
        # Если select_all снят и выбраны все значения, снимаем select_all
        elif len(selected_citation_values) == 11:
            # Обновляем состояние чекбокса через callback
            st.session_state.citation_all = True
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Преобразуем выбранные значения в диапазоны
    if selected_citation_values:
        selected_citation_values.sort()
        citation_ranges = []
        start = selected_citation_values[0]
        end = selected_citation_values[0]
        
        for i in range(1, len(selected_citation_values)):
            if selected_citation_values[i] == end + 1:
                end = selected_citation_values[i]
            else:
                citation_ranges.append((start, end))
                start = selected_citation_values[i]
                end = selected_citation_values[i]
        
        citation_ranges.append((start, end))
        st.session_state.selected_citations = citation_ranges
    
    # Если ничего не выбрано, используем значения по умолчанию
    if not selected_citation_values:
        st.session_state.selected_citations = [(0, 2)]
        # Обновляем чекбоксы
        for i in range(3):
            st.session_state[f"citation_{i}"] = True
    
    st.markdown(f"<div style='font-size: 0.85rem; color: #666; margin-top: 10px;'>Selected citation ranges: {format_citation_ranges(st.session_state.selected_citations)}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Кнопка запуска анализа
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🔍 Start Filtered Analysis", type="primary", use_container_width=True, key="start_filtered_analysis"):
            # Сбрасываем кэш предыдущих результатов
            if 'filtered_works' in st.session_state:
                del st.session_state['filtered_works']
            if 'filtered_total_count' in st.session_state:
                del st.session_state['filtered_total_count']
            if 'filter_stats' in st.session_state:
                del st.session_state['filter_stats']
            if 'top_keywords' in st.session_state:
                del st.session_state['top_keywords']
            
            # Сохраняем статистику фильтров для отображения
            st.session_state.filter_stats = {
                'total_works': total_works,
                'selected_years': st.session_state.selected_years,
                'selected_citations': st.session_state.selected_citations
            }
            
            st.session_state.current_step = 5
            st.rerun()

# ============================================================================
# ШАГИ МАСТЕР-ПРОЦЕССА
# ============================================================================

def step_data_input():
    """Шаг 1: Ввод данных (компактный)"""
    create_back_button()
    
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📥 Step 1: Input Research DOIs</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Enter DOI identifiers to analyze topics and keywords.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Компактный ввод
    doi_input = st.text_area(
        "**DOI Input** (one per line or comma-separated):",
        height=150,
        placeholder="Examples:\n10.1038/nmat1849\nhttps://doi.org/10.1038/nmat1849\nGeim, A., Novoselov, K. The rise of graphene. Nature Mater 6, 183–191 (2007). https://doi.org/10.1038/nmat1849",
        help="Enter up to 300 DOI identifiers"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
            if doi_input:
                dois = parse_doi_input(doi_input)
                if dois:
                    st.session_state.dois = dois
                    st.session_state.current_step = 2
                    st.rerun()
                else:
                    st.error("❌ No valid DOI identifiers found.")
            else:
                st.error("❌ Please enter at least one DOI")
    
    with col2:
        if st.button("🔄 Clear", use_container_width=True):
            st.rerun()

def step_analysis():
    """Шаг 2: Анализ (компактный)"""
    create_back_button()
    
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">🔍 Step 2: Analysis in Progress</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Fetching data from OpenAlex...</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'dois' not in st.session_state:
        st.error("❌ No data to analyze. Please go back to Step 1.")
        return
    
    dois = st.session_state.dois
    
    # Компактные метрики
    col1, col2, col3 = st.columns(3)
    with col1:
        create_metric_card_compact("DOIs", len(dois), "🔢")
    with col2:
        create_metric_card_compact("Est. Time", f"{len(dois)//10}s", "⏱️")
    with col3:
        create_metric_card_compact("API Rate", "8/sec", "⚡")
    
    # Загрузка данных
    with st.spinner("Fetching data..."):
        results, successful, failed = fetch_works_by_dois_sync(dois)
    
    # Обработка результатов
    works_data = []
    topic_counter = Counter()
    titles = []
    
    for result in results:
        if result.get('success') and result.get('data'):
            work = result['data']
            enriched = enrich_work_data(work)
            
            if enriched.get('primary_topic'):
                topic_counter[enriched['primary_topic']] += 1
            
            works_data.append(enriched)
            titles.append(enriched.get('title', ''))
    
    # Анализ ключевых слов
    keyword_counter = analyze_keywords_parallel(titles)
    
    # Сохранение результатов
    st.session_state.works_data = works_data
    st.session_state.topic_counter = topic_counter
    st.session_state.keyword_counter = keyword_counter
    st.session_state.successful = successful
    st.session_state.failed = failed
    
    # Результаты анализа
    st.markdown(f"""
    <div class="info-message">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>✅ Analysis Complete!</strong><br>
                Successfully processed {successful} papers
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Статистика
    col1, col2, col3 = st.columns(3)
    with col1:
        create_metric_card_compact("Successful", successful, "✅")
    with col2:
        create_metric_card_compact("Failed", failed, "❌")
    with col3:
        create_metric_card_compact("Topics", len(topic_counter), "🏷️")
    
    # Кнопка продолжения
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 Continue to Topic Selection", type="primary", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()

def step_topic_selection():
    """Шаг 3: Выбор темы (компактный)"""
    create_back_button()
    
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">🎯 Step 3: Select Research Topic</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Choose a topic for deep analysis of fresh papers.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.works_data:
        st.error("❌ No data available. Please start from Step 1.")
        return
    
    create_topic_selection_ui()

def step_results():
    """Шаг 5: Результаты (обновленный с фильтрацией на стороне API)"""
    create_back_button()
    
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📊 Step 5: Analysis Results</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Fresh papers in your research area with server-side filtering.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'selected_topic_id' not in st.session_state:
        st.error("❌ Topic not selected. Please go back to Step 3.")
        return
    
    # Получаем фильтры
    selected_years = st.session_state.get('selected_years', [])
    if not selected_years:
        current_year = datetime.now().year
        selected_years = [current_year - 2, current_year - 1, current_year]
        st.session_state.selected_years = selected_years
    
    selected_citations = st.session_state.get('selected_citations', [])
    if not selected_citations:
        selected_citations = [(0, 2)]
        st.session_state.selected_citations = selected_citations
    
    # Показываем статистику фильтров
    if 'filter_stats' in st.session_state:
        stats = st.session_state.filter_stats
        st.markdown(f"""
        <div class="filter-stats">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>📊 Filter Summary</strong><br>
                    <span style="font-size: 0.9rem; color: #666;">
                        Years: {', '.join(map(str, stats['selected_years']))} | 
                        Citations: {format_citation_ranges(stats['selected_citations'])}
                    </span>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 1.2rem; font-weight: 700; color: #667eea;">{stats['total_works']:,}</span><br>
                    <span style="font-size: 0.8rem; color: #666;">total works in topic</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Анализ работ по теме с фильтрацией на стороне API
    if 'filtered_works' not in st.session_state:
        with st.spinner("Searching for fresh papers with server-side filtering..."):
            # Получаем топ-10 ключевых слов
            top_keywords = [kw for kw, _ in st.session_state.keyword_counter.most_common(10)]
            
            # Сохраняем ключевые слова в сессии
            st.session_state.top_keywords = top_keywords
            
            # Выполняем улучшенный анализ с фильтрацией на стороне API
            relevant_works, filtered_total_count = analyze_filtered_works_for_topic(
                topic_id=st.session_state.selected_topic_id,
                keywords=top_keywords,
                selected_years=selected_years,
                selected_citations=selected_citations,
                max_works=15000,  # Увеличили лимит для полноты
                top_n=100
            )
        
        st.session_state.filtered_works = relevant_works
        st.session_state.filtered_total_count = filtered_total_count
    else:
        relevant_works = st.session_state.filtered_works
        filtered_total_count = st.session_state.filtered_total_count
    
    # Статистика
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        create_metric_card_compact("Filtered Works", f"{filtered_total_count:,}", "📄")
    with col2:
        create_metric_card_compact("Papers Found", len(relevant_works), "🎯")
    with col3:
        if relevant_works:
            avg_citations = np.mean([w.get('cited_by_count', 0) for w in relevant_works])
            create_metric_card_compact("Avg Citations", f"{avg_citations:.1f}", "📈")
        else:
            create_metric_card_compact("Avg Citations", "0", "📈")
    with col4:
        oa_count = sum(1 for w in relevant_works if w.get('is_oa'))
        create_metric_card_compact("Open Access", oa_count, "🔓")
    with col5:
        current_year = datetime.now().year
        recent_count = sum(1 for w in relevant_works if w.get('publication_year', 0) >= current_year - 2)
        create_metric_card_compact("Recent (≤2y)", recent_count, "🕒")
    
    if not relevant_works:
        # Добавляем отладочную информацию
        st.markdown(f"""
        <div class="warning-message">
            <strong>⚠️ No papers match your filters</strong><br>
            <strong>Debug info:</strong><br>
            - Topic ID: {st.session_state.get('selected_topic_id', 'Not set')}<br>
            - Years filter: {selected_years}<br>
            - Citation ranges: {format_citation_ranges(selected_citations)}<br>
            - Total works after filters: {filtered_total_count}<br>
            <br>
            This might happen when:<br>
            1. Current year selected with high citation threshold (papers might not have enough citations yet)<br>
            2. Very specific citation range selected<br>
            3. Topic has limited publications in selected years<br>
            <br>
            Try adjusting your filters in Step 4.
        </div>
        """, unsafe_allow_html=True)
        
        # Для отладки также покажем логи
        logger.warning(f"No relevant works found for topic {st.session_state.get('selected_topic_id')}")
        logger.warning(f"Filters: years={selected_years}, citation_ranges={selected_citations}")
        logger.warning(f"Total works after filters: {filtered_total_count}")
    else:
        # Результаты в виде карточек
        st.markdown("<h4>🎯 Recommended Papers:</h4>", unsafe_allow_html=True)
        
        for idx, work in enumerate(relevant_works[:10], 1):
            create_result_card_compact(work, idx)
        
        # Таблица для детального просмотра
        st.markdown("<h4>📋 Detailed View:</h4>", unsafe_allow_html=True)
        
        display_data = []
        for i, work in enumerate(relevant_works, 1):
            doi_url = work.get('doi_url', '')
            title = work.get('title', '')
            
            display_data.append({
                '#': i,
                'Title': title[:60] + '...' if len(title) > 60 else title,
                'Citations': work.get('cited_by_count', 0),
                'Relevance': work.get('relevance_score', 0),
                'Year': work.get('publication_year', ''),
                'Journal': work.get('journal_name', '')[:20],
                'DOI': doi_url if doi_url else 'N/A',
                'OA': '✅' if work.get('is_oa') else '❌',
                'Authors': ', '.join(work.get('authors', [])[:2])
            })
        
        df = pd.DataFrame(display_data)
        
        # Используем column_config без LinkColumn для чистых URL
        st.dataframe(
            df,
            use_container_width=True,
            height=300,
            column_config={
                "DOI": st.column_config.TextColumn(
                    "DOI",
                    help="Click to copy or open in browser",
                    width="medium"
                ),
                "Relevance": st.column_config.ProgressColumn(
                    "Relevance",
                    help="Relevance score (higher is better)",
                    format="%d",
                    min_value=1,
                    max_value=10
                )
            }
        )
        
        # Экспорт в разные форматы
        st.markdown("<h4>📥 Export Results:</h4>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            csv = generate_csv(relevant_works)
            st.download_button(
                label="📊 CSV",
                data=csv,
                file_name=f"under_cited_papers_{st.session_state.get('selected_topic', 'results').replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            excel_data = generate_excel(relevant_works)
            st.download_button(
                label="📈 Excel",
                data=excel_data,
                file_name=f"under_cited_papers_{st.session_state.get('selected_topic', 'results').replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col3:
            txt_data = generate_txt(relevant_works, st.session_state.get('selected_topic', 'Results'))
            st.download_button(
                label="📝 TXT",
                data=txt_data,
                file_name=f"under_cited_papers_{st.session_state.get('selected_topic', 'results').replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col4:
            pdf_data = generate_pdf(relevant_works[:50], st.session_state.get('selected_topic', 'Results'))
            st.download_button(
                label="📄 PDF",
                data=pdf_data,
                file_name=f"under_cited_papers_{st.session_state.get('selected_topic', 'results').replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        # Кнопка перехода к кластеризации
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🌳 Proceed to Hierarchical Clustering", type="primary", use_container_width=True):
                st.session_state.current_step = 6
                st.rerun()

# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def main():
    """Главная функция приложения"""
    
    # Инициализация состояния
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    
    # Заголовок (компактный)
    st.markdown("""
    <h1 class="main-header">🔬 CTA Article Recommender Pro</h1>
    <p style="font-size: 1rem; color: #666; margin-bottom: 1.5rem;">
    Discover fresh papers using AI-powered analysis with server-side filtering
    </p>
    """, unsafe_allow_html=True)
    
    # Прогресс бар (обновлен для 7 шагов)
    create_progress_bar(st.session_state.current_step, 7)
    
    # Очистка старого кэша
    clear_old_cache()
    
    # Отображение текущего шага
    if st.session_state.current_step == 1:
        step_data_input()
    elif st.session_state.current_step == 2:
        step_analysis()
    elif st.session_state.current_step == 3:
        step_topic_selection()
    elif st.session_state.current_step == 4:
        step_filters()
    elif st.session_state.current_step == 5:
        step_results()
    elif st.session_state.current_step == 6:
        hierarchical_clustering_interface()
    elif st.session_state.current_step == 7:
        step_classification_results()
    
    # Футер
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888; font-size: 0.8rem; margin-top: 1rem;">
        <p>© CTA, https://chimicatechnoacta.ru / developed by daM©</p>
        <p style="font-size: 0.7rem; color: #aaa;">v3.0 with hierarchical clustering and classification</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
