#!/usr/bin/env python3
"""
Evaluation script for subtitle quality assessment using LLM.

This script parses English and Russian subtitle files, randomly selects N pairs,
and evaluates how well they match using an LLM (OpenRouter or LMStudio).
"""

import os
import sys
import argparse
import random
import json
from typing import List, Dict, Tuple
from pathlib import Path

# Add backend to path to import SRT parser
backend_path = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_path))

from infrastructure.srt_parser import parse_srt, match_cues, Cue


# ============================================================================
# LLM Evaluators
# ============================================================================

class LLMEvaluator:
    """Base class for LLM evaluators."""

    def evaluate(self, en_text: str, ru_text: str) -> int:
        """
        Evaluate how well the Russian text matches the English text.

        Args:
            en_text: English subtitle text
            ru_text: Russian subtitle text

        Returns:
            Score from 1 to 10
        """
        raise NotImplementedError


class OpenRouterEvaluator(LLMEvaluator):
    """Evaluator using OpenRouter API."""

    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet"):
        """
        Initialize OpenRouter evaluator.

        Args:
            api_key: OpenRouter API key
            model: Model identifier (default: claude-3.5-sonnet)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def evaluate(self, en_text: str, ru_text: str) -> int:
        """Evaluate using OpenRouter API."""
        import requests

        prompt = f"""Оцени по шкале от 1 до 10, насколько хорошо русский перевод соответствует английскому тексту из субтитров.

Английский текст: "{en_text}"
Русский текст: "{ru_text}"

Верни ТОЛЬКО число от 1 до 10, где:
- 1-3: Плохое соответствие (смысл полностью искажен или тексты не связаны)
- 4-6: Среднее соответствие (общий смысл передан, но есть заметные расхождения)
- 7-9: Хорошее соответствие (точный перевод с небольшими различиями)
- 10: Отличное соответствие (практически идеальный перевод)

Ответ (только число):"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 10
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()

            # Extract number from response
            score = int(''.join(filter(str.isdigit, content))[:2])
            return max(1, min(10, score))  # Clamp to 1-10

        except Exception as e:
            print(f"⚠️  OpenRouter API error: {e}")
            return -1


class LMStudioEvaluator(LLMEvaluator):
    """Evaluator using local LMStudio instance."""

    def __init__(self, base_url: str = "http://localhost:1234/v1/chat/completions",
                 model: str = "local-model"):
        """
        Initialize LMStudio evaluator.

        Args:
            base_url: LMStudio API endpoint
            model: Model identifier (typically "local-model" or specific model name)
        """
        self.base_url = base_url
        self.model = model

    def evaluate(self, en_text: str, ru_text: str) -> int:
        """Evaluate using LMStudio local API."""
        import requests

        prompt = f"""Оцени по шкале от 1 до 10, насколько хорошо русский перевод соответствует английскому тексту из субтитров.

Английский текст: "{en_text}"
Русский текст: "{ru_text}"

Верни ТОЛЬКО число от 1 до 10, где:
- 1-3: Плохое соответствие (смысл полностью искажен или тексты не связаны)
- 4-6: Среднее соответствие (общий смысл передан, но есть заметные расхождения)
- 7-9: Хорошее соответствие (точный перевод с небольшими различиями)
- 10: Отличное соответствие (практически идеальный перевод)

Ответ (только число):"""

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 10
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()

            # Extract number from response
            score = int(''.join(filter(str.isdigit, content))[:2])
            return max(1, min(10, score))  # Clamp to 1-10

        except Exception as e:
            print(f"⚠️  LMStudio API error: {e}")
            return -1


# ============================================================================
# Main Evaluation Logic
# ============================================================================

def create_subtitle_pairs(en_path: str, ru_path: str) -> List[Dict[str, str]]:
    """
    Parse subtitle files and create list of {'en': ..., 'ru': ...} dictionaries.

    Uses the same logic as file upload process in SubReverse.

    Args:
        en_path: Path to English .srt file
        ru_path: Path to Russian .srt file

    Returns:
        List of subtitle pair dictionaries
    """
    print(f"📄 Parsing English subtitles: {en_path}")
    en_cues = parse_srt(en_path)
    print(f"   Found {len(en_cues)} English cues")

    print(f"📄 Parsing Russian subtitles: {ru_path}")
    ru_cues = parse_srt(ru_path)
    print(f"   Found {len(ru_cues)} Russian cues")

    print("🔗 Matching subtitle pairs by timing...")
    matched_pairs = match_cues(en_cues, ru_cues, tolerance_ms=1000)
    print(f"   Matched {len(matched_pairs)} pairs")

    # Convert to dictionary format
    result = []
    for en_cue, ru_cue in matched_pairs:
        if ru_cue:  # Only include pairs with both languages
            result.append({
                'en': en_cue.text,
                'ru': ru_cue.text
            })

    print(f"✅ Created {len(result)} complete pairs\n")
    return result


def evaluate_pairs(pairs: List[Dict[str, str]],
                   count: int,
                   evaluator: LLMEvaluator) -> Tuple[List[int], float]:
    """
    Randomly select and evaluate N subtitle pairs.

    Args:
        pairs: List of subtitle pair dictionaries
        count: Number of pairs to evaluate
        evaluator: LLM evaluator instance

    Returns:
        Tuple of (list of scores, average score)
    """
    if count > len(pairs):
        print(f"⚠️  Requested {count} evaluations, but only {len(pairs)} pairs available")
        count = len(pairs)

    print(f"🎲 Randomly selecting {count} pairs for evaluation...\n")
    selected = random.sample(pairs, count)

    scores = []
    valid_scores = []

    for i, pair in enumerate(selected, 1):
        print(f"[{i}/{count}] Evaluating pair:")
        print(f"   EN: {pair['en'][:80]}{'...' if len(pair['en']) > 80 else ''}")
        print(f"   RU: {pair['ru'][:80]}{'...' if len(pair['ru']) > 80 else ''}")

        score = evaluator.evaluate(pair['en'], pair['ru'])
        scores.append(score)

        if score > 0:
            valid_scores.append(score)
            print(f"   ⭐ Score: {score}/10\n")
        else:
            print(f"   ❌ Evaluation failed\n")

    if valid_scores:
        avg_score = sum(valid_scores) / len(valid_scores)
    else:
        avg_score = 0.0

    return scores, avg_score


def print_results(scores: List[int], avg_score: float):
    """Print evaluation results summary."""
    print("=" * 60)
    print("📊 EVALUATION RESULTS")
    print("=" * 60)

    valid_scores = [s for s in scores if s > 0]
    failed_count = len(scores) - len(valid_scores)

    print(f"\n📝 Individual Scores: {valid_scores}")

    if failed_count > 0:
        print(f"❌ Failed evaluations: {failed_count}")

    if valid_scores:
        print(f"\n📈 Statistics:")
        print(f"   Average Score: {avg_score:.2f}/10")
        print(f"   Min Score: {min(valid_scores)}/10")
        print(f"   Max Score: {max(valid_scores)}/10")
        print(f"   Total Evaluated: {len(valid_scores)}")

        # Quality assessment
        if avg_score >= 8:
            quality = "Excellent ⭐⭐⭐"
        elif avg_score >= 6:
            quality = "Good ⭐⭐"
        elif avg_score >= 4:
            quality = "Fair ⭐"
        else:
            quality = "Poor ❌"

        print(f"   Overall Quality: {quality}")
    else:
        print("\n❌ No successful evaluations")

    print("\n" + "=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate subtitle pair quality using LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using OpenRouter (set OPENROUTER_API_KEY environment variable)
  python evaluate.py movie_en.srt movie_ru.srt 10 --provider openrouter

  # Using OpenRouter with explicit API key
  python evaluate.py movie_en.srt movie_ru.srt 10 --provider openrouter --api-key sk-xxx

  # Using LMStudio (default endpoint: http://localhost:1234)
  python evaluate.py movie_en.srt movie_ru.srt 10 --provider lmstudio

  # Using LMStudio with custom endpoint
  python evaluate.py movie_en.srt movie_ru.srt 10 --provider lmstudio --lmstudio-url http://localhost:5000/v1/chat/completions
        """
    )

    parser.add_argument(
        "en_file",
        help="Path to English .srt subtitle file"
    )
    parser.add_argument(
        "ru_file",
        help="Path to Russian .srt subtitle file"
    )
    parser.add_argument(
        "count",
        type=int,
        help="Number of pairs to evaluate"
    )
    parser.add_argument(
        "--provider",
        choices=["openrouter", "lmstudio"],
        default="openrouter",
        help="LLM provider to use (default: openrouter)"
    )
    parser.add_argument(
        "--api-key",
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)"
    )
    parser.add_argument(
        "--model",
        help="Model identifier (OpenRouter: anthropic/claude-3.5-sonnet, LMStudio: model name)"
    )
    parser.add_argument(
        "--lmstudio-url",
        default="http://localhost:1234/v1/chat/completions",
        help="LMStudio API endpoint (default: http://localhost:1234/v1/chat/completions)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducible sampling"
    )

    args = parser.parse_args()

    # Validate files exist
    if not os.path.isfile(args.en_file):
        print(f"❌ Error: English file not found: {args.en_file}")
        sys.exit(1)

    if not os.path.isfile(args.ru_file):
        print(f"❌ Error: Russian file not found: {args.ru_file}")
        sys.exit(1)

    if args.count <= 0:
        print(f"❌ Error: Count must be positive, got: {args.count}")
        sys.exit(1)

    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
        print(f"🎲 Using random seed: {args.seed}\n")

    # Create evaluator
    print(f"🤖 Initializing {args.provider.upper()} evaluator...")

    if args.provider == "openrouter":
        api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("❌ Error: OpenRouter API key required")
            print("   Set OPENROUTER_API_KEY environment variable or use --api-key")
            sys.exit(1)

        model = args.model or "anthropic/claude-3.5-sonnet"
        evaluator = OpenRouterEvaluator(api_key, model)
        print(f"   Model: {model}\n")

    else:  # lmstudio
        model = args.model or "local-model"
        evaluator = LMStudioEvaluator(args.lmstudio_url, model)
        print(f"   Endpoint: {args.lmstudio_url}")
        print(f"   Model: {model}\n")

    # Parse subtitle files
    try:
        pairs = create_subtitle_pairs(args.en_file, args.ru_file)
    except Exception as e:
        print(f"❌ Error parsing subtitle files: {e}")
        sys.exit(1)

    if not pairs:
        print("❌ Error: No valid subtitle pairs found")
        sys.exit(1)

    # Evaluate pairs
    print(f"🚀 Starting evaluation of {args.count} pairs...\n")
    scores, avg_score = evaluate_pairs(pairs, args.count, evaluator)

    # Print results
    print_results(scores, avg_score)


if __name__ == "__main__":
    main()
