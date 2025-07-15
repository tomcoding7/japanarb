from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import re
import logging
from dataclasses import dataclass
from openai import OpenAI
import os
from dotenv import load_dotenv
import json

logger = logging.getLogger(__name__)

class CardCondition(Enum):
    MINT = "MINT"
    NEAR_MINT = "NEAR_MINT"
    EXCELLENT = "EXCELLENT"
    VERY_GOOD = "VERY_GOOD"
    GOOD = "GOOD"
    LIGHT_PLAYED = "LIGHT_PLAYED"
    PLAYED = "PLAYED"
    HEAVILY_PLAYED = "HEAVILY_PLAYED"
    DAMAGED = "DAMAGED"
    UNKNOWN = "UNKNOWN"

@dataclass
class CardInfo:
    condition: Optional[CardCondition] = None
    rarity: Optional[str] = None
    set_code: Optional[str] = None
    card_number: Optional[str] = None
    edition: Optional[str] = None
    region: Optional[str] = None
    is_valuable: bool = False
    confidence_score: float = 0.0
    matched_keywords: List[str] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    estimated_value: Optional[Dict[str, float]] = None
    profit_potential: Optional[float] = None
    recommendation: Optional[str] = None

class CardAnalyzer:
    def __init__(self, use_llm: bool = False):
        self.use_llm = False  # Always disable LLM/AI
        
        # Initialize OpenAI client only if LLM is enabled and API key is available
        self.client = None
        if self.use_llm:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key and api_key != 'your_openai_api_key_here':
                try:
                    self.client = OpenAI(api_key=api_key)
                    logger.info("LLM analysis enabled - OpenAI client initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI client: {str(e)}")
                    self.use_llm = False
            else:
                logger.warning("LLM analysis disabled - No valid OpenAI API key found")
                self.use_llm = False
        
        if not self.use_llm:
            logger.info("Using rule-based analysis only (LLM disabled)")
        
        # Valuable card names (both Japanese and English)
        self.valuable_card_names = [
            'デーモンの召喚', 'Summoned Skull',
            'ブルーアイズ', 'Blue-Eyes', 'ブラックマジシャン', 'Dark Magician',
            '真紅眼の黒竜', 'Red-Eyes Black Dragon',
            '青眼の白龍', 'Blue-Eyes White Dragon',
            'ブラック・マジシャン', 'Dark Magician',
            '混沌の黒魔術師', 'Dark Magician of Chaos',
            'サイバー・ドラゴン', 'Cyber Dragon',
            'E・HERO ネオス', 'Elemental HERO Neos',
            'スターダスト・ドラゴン', 'Stardust Dragon',
            'ブラック・ローズ・ドラゴン', 'Black Rose Dragon',
            'マジシャンズ・ヴァルキリア', 'Magician\'s Valkyria',
            'チョコレート・マジシャン・ガール', 'Chocolate Magician Girl',
            '青き眼の乙女', 'Maiden with Eyes of Blue',
            'ドラゴン・ナイト・ガイア', 'Dragon Knight Gaia'
        ]
        
        # Valuable sets, promos, and editions
        self.valuable_sets_and_promos = [
            'DMG', 'DM1', 'GB', 'GB特典', '初期版', 'AYUJ-JPN', 'お買い上げ特典', 'プロモ', 'promo', '限定',
            'LOB', 'SDK', 'SRL', 'PSV', 'MRL', 'MRD', 'SKE', 'SDJ', 'SDY', 'SDK',
            '1st', 'first edition', '初版', '初刷', 'limited edition', '限定版',
            'game boy', 'GB', 'DMG', 'DM1', 'DM2', 'DM3', 'DM4', 'DM5',
            'tournament pack', 'TP', 'championship', 'champion', 'champions',
            'shonen jump', 'SJ', 'jump', 'vjump', 'v-jump', 'vj', 'v-j',
            'duelist league', 'DL', 'duelist', 'league',
            'world championship', 'WC', 'world', 'championship',
            'promotional', 'promo', 'promotional card', 'promotional pack',
            'special edition', 'special pack', 'special set',
            'collector\'s tin', 'collector\'s box', 'collector\'s pack',
            'anniversary', 'anniversary pack', 'anniversary box',
            'premium pack', 'premium box', 'premium tin',
            'gold series', 'gold', 'gold pack', 'gold box',
            'platinum', 'platinum pack', 'platinum box',
            'secret', 'secret rare', 'ultimate', 'ultimate rare',
            'ghost', 'ghost rare', 'starlight', 'starlight rare',
            'quarter century', 'qcsr', 'prismatic', 'prismatic secret'
        ]
        
        # Condition keywords (Japanese and English)
        self.condition_keywords = {
            CardCondition.MINT: ['mint', '未使用', '新品', 'perfect', 'perfect condition'],
            CardCondition.NEAR_MINT: ['near mint', 'ほぼ新品', '美品', 'excellent', 'excellent condition'],
            CardCondition.EXCELLENT: ['excellent', '優良', 'very good', 'very good condition'],
            CardCondition.VERY_GOOD: ['very good', '良好', 'good', 'good condition'],
            CardCondition.GOOD: ['good', '普通', 'fair', 'fair condition'],
            CardCondition.LIGHT_PLAYED: ['light played', '軽度使用', 'lightly played', 'lightly used'],
            CardCondition.PLAYED: ['played', '使用済み', 'used', 'used condition'],
            CardCondition.HEAVILY_PLAYED: ['heavily played', '重度使用', 'heavily used', 'damaged'],
            CardCondition.DAMAGED: ['damaged', '損傷', 'broken', 'broken condition']
        }
        
        # Rarity keywords (Japanese and English)
        self.rarity_keywords = {
            'Secret Rare': ['secret rare', 'シークレットレア', 'sr'],
            'Ultimate Rare': ['ultimate rare', 'アルティメットレア', 'ur'],
            'Ghost Rare': ['ghost rare', 'ゴーストレア', 'gr'],
            'Collector\'s Rare': ['collector\'s rare', 'コレクターズレア', 'cr'],
            'Starlight Rare': ['starlight rare', 'スターライトレア', 'str'],
            'Quarter Century Secret Rare': ['quarter century secret rare', 'クォーターセンチュリーシークレットレア', 'qcsr'],
            'Prismatic Secret Rare': ['prismatic secret rare', 'プリズマティックシークレットレア', 'psr'],
            'Platinum Secret Rare': ['platinum secret rare', 'プラチナシークレットレア', 'plsr'],
            'Gold Secret Rare': ['gold secret rare', 'ゴールドシークレットレア', 'gsr'],
            'Ultra Rare': ['ultra rare', 'ウルトラレア', 'ur'],
            'Super Rare': ['super rare', 'スーパーレア', 'sr'],
            'Rare': ['rare', 'レア', 'r'],
            'Common': ['common', 'ノーマル', 'n']
        }
        
        # Edition keywords (Japanese and English)
        self.edition_keywords = {
            '1st Edition': ['1st', 'first edition', '初版', '初刷'],
            'Unlimited': ['unlimited', '無制限', '再版', '再刷']
        }
        
        # Region keywords (Japanese and English)
        self.region_keywords = {
            'Asia': ['asia', 'asian', 'アジア', 'アジア版'],
            'English': ['english', '英', '英語版'],
            'Japanese': ['japanese', '日', '日本語版'],
            'Korean': ['korean', '韓', '韓国版']
        }

    def analyze_card(self, item_data: Dict[str, Any], rank_analysis_results: Optional[Dict] = None, llm_analysis: Optional[Dict] = None) -> CardInfo:
        """
        Analyze a card listing using both rule-based and AI analysis.
        
        Args:
            item_data: Dictionary containing card information (title, description, price, etc.)
            rank_analysis_results: Optional results from RankAnalyzer
            llm_analysis: Optional results from previous LLM analysis
            
        Returns:
            CardInfo object with analysis results
        """
        try:
            title = item_data.get('title', '')
            description = item_data.get('description', '')
            price = item_data.get('price', 0)
            image_urls = item_data.get('image_urls', [])
            
            # Initialize CardInfo
            card_info = CardInfo(
                matched_keywords=[],
                ai_analysis={},
                estimated_value={'min': 0.0, 'max': 0.0},
                profit_potential=0.0,
                recommendation=""
            )
            
            # 1. Basic Text Analysis
            title_lower = title.lower()
            description_lower = description.lower() if description else ""
            
            # Check for valuable card names
            valuable_name_matches = [name for name in self.valuable_card_names if name.lower() in title_lower or name.lower() in description_lower]
            if valuable_name_matches:
                card_info.matched_keywords.extend(valuable_name_matches)
            
            # Check for valuable sets/promos
            valuable_set_matches = [term for term in self.valuable_sets_and_promos if term.lower() in title_lower or term.lower() in description_lower]
            if valuable_set_matches:
                card_info.matched_keywords.extend(valuable_set_matches)
            
            # 2. AI Analysis
            # Only do rule-based analysis, never call OpenAI
            
            # 3. Combine Rule-Based and AI Analysis
            # If we have both valuable name and set/promo matches, boost confidence
            if valuable_name_matches and valuable_set_matches:
                card_info.is_valuable = True
                card_info.confidence_score = max(card_info.confidence_score, 0.7)  # Minimum 0.7 if both present
            
            # If AI analysis suggests high value, boost confidence
            # This part is now always rule-based, so no LLM influence here.
            # card_info.is_valuable = True
            # card_info.confidence_score = max(card_info.confidence_score, 0.8)
            
            # 4. Extract Additional Details
            # Set code and card number
            set_code_match = re.search(r'([A-Z]{2,4})-([A-Z]{2})(\d{3})', title)
            if set_code_match:
                card_info.set_code = set_code_match.group(1)
                card_info.card_number = set_code_match.group(3)
            
            # Rarity
            for rarity, keywords in self.rarity_keywords.items():
                if any(keyword.lower() in title_lower or keyword.lower() in description_lower for keyword in keywords):
                    card_info.rarity = rarity
                    break
            
            # Edition
            for edition, keywords in self.edition_keywords.items():
                if any(keyword.lower() in title_lower or keyword.lower() in description_lower for keyword in keywords):
                    card_info.edition = edition
                    break
            
            # Region
            for region, keywords in self.region_keywords.items():
                if any(keyword.lower() in title_lower or keyword.lower() in description_lower for keyword in keywords):
                    card_info.region = region
                    break
            
            # Condition (from rank analysis if available)
            if rank_analysis_results and 'condition' in rank_analysis_results:
                try:
                    card_info.condition = CardCondition(rank_analysis_results['condition'])
                except ValueError:
                    card_info.condition = CardCondition.UNKNOWN
            
            return card_info
            
        except Exception as e:
            logger.error(f"Error analyzing card: {str(e)}")
            return CardInfo(
                condition=CardCondition.UNKNOWN,
                is_valuable=False,
                confidence_score=0.0,
                matched_keywords=[],
                estimated_value={'min': 0.0, 'max': 0.0},
                profit_potential=0.0,
                recommendation="Error in analysis"
            ) 