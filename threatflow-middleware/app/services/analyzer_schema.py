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
                # VERIFIED from actual response
                SchemaField('report.md5', FieldType.STRING, 'MD5 hash', ['a1b2c3d4...']),
                SchemaField('report.sha1', FieldType.STRING, 'SHA1 hash', []),
                SchemaField('report.sha256', FieldType.STRING, 'SHA256 hash', ['e5f6g7h8...']),
                SchemaField('report.tlsh', FieldType.STRING, 'TLSH hash', []),
                SchemaField('report.ssdeep', FieldType.STRING, 'Fuzzy hash', ['3:ABC123:XYZ']),
                SchemaField('report.magic', FieldType.STRING, 'File type from magic bytes', ['PE32 executable', 'PDF document', 'ASCII text']),
                SchemaField('report.mimetype', FieldType.STRING, 'MIME type', ['application/x-executable', 'application/pdf', 'text/plain']),
                SchemaField('report.filetype', FieldType.STRING, 'File type short name', ['PE', 'PDF', 'TXT']),
                SchemaField('report.exiftool', FieldType.OBJECT, 'ExifTool metadata', []),
            ],
            'condition_templates': [
                ConditionTemplate('File type check', 'Check specific file type', 'field_equals',
                                'report.filetype', 'PE', 'Route PE files to PE analyzers'),
                ConditionTemplate('Executable check', 'Check if file is executable', 'field_contains',
                                'report.mimetype', 'executable', 'Apply PE analysis only to executables'),
            ],
            'malware_indicators': [],  # VERIFIED: metadata only, no malware detection
            'success_patterns': ['md5', 'sha256', 'mimetype'],
        },
        
        'Strings_Info': {
            'description': 'Extract and analyze strings from binary files',
            'output_fields': [
                # VERIFIED from actual response
                SchemaField('report.data', FieldType.ARRAY, 'Extracted strings', []),
                SchemaField('report.uris', FieldType.ARRAY, 'Detected URIs', []),
                SchemaField('report.exceeded_max_number_of_strings', FieldType.BOOLEAN, 'String limit exceeded', [False]),
            ],
            'condition_templates': [
                ConditionTemplate('Has strings', 'Check if strings were extracted', 'has_detections',
                                use_case='Route based on string content availability'),
                ConditionTemplate('Suspicious URL check', 'Check for malicious domains', 'field_contains',
                                'report.data', 'malicious', 'Flag files with suspicious patterns'),
            ],
            'malware_indicators': ['data'],  # VERIFIED: check strings for patterns
            'success_patterns': ['data'],
        },
        
        'Doc_Info': {
            'description': 'Microsoft Office document analysis (OLE/VBA)',
            'output_fields': [
                # VERIFIED from actual response
                SchemaField('report.mraptor', FieldType.STRING, 'Macro security rating', ['ok', 'suspicious']),
                SchemaField('report.olevba', FieldType.OBJECT, 'VBA macro analysis', []),
                SchemaField('report.msodde', FieldType.STRING, 'DDE link extraction', []),
                SchemaField('report.uris', FieldType.ARRAY, 'Extracted URIs', []),
                SchemaField('report.extracted_CVEs', FieldType.ARRAY, 'CVE references', []),
            ],
            'condition_templates': [
                ConditionTemplate('Suspicious macro', 'Check mraptor result', 'field_equals',
                                'report.mraptor', 'suspicious', 'Flag documents with suspicious macros'),
                ConditionTemplate('Clean document', 'Check mraptor is ok', 'field_equals',
                                'report.mraptor', 'ok', 'Verified safe document'),
            ],
            'malware_indicators': ['mraptor'],  # VERIFIED: "suspicious" indicates threat
            'success_patterns': ['mraptor', 'olevba'],
        },
        
        # ========== Malware Detection Tools ==========
        'ClamAV': {
            'description': 'Open-source antivirus scanner',
            'output_fields': [
                # VERIFIED from actual response
                SchemaField('report.detections', FieldType.ARRAY, 'Malware detection names', [['Eicar-Signature', 'Unix.Tool.13409-1']]),
                SchemaField('report.raw_report', FieldType.STRING, 'Raw ClamAV scan output', ['Infected files: 1\nEicar-Signature FOUND']),
            ],
            'condition_templates': [
                ConditionTemplate('Malware detected', 'Check if ClamAV found threats', 'verdict_malicious',
                                use_case='Trigger advanced analysis on infected files'),
                ConditionTemplate('Clean file', 'Verify file is clean', 'verdict_clean',
                                use_case='Skip resource-intensive analysis for clean files'),
                ConditionTemplate('Has detections', 'Check if detections array is not empty', 'has_detections',
                                use_case='Route based on any detection'),
            ],
            'malware_indicators': ['detections'],  # VERIFIED
            'success_patterns': ['detections', 'raw_report'],
        },
        
        'Yara': {
            'description': 'Pattern matching for malware identification using multiple rule sets',
            'output_fields': [
                # VERIFIED from actual response - multiple rule set fields
                SchemaField('report.yara-rules_rules', FieldType.ARRAY, 'Yara-Rules community rules', []),
                SchemaField('report.elastic_protections-artifacts', FieldType.ARRAY, 'Elastic security rules', []),
                SchemaField('report.advanced-threat-research_yara-rules', FieldType.ARRAY, 'McAfee ATR rules', []),
                SchemaField('report.neo23x0_signature-base', FieldType.ARRAY, 'Florian Roth signature base', []),
                SchemaField('report.bartblaze_yara-rules', FieldType.ARRAY, 'Bartblaze rules', []),
                SchemaField('report.intezer_yara-rules', FieldType.ARRAY, 'Intezer rules', []),
                SchemaField('report.inquest_yara-rules', FieldType.ARRAY, 'InQuest rules', []),
                SchemaField('report.reversinglabs_reversinglabs-yara-rules', FieldType.ARRAY, 'ReversingLabs rules', []),
                # data_model fields from job level
                SchemaField('data_model.evaluation', FieldType.STRING, 'Overall evaluation', ['malicious', 'clean']),
                SchemaField('data_model.signatures', FieldType.ARRAY, 'Matched signatures', []),
            ],
            'condition_templates': [
                ConditionTemplate('YARA rule match', 'Check if any rules matched', 'yara_rule_match',
                                use_case='High-priority alert for rule matches'),
                ConditionTemplate('Specific rule match', 'Check for specific rule set', 'field_contains',
                                'report.elastic_protections-artifacts', None, 'Elastic rule match'),
            ],
            'malware_indicators': [
                'yara-rules_rules', 'elastic_protections-artifacts',
                'advanced-threat-research_yara-rules', 'neo23x0_signature-base'
            ],  # VERIFIED
            'success_patterns': ['yara-rules_rules'],
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
                # VERIFIED from actual response
                SchemaField('report.rtfobj', FieldType.OBJECT, 'RTF object analysis', [{'ole_objects': []}]),
                SchemaField('report.follina', FieldType.ARRAY, 'Follina exploit detection', []),
            ],
            'condition_templates': [
                ConditionTemplate('OLE objects detected', 'Check for embedded OLE', 'has_detections',
                                use_case='Route to OLE analysis'),
                ConditionTemplate('Follina exploit', 'Check for CVE-2022-30190', 'field_contains',
                                'report.follina', None, 'Immediate threat response'),
            ],
            'malware_indicators': ['rtfobj.ole_objects', 'follina'],  # VERIFIED
            'success_patterns': ['rtfobj'],
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
            'description': 'JavaScript deobfuscation and analysis sandbox',
            'output_fields': [
                # VERIFIED from actual response
                SchemaField('report.IOC.json', FieldType.ARRAY, 'Indicators of compromise', []),
                SchemaField('report.snippets.json', FieldType.OBJECT, 'Deobfuscated code snippets', {}),
                SchemaField('report.analysis.log', FieldType.ARRAY, 'Analysis log entries', []),
                SchemaField('report.uris', FieldType.ARRAY, 'Extracted URIs', []),
                # Note: urls.json, resources.json, active_urls.json may return FileNotFoundError
            ],
            'condition_templates': [
                ConditionTemplate('IOC detection', 'Check for indicators of compromise', 'has_detections',
                                use_case='Alert on detected IOCs'),
            ],
            'malware_indicators': ['IOC.json'],  # VERIFIED
            'success_patterns': ['snippets.json', 'analysis.log'],
        },
        
        # ========== Mobile Analysis ==========
        'APK_Artifacts': {
            'description': 'Android APK metadata and permission analysis',
            'output_fields': [
                # VERIFIED from actual response
                SchemaField('report.permission', FieldType.ARRAY, 'Requested permissions', [
                    ['android.permission.INTERNET', 'android.permission.READ_SMS']
                ]),
                SchemaField('report.intent', FieldType.ARRAY, 'Intent filters', [
                    ['android.intent.action.MAIN', 'android.intent.category.LAUNCHER']
                ]),
                SchemaField('report.application', FieldType.ARRAY, 'Application identifiers', [
                    ['com.example.app']
                ]),
            ],
            'condition_templates': [
                ConditionTemplate('Dangerous permissions', 'Check for SMS/Contacts access', 'field_contains',
                                'report.permission', 'READ_SMS', 'Flag privacy-invasive apps'),
                ConditionTemplate('Has permissions', 'Check if any permissions requested', 'has_detections',
                                use_case='Route based on permission count'),
            ],
            'malware_indicators': ['permission'],  # VERIFIED: check for dangerous permissions
            'success_patterns': ['permission', 'intent', 'application'],
        },
        
        'Androguard': {
            'description': 'Android APK reverse engineering analysis',
            'output_fields': [
                SchemaField('report.package', FieldType.STRING, 'Package name', []),
                SchemaField('report.permissions', FieldType.ARRAY, 'Permissions list', []),
                SchemaField('report.activities', FieldType.ARRAY, 'Activity components', []),
                SchemaField('report.services', FieldType.ARRAY, 'Service components', []),
                SchemaField('report.receivers', FieldType.ARRAY, 'Broadcast receivers', []),
            ],
            'condition_templates': [
                ConditionTemplate('APK analysis success', 'Check if analysis succeeded', 'analyzer_success',
                                use_case='Route based on valid APK'),
            ],
            'malware_indicators': [],  # Complex analysis, check specific fields
            'success_patterns': ['package'],
        },
        
        'APKiD': {
            'description': 'Android APK compiler/packer identification',
            'output_fields': [
                # VERIFIED from actual response
                SchemaField('report.files', FieldType.ARRAY, 'Detected packers/obfuscators', []),
                SchemaField('report.rules_sha256', FieldType.STRING, 'Rules hash', []),
                SchemaField('report.apkid_version', FieldType.STRING, 'APKiD version', ['2.1.4']),
            ],
            'condition_templates': [
                ConditionTemplate('Packer detected', 'Check for APK packer', 'has_detections',
                                use_case='Route to unpacker'),
            ],
            'malware_indicators': ['files'],  # VERIFIED: detections appear here
            'success_patterns': ['apkid_version'],
        },
        
        'Quark_Engine': {
            'description': 'Android malware scoring engine',
            'output_fields': [
                # VERIFIED from actual response
                SchemaField('report.threat_level', FieldType.STRING, 'Threat classification', ['Low Risk', 'Medium Risk', 'High Risk']),
                SchemaField('report.total_score', FieldType.NUMBER, 'Malware threat score (0-100)', [0, 50, 100]),
                SchemaField('report.crimes', FieldType.ARRAY, 'Detected malicious behaviors', []),
                SchemaField('report.md5', FieldType.STRING, 'File MD5 hash', []),
                SchemaField('report.size_bytes', FieldType.NUMBER, 'File size', []),
                SchemaField('report.apk_filename', FieldType.STRING, 'APK filename', []),
            ],
            'condition_templates': [
                ConditionTemplate('High threat score', 'Check threat level', 'field_equals',
                                'report.threat_level', 'High Risk', 'Immediate threat response'),
                ConditionTemplate('Score threshold', 'Check if score exceeds threshold', 'field_greater_than',
                                'report.total_score', 50, 'Medium-high risk threshold'),
                ConditionTemplate('Low risk', 'Verify low threat level', 'field_equals',
                                'report.threat_level', 'Low Risk', 'Safe APK routing'),
            ],
            'malware_indicators': ['threat_level', 'total_score', 'crimes'],  # VERIFIED
            'success_patterns': ['threat_level', 'total_score'],
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
