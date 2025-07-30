import os
import google.generativeai as genai
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

genai_api_key = os.getenv('GEMINI_API_KEY')
if not genai_api_key:
    raise RuntimeError('GEMINI_API_KEY not set in environment')

genai.configure(api_key=genai_api_key)

class GeminiAnalyzer:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')

    def analyze_deal(self, card_title: str, price_usd: float, comps: Dict[str, Any], image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Analyze a card deal using Gemini. Returns a dict with 'score' (0-100) and 'explanation'.
        """
        prompt = self._build_prompt(card_title, price_usd, comps)
        if image_bytes:
            # Use vision model if image is provided
            response = self.vision_model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_bytes}
            ])
        else:
            response = self.model.generate_content(prompt)
        text = response.text.strip()
        # Try to extract score and explanation
        score, explanation = self._parse_response(text)
        return {"score": score, "explanation": explanation, "raw": text}

    def _build_prompt(self, card_title, price_usd, comps):
        comps_str = self._comps_to_str(comps)
        return (
            f"""
You are an expert in trading card arbitrage. Analyze the following card listing and comps, and rate its arbitrage potential on a scale of 0-100 (higher is better). Provide a short explanation.\n\n"
            f"Card Title: {card_title}\n"
            f"Sale Price (USD): {price_usd}\n"
            f"Comps: {comps_str}\n"
            f"\nRespond in the format:\nScore: <number>\nExplanation: <short explanation>\n"
        )

    def _comps_to_str(self, comps):
        # Convert comps dict to a readable string
        if not comps:
            return "No comps available."
        lines = []
        for k, v in comps.items():
            lines.append(f"{k}: {v}")
        return " | ".join(lines)

    def _parse_response(self, text: str):
        import re
        score_match = re.search(r"Score:\s*(\d+)", text)
        explanation_match = re.search(r"Explanation:\s*(.*)", text, re.DOTALL)
        score = int(score_match.group(1)) if score_match else None
        explanation = explanation_match.group(1).strip() if explanation_match else text
        return score, explanation 