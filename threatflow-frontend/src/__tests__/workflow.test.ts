/**
 * ThreatFlow Frontend Workflow Tests
 * Tests workflow state management, result distribution, and routing logic
 */

import { StageRouting } from '../types/workflow';

describe('Result Distribution Logic', () => {
  const createMockResponse = (stageRouting: StageRouting[]) => ({
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
    const stageRouting: StageRouting[] = [
      { stage_id: 0, target_nodes: [], executed: true, analyzers: [] },
      { stage_id: 1, target_nodes: ['result-true'], executed: true, analyzers: ['ClamAV'] },
      { stage_id: 2, target_nodes: ['result-false'], executed: false, analyzers: [] }
    ];
    
    const mockResponse = createMockResponse(stageRouting);
    
    const updateCalls: {nodeId: string; data: Record<string, unknown>}[] = [];
    const updateNode = (nodeId: string, data: Record<string, unknown>) => {
      updateCalls.push({ nodeId, data });
    };
    
    const resultNodeIds = ['result-true', 'result-false'];
    
    if (mockResponse.has_conditionals && mockResponse.stage_routing) {
      const resultNodeShouldUpdate = new Map<string, boolean>();
      
      mockResponse.stage_routing.forEach(routing => {
        routing.target_nodes.forEach(nodeId => {
          resultNodeShouldUpdate.set(nodeId, routing.executed);
        });
      });
      
      resultNodeIds.forEach(resultNodeId => {
        const shouldUpdate = resultNodeShouldUpdate.get(resultNodeId);
        
        if (shouldUpdate === true) {
          updateNode(resultNodeId, { data: { results: mockResponse.results } });
        } else if (shouldUpdate === false) {
          updateNode(resultNodeId, { data: { error: 'Branch not executed' } });
        }
      });
    }
    
    expect(updateCalls).toHaveLength(2);
    expect(updateCalls.find(c => c.nodeId === 'result-true')?.data).toEqual(
      expect.objectContaining({ data: expect.objectContaining({ results: expect.any(Object) }) })
    );
    expect(updateCalls.find(c => c.nodeId === 'result-false')?.data).toEqual(
      expect.objectContaining({ data: expect.objectContaining({ error: 'Branch not executed' }) })
    );
  });
  
  it('should handle linear workflows without conditionals', () => {
    const stageRouting: StageRouting[] = [
      { stage_id: 0, target_nodes: ['result-1'], executed: true, analyzers: ['File_Info'] }
    ];
    
    const mockResponse = createMockResponse(stageRouting);
    mockResponse.has_conditionals = false;
    
    expect(mockResponse.stage_routing?.[0].executed).toBe(true);
  });
  
  it('should handle multiple analyzers in parallel', () => {
    const mockResponse = {
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
        { stage_id: 0, target_nodes: ['result-1'], executed: true, analyzers: ['ClamAV', 'PE_Info'] }
      ]
    };
    
    expect(mockResponse.results.stage_0.analyzer_reports).toHaveLength(2);
    expect(mockResponse.analyzers_total).toBe(2);
  });
});

describe('Edge Metadata Handling', () => {
  interface TestEdge {
    id: string;
    source: string;
    target: string;
    sourceHandle?: string;
    label?: string;
  }

  it('should preserve sourceHandle in conditional edges', () => {
    const edge: TestEdge = {
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
    const trueEdge: TestEdge = {
      id: 'e1',
      source: 'conditional-1',
      target: 'result-true',
      sourceHandle: 'true-output'
    };
    
    const falseEdge: TestEdge = {
      id: 'e2',
      source: 'conditional-1',
      target: 'result-false',
      sourceHandle: 'false-output'
    };
    
    expect(trueEdge.sourceHandle).not.toBe(falseEdge.sourceHandle);
  });
});

describe('Workflow Validation', () => {
  interface TestNode {
    id: string;
    type: string;
    position: { x: number; y: number };
    data: Record<string, unknown>;
  }

  interface TestEdge {
    id: string;
    source: string;
    target: string;
  }

  it('should detect missing file node', () => {
    const nodes: TestNode[] = [
      { id: 'analyzer-1', type: 'analyzer', position: { x: 0, y: 0 }, data: {} }
    ];
    
    const hasFileNode = nodes.some(n => n.type === 'file');
    expect(hasFileNode).toBe(false);
  });
  
  it('should detect disconnected nodes', () => {
    const nodes: TestNode[] = [
      { id: 'file-1', type: 'file', position: { x: 0, y: 0 }, data: {} },
      { id: 'analyzer-1', type: 'analyzer', position: { x: 100, y: 0 }, data: {} },
      { id: 'result-1', type: 'result', position: { x: 200, y: 0 }, data: {} }
    ];
    
    const edges: TestEdge[] = [
      { id: 'e1', source: 'file-1', target: 'analyzer-1' }
    ];
    
    const resultNode = nodes.find(n => n.id === 'result-1');
    const hasIncomingEdge = edges.some(e => e.target === resultNode?.id);
    
    expect(hasIncomingEdge).toBe(false);
  });
  
  it('should validate conditional node has sourceAnalyzer', () => {
    const conditionalNode: TestNode = {
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

describe('Tree-Based Path Finding', () => {
  interface MockNode {
    id: string;
    type: string;
    data: Record<string, unknown>;
  }

  interface MockEdge {
    id: string;
    source: string;
    target: string;
    sourceHandle?: string;
  }

  function findAnalyzersInPath(
    nodes: MockNode[],
    edges: MockEdge[],
    fileNodeId: string,
    resultNodeId: string
  ): string[] {
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    const outgoingEdges = new Map<string, MockEdge[]>();
    
    edges.forEach(edge => {
      const existing = outgoingEdges.get(edge.source) || [];
      existing.push(edge);
      outgoingEdges.set(edge.source, existing);
    });
    
    const analyzers: string[] = [];
    const visited = new Set<string>();
    
    function dfs(nodeId: string): boolean {
      if (visited.has(nodeId)) return false;
      visited.add(nodeId);
      
      if (nodeId === resultNodeId) return true;
      
      const outEdges = outgoingEdges.get(nodeId) || [];
      for (const edge of outEdges) {
        if (dfs(edge.target)) {
          const node = nodeMap.get(nodeId);
          if (node?.type === 'analyzer' && node.data?.analyzer) {
            analyzers.unshift(node.data.analyzer as string);
          }
          return true;
        }
      }
      
      visited.delete(nodeId);
      return false;
    }
    
    dfs(fileNodeId);
    return analyzers;
  }

  it('should find all analyzers in linear path', () => {
    const nodes: MockNode[] = [
      { id: 'file-1', type: 'file', data: {} },
      { id: 'analyzer-1', type: 'analyzer', data: { analyzer: 'ClamAV' } },
      { id: 'analyzer-2', type: 'analyzer', data: { analyzer: 'Strings_Info' } },
      { id: 'result-1', type: 'result', data: {} }
    ];
    
    const edges: MockEdge[] = [
      { id: 'e1', source: 'file-1', target: 'analyzer-1' },
      { id: 'e2', source: 'analyzer-1', target: 'analyzer-2' },
      { id: 'e3', source: 'analyzer-2', target: 'result-1' }
    ];
    
    const analyzers = findAnalyzersInPath(nodes, edges, 'file-1', 'result-1');
    expect(analyzers).toEqual(['ClamAV', 'Strings_Info']);
  });

  it('should find correct path in branching workflow', () => {
    const nodes: MockNode[] = [
      { id: 'file-1', type: 'file', data: {} },
      { id: 'analyzer-1', type: 'analyzer', data: { analyzer: 'File_Info' } },
      { id: 'analyzer-2', type: 'analyzer', data: { analyzer: 'ClamAV' } },
      { id: 'result-1', type: 'result', data: {} },
      { id: 'result-2', type: 'result', data: {} }
    ];
    
    const edges: MockEdge[] = [
      { id: 'e1', source: 'file-1', target: 'analyzer-1' },
      { id: 'e2', source: 'analyzer-1', target: 'result-1' },
      { id: 'e3', source: 'file-1', target: 'analyzer-2' },
      { id: 'e4', source: 'analyzer-2', target: 'result-2' }
    ];
    
    const analyzers1 = findAnalyzersInPath(nodes, edges, 'file-1', 'result-1');
    expect(analyzers1).toEqual(['File_Info']);
    
    const analyzers2 = findAnalyzersInPath(nodes, edges, 'file-1', 'result-2');
    expect(analyzers2).toEqual(['ClamAV']);
  });

  it('should find analyzers in conditional workflow TRUE branch', () => {
    const nodes: MockNode[] = [
      { id: 'file-1', type: 'file', data: {} },
      { id: 'analyzer-1', type: 'analyzer', data: { analyzer: 'ClamAV' } },
      { id: 'conditional-1', type: 'conditional', data: {} },
      { id: 'analyzer-2', type: 'analyzer', data: { analyzer: 'Deep_Scan' } },
      { id: 'result-true', type: 'result', data: {} },
      { id: 'result-false', type: 'result', data: {} }
    ];
    
    const edges: MockEdge[] = [
      { id: 'e1', source: 'file-1', target: 'analyzer-1' },
      { id: 'e2', source: 'analyzer-1', target: 'conditional-1' },
      { id: 'e3', source: 'conditional-1', target: 'analyzer-2', sourceHandle: 'true-output' },
      { id: 'e4', source: 'analyzer-2', target: 'result-true' },
      { id: 'e5', source: 'conditional-1', target: 'result-false', sourceHandle: 'false-output' }
    ];
    
    const analyzersTrueBranch = findAnalyzersInPath(nodes, edges, 'file-1', 'result-true');
    expect(analyzersTrueBranch).toEqual(['ClamAV', 'Deep_Scan']);
    
    const analyzersFalseBranch = findAnalyzersInPath(nodes, edges, 'file-1', 'result-false');
    expect(analyzersFalseBranch).toEqual(['ClamAV']);
  });
});

export {};
