import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Monaco } from '@monaco-editor/react';
import { Button } from './common/Button';

interface DevToolsProps {
  onDeploy: (config: any) => Promise<void>;
}

export const DevelopmentTools: React.FC<DevToolsProps> = ({ onDeploy }) => {
  const [configCode, setConfigCode] = useState('');
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const validateConfig = async (config: string) => {
    try {
      const parsed = JSON.parse(config);
      // Add validation logic
      setValidationErrors([]);
      return parsed;
    } catch (e) {
      setValidationErrors([e.message]);
      throw e;
    }
  };

  const deployMutation = useMutation({
    mutationFn: onDeploy,
    onSuccess: () => {
      // Handle success
    },
    onError: (error) => {
      setValidationErrors([error.message]);
    },
  });

  const handleDeploy = async () => {
    try {
      const config = await validateConfig(configCode);
      await deployMutation.mutateAsync(config);
    } catch (e) {
      // Error already handled
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Development Tools</h2>

      <div className="mb-4">
        <Monaco
          height="400px"
          language="json"
          theme="vs-dark"
          value={configCode}
          onChange={(value) => setConfigCode(value || '')}
          options={{
            minimap: { enabled: false },
            formatOnPaste: true,
            formatOnType: true,
          }}
        />
      </div>

      {validationErrors.length > 0 && (
        <div className="mb-4 p-4 bg-red-50 text-red-900 rounded-md">
          {validationErrors.map((error, index) => (
            <p key={index}>{error}</p>
          ))}
        </div>
      )}

      <div className="flex justify-end space-x-4">
        <Button
          variant="outline"
          onClick={() => setConfigCode('')}
        >
          Clear
        </Button>
        <Button
          variant="primary"
          onClick={handleDeploy}
          loading={deployMutation.isPending}
        >
          Deploy
        </Button>
      </div>
    </div>
  );
};
