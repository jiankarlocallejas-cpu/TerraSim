"""
Statistical analysis for erosion modeling and model validation.

Provides comprehensive statistical methods including:
- Correlation analysis (Pearson)
- Regression analysis (linear, log-transform)
- Model validation (RUSLE comparison, agreement metrics)
- Uncertainty quantification (Monte Carlo, VaR, CVaR)
- Sensitivity analysis (parameter perturbation)
"""

import numpy as np
import logging
from typing import Dict, Tuple, List, Optional, Any, Callable
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

logger = logging.getLogger(__name__)


class CorrelationAnalysis:
    """
    Correlation analysis between environmental factors and erosion.
    
    Uses Pearson correlation coefficient to measure linear relationships
    between environmental variables and erosion measurements.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def pearson_correlation(
        self,
        variable1: np.ndarray,
        variable2: np.ndarray
    ) -> Dict[str, Any]:
        """
        Compute Pearson correlation coefficient with significance testing.
        
        Measures linear relationship strength and direction between two variables.
        
        Args:
            variable1: First variable array
            variable2: Second variable array
            
        Returns:
            Dictionary with:
            - coefficient: Pearson r value (-1 to 1)
            - p_value: Statistical significance
            - significance: Verbal significance level
            - strength: Correlation strength interpretation
            - direction: positive or negative
            - n_samples: Sample count
            - interpretation: Human-readable summary
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
            result = stats.pearsonr(v1, v2)
            # Handle both tuple and PearsonRResult object
            r_val: float = 0.0
            p_val: float = 1.0
            try:
                r_val, p_val = result  # type: ignore
            except (TypeError, ValueError):
                # Newer scipy returns a result object - use getattr for safety
                try:
                    stat_attr = getattr(result, 'statistic', None)
                    pval_attr = getattr(result, 'pvalue', None)
                    if stat_attr is not None:
                        r_val = float(stat_attr)
                    if pval_attr is not None:
                        p_val = float(pval_attr)
                except Exception:
                    pass
            
            # Interpret significance
            if p_val < 0.001:
                significance = 'Highly significant (p < 0.001)'
            elif p_val < 0.01:
                significance = 'Very significant (p < 0.01)'
            elif p_val < 0.05:
                significance = 'Significant (p < 0.05)'
            else:
                significance = 'Not significant'
            
            # Interpret correlation strength
            abs_r = abs(r_val)
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
            
            direction = 'positive' if r_val > 0 else 'negative'
            
            return {
                'coefficient': r_val,
                'p_value': p_val,
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
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze correlations between all environmental factors and erosion.
        
        Args:
            factors: Dictionary mapping factor names to value arrays
            erosion_values: Simulated or measured erosion values
            
        Returns:
            Dictionary mapping factor names to correlation analysis results
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
    Regression analysis for model parameter estimation and validation.
    
    Includes linear regression, log-transform analysis, and residual diagnostics.
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
        
        Model: y = b0 + b1*X1 + b2*X2 + ... + bn*Xn
        
        Standardizes features before fitting for better interpretability
        of coefficients.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target variable
            feature_names: Optional names of features
            
        Returns:
            Dictionary with:
            - intercept: Model intercept
            - coefficients: Standardized feature coefficients
            - r_squared: Model R-squared
            - rmse: Root mean square error
            - mae: Mean absolute error
            - n_samples: Sample count
            - residuals: First 100 residuals for diagnostics
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
        Test whether log transformation improves data normality.
        
        Uses Shapiro-Wilk test to assess normality before and after
        log transformation.
        
        Args:
            variable: Variable to analyze
            name: Name of variable for logging
            
        Returns:
            Dictionary with:
            - original_statistic: Shapiro-Wilk stat (original)
            - original_p_value: p-value (original)
            - original_normal: Boolean normality test
            - log_transformed_*: Same for log-transformed data
            - improvement: Whether log transform improved normality
            - recommendation: 'Use log transformation' or 'Use original scale'
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
    Validate TerraSim predictions against reference data and RUSLE.
    
    Computes agreement metrics and performs statistical hypothesis testing.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def compute_agreement_metrics(
        self,
        predicted: np.ndarray,
        observed: np.ndarray
    ) -> Dict[str, Any]:
        """
        Compute model agreement metrics.
        
        Standard metrics for comparing predicted vs observed values:
        - RMSE: Root Mean Square Error (penalizes large errors)
        - MAE: Mean Absolute Error (robust)
        - MAPE: Mean Absolute Percentage Error
        - NSE: Nash-Sutcliffe Efficiency (0-1, 1=perfect)
        - R²: Coefficient of determination
        
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
        Compare TerraSim predictions with RUSLE results using paired t-test.
        
        Tests hypothesis: TerraSim predictions are statistically consistent
        with RUSLE model results.
        
        Args:
            terrasim_values: TerraSim predicted erosion values
            rusle_values: RUSLE computed values
            
        Returns:
            Comparison report with agreement metrics and hypothesis test results
        """
        try:
            # Compute agreement metrics
            agreement = self.compute_agreement_metrics(terrasim_values, rusle_values)
            
            # Paired t-test
            # H0: Mean difference = 0 (models predict same values)
            mask = ~(np.isnan(terrasim_values) | np.isnan(rusle_values))
            t_stat, p_value = stats.ttest_rel(
                terrasim_values[mask],
                rusle_values[mask]
            )
            
            # Interpret results
            if p_value > 0.05:
                consistency = 'Statistically consistent with RUSLE (Ha1 supported)'
                hypothesis = 'Ha1'
            else:
                consistency = 'Statistically different from RUSLE (Ho1 supported)'
                hypothesis = 'Ho1'
            
            return {
                'agreement_metrics': agreement,
                'paired_t_test': {
                    't_statistic': float(t_stat),
                    'p_value': float(p_value),
                    'significance': 'p < 0.05' if p_value < 0.05 else 'p >= 0.05'
                },
                'consistency': consistency,
                'hypothesis_support': hypothesis
            }
        except Exception as e:
            self.logger.error(f"Error comparing with RUSLE: {e}")
            return {'error': str(e)}


class UncertaintyQuantification:
    """
    Quantify uncertainty in predictions using statistical methods.
    
    Includes Monte Carlo simulation, Value at Risk (VaR), and sensitivity analysis.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def compute_var_cvar(
        self,
        values: np.ndarray,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Compute Value at Risk (VaR) and Conditional Value at Risk (CVaR).
        
        - VaR: Percentile loss at specified confidence level
        - CVaR: Expected loss in worst-case scenarios (beyond VaR)
        
        Args:
            values: Array of erosion/loss values
            confidence_level: Confidence level (0-1), default 0.95
            
        Returns:
            Dictionary with VaR, CVaR, and interpretation
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
        erosion_func: Callable,
        parameter_distributions: Dict[str, Tuple[float, float]],
        n_simulations: int = 1000
    ) -> Dict[str, Any]:
        """
        Perform Monte Carlo uncertainty analysis by varying parameters.
        
        Samples parameters from distributions, runs simulations, and
        computes statistical summaries of predictions.
        
        Args:
            erosion_func: Function that computes erosion given parameters
            parameter_distributions: Dict of (mean, std) for each parameter
            n_simulations: Number of Monte Carlo simulations
            
        Returns:
            Dictionary with uncertainty statistics and distribution samples
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
        erosion_func: Callable,
        perturbation_percent: float = 10
    ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis by perturbating parameters.
        
        Varies each parameter independently and measures impact on
        erosion output.
        
        Args:
            base_values: Base parameter values
            erosion_func: Function that computes erosion
            perturbation_percent: Percentage to vary parameters (default 10%)
            
        Returns:
            Dictionary mapping parameter names to sensitivity indices
        """
        try:
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
                
                sensitivity_index = (
                    delta_erosion / (delta_param_percent / 100 * base_value)
                    if base_value != 0
                    else 0
                )
                
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
