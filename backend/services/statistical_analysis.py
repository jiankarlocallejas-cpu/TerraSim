"""
TerraSim Statistical Analysis Module

Provides statistical validation and analysis methods for erosion modeling,
including correlation analysis, parameter estimation, and uncertainty quantification.

References:
- Research plan statistical procedures
- Pearson correlation analysis
- Regression analysis for model validation
- Value at Risk (VaR) and Conditional Value at Risk (CVaR) analysis
"""

import numpy as np
import logging
from typing import Dict, Tuple, List, Optional, Any
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class CorrelationAnalysis:
    """
    Perform correlation analysis between environmental factors and erosion.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def pearson_correlation(
        self,
        variable1: np.ndarray,
        variable2: np.ndarray
    ) -> Dict[str, float]:
        """
        Compute Pearson correlation coefficient and significance.
        
        Measures linear relationship between two variables.
        
        Args:
            variable1: First variable array
            variable2: Second variable array
            
        Returns:
            Dictionary with correlation coefficient, p-value, and interpretation
        """
        try:
            # Remove NaN values
            mask = ~(np.isnan(variable1) | np.isnan(variable2))
            v1 = variable1[mask]
            v2 = variable2[mask]
            
            if len(v1) < 2:
                return {
                    'coefficient': 0.0,
                    'p_value': 1.0,
                    'significance': 'Not significant',
                    'interpretation': 'Insufficient data'
                }
            
            # Compute Pearson correlation
            r, p_value = stats.pearsonr(v1, v2)
            
            # Interpret significance
            if p_value < 0.001:
                significance = 'Highly significant (p < 0.001)'
            elif p_value < 0.01:
                significance = 'Very significant (p < 0.01)'
            elif p_value < 0.05:
                significance = 'Significant (p < 0.05)'
            else:
                significance = 'Not significant'
            
            # Interpret correlation strength
            abs_r = abs(r)
            if abs_r >= 0.8:
                strength = 'Very strong'
            elif abs_r >= 0.6:
                strength = 'Strong'
            elif abs_r >= 0.4:
                strength = 'Moderate'
            elif abs_r >= 0.2:
                strength = 'Weak'
            else:
                strength = 'Very weak'
            
            direction = 'positive' if r > 0 else 'negative'
            
            return {
                'coefficient': float(r),
                'p_value': float(p_value),
                'significance': significance,
                'strength': strength,
                'direction': direction,
                'n_samples': len(v1),
                'interpretation': f'{strength} {direction} correlation'
            }
        except Exception as e:
            self.logger.error(f"Error computing Pearson correlation: {e}")
            return {'coefficient': 0.0, 'p_value': 1.0, 'error': str(e)}
    
    def analyze_factor_relationships(
        self,
        factors: Dict[str, np.ndarray],
        erosion_values: np.ndarray
    ) -> Dict[str, Dict[str, float]]:
        """
        Analyze correlations between all factors and erosion.
        
        Args:
            factors: Dictionary of environmental factors
            erosion_values: Simulated or measured erosion values
            
        Returns:
            Dictionary of correlation results for each factor
        """
        results = {}
        for factor_name, factor_values in factors.items():
            results[factor_name] = self.pearson_correlation(
                factor_values,
                erosion_values
            )
        return results


class RegressionAnalysis:
    """
    Perform regression analysis for model parameter estimation and validation.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def linear_regression(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform multiple linear regression analysis.
        
        y = b0 + b1*X1 + b2*X2 + ... + bn*Xn
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target variable
            feature_names: Names of features
            
        Returns:
            Dictionary with regression results and statistics
        """
        try:
            # Remove NaN values
            mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
            X_clean = X[mask]
            y_clean = y[mask]
            
            if len(X_clean) < X_clean.shape[1] + 1:
                return {'error': 'Insufficient samples for regression'}
            
            # Standardize features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_clean)
            
            # Fit linear regression
            model = LinearRegression()
            model.fit(X_scaled, y_clean)
            
            # Compute predictions and residuals
            y_pred = model.predict(X_scaled)
            residuals = y_clean - y_pred
            
            # Compute R-squared
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            
            # Compute RMSE
            rmse = np.sqrt(np.mean(residuals ** 2))
            
            # Compute MAE
            mae = np.mean(np.abs(residuals))
            
            # Feature importance (standardized coefficients)
            if feature_names is None:
                feature_names = [f'Feature_{i}' for i in range(X_clean.shape[1])]
            
            feature_importance = {
                name: float(coef)
                for name, coef in zip(feature_names, model.coef_)
            }
            
            return {
                'intercept': float(model.intercept_),
                'coefficients': feature_importance,
                'r_squared': float(r_squared),
                'rmse': float(rmse),
                'mae': float(mae),
                'n_samples': len(X_clean),
                'residuals': residuals.tolist()[:100]  # First 100 residuals
            }
        except Exception as e:
            self.logger.error(f"Error in regression analysis: {e}")
            return {'error': str(e)}
    
    def log_transform_analysis(
        self,
        variable: np.ndarray,
        name: str = 'Variable'
    ) -> Dict[str, Any]:
        """
        Analyze whether log transformation improves normality.
        
        Args:
            variable: Variable to analyze
            name: Name of variable
            
        Returns:
            Dictionary with normality test results
        """
        try:
            # Remove non-positive values for log transformation
            positive_mask = variable > 0
            var_positive = variable[positive_mask]
            
            if len(var_positive) < 3:
                return {'error': 'Insufficient positive values for log transform'}
            
            # Shapiro-Wilk normality test
            stat_original, p_original = stats.shapiro(var_positive)
            
            # Log transform
            var_log = np.log(var_positive)
            stat_log, p_log = stats.shapiro(var_log)
            
            return {
                'original_statistic': float(stat_original),
                'original_p_value': float(p_original),
                'original_normal': p_original > 0.05,
                'log_transformed_statistic': float(stat_log),
                'log_transformed_p_value': float(p_log),
                'log_transformed_normal': p_log > 0.05,
                'improvement': p_log > p_original,
                'recommendation': 'Use log transformation' if p_log > p_original else 'Use original scale'
            }
        except Exception as e:
            self.logger.error(f"Error in log transform analysis: {e}")
            return {'error': str(e)}


class ModelValidation:
    """
    Validate TerraSim predictions against RUSLE and observed data.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def compute_agreement_metrics(
        self,
        predicted: np.ndarray,
        observed: np.ndarray
    ) -> Dict[str, float]:
        """
        Compute model agreement metrics.
        
        Metrics:
        - RMSE: Root Mean Square Error
        - MAE: Mean Absolute Error
        - MAPE: Mean Absolute Percentage Error
        - NSE: Nash-Sutcliffe Efficiency
        
        Args:
            predicted: Model predictions
            observed: Observed/reference values
            
        Returns:
            Dictionary of agreement metrics
        """
        try:
            # Remove NaN values
            mask = ~(np.isnan(predicted) | np.isnan(observed))
            pred = predicted[mask]
            obs = observed[mask]
            
            if len(pred) == 0:
                return {'error': 'No valid data pairs'}
            
            # RMSE
            rmse = np.sqrt(np.mean((pred - obs) ** 2))
            
            # MAE
            mae = np.mean(np.abs(pred - obs))
            
            # MAPE (avoid division by zero)
            mape = np.mean(np.abs((pred - obs) / np.maximum(np.abs(obs), 0.001))) * 100
            
            # NSE (Nash-Sutcliffe Efficiency)
            ss_res = np.sum((obs - pred) ** 2)
            ss_tot = np.sum((obs - np.mean(obs)) ** 2)
            nse = 1 - (ss_res / max(ss_tot, 1e-10))
            
            # R-squared
            r_squared = np.corrcoef(pred, obs)[0, 1] ** 2
            
            return {
                'rmse': float(rmse),
                'mae': float(mae),
                'mape': float(mape),
                'nse': float(nse),
                'r_squared': float(r_squared),
                'n_pairs': len(pred),
                'prediction_mean': float(np.mean(pred)),
                'observed_mean': float(np.mean(obs)),
                'prediction_std': float(np.std(pred)),
                'observed_std': float(np.std(obs))
            }
        except Exception as e:
            self.logger.error(f"Error computing agreement metrics: {e}")
            return {'error': str(e)}
    
    def compare_with_rusle(
        self,
        terrasim_values: np.ndarray,
        rusle_values: np.ndarray
    ) -> Dict[str, Any]:
        """
        Compare TerraSim predictions with RUSLE results.
        
        Tests hypothesis: TerraSim predictions are consistent with RUSLE
        
        Args:
            terrasim_values: TerraSim predicted erosion values
            rusle_values: RUSLE computed values
            
        Returns:
            Comparison report
        """
        try:
            # Compute agreement metrics
            agreement = self.compute_agreement_metrics(terrasim_values, rusle_values)
            
            # Paired t-test
            # H0: Mean difference = 0
            mask = ~(np.isnan(terrasim_values) | np.isnan(rusle_values))
            t_stat, p_value = stats.ttest_rel(
                terrasim_values[mask],
                rusle_values[mask]
            )
            
            # Interpret results
            if p_value > 0.05:
                consistency = 'Statistically consistent with RUSLE (Ha1 supported)'
            else:
                consistency = 'Statistically different from RUSLE (Ho1 supported)'
            
            return {
                'agreement_metrics': agreement,
                'paired_t_test': {
                    't_statistic': float(t_stat),
                    'p_value': float(p_value),
                    'significance': 'p < 0.05' if p_value < 0.05 else 'p >= 0.05'
                },
                'consistency': consistency,
                'hypothesis_support': 'Ha1' if p_value > 0.05 else 'Ho1'
            }
        except Exception as e:
            self.logger.error(f"Error comparing with RUSLE: {e}")
            return {'error': str(e)}


class UncertaintyQuantification:
    """
    Quantify uncertainty and compute risk metrics.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def compute_var_cvar(
        self,
        values: np.ndarray,
        confidence_level: float = 0.95
    ) -> Dict[str, float]:
        """
        Compute Value at Risk (VaR) and Conditional Value at Risk (CVaR).
        
        VaR = percentile loss at confidence level
        CVaR = expected loss given worst-case scenarios
        
        Args:
            values: Array of erosion/loss values
            confidence_level: Confidence level (0-1)
            
        Returns:
            Dictionary with VaR and CVaR values
        """
        try:
            values_clean = values[~np.isnan(values)]
            
            if len(values_clean) == 0:
                return {'error': 'No valid data'}
            
            # Compute VaR (percentile at (1-confidence)*100)
            percentile = (1 - confidence_level) * 100
            var = np.percentile(values_clean, percentile)
            
            # Compute CVaR (mean of values >= VaR)
            worst_values = values_clean[values_clean >= var]
            cvar = np.mean(worst_values) if len(worst_values) > 0 else var
            
            return {
                'var': float(var),
                'cvar': float(cvar),
                'confidence_level': confidence_level,
                'n_values': len(values_clean),
                'interpretation': f'At {confidence_level*100:.0f}% confidence, erosion could exceed {var:.2f} units'
            }
        except Exception as e:
            self.logger.error(f"Error computing VaR/CVaR: {e}")
            return {'error': str(e)}
    
    def monte_carlo_uncertainty(
        self,
        erosion_func,
        parameter_distributions: Dict[str, Tuple[float, float]],
        n_simulations: int = 1000
    ) -> Dict[str, Any]:
        """
        Perform Monte Carlo uncertainty analysis by varying parameters.
        
        Args:
            erosion_func: Function that computes erosion given parameters
            parameter_distributions: Dict of (mean, std) for each parameter
            n_simulations: Number of Monte Carlo simulations
            
        Returns:
            Uncertainty analysis results
        """
        try:
            results = []
            
            for i in range(n_simulations):
                # Sample parameters from distributions
                params = {}
                for param_name, (mean, std) in parameter_distributions.items():
                    params[param_name] = np.random.normal(mean, std)
                
                # Compute erosion
                erosion = erosion_func(params)
                results.append(erosion)
            
            results = np.array(results)
            
            # Compute statistics
            return {
                'mean': float(np.mean(results)),
                'std': float(np.std(results)),
                'min': float(np.min(results)),
                'max': float(np.max(results)),
                'median': float(np.median(results)),
                'percentile_5': float(np.percentile(results, 5)),
                'percentile_95': float(np.percentile(results, 95)),
                'n_simulations': n_simulations,
                'distribution': results[:100].tolist()  # First 100 for visualization
            }
        except Exception as e:
            self.logger.error(f"Error in Monte Carlo uncertainty: {e}")
            return {'error': str(e)}
    
    def sensitivity_analysis(
        self,
        base_values: Dict[str, float],
        erosion_func,
        perturbation_percent: float = 10
    ) -> Dict[str, Dict[str, float]]:
        """
        Perform sensitivity analysis by varying parameters.
        
        Args:
            base_values: Base parameter values
            erosion_func: Function that computes erosion
            perturbation_percent: Percentage to vary parameters (default 10%)
            
        Returns:
            Sensitivity indices for each parameter
        """
        try:
            # Compute base erosion
            base_erosion = erosion_func(base_values)
            
            sensitivity = {}
            
            for param_name, base_value in base_values.items():
                # Perturb parameter upward
                params_up = base_values.copy()
                params_up[param_name] = base_value * (1 + perturbation_percent / 100)
                erosion_up = erosion_func(params_up)
                
                # Perturb parameter downward
                params_down = base_values.copy()
                params_down[param_name] = base_value * (1 - perturbation_percent / 100)
                erosion_down = erosion_func(params_down)
                
                # Compute sensitivity index
                delta_erosion = erosion_up - erosion_down
                delta_param_percent = 2 * perturbation_percent
                
                sensitivity_index = delta_erosion / (delta_param_percent / 100 * base_value) if base_value != 0 else 0
                
                sensitivity[param_name] = {
                    'sensitivity_index': float(sensitivity_index),
                    'erosion_up': float(erosion_up),
                    'erosion_down': float(erosion_down),
                    'delta_erosion': float(delta_erosion)
                }
            
            return sensitivity
        except Exception as e:
            self.logger.error(f"Error in sensitivity analysis: {e}")
            return {'error': str(e)}
