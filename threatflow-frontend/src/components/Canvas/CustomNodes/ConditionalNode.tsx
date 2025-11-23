import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import './ConditionalNode.css';
import { ConditionalNodeData } from '../../../types/workflow';

export const ConditionalNode = memo(({ data, selected }: NodeProps<ConditionalNodeData>) => {
  const getConditionLabel = (conditionType?: string) => {
    switch (conditionType) {
      case 'verdict_malicious':
        return 'Malware Detected';
      case 'verdict_suspicious':
        return 'Suspicious';
      case 'verdict_clean':
        return 'Clean';
      case 'analyzer_success':
        return 'Analyzer Success';
      case 'analyzer_failed':
        return 'Analyzer Failed';
      case 'field_equals':
        return 'Field Equals';
      case 'field_contains':
        return 'Field Contains';
      case 'field_greater_than':
        return 'Field > Value';
      case 'field_less_than':
        return 'Field < Value';
      case 'yara_rule_match':
        return 'YARA Rule Match';
      case 'capability_detected':
        return 'Capability Detected';
      default:
        return 'Condition';
    }
  };

  const getConditionIcon = (conditionType?: string) => {
    switch (conditionType) {
      case 'verdict_malicious':
        return '🛡️';
      case 'verdict_suspicious':
        return '⚠️';
      case 'verdict_clean':
        return '✅';
      case 'analyzer_success':
        return '✓';
      case 'analyzer_failed':
        return '✗';
      case 'field_equals':
      case 'field_contains':
      case 'field_greater_than':
      case 'field_less_than':
        return '🔍';
      case 'yara_rule_match':
        return '🎯';
      case 'capability_detected':
        return '⚙️';
      default:
        return '◊';
    }
  };

  return (
    <div 
      className={`conditional-node ${selected ? 'selected' : ''}`}
      style={{
        padding: '15px 20px',
        border: `2px solid ${selected ? '#ff5722' : '#ff9800'}`,
        borderRadius: '8px',
        background: '#fff3e0',
        minWidth: '180px',
        position: 'relative',
        boxShadow: selected ? '0 4px 12px rgba(255,152,0,0.3)' : '0 2px 4px rgba(0,0,0,0.1)'
      }}
    >
      {/* Input handle (left side) */}
      <Handle 
        type="target" 
        position={Position.Left}
        id="input"
        style={{ 
          background: '#666',
          width: '12px',
          height: '12px'
        }}
      />
      
      {/* Node content */}
      <div style={{ textAlign: 'center' }}>
        <div style={{ 
          fontSize: '20px',
          marginBottom: '4px'
        }}>
          {getConditionIcon(data.conditionType)}
        </div>
        <div style={{ 
          fontWeight: 'bold', 
          fontSize: '12px',
          marginBottom: '4px',
          color: '#e65100'
        }}>
          {getConditionLabel(data.conditionType)}
        </div>
        {data.sourceAnalyzer && (
          <div style={{ 
            fontSize: '10px', 
            color: '#666',
            fontStyle: 'italic',
            marginBottom: '2px'
          }}>
            from: {data.sourceAnalyzer}
          </div>
        )}
        {data.fieldPath && (
          <div style={{ 
            fontSize: '9px', 
            color: '#888',
            fontFamily: 'monospace',
            maxWidth: '140px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            {data.fieldPath}
          </div>
        )}
        {data.expectedValue !== undefined && (
          <div style={{ 
            fontSize: '9px', 
            color: '#888',
            fontFamily: 'monospace',
            maxWidth: '140px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            = {String(data.expectedValue)}
          </div>
        )}
      </div>
      
      {/* True output (top-right) */}
      <Handle 
        type="source" 
        position={Position.Right}
        id="true-output"
        style={{ 
          background: '#4caf50',
          width: '12px',
          height: '12px',
          top: '30%'
        }}
      />
      
      {/* False output (bottom-right) */}
      <Handle 
        type="source" 
        position={Position.Right}
        id="false-output"
        style={{ 
          background: '#f44336',
          width: '12px',
          height: '12px',
          top: '70%'
        }}
      />
      
      {/* Branch labels */}
      <div style={{
        position: 'absolute',
        right: '-50px',
        top: 'calc(30% - 10px)',
        fontSize: '11px',
        color: '#4caf50',
        fontWeight: 'bold',
        pointerEvents: 'none'
      }}>
        ✓ True
      </div>
      
      <div style={{
        position: 'absolute',
        right: '-50px',
        top: 'calc(70% - 10px)',
        fontSize: '11px',
        color: '#f44336',
        fontWeight: 'bold',
        pointerEvents: 'none'
      }}>
        ✗ False
      </div>
    </div>
  );
});

ConditionalNode.displayName = 'ConditionalNode';
