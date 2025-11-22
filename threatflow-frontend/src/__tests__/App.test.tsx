import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../App';

// Mock axios to avoid ES module issues
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    interceptors: {
      request: { use: jest.fn(), eject: jest.fn() },
      response: { use: jest.fn(), eject: jest.fn() },
    },
    get: jest.fn(),
    post: jest.fn(),
  })),
  isAxiosError: jest.fn(),
}));

// Mock the WorkflowCanvas component to avoid React Flow complexity
jest.mock('../components/Canvas/WorkflowCanvas', () => ({
  __esModule: true,
  default: () => <div data-testid="workflow-canvas">Workflow Canvas Mock</div>,
}));

test('renders ThreatFlow title', () => {
  render(<App />);
  const titleElement = screen.getByText(/ThreatFlow/i);
  expect(titleElement).toBeInTheDocument();
});

test('renders node palette', () => {
  render(<App />);
  const paletteElement = screen.getByText(/Node Palette/i);
  expect(paletteElement).toBeInTheDocument();
});

test('renders execute button', () => {
  render(<App />);
  const executeButtons = screen.getAllByText(/Execute/i);
  expect(executeButtons.length).toBeGreaterThan(0);
});
