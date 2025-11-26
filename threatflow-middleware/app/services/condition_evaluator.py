"""
Enterprise Condition Evaluation Logic
Separated for clarity and maintainability
Contains all evaluation strategies (primary, schema fallback, generic fallback)

UPDATED: Based on actual IntelOwl analyzer responses from comprehensive testing.
Field paths are verified against real response data from testing_responses/responses/.
"""

import logging
from typing import Dict, Any, Optional
from app.services.analyzer_schema import schema_manager

logger = logging.getLogger(__name__)


# Actual malware indicator fields verified from real IntelOwl responses
VERIFIED_MALWARE_INDICATORS = {
    "ClamAV": ["detections"],  # Array of detection names
    "Yara": [
        "yara-rules_rules", "elastic_protections-artifacts", 
        "advanced-threat-research_yara-rules", "neo23x0_signature-base"
    ],  # Multiple rule set arrays
    "Doc_Info": ["mraptor"],  # "suspicious" or "ok"
    "Quark_Engine": ["threat_level", "total_score", "crimes"],
    "APK_Artifacts": ["permission"],  # Dangerous permissions
    "APKiD": ["files"],  # Detected packers/obfuscators
    "Rtf_Info": ["rtfobj.ole_objects", "follina"],
    "BoxJS": ["IOC.json"],
    "Strings_Info": ["data"],  # Check for suspicious patterns
    "File_Info": [],  # Metadata only, no malware detection
}


class ConditionEvaluatorMixin:
    """
    Mixin class containing all condition evaluation strategies
    To be used by IntelOwlService
    """
    
    def _evaluate_with_schema_fallback(
        self, 
        condition: Dict[str, Any], 
        analyzer_report: Dict[str, Any]
    ) -> bool:
        """
        Schema-based fallback evaluation
        Uses verified field paths from actual analyzer responses
        """
        cond_type = condition.get("type")
        analyzer_name = analyzer_report.get("name")
        report_data = analyzer_report.get("report", {})
        
        # Use verified malware indicators first
        if analyzer_name in VERIFIED_MALWARE_INDICATORS:
            indicator_fields = VERIFIED_MALWARE_INDICATORS[analyzer_name]
        else:
            # Fall back to schema manager
            indicator_fields = schema_manager.get_malware_indicators(analyzer_name)
        
        if cond_type == "verdict_malicious":
            # Check verified malware indicator fields
            for indicator_field in indicator_fields:
                value = self._navigate_field_path(report_data, indicator_field)
                if value is not None:
                    # ClamAV detections
                    if indicator_field == "detections" and isinstance(value, list) and len(value) > 0:
                        logger.debug(f"Schema fallback: detections has {len(value)} items -> True")
                        return True
                    
                    # Doc_Info mraptor
                    if indicator_field == "mraptor" and value == "suspicious":
                        logger.debug(f"Schema fallback: mraptor = 'suspicious' -> True")
                        return True
                    
                    # Quark threat_level
                    if indicator_field == "threat_level" and value in ["High Risk", "Critical", "Malicious"]:
                        logger.debug(f"Schema fallback: threat_level = '{value}' -> True")
                        return True
                    
                    # Quark total_score
                    if indicator_field == "total_score" and isinstance(value, (int, float)) and value > 50:
                        logger.debug(f"Schema fallback: total_score = {value} > 50 -> True")
                        return True
                    
                    # Array fields (crimes, files, etc.)
                    if isinstance(value, list) and len(value) > 0:
                        logger.debug(f"Schema fallback: {indicator_field} has items -> True")
                        return True
                    
                    # Dict fields
                    if isinstance(value, dict) and value:
                        logger.debug(f"Schema fallback: {indicator_field} has data -> True")
                        return True
            
            # Check Yara rule sets specifically
            if analyzer_name == "Yara":
                for key in report_data.keys():
                    if "yara" in key.lower() or "rules" in key.lower():
                        value = report_data.get(key, [])
                        if isinstance(value, list) and len(value) > 0:
                            logger.debug(f"Schema fallback: Yara {key} has matches -> True")
                            return True
            
            logger.debug("Schema fallback: No malware indicators found -> False")
            return False
        
        elif cond_type in ["field_equals", "field_contains", "field_greater_than", "field_less_than"]:
            field_path = condition.get("field_path", "")
            expected_value = condition.get("expected_value")
            
            # Try to find similar field paths using schema
            suggestions = schema_manager.suggest_field_paths(analyzer_name, field_path)
            
            for suggested_path in suggestions:
                try:
                    value = self._navigate_field_path(report_data, suggested_path)
                    if value is not None:
                        # Try the comparison with suggested field
                        if cond_type == "field_equals":
                            if value == expected_value:
                                logger.debug(f"Schema fallback used field '{suggested_path}': {value} == {expected_value}")
                                return True
                        elif cond_type == "field_contains":
                            if self._check_contains(value, expected_value):
                                logger.debug(f"Schema fallback used field '{suggested_path}': contains {expected_value}")
                                return True
                except Exception as e:
                    logger.debug(f"Schema fallback failed for '{suggested_path}': {e}")
                    continue
            
            return False
        
        # For other condition types, try primary logic as fallback
        return False
    
    def _evaluate_generic_fallback(
        self, 
        condition: Dict[str, Any], 
        analyzer_report: Dict[str, Any]
    ) -> bool:
        """
        Generic pattern-based fallback
        Uses broad heuristics when specific fields not found
        """
        cond_type = condition.get("type")
        report_data = analyzer_report.get("report", {})
        report_str = str(report_data).lower()
        
        if cond_type == "verdict_malicious":
            # Generic pattern matching for malware indicators
            malware_patterns = [
                "malicious", "malware", "virus", "trojan", "ransomware",
                "suspicious", "threat", "infected", "exploit", "backdoor",
                "detection", "alert", "warning"
            ]
            
            for pattern in malware_patterns:
                if pattern in report_str:
                    logger.debug(f"Generic fallback: found pattern '{pattern}' -> True")
                    return True
            
            logger.debug("Generic fallback: No malware patterns found -> False")
            return False
        
        elif cond_type == "has_detections":
            # Look for any detection-related fields
            detection_keywords = ["detection", "alert", "match", "finding", "signature"]
            for keyword in detection_keywords:
                if keyword in report_str and not "no " + keyword in report_str:
                    logger.debug(f"Generic fallback: found detection keyword '{keyword}' -> True")
                    return True
            return False
        
        elif cond_type == "yara_rule_match":
            # Look for YARA-related content
            if "match" in report_str or "rule" in report_str:
                logger.debug("Generic fallback: YARA keywords found -> True")
                return True
            return False
        
        # For field-based conditions, cannot use generic fallback reliably
        return False
    
    def _get_safe_default(self, condition: Dict[str, Any]) -> bool:
        """
        Safe default when all evaluation strategies fail
        Conservative approach to minimize false positives
        """
        cond_type = condition.get("type")
        
        # For malware detection, default to False (don't raise false alarms)
        if cond_type in ["verdict_malicious", "verdict_suspicious", "has_detections", "yara_rule_match"]:
            logger.warning(f"Using safe default FALSE for {cond_type} (cannot evaluate)")
            return False
        
        # For clean/success checks, default to False (conservative)
        elif cond_type in ["verdict_clean", "analyzer_success"]:
            logger.warning(f"Using safe default FALSE for {cond_type} (cannot evaluate)")
            return False
        
        # For failure checks, default to True (assume failure when unsure)
        elif cond_type == "analyzer_failed":
            logger.warning(f"Using safe default TRUE for {cond_type} (assume failure)")
            return True
        
        # For field comparisons, default to False
        else:
            logger.warning(f"Using safe default FALSE for {cond_type}")
            return False
    
    def _navigate_field_path(self, data: Any, field_path: str) -> Any:
        """
        Navigate nested JSON structure using dot notation
        Supports array indexing: "report.sections[0].entropy"
        """
        if not field_path:
            return data
        
        current = data
        parts = field_path.split(".")
        
        for part in parts:
            # Handle array indexing
            if "[" in part and "]" in part:
                field_name = part[:part.index("[")]
                index_str = part[part.index("[")+1:part.index("]")]
                
                if isinstance(current, dict):
                    current = current.get(field_name)
                
                if isinstance(current, list):
                    try:
                        index = int(index_str)
                        current = current[index] if index < len(current) else None
                    except (ValueError, IndexError):
                        return None
            else:
                # Normal dict navigation
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
            
            if current is None:
                return None
        
        return current
    
    def _check_contains(self, value: Any, expected: Any) -> bool:
        """Check if value contains expected (works for strings and lists)"""
        if isinstance(value, str):
            return str(expected) in value
        elif isinstance(value, list):
            # Check if expected is in list, or if any item contains expected
            if expected in value:
                return True
            for item in value:
                if str(expected) in str(item):
                    return True
        return False
