"""
Enterprise-Grade Analyzer Schema Management System
Provides dynamic schema detection, validation, and field mapping for all 18 IntelOwl analyzers

This system ensures conditional logic works reliably across different analyzer output formats
with intelligent fallback strategies and comprehensive error handling.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import json
import re

logger = logging.getLogger(__name__)


class FieldType(Enum):
    """Field data types for schema validation"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ANY = "any"


@dataclass
class SchemaField:
    """Represents a field in analyzer output schema"""
    path: str
    field_type: FieldType
    description: str
    examples: List[Any]
    required: bool = False
    
    
@dataclass
class ConditionTemplate:
    """Pre-built condition template for common use cases"""
    name: str
    description: str
    condition_type: str
    field_path: Optional[str] = None
    expected_value: Optional[Any] = None
    use_case: str = ""


class AnalyzerSchemaManager:
    """
    Manages output schemas for all 18 IntelOwl file analyzers
    Provides schema detection, validation, and intelligent field mapping
    """
    
    # Comprehensive schema definitions for all 18 analyzers
    ANALYZER_SCHEMAS: Dict[str, Dict[str, Any]] = {
        
        # ========== File Analysis Tools ==========
        'File_Info': {
            'description': 'Basic file metadata and signature analysis',
            'output_fields': [
                SchemaField('report.md5', FieldType.STRING, 'MD5 hash', ['a1b2c3d4...']),
                SchemaField('report.sha256', FieldType.STRING, 'SHA256 hash', ['e5f6g7h8...']),
                SchemaField('report.mime_type', FieldType.STRING, 'MIME type', ['application/x-executable', 'application/pdf']),
                SchemaField('report.size', FieldType.NUMBER, 'File size in bytes', [1024, 2048576]),
                SchemaField('report.magic', FieldType.STRING, 'File type from magic bytes', ['PE32 executable', 'PDF document']),
                SchemaField('report.ssdeep', FieldType.STRING, 'Fuzzy hash', ['3:ABC123:XYZ']),
            ],
            'condition_templates': [
                ConditionTemplate('Large file check', 'Detect files larger than threshold', 'field_greater_than', 
                                'report.size', 10000000, 'Route large files to specialized analyzers'),
                ConditionTemplate('Executable check', 'Check if file is executable', 'field_contains',
                                'report.mime_type', 'executable', 'Apply PE analysis only to executables'),
            ],
            'malware_indicators': [],
            'success_patterns': ['md5', 'sha256', 'mime_type'],
        },
        
        'Strings_Info': {
            'description': 'Extract and analyze strings from binary files',
            'output_fields': [
                SchemaField('report.strings', FieldType.ARRAY, 'Extracted ASCII strings', [['http://example.com', 'C:\\Windows\\System32']]),
                SchemaField('report.urls', FieldType.ARRAY, 'Detected URLs', [['http://malicious.com', 'https://c2server.net']]),
                SchemaField('report.ip_addresses', FieldType.ARRAY, 'Detected IP addresses', [['192.168.1.1', '10.0.0.1']]),
                SchemaField('report.registry_keys', FieldType.ARRAY, 'Windows registry keys', [['HKEY_LOCAL_MACHINE\\Software\\...']]),
                SchemaField('report.file_paths', FieldType.ARRAY, 'File system paths', [['C:\\Users\\Admin\\malware.exe']]),
            ],
            'condition_templates': [
                ConditionTemplate('Suspicious URL check', 'Check for malicious domains', 'field_contains',
                                'report.urls', 'malicious', 'Flag files with known bad domains'),
                ConditionTemplate('C2 IP detection', 'Detect command & control IPs', 'field_contains',
                                'report.ip_addresses', None, 'Cross-reference with threat intel feeds'),
            ],
            'malware_indicators': ['urls', 'ip_addresses', 'registry_keys'],
            'success_patterns': ['strings'],
        },
        
        'Doc_Info': {
            'description': 'Microsoft Office document analysis',
            'output_fields': [
                SchemaField('report.macros', FieldType.ARRAY, 'VBA macros found', [['AutoOpen', 'Document_Open']]),
                SchemaField('report.ole_streams', FieldType.ARRAY, 'OLE streams', [['Macros/VBA/Module1']]),
                SchemaField('report.suspicious_keywords', FieldType.ARRAY, 'Suspicious VBA keywords', [['Shell', 'CreateObject', 'WScript']]),
                SchemaField('report.embedded_objects', FieldType.ARRAY, 'Embedded files/objects', [['oleObject1.bin']]),
            ],
            'condition_templates': [
                ConditionTemplate('Macro detection', 'Check for VBA macros', 'field_contains',
                                'report.macros', 'AutoOpen', 'Route to sandbox if macros detected'),
                ConditionTemplate('Suspicious keywords', 'Detect malicious VBA patterns', 'field_contains',
                                'report.suspicious_keywords', 'Shell', 'Flag for manual review'),
            ],
            'malware_indicators': ['macros', 'suspicious_keywords', 'embedded_objects'],
            'success_patterns': ['ole_streams'],
        },
        
        # ========== Malware Detection Tools ==========
        'ClamAV': {
            'description': 'Open-source antivirus scanner',
            'output_fields': [
                SchemaField('report.detections', FieldType.ARRAY, 'Malware detections', [['Win.Trojan.Generic-123', 'EICAR-Test-File']]),
                SchemaField('report.raw_report', FieldType.STRING, 'Raw ClamAV output', ['Infected files: 1']),
                SchemaField('report.verdict', FieldType.STRING, 'Scan verdict', ['malicious', 'clean']),
            ],
            'condition_templates': [
                ConditionTemplate('Malware detected', 'Check if ClamAV found threats', 'verdict_malicious',
                                use_case='Trigger advanced analysis on infected files'),
                ConditionTemplate('Clean file', 'Verify file is clean', 'verdict_clean',
                                use_case='Skip resource-intensive analysis for clean files'),
            ],
            'malware_indicators': ['detections'],
            'success_patterns': ['detections', 'raw_report'],
        },
        
        'Yara': {
            'description': 'Pattern matching for malware identification',
            'output_fields': [
                SchemaField('report.matches', FieldType.ARRAY, 'Matched YARA rules', [
                    [{'rule': 'Ransomware_Generic', 'strings': ['$crypt1', '$crypt2']}]
                ]),
                SchemaField('report.rules', FieldType.ARRAY, 'Rule names', [['Trojan_Emotet', 'APT_Lazarus']]),
                SchemaField('report.meta', FieldType.OBJECT, 'Rule metadata', [{'author': 'researcher', 'date': '2024-01-01'}]),
            ],
            'condition_templates': [
                ConditionTemplate('YARA rule match', 'Check if any rules matched', 'yara_rule_match',
                                use_case='High-priority alert for rule matches'),
                ConditionTemplate('Specific rule match', 'Check for specific rule', 'field_contains',
                                'report.rules', 'Ransomware', 'Activate ransomware response protocol'),
            ],
            'malware_indicators': ['matches', 'rules'],
            'success_patterns': ['matches'],
        },
        
        # ========== PE File Analyzers ==========
        'PE_Info': {
            'description': 'Portable Executable (Windows) file analysis',
            'output_fields': [
                SchemaField('report.pe_info.signature.valid', FieldType.BOOLEAN, 'Digital signature valid', [True, False]),
                SchemaField('report.pe_info.signature.signer', FieldType.STRING, 'Code signer', ['Microsoft Corporation', 'Unknown']),
                SchemaField('report.pe_info.imphash', FieldType.STRING, 'Import hash', ['a1b2c3d4...']),
                SchemaField('report.pe_info.sections', FieldType.ARRAY, 'PE sections', [[{'name': '.text', 'entropy': 6.5}]]),
                SchemaField('report.pe_info.imports', FieldType.ARRAY, 'Imported functions', [['kernel32.dll!CreateFile']]),
                SchemaField('report.pe_info.exports', FieldType.ARRAY, 'Exported functions', [['DllMain']]),
                SchemaField('report.pe_info.compile_time', FieldType.STRING, 'Compilation timestamp', ['2024-01-01 12:00:00']),
            ],
            'condition_templates': [
                ConditionTemplate('Signature validation', 'Check digital signature', 'field_equals',
                                'report.pe_info.signature.valid', True, 'Trust signed binaries from known publishers'),
                ConditionTemplate('High entropy section', 'Detect packed/encrypted sections', 'field_greater_than',
                                'report.pe_info.sections[0].entropy', 7.0, 'Route to unpacker analyzers'),
                ConditionTemplate('Suspicious imports', 'Check for API hooking functions', 'field_contains',
                                'report.pe_info.imports', 'SetWindowsHook', 'Flag keylogger indicators'),
            ],
            'malware_indicators': ['imports', 'sections'],
            'success_patterns': ['pe_info', 'imphash'],
        },
        
        'Capa_Info': {
            'description': 'Detect malware capabilities using capa',
            'output_fields': [
                SchemaField('report.capabilities', FieldType.ARRAY, 'Detected capabilities', [
                    ['persistence', 'keylogging', 'network-communication', 'anti-analysis']
                ]),
                SchemaField('report.mitre_attack', FieldType.ARRAY, 'MITRE ATT&CK techniques', [['T1055', 'T1082']]),
                SchemaField('report.mbc', FieldType.ARRAY, 'Malware Behavior Catalog', [['Defense Evasion::Obfuscated Files']]),
            ],
            'condition_templates': [
                ConditionTemplate('Keylogger detection', 'Check for keylogging capability', 'capability_detected',
                                expected_value='keylogging', use_case='High-priority alert for keyloggers'),
                ConditionTemplate('Persistence mechanism', 'Detect persistence techniques', 'capability_detected',
                                expected_value='persistence', use_case='Enhanced monitoring for persistent threats'),
                ConditionTemplate('Anti-analysis detected', 'Check for evasion techniques', 'capability_detected',
                                expected_value='anti-analysis', use_case='Route to advanced sandbox analysis'),
            ],
            'malware_indicators': ['capabilities', 'mitre_attack'],
            'success_patterns': ['capabilities'],
        },
        
        'PEframe': {
            'description': 'PE malware analysis framework',
            'output_fields': [
                SchemaField('report.suspicious_functions', FieldType.ARRAY, 'Suspicious API calls', [['VirtualAlloc', 'WriteProcessMemory']]),
                SchemaField('report.suspicious_sections', FieldType.ARRAY, 'Suspicious PE sections', [['.upx', '.aspack']]),
                SchemaField('report.meta', FieldType.OBJECT, 'Metadata analysis', [{'packer': 'UPX', 'compiler': 'MSVC'}]),
            ],
            'condition_templates': [
                ConditionTemplate('Packer detection', 'Check for packed executable', 'field_contains',
                                'report.suspicious_sections', 'upx', 'Route to unpacker'),
                ConditionTemplate('Code injection API', 'Detect injection techniques', 'field_contains',
                                'report.suspicious_functions', 'WriteProcessMemory', 'Flag for advanced analysis'),
            ],
            'malware_indicators': ['suspicious_functions', 'suspicious_sections'],
            'success_patterns': ['suspicious_functions', 'meta'],
        },
        
        # ========== Specialized Analyzers ==========
        'PDF_Info': {
            'description': 'PDF document analysis',
            'output_fields': [
                SchemaField('report.javascript', FieldType.ARRAY, 'Embedded JavaScript', [['eval(unescape(...))']]),
                SchemaField('report.suspicious_objects', FieldType.ARRAY, 'Suspicious PDF objects', [['/OpenAction', '/AA']]),
                SchemaField('report.urls', FieldType.ARRAY, 'Embedded URLs', [['http://phishing-site.com']]),
                SchemaField('report.embedded_files', FieldType.ARRAY, 'Embedded files', [['malware.exe']]),
            ],
            'condition_templates': [
                ConditionTemplate('JavaScript in PDF', 'Check for embedded JS', 'field_contains',
                                'report.javascript', 'eval', 'Route to sandbox for JS execution'),
                ConditionTemplate('Auto-execute action', 'Detect auto-open actions', 'field_contains',
                                'report.suspicious_objects', 'OpenAction', 'Flag for manual review'),
            ],
            'malware_indicators': ['javascript', 'suspicious_objects', 'embedded_files'],
            'success_patterns': ['suspicious_objects'],
        },
        
        'Rtf_Info': {
            'description': 'Rich Text Format document analysis',
            'output_fields': [
                SchemaField('report.ole_objects', FieldType.ARRAY, 'Embedded OLE objects', [['oleObject1']]),
                SchemaField('report.exploits', FieldType.ARRAY, 'Detected exploit attempts', [['CVE-2017-11882']]),
                SchemaField('report.urls', FieldType.ARRAY, 'Embedded URLs', [['http://exploit-kit.com']]),
            ],
            'condition_templates': [
                ConditionTemplate('Exploit detection', 'Check for known exploits', 'field_contains',
                                'report.exploits', 'CVE', 'Immediate threat response'),
            ],
            'malware_indicators': ['exploits', 'ole_objects'],
            'success_patterns': ['ole_objects'],
        },
        
        'Xlm_Macro_Deobfuscator': {
            'description': 'Excel 4.0 macro analysis',
            'output_fields': [
                SchemaField('report.macros', FieldType.ARRAY, 'XLM macros', [['AUTO_OPEN', 'EXEC']]),
                SchemaField('report.suspicious_calls', FieldType.ARRAY, 'Suspicious function calls', [['CALL', 'EXEC', 'REGISTER']]),
                SchemaField('report.deobfuscated_code', FieldType.STRING, 'Deobfuscated macro code', ['=EXEC("cmd.exe")...']),
            ],
            'condition_templates': [
                ConditionTemplate('Auto-execute macro', 'Check for auto-open macros', 'field_contains',
                                'report.macros', 'AUTO_OPEN', 'Route to sandbox execution'),
            ],
            'malware_indicators': ['suspicious_calls', 'macros'],
            'success_patterns': ['macros'],
        },
        
        # ========== Signature & Behavioral Analysis ==========
        'Signature_Info': {
            'description': 'Digital signature verification',
            'output_fields': [
                SchemaField('report.signed', FieldType.BOOLEAN, 'File is signed', [True, False]),
                SchemaField('report.valid', FieldType.BOOLEAN, 'Signature is valid', [True, False]),
                SchemaField('report.signer', FieldType.STRING, 'Certificate signer', ['Microsoft Corporation']),
                SchemaField('report.timestamp', FieldType.STRING, 'Signature timestamp', ['2024-01-01 12:00:00']),
            ],
            'condition_templates': [
                ConditionTemplate('Valid signature', 'Check signature validity', 'field_equals',
                                'report.valid', True, 'Trust validation for signed files'),
                ConditionTemplate('Known signer', 'Verify trusted publisher', 'field_equals',
                                'report.signer', 'Microsoft Corporation', 'Whitelist trusted publishers'),
            ],
            'malware_indicators': [],
            'success_patterns': ['signed', 'valid'],
        },
        
        'BoxJS': {
            'description': 'JavaScript deobfuscation and analysis',
            'output_fields': [
                SchemaField('report.deobfuscated_code', FieldType.STRING, 'Deobfuscated JavaScript', ['var payload = ...']),
                SchemaField('report.urls', FieldType.ARRAY, 'Extracted URLs', [['http://c2-server.com']]),
                SchemaField('report.iocs', FieldType.ARRAY, 'Indicators of compromise', [['malicious_function()']]),
            ],
            'condition_templates': [
                ConditionTemplate('IOC detection', 'Check for compromise indicators', 'field_contains',
                                'report.iocs', None, 'Immediate threat alert'),
            ],
            'malware_indicators': ['iocs', 'urls'],
            'success_patterns': ['deobfuscated_code'],
        },
        
        # ========== Mobile Analysis ==========
        'APKiD': {
            'description': 'Android APK identification',
            'output_fields': [
                SchemaField('report.compiler', FieldType.STRING, 'DEX compiler', ['dx', 'dexlib']),
                SchemaField('report.packer', FieldType.STRING, 'APK packer', ['UPX', 'Bangcle']),
                SchemaField('report.obfuscator', FieldType.STRING, 'Code obfuscator', ['ProGuard', 'DexGuard']),
            ],
            'condition_templates': [
                ConditionTemplate('Packed APK', 'Check for APK packer', 'field_contains',
                                'report.packer', None, 'Route to unpacker'),
            ],
            'malware_indicators': ['packer', 'obfuscator'],
            'success_patterns': ['compiler'],
        },
        
        'Quark_Engine': {
            'description': 'Android malware scoring engine',
            'output_fields': [
                SchemaField('report.threat_score', FieldType.NUMBER, 'Malware threat score (0-100)', [85, 12]),
                SchemaField('report.matched_rules', FieldType.ARRAY, 'Matched behavior rules', [['SMS_Trojan', 'Banking_Malware']]),
                SchemaField('report.permissions', FieldType.ARRAY, 'Requested permissions', [['SEND_SMS', 'READ_CONTACTS']]),
            ],
            'condition_templates': [
                ConditionTemplate('High threat score', 'Check threat level', 'field_greater_than',
                                'report.threat_score', 70, 'Immediate threat response for high scores'),
                ConditionTemplate('SMS trojan', 'Detect SMS malware', 'field_contains',
                                'report.matched_rules', 'SMS_Trojan', 'Specialized SMS malware analysis'),
            ],
            'malware_indicators': ['matched_rules', 'threat_score'],
            'success_patterns': ['threat_score'],
        },
        
        # ========== Additional File Analyzers ==========
        'Flare_Capa': {
            'description': 'FLARE team capability detection',
            'output_fields': [
                SchemaField('report.capabilities', FieldType.ARRAY, 'Detected capabilities', [
                    ['anti-debugging', 'encrypted-strings', 'registry-manipulation']
                ]),
                SchemaField('report.attack_patterns', FieldType.ARRAY, 'Attack patterns', [['T1055', 'T1027']]),
            ],
            'condition_templates': [
                ConditionTemplate('Anti-debugging', 'Check for debugger detection', 'capability_detected',
                                expected_value='anti-debugging', use_case='Use specialized analysis environment'),
            ],
            'malware_indicators': ['capabilities', 'attack_patterns'],
            'success_patterns': ['capabilities'],
        },
        
        'UnpacMe': {
            'description': 'Automated unpacking service',
            'output_fields': [
                SchemaField('report.unpacked', FieldType.BOOLEAN, 'Successfully unpacked', [True, False]),
                SchemaField('report.packer_type', FieldType.STRING, 'Detected packer', ['UPX', 'ASPack', 'Themida']),
                SchemaField('report.unpacked_hash', FieldType.STRING, 'Hash of unpacked file', ['abc123...']),
            ],
            'condition_templates': [
                ConditionTemplate('Unpacking success', 'Check if unpacking succeeded', 'field_equals',
                                'report.unpacked', True, 'Analyze unpacked payload'),
            ],
            'malware_indicators': ['packer_type'],
            'success_patterns': ['unpacked'],
        },
        
        'VirusTotal_v3_Get_File': {
            'description': 'VirusTotal file reputation lookup',
            'output_fields': [
                SchemaField('report.stats.malicious', FieldType.NUMBER, 'Malicious detections', [45, 0]),
                SchemaField('report.stats.suspicious', FieldType.NUMBER, 'Suspicious detections', [5, 0]),
                SchemaField('report.stats.harmless', FieldType.NUMBER, 'Harmless votes', [0, 60]),
                SchemaField('report.total_votes', FieldType.NUMBER, 'Total AV vendors', [70]),
            ],
            'condition_templates': [
                ConditionTemplate('High detection rate', 'Check AV detection ratio', 'field_greater_than',
                                'report.stats.malicious', 10, 'Confirmed malware by multiple AVs'),
                ConditionTemplate('Zero detections', 'Verify clean file', 'field_equals',
                                'report.stats.malicious', 0, 'Low-risk file processing'),
            ],
            'malware_indicators': ['stats.malicious', 'stats.suspicious'],
            'success_patterns': ['stats', 'total_votes'],
        },
        
        'Suricata': {
            'description': 'Network IDS/IPS signature matching',
            'output_fields': [
                SchemaField('report.alerts', FieldType.ARRAY, 'Triggered alerts', [
                    [{'signature': 'ET MALWARE Trojan Traffic', 'severity': 1}]
                ]),
                SchemaField('report.flows', FieldType.ARRAY, 'Network flows', [['192.168.1.1 -> 10.0.0.1:443']]),
            ],
            'condition_templates': [
                ConditionTemplate('IDS alert', 'Check for network signatures', 'has_detections',
                                use_case='Network-based threat detection'),
            ],
            'malware_indicators': ['alerts'],
            'success_patterns': ['flows'],
        },
    }
    
    @classmethod
    def get_analyzer_schema(cls, analyzer_name: str) -> Optional[Dict[str, Any]]:
        """Get schema for specific analyzer"""
        schema = cls.ANALYZER_SCHEMAS.get(analyzer_name)
        if not schema:
            logger.warning(f"No schema defined for analyzer: {analyzer_name}")
        return schema
    
    @classmethod
    def get_output_fields(cls, analyzer_name: str) -> List[SchemaField]:
        """Get list of output fields for analyzer"""
        schema = cls.get_analyzer_schema(analyzer_name)
        return schema.get('output_fields', []) if schema else []
    
    @classmethod
    def get_condition_templates(cls, analyzer_name: str) -> List[ConditionTemplate]:
        """Get pre-built condition templates for analyzer"""
        schema = cls.get_analyzer_schema(analyzer_name)
        return schema.get('condition_templates', []) if schema else []
    
    @classmethod
    def get_malware_indicators(cls, analyzer_name: str) -> List[str]:
        """Get fields that indicate malware presence"""
        schema = cls.get_analyzer_schema(analyzer_name)
        return schema.get('malware_indicators', []) if schema else []
    
    @classmethod
    def validate_field_path(cls, analyzer_name: str, field_path: str) -> Tuple[bool, str]:
        """
        Validate if field path exists in analyzer schema
        
        Returns:
            (is_valid, message)
        """
        schema = cls.get_analyzer_schema(analyzer_name)
        if not schema:
            return (False, f"Unknown analyzer: {analyzer_name}")
        
        fields = schema.get('output_fields', [])
        field_paths = [f.path for f in fields]
        
        # Exact match
        if field_path in field_paths:
            return (True, "Valid field path")
        
        # Check if it's a partial match (e.g., user typed "report.pe_info" but schema has "report.pe_info.signature")
        matching_fields = [fp for fp in field_paths if fp.startswith(field_path) or field_path.startswith(fp)]
        if matching_fields:
            return (True, f"Field path matches: {', '.join(matching_fields[:3])}")
        
        return (False, f"Field path not found in {analyzer_name} schema. Available fields: {', '.join(field_paths[:5])}")
    
    @classmethod
    def suggest_field_paths(cls, analyzer_name: str, partial_path: str = "") -> List[str]:
        """Get autocomplete suggestions for field paths"""
        fields = cls.get_output_fields(analyzer_name)
        
        if not partial_path:
            return [f.path for f in fields]
        
        # Filter fields that start with partial path
        suggestions = [f.path for f in fields if f.path.startswith(partial_path)]
        
        # If no exact matches, try fuzzy matching
        if not suggestions:
            suggestions = [f.path for f in fields if partial_path.lower() in f.path.lower()]
        
        return suggestions[:10]  # Limit to 10 suggestions
    
    @classmethod
    def detect_schema_from_sample(cls, analyzer_name: str, sample_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically detect schema from actual analyzer output
        Useful when analyzer output format changes or for custom analyzers
        """
        detected_fields = []
        
        def traverse_dict(obj: Any, path: str = "report"):
            """Recursively traverse output and detect fields"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    field_path = f"{path}.{key}" if path else key
                    field_type = cls._infer_field_type(value)
                    
                    detected_fields.append({
                        'path': field_path,
                        'type': field_type.value,
                        'sample_value': value if not isinstance(value, (dict, list)) else str(type(value))
                    })
                    
                    if isinstance(value, (dict, list)):
                        traverse_dict(value, field_path)
            elif isinstance(obj, list) and len(obj) > 0:
                # Analyze first item in array
                traverse_dict(obj[0], path)
        
        # Traverse the sample output
        if 'report' in sample_output:
            traverse_dict(sample_output['report'], 'report')
        else:
            traverse_dict(sample_output, '')
        
        logger.info(f"Detected {len(detected_fields)} fields in {analyzer_name} output")
        
        return {
            'analyzer_name': analyzer_name,
            'detected_fields': detected_fields,
            'sample_timestamp': 'runtime',
        }
    
    @staticmethod
    def _infer_field_type(value: Any) -> FieldType:
        """Infer field type from value"""
        if isinstance(value, bool):
            return FieldType.BOOLEAN
        elif isinstance(value, int) or isinstance(value, float):
            return FieldType.NUMBER
        elif isinstance(value, str):
            return FieldType.STRING
        elif isinstance(value, list):
            return FieldType.ARRAY
        elif isinstance(value, dict):
            return FieldType.OBJECT
        else:
            return FieldType.ANY
    
    @classmethod
    def validate_condition(cls, condition: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Comprehensive condition validation
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        if 'type' not in condition:
            errors.append("Condition must have 'type' field")
        
        if 'source_analyzer' not in condition:
            errors.append("Condition must have 'source_analyzer' field")
        
        if errors:
            return (False, errors)
        
        cond_type = condition['type']
        analyzer = condition['source_analyzer']
        
        # Validate analyzer exists in schema
        if not cls.get_analyzer_schema(analyzer):
            errors.append(f"Unknown analyzer: {analyzer}")
        
        # Validate field-based conditions
        if cond_type in ['field_equals', 'field_contains', 'field_greater_than', 'field_less_than']:
            if 'field_path' not in condition:
                errors.append(f"Condition type '{cond_type}' requires 'field_path'")
            elif analyzer in cls.ANALYZER_SCHEMAS:
                is_valid, msg = cls.validate_field_path(analyzer, condition['field_path'])
                if not is_valid:
                    errors.append(msg)
            
            if 'expected_value' not in condition:
                errors.append(f"Condition type '{cond_type}' requires 'expected_value'")
        
        # Validate capability detection
        if cond_type == 'capability_detected':
            if 'expected_value' not in condition:
                errors.append("Capability detection requires 'expected_value' (capability name)")
        
        return (len(errors) == 0, errors)
    
    @classmethod
    def get_all_analyzers(cls) -> List[str]:
        """Get list of all supported analyzers"""
        return list(cls.ANALYZER_SCHEMAS.keys())
    
    @classmethod
    def get_analyzer_description(cls, analyzer_name: str) -> str:
        """Get human-readable description of analyzer"""
        schema = cls.get_analyzer_schema(analyzer_name)
        return schema.get('description', 'No description available') if schema else 'Unknown analyzer'


# Global schema manager instance
schema_manager = AnalyzerSchemaManager()
