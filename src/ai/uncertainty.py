"""
Uncertainty estimation for traffic predictions.
Calculates ensemble tree variances, confidence intervals, and normalized uncertainty scores.
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np


class UncertaintyEstimator:
    """
    Quantifies prediction uncertainty using ensemble variance and residual bounds.
    """

    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        # Z-score for two-tailed normal distribution (1.96 for 95%)
        self.z_score = 1.96 if confidence_level == 0.95 else 1.645

    def estimate_from_trees(
        self,
        tree_predictions: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculates mean, standard error, upper/lower bounds, and normalized score from tree outputs.
        tree_predictions: shape (n_estimators, n_samples)
        """
        mean = np.mean(tree_predictions, axis=0)
        std_err = np.std(tree_predictions, axis=0)
        margin = self.z_score * std_err

        lower_bound = np.maximum(0.0, mean - margin)
        upper_bound = mean + margin

        # Normalized uncertainty index between 0.0 and 1.0 (relative to mean + std)
        coeff_of_variation = std_err / (np.maximum(1.0, mean))
        norm_uncertainty = np.clip(coeff_of_variation * 3.0, 0.05, 0.95)

        return mean, std_err, lower_bound, upper_bound

    def quantify_intersection_uncertainties(
        self,
        predictions: Dict[str, Dict[str, float]],
        volatilities: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Produce uncertainty profiles for all intersections.
        """
        results: Dict[str, Dict[str, float]] = {}
        for node_id, preds in predictions.items():
            vol = preds.get("volume", 50.0)
            volatility = volatilities.get(node_id, 0.15) if volatilities else 0.15

            # Standard deviation estimated from prediction volatility
            sigma = max(2.5, vol * volatility)
            margin = round(self.z_score * sigma, 1)

            norm_uncertainty = min(1.0, (sigma / max(10.0, vol)) * 2.5)

            results[node_id] = {
                "predicted_volume": vol,
                "uncertainty_sigma": round(sigma, 2),
                "confidence_margin": margin,
                "ci_lower": max(0.0, round(vol - margin, 1)),
                "ci_upper": round(vol + margin, 1),
                "normalized_uncertainty": round(norm_uncertainty, 3),
            }
        return results
