"""
Safety engine for medical report analysis
Detects critical values and flags abnormal results
NO DIAGNOSIS - Only flags and educational information
"""
from typing import Literal, Optional, Dict, Any
import re


class SafetyService:
    """
    Service for detecting critical values and flagging abnormal results
    CRITICAL: This service does NOT provide diagnosis or treatment recommendations
    """
    
    # Critical thresholds for common parameters (example values - should be configurable)
    CRITICAL_THRESHOLDS: Dict[str, Dict[str, float]] = {
        "glucose": {
            "critical_high": 400,  # mg/dL
            "critical_low": 40,   # mg/dL
            "normal_high": 100,
            "normal_low": 70,
        },
        "creatinine": {
            "critical_high": 5.0,  # mg/dL
            "normal_high": 1.2,
            "normal_low": 0.6,
        },
        "hemoglobin": {
            "critical_low": 7.0,  # g/dL
            "normal_high": 17.5,
            "normal_low": 13.5,
        },
        # Add more as needed
    }
    
    def classify_flag(
        self,
        parameter_name: str,
        value: float,
        normal_range: str,
        unit: Optional[str] = None
    ) -> Literal['normal', 'high', 'low']:
        """
        Classify parameter value as normal, high, or low
        
        Args:
            parameter_name: Name of the parameter (e.g., "glucose", "cholesterol")
            value: Numeric value
            normal_range: String representation of normal range (e.g., "< 200 mg/dL")
            unit: Unit of measurement
        
        Returns:
            'normal', 'high', or 'low'
        """
        # Parse normal range
        range_info = self._parse_range(normal_range)
        
        if not range_info:
            # If we can't parse, try to use thresholds
            return self._classify_by_thresholds(parameter_name.lower(), value)
        
        # Check if value is within range
        if range_info.get("min") is not None and value < range_info["min"]:
            return 'low'
        if range_info.get("max") is not None and value > range_info["max"]:
            return 'high'
        
        return 'normal'
    
    def _parse_range(self, range_str: str) -> Optional[Dict[str, Optional[float]]]:
        """
        Parse normal range string to extract min/max values
        
        Examples:
            "< 200 mg/dL" -> {"max": 200}
            "70-100 mg/dL" -> {"min": 70, "max": 100}
            "> 40 mg/dL" -> {"min": 40}
        """
        # Remove unit
        range_str = re.sub(r'\s*(mg/dL|g/dL|mmol/L|%|IU/L|U/L)\s*', '', range_str, flags=re.IGNORECASE)
        
        # Extract numbers
        numbers = re.findall(r'\d+\.?\d*', range_str)
        
        if not numbers:
            return None
        
        numbers = [float(n) for n in numbers]
        
        result = {"min": None, "max": None}
        
        if '<' in range_str:
            result["max"] = numbers[0]
        elif '>' in range_str:
            result["min"] = numbers[0]
        elif len(numbers) == 2:
            result["min"] = min(numbers)
            result["max"] = max(numbers)
        elif len(numbers) == 1:
            # Assume it's a max value if single number
            result["max"] = numbers[0]
        
        return result
    
    def _classify_by_thresholds(self, parameter_name: str, value: float) -> Literal['normal', 'high', 'low']:
        """Classify using predefined thresholds"""
        param_key = parameter_name.lower()
        
        # Try to find matching threshold
        for key, thresholds in self.CRITICAL_THRESHOLDS.items():
            if key in param_key:
                normal_low = thresholds.get("normal_low")
                normal_high = thresholds.get("normal_high")
                
                if normal_low and value < normal_low:
                    return 'low'
                if normal_high and value > normal_high:
                    return 'high'
                return 'normal'
        
        # Default to normal if no thresholds found
        return 'normal'
    
    def get_flag_level(
        self,
        parameters: list[Dict[str, Any]]
    ) -> Literal['green', 'yellow', 'red']:
        """
        Determine overall flag level for a report based on parameters
        
        Args:
            parameters: List of parameter dicts with 'flag' field
        
        Returns:
            'green', 'yellow', or 'red'
        """
        if not parameters:
            return 'green'
        
        has_red = any(p.get('flag') == 'high' or p.get('flag') == 'low' for p in parameters)
        has_yellow = any(p.get('flag') == 'high' or p.get('flag') == 'low' for p in parameters)
        
        # Red if any critical values
        # Yellow if any abnormal values
        # Green if all normal
        
        # For now, simple logic:
        # - Red: any high/low values
        # - Yellow: could be used for borderline cases (not implemented yet)
        # - Green: all normal
        
        if has_red:
            return 'red'
        if has_yellow:
            return 'yellow'
        
        return 'green'
    
    def is_critical_value(
        self,
        parameter_name: str,
        value: float,
        flag: Literal['normal', 'high', 'low']
    ) -> bool:
        """
        Check if a value is critically abnormal (requires immediate attention)
        
        Args:
            parameter_name: Parameter name
            value: Numeric value
            flag: Flag classification
        
        Returns:
            True if critical, False otherwise
        """
        if flag == 'normal':
            return False
        
        param_key = parameter_name.lower()
        
        # Check against critical thresholds
        for key, thresholds in self.CRITICAL_THRESHOLDS.items():
            if key in param_key:
                if flag == 'high' and thresholds.get("critical_high"):
                    return value >= thresholds["critical_high"]
                if flag == 'low' and thresholds.get("critical_low"):
                    return value <= thresholds["critical_low"]
        
        return False
