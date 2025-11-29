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

  // Determine styling based on execution result
  const getExecutionStyling = () => {
    if (data.executionResult === null || data.executionResult === undefined) {
      // Not executed yet - default styling
      return {
        borderColor: selected ? '#ff5722' : '#ff9800',
        background: '#fff3e0',
        boxShadow: selected ? '0 4px 12px rgba(255,152,0,0.3)' : '0 2px 4px rgba(0,0,0,0.1)',
        resultIcon: null,
        resultLabel: null
      };
    } else if (data.executionResult === true) {
      // Condition evaluated to TRUE
      return {
        borderColor: '#4caf50',
        background: 'linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%)',
        boxShadow: selected ? '0 4px 12px rgba(76,175,80,0.4)' : '0 2px 8px rgba(76,175,80,0.2)',
        resultIcon: '✅',
        resultLabel: 'TRUE'
      };
    } else {
      // Condition evaluated to FALSE
      return {
        borderColor: '#f44336',
        background: 'linear-gradient(135deg, #ffebee 0%, #fce4ec 100%)',
        boxShadow: selected ? '0 4px 12px rgba(244,67,54,0.4)' : '0 2px 8px rgba(244,67,54,0.2)',
        resultIcon: '❌',
        resultLabel: 'FALSE'
      };
    }
  };

  const executionStyle = getExecutionStyling();

  return (
    <div 
      className={`conditional-node ${selected ? 'selected' : ''} ${data.executionResult !== null && data.executionResult !== undefined ? 'executed' : ''}`}
      style={{
        padding: '15px 20px',
        border: `4px solid ${executionStyle.borderColor}`,
        borderRadius: '12px',
        background: executionStyle.background,
        minWidth: '200px',
        position: 'relative',
        boxShadow: executionStyle.boxShadow,
        transition: 'all 0.4s ease',
        transform: data.executionResult !== null && data.executionResult !== undefined ? 'scale(1.05)' : 'scale(1)'
      }}
    >
      {/* LARGE EXECUTION RESULT BADGE - TOP CENTER */}
      {executionStyle.resultIcon && (
        <div style={{
          position: 'absolute',
          top: '-15px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: executionStyle.borderColor,
          color: 'white',
          borderRadius: '20px',
          padding: '6px 12px',
          fontSize: '14px',
          fontWeight: 'bold',
          boxShadow: '0 4px 8px rgba(0,0,0,0.3)',
          zIndex: 10,
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          minWidth: '80px',
          justifyContent: 'center'
        }}>
          <span style={{ fontSize: '16px' }}>{executionStyle.resultIcon}</span>
          <span>{executionStyle.resultLabel}</span>
        </div>
      )}

      {/* Input handle (left side) */}
      <Handle 
        type="target" 
        position={Position.Left}
        id="input"
        style={{ 
          background: '#666',
          width: '14px',
          height: '14px'
        }}
      />
      
      {/* Node content */}
      <div style={{ textAlign: 'center', marginTop: executionStyle.resultIcon ? '15px' : '0' }}>
        <div style={{ 
          fontSize: '22px',
          marginBottom: '6px'
        }}>
          {getConditionIcon(data.conditionType)}
        </div>
        <div style={{ 
          fontWeight: 'bold', 
          fontSize: '13px',
          marginBottom: '6px',
          color: data.executionResult !== null && data.executionResult !== undefined ? 
            (data.executionResult ? '#2e7d32' : '#c62828') : '#e65100'
        }}>
          {getConditionLabel(data.conditionType)}
        </div>
        
        {data.sourceAnalyzer && (
          <div style={{ 
            fontSize: '11px', 
            color: '#666',
            fontStyle: 'italic',
            marginBottom: '4px'
          }}>
            from: {data.sourceAnalyzer}
          </div>
        )}
        {data.fieldPath && (
          <div style={{ 
            fontSize: '10px', 
            color: '#888',
            fontFamily: 'monospace',
            maxWidth: '160px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            {data.fieldPath}
          </div>
        )}
        {data.expectedValue !== undefined && (
          <div style={{ 
            fontSize: '10px', 
            color: '#888',
            fontFamily: 'monospace',
            maxWidth: '160px',
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
          background: data.executionResult === true ? '#4caf50' : '#4caf50',
          width: data.executionResult === true ? '18px' : '14px',
          height: data.executionResult === true ? '18px' : '14px',
          top: '30%',
          border: data.executionResult === true ? '3px solid #fff' : 'none',
          boxShadow: data.executionResult === true ? '0 0 12px rgba(76,175,80,0.8)' : 'none'
        }}
      />
      
      {/* False output (bottom-right) */}
      <Handle 
        type="source" 
        position={Position.Right}
        id="false-output"
        style={{ 
          background: data.executionResult === false ? '#f44336' : '#f44336',
          width: data.executionResult === false ? '18px' : '14px',
          height: data.executionResult === false ? '18px' : '14px',
          top: '70%',
          border: data.executionResult === false ? '3px solid #fff' : 'none',
          boxShadow: data.executionResult === false ? '0 0 12px rgba(244,67,54,0.8)' : 'none'
        }}
      />
      
      {/* Branch labels with execution highlighting */}
      <div style={{
        position: 'absolute',
        right: '-55px',
        top: 'calc(30% - 12px)',
        fontSize: '12px',
        color: data.executionResult === true ? '#4caf50' : '#4caf50',
        fontWeight: data.executionResult === true ? 'bold' : 'normal',
        pointerEvents: 'none',
        textShadow: data.executionResult === true ? '0 0 6px rgba(76,175,80,0.7)' : 'none',
        background: data.executionResult === true ? 'rgba(76,175,80,0.1)' : 'transparent',
        padding: '2px 6px',
        borderRadius: '8px',
        border: data.executionResult === true ? '2px solid #4caf50' : 'none'
      }}>
        ✓ TRUE
      </div>
      
      <div style={{
        position: 'absolute',
        right: '-55px',
        top: 'calc(70% - 12px)',
        fontSize: '12px',
        color: data.executionResult === false ? '#f44336' : '#f44336',
        fontWeight: data.executionResult === false ? 'bold' : 'normal',
        pointerEvents: 'none',
        textShadow: data.executionResult === false ? '0 0 6px rgba(244,67,54,0.7)' : 'none',
        background: data.executionResult === false ? 'rgba(244,67,54,0.1)' : 'transparent',
        padding: '2px 6px',
        borderRadius: '8px',
        border: data.executionResult === false ? '2px solid #f44336' : 'none'
      }}>
        ✗ FALSE
      </div>
    </div>
  );
});

ConditionalNode.displayName = 'ConditionalNode';
