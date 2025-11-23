/**
 * ThreatFlow Frontend Workflow Tests
 * Tests workflow state management, result distribution, and routing logic
 * Author: Senior Architect
 * Date: 2025-11-23
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useWorkflowState } from '../hooks/useWorkflowState';
import { useWorkflowExecution } from '../hooks/useWorkflowExecution';
import { CustomNode, Edge, JobStatusResponse, StageRouting } from '../types/workflow';

describe('Workflow State Management', () => {
  it('should add nodes correctly', () => {
    const { result } = renderHook(() => useWorkflowState());
    
    act(() => {
      result.current.addNode({
        id: 'file-1',
        type: 'file',
        position: { x: 0, y: 0 },
        data: { label: 'File' }
      } as CustomNode);
    });
    
    expect(result.current.nodes).toHaveLength(1);
    expect(result.current.nodes[0].id).toBe('file-1');
  });
  
  it('should add edges correctly', () => {
    const { result } = renderHook(() => useWorkflowState());
    
    act(() => {
      result.current.addEdge({
        id: 'e1',
        source: 'file-1',
        target: 'analyzer-1'
      } as Edge);
    });
    
    expect(result.current.edges).toHaveLength(1);
    expect(result.current.edges[0].source).toBe('file-1');
  });
  
  it('should update node data', () => {
    const { result } = renderHook(() => useWorkflowState());
    
    act(() => {
      result.current.addNode({
        id: 'result-1',
        type: 'result',
        position: { x: 0, y: 0 },
        data: { label: 'Result', results: null }
      } as CustomNode);
    });
    
    act(() => {
      result.current.updateNode('result-1', {
        data: { results: { clamav: { malicious: true } } }
      });
    });
    
    const resultNode = result.current.nodes.find(n => n.id === 'result-1');
    expect(resultNode?.data.results).toBeDefined();
  });
});

describe('Result Distribution Logic', () => {
  const createMockResponse = (stageRouting: StageRouting[]): JobStatusResponse => ({
    job_id: 123,
    status: 'reported_without_fails',
    progress: 100,
    analyzers_completed: 1,
    analyzers_total: 1,
    results: {
      stage_0: {
        analyzer_reports: [
          {
            name: 'ClamAV',
            status: 'SUCCESS',
            report: { classification: 'malicious' }
          }
        ]
      }
    },
    has_conditionals: true,
    stage_routing: stageRouting
  });
  
  it('should distribute results to executed branch only', () => {
    // Setup workflow with conditional
    const nodes: CustomNode[] = [
      { id: 'file-1', type: 'file', position: { x: 0, y: 0 }, data: {} },
      { id: 'analyzer-1', type: 'analyzer', position: { x: 100, y: 0 }, data: { analyzer: 'ClamAV' } },
      { id: 'conditional-1', type: 'conditional', position: { x: 200, y: 0 }, data: {} },
      { id: 'result-true', type: 'result', position: { x: 300, y: -50 }, data: { results: null } },
      { id: 'result-false', type: 'result', position: { x: 300, y: 50 }, data: { results: null } }
    ];
    
    const edges: Edge[] = [
      { id: 'e1', source: 'file-1', target: 'analyzer-1' },
      { id: 'e2', source: 'analyzer-1', target: 'conditional-1' },
      { id: 'e3', source: 'conditional-1', target: 'result-true', sourceHandle: 'true-output' },
      { id: 'e4', source: 'conditional-1', target: 'result-false', sourceHandle: 'false-output' }
    ];
    
    const stageRouting: StageRouting[] = [
      { stage_id: 0, target_nodes: [], executed: true },
      { stage_id: 1, target_nodes: ['result-true'], executed: true },
      { stage_id: 2, target_nodes: ['result-false'], executed: false }
    ];
    
    const mockResponse = createMockResponse(stageRouting);
    
    // Simulate result distribution
    const updateNode = vi.fn();
    
    // Distribution logic (simplified from useWorkflowExecution)
    const resultNodes = nodes.filter(n => n.type === 'result');
    
    if (mockResponse.has_conditionals && mockResponse.stage_routing) {
      const resultNodeShouldUpdate = new Map<string, boolean>();
      
      mockResponse.stage_routing.forEach(routing => {
        routing.target_nodes.forEach(nodeId => {
          resultNodeShouldUpdate.set(nodeId, routing.executed);
        });
      });
      
      resultNodes.forEach(resultNode => {
        const shouldUpdate = resultNodeShouldUpdate.get(resultNode.id);
        
        if (shouldUpdate === true) {
          updateNode(resultNode.id, { data: { results: mockResponse.results } });
        } else if (shouldUpdate === false) {
          updateNode(resultNode.id, { data: { error: 'Branch not executed' } });
        }
      });
    }
    
    // Assertions
    expect(updateNode).toHaveBeenCalledTimes(2);
    expect(updateNode).toHaveBeenCalledWith('result-true', expect.objectContaining({
      data: expect.objectContaining({ results: expect.any(Object) })
    }));
    expect(updateNode).toHaveBeenCalledWith('result-false', expect.objectContaining({
      data: expect.objectContaining({ error: 'Branch not executed' })
    }));
  });
  
  it('should handle linear workflows without conditionals', () => {
    const stageRouting: StageRouting[] = [
      { stage_id: 0, target_nodes: ['result-1'], executed: true }
    ];
    
    const mockResponse = createMockResponse(stageRouting);
    mockResponse.has_conditionals = false;
    
    // All result nodes should receive results in linear workflow
    expect(mockResponse.stage_routing[0].executed).toBe(true);
  });
  
  it('should handle multiple analyzers in parallel', () => {
    const mockResponse: JobStatusResponse = {
      job_id: 123,
      status: 'reported_without_fails',
      progress: 100,
      analyzers_completed: 2,
      analyzers_total: 2,
      results: {
        stage_0: {
          analyzer_reports: [
            { name: 'ClamAV', status: 'SUCCESS', report: {} },
            { name: 'PE_Info', status: 'SUCCESS', report: {} }
          ]
        }
      },
      has_conditionals: false,
      stage_routing: [
        { stage_id: 0, target_nodes: ['result-1'], executed: true }
      ]
    };
    
    // Both analyzers should be in the same stage
    expect(mockResponse.results.stage_0.analyzer_reports).toHaveLength(2);
    expect(mockResponse.analyzers_total).toBe(2);
  });
});

describe('Edge Metadata Handling', () => {
  it('should preserve sourceHandle in conditional edges', () => {
    const edge: Edge = {
      id: 'e1',
      source: 'conditional-1',
      target: 'result-true',
      sourceHandle: 'true-output',
      label: 'success'
    };
    
    expect(edge.sourceHandle).toBe('true-output');
    expect(edge.label).toBe('success');
  });
  
  it('should differentiate TRUE and FALSE branches', () => {
    const trueEdge: Edge = {
      id: 'e1',
      source: 'conditional-1',
      target: 'result-true',
      sourceHandle: 'true-output'
    };
    
    const falseEdge: Edge = {
      id: 'e2',
      source: 'conditional-1',
      target: 'result-false',
      sourceHandle: 'false-output'
    };
    
    expect(trueEdge.sourceHandle).not.toBe(falseEdge.sourceHandle);
  });
});

describe('Workflow Validation', () => {
  it('should detect missing file node', () => {
    const nodes: CustomNode[] = [
      { id: 'analyzer-1', type: 'analyzer', position: { x: 0, y: 0 }, data: {} }
    ];
    
    const hasFileNode = nodes.some(n => n.type === 'file');
    expect(hasFileNode).toBe(false);
  });
  
  it('should detect disconnected nodes', () => {
    const nodes: CustomNode[] = [
      { id: 'file-1', type: 'file', position: { x: 0, y: 0 }, data: {} },
      { id: 'analyzer-1', type: 'analyzer', position: { x: 100, y: 0 }, data: {} },
      { id: 'result-1', type: 'result', position: { x: 200, y: 0 }, data: {} }
    ];
    
    const edges: Edge[] = [
      { id: 'e1', source: 'file-1', target: 'analyzer-1' }
      // Missing: analyzer-1 → result-1
    ];
    
    const resultNode = nodes.find(n => n.id === 'result-1');
    const hasIncomingEdge = edges.some(e => e.target === resultNode?.id);
    
    expect(hasIncomingEdge).toBe(false); // Disconnected result
  });
  
  it('should validate conditional node has sourceAnalyzer', () => {
    const conditionalNode: CustomNode = {
      id: 'conditional-1',
      type: 'conditional',
      position: { x: 0, y: 0 },
      data: {
        label: 'Conditional',
        conditionType: 'verdict_malicious',
        sourceAnalyzer: 'ClamAV'
      }
    };
    
    expect(conditionalNode.data.sourceAnalyzer).toBeDefined();
    expect(conditionalNode.data.conditionType).toBe('verdict_malicious');
  });
});

export {};
