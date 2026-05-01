"""
Memory Manager - Persistent storage of predictions and outcomes
Reduces compute by referencing past analysis instead of recomputing
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
import shutil
import yfinance as yf

from config import MEMORY_DIR, MEMORY_FILE, OUTCOMES_FILE, MAX_MEMORY_ENTRIES


class PredictionMemory:
    """
    Stores past predictions and their outcomes
    Allows the system to learn without recomputing everything
    """

    def __init__(self):
        self.memory_file = MEMORY_FILE
        self.outcomes_file = OUTCOMES_FILE
        self.memory = self._load_memory()
        self.outcomes = self._load_outcomes()

    def _load_memory(self) -> Dict:
        """Load prediction memory from disk"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'predictions': [], 'metadata': {'last_update': '', 'version': '1.0'}}

    def _load_outcomes(self) -> Dict:
        """Load prediction outcomes from disk"""
        if self.outcomes_file.exists():
            try:
                with open(self.outcomes_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'outcomes': [], 'metadata': {'last_update': ''}}

    def save(self):
        """Atomically save data to disk"""
        # Write memory to temp file first
        temp_file = self.memory_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                json.dump(self.memory, f, indent=2, default=str)
            # Atomic replace
            shutil.move(str(temp_file), str(self.memory_file))

            # Remove old backup if exists
            if self.memory_file.with_suffix('.bak').exists():
                self.memory_file.with_suffix('.bak').unlink()
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            if temp_file.exists():
                temp_file.unlink()

        # Write outcomes to temp file first
        temp_file = self.outcomes_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                json.dump(self.outcomes, f, indent=2, default=str)
            # Atomic replace
            shutil.move(str(temp_file), str(self.outcomes_file))

            # Remove old backup if exists
            if self.outcomes_file.with_suffix('.bak').exists():
                self.outcomes_file.with_suffix('.bak').unlink()
        except Exception as e:
            logger.error(f"Failed to save outcomes: {e}")
            if temp_file.exists():
                temp_file.unlink()

    def add_prediction(self, ticker: str, prediction: Dict):
        """Store a new prediction"""
        entry = {
            'id': f"{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'prediction': prediction,
            'outcome_recorded': False
        }

        self.memory['predictions'].append(entry)
        self.memory['metadata']['last_update'] = datetime.now().isoformat()

        # Trim old entries to keep memory manageable
        if len(self.memory['predictions']) > MAX_MEMORY_ENTRIES:
            self.memory['predictions'] = self.memory['predictions'][-MAX_MEMORY_ENTRIES:]

        self.save()

    def get_past_predictions(self, ticker: str, days: int = 30) -> List[Dict]:
        """Retrieve past predictions for a ticker"""
        cutoff = datetime.now() - timedelta(days=days)

        return [
            p for p in self.memory['predictions']
            if p['ticker'] == ticker and
               datetime.fromisoformat(p['timestamp']) > cutoff
        ]

    def get_similar_predictions(self, ticker: str, signal_type: str, days: int = 60) -> List[Dict]:
        """Find similar past predictions to avoid recomputing"""
        past = self.get_past_predictions(ticker, days)

        return [
            p for p in past
            if p['prediction'].get('signal') == signal_type
        ]

    def record_outcome(self, prediction_id: str, actual_outcome: Dict):
        """Record the actual outcome of a prediction"""
        outcome = {
            'prediction_id': prediction_id,
            'timestamp': datetime.now().isoformat(),
            'outcome': actual_outcome,
            'correct': self._evaluate_prediction(prediction_id, actual_outcome)
        }

        self.outcomes['outcomes'].append(outcome)

        # Mark prediction as having outcome recorded
        for pred in self.memory['predictions']:
            if pred['id'] == prediction_id:
                pred['outcome_recorded'] = True
                break

        self.save()

    def _evaluate_prediction(self, prediction_id: str, outcome: Dict) -> Optional[bool]:
        """Evaluate if a prediction was correct"""
        for pred in self.memory['predictions']:
            if pred['id'] == prediction_id:
                predicted_signal = pred['prediction'].get('signal')
                actual_return = outcome.get('return_pct', 0)

                if predicted_signal == 'BUY' and actual_return > 0:
                    return True
                elif predicted_signal == 'SELL' and actual_return < 0:
                    return True
                elif predicted_signal == 'HOLD' and abs(actual_return) < 0.02:
                    return True
                return False
        return None

    def get_prediction_accuracy(self, ticker: str = None, days: int = 90) -> Dict:
        """Calculate prediction accuracy from past outcomes"""
        cutoff = datetime.now() - timedelta(days=days)

        relevant_outcomes = [
            o for o in self.outcomes['outcomes']
            if datetime.fromisoformat(o['timestamp']) > cutoff
        ]

        if ticker:
            # Filter by ticker
            relevant_outcomes = [
                o for o in relevant_outcomes
                if any(p['ticker'] == ticker for p in self.memory['predictions']
                       if p['id'] == o['prediction_id'])
            ]

        if not relevant_outcomes:
            return {'accuracy': 0.0, 'count': 0}

        correct = sum(1 for o in relevant_outcomes if o.get('correct') is True)
        total = len(relevant_outcomes)

        return {
            'accuracy': correct / total if total > 0 else 0.0,
            'correct': correct,
            'total': total,
            'last_updated': datetime.now().isoformat()
        }

    def get_ticker_stats(self, ticker: str) -> Dict:
        """Get statistics for a specific ticker"""
        past_preds = self.get_past_predictions(ticker, days=365)
        accuracy = self.get_prediction_accuracy(ticker)

        # Count signals
        signals = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        for p in past_preds:
            sig = p['prediction'].get('signal', 'HOLD')
            if sig in signals:
                signals[sig] += 1

        return {
            'ticker': ticker,
            'total_predictions': len(past_preds),
            'signal_distribution': signals,
            'prediction_accuracy': accuracy['accuracy'],
            'correct_predictions': accuracy['correct'],
            'last_prediction': past_preds[-1]['timestamp'] if past_preds else None
        }

    def should_recompute(self, ticker: str, min_hours: int = 24, force: bool = False) -> bool:
        """
        Check if we should recompute analysis for a ticker
        Returns False if we have recent analysis (saves compute)
        If force is True, always return True (recompute)
        """
        if force:
            return True
        # Calculate cutoff based on min_hours, not fixed 1 day
        cutoff = datetime.now() - timedelta(hours=min_hours)

        recent_preds = [
            p for p in self.memory['predictions']
            if p['ticker'] == ticker and
            datetime.fromisoformat(p['timestamp']) > cutoff
        ]

        if not recent_preds:
            return True

        # Get most recent prediction
        last_pred_time = datetime.fromisoformat(
            max(recent_preds, key=lambda x: x['timestamp'])['timestamp']
        )
        hours_since = (datetime.now() - last_pred_time).total_seconds() / 3600

        return hours_since >= min_hours

    def auto_verify_outcomes(self, min_days_old: int = 30):
        """Check past predictions and auto-record outcomes."""
        cutoff = datetime.now() - timedelta(days=min_days_old)
        unverified = [
            p for p in self.memory['predictions']
            if not p.get('outcome_recorded')
            and datetime.fromisoformat(p['timestamp']) < cutoff
        ]
        for pred in unverified:
            try:
                ticker = pred['ticker']
                hist = yf.Ticker(ticker).history(
                    start=pred['timestamp'][:10],
                    period='1mo'
                )
                if hist.empty or len(hist) < 5:
                    continue
                return_pct = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
                self.record_outcome(pred['id'], {'return_pct': return_pct})
            except Exception:
                continue


class MarketContextMemory:
    """
    Stores market context (sector performance, market regime, etc.)
    Avoids recomputing market-wide analysis
    """

    def __init__(self):
        self.context_file = MEMORY_DIR / "market_context.json"
        self.context = self._load_context()

    def _load_context(self) -> Dict:
        if self.context_file.exists():
            try:
                with open(self.context_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'market_regime': 'unknown',
            'sector_performance': {},
            'fear_greed_index': None,
            'last_update': '',
            'vix_level': None
        }

    def save(self):
        """Atomically save market context to disk"""
        temp_file = self.context_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                json.dump(self.context, f, indent=2, default=str)
            # Atomic replace
            shutil.move(str(temp_file), str(self.context_file))

            # Remove old backup if exists
            if self.context_file.with_suffix('.bak').exists():
                self.context_file.with_suffix('.bak').unlink()
        except Exception as e:
            logger.error(f"Failed to save market context: {e}")
            if temp_file.exists():
                temp_file.unlink()

    def update_market_context(self, new_context: Dict):
        """Update market context"""
        self.context.update(new_context)
        self.context['last_update'] = datetime.now().isoformat()
        self.save()

    def get_market_context(self) -> Dict:
        """Get cached market context"""
        return self.context

    def is_context_stale(self, max_hours: int = 6) -> bool:
        """Check if market context needs updating"""
        if not self.context.get('last_update'):
            return True

        last_update = datetime.fromisoformat(self.context['last_update'])
        hours_since = (datetime.now() - last_update).total_seconds() / 3600

        return hours_since >= max_hours
