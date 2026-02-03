import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from '../Dashboard';
import { SystemMetrics } from '../SystemMetrics';
import { NodeList } from '../NodeList';
import { ModelManager } from '../ModelManager';

const queryClient = new QueryClient();

describe('Dashboard Components', () => {
  beforeEach(() => {
    // Setup test environment
  });

  test('renders dashboard with all components', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    );

    expect(screen.getByText('ExoStack Dashboard')).toBeInTheDocument();
    expect(screen.getByText('System Metrics')).toBeInTheDocument();
    expect(screen.getByText('Node Management')).toBeInTheDocument();
  });

  test('system metrics displays correct data', async () => {
    const mockMetrics = {
      cpu_usage: 50,
      memory_usage: 60,
      gpu_usage: 30
    };

    render(
      <QueryClientProvider client={queryClient}>
        <SystemMetrics metrics={mockMetrics} />
      </QueryClientProvider>
    );

    expect(screen.getByText('50%')).toBeInTheDocument();
    expect(screen.getByText('60%')).toBeInTheDocument();
    expect(screen.getByText('30%')).toBeInTheDocument();
  });

  test('model manager handles deployment', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ModelManager />
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByText('Deploy New Model'));
    
    // Fill form
    fireEvent.change(screen.getByLabelText('Model Name'), {
      target: { value: 'test-model' }
    });

    fireEvent.click(screen.getByText('Deploy'));

    await waitFor(() => {
      expect(screen.getByText('Deployment successful')).toBeInTheDocument();
    });
  });
});
