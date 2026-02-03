import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchModels, deployModel, undeployModel } from '../api/models';
import { Button } from './common/Button';
import { Modal } from './common/Modal';
import { Input } from './common/Input';
import { Select } from './common/Select';
import { Alert } from './common/Alert';

export const ModelManager: React.FC = () => {
  const [isDeployModalOpen, setIsDeployModalOpen] = useState(false);
  const [deployConfig, setDeployConfig] = useState({
    modelName: '',
    version: '',
    replicas: 1,
    gpuRequired: false,
    memoryLimit: 4000,
  });

  const queryClient = useQueryClient();

  const { data: models, isLoading } = useQuery({
    queryKey: ['models'],
    queryFn: fetchModels,
  });

  const deployMutation = useMutation({
    mutationFn: deployModel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
      setIsDeployModalOpen(false);
    },
  });

  const undeployMutation = useMutation({
    mutationFn: undeployModel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
  });

  const handleDeploy = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await deployMutation.mutateAsync(deployConfig);
    } catch (error) {
      console.error('Error deploying model:', error);
    }
  };

  const handleUndeploy = async (modelId: string) => {
    try {
      await undeployMutation.mutateAsync(modelId);
    } catch (error) {
      console.error('Error undeploying model:', error);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Model Management
        </h2>
        <Button
          variant="primary"
          onClick={() => setIsDeployModalOpen(true)}
        >
          Deploy New Model
        </Button>
      </div>

      {/* Models List */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Model Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Version
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Replicas
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {models?.map((model: any) => (
              <tr key={model.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                  {model.name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {model.version}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    model.status === 'running'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {model.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {model.replicas}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleUndeploy(model.id)}
                    loading={undeployMutation.isPending}
                  >
                    Undeploy
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Deploy Model Modal */}
      <Modal
        isOpen={isDeployModalOpen}
        onClose={() => setIsDeployModalOpen(false)}
        title="Deploy New Model"
      >
        <form onSubmit={handleDeploy} className="p-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Model Name
              </label>
              <Input
                type="text"
                value={deployConfig.modelName}
                onChange={(e) => setDeployConfig({
                  ...deployConfig,
                  modelName: e.target.value
                })}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Version
              </label>
              <Input
                type="text"
                value={deployConfig.version}
                onChange={(e) => setDeployConfig({
                  ...deployConfig,
                  version: e.target.value
                })}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Replicas
              </label>
              <Input
                type="number"
                min="1"
                value={deployConfig.replicas}
                onChange={(e) => setDeployConfig({
                  ...deployConfig,
                  replicas: parseInt(e.target.value)
                })}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Memory Limit (MB)
              </label>
              <Input
                type="number"
                min="1000"
                step="100"
                value={deployConfig.memoryLimit}
                onChange={(e) => setDeployConfig({
                  ...deployConfig,
                  memoryLimit: parseInt(e.target.value)
                })}
                required
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={deployConfig.gpuRequired}
                onChange={(e) => setDeployConfig({
                  ...deployConfig,
                  gpuRequired: e.target.checked
                })}
                className="h-4 w-4 text-blue-600"
              />
              <label className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Requires GPU
              </label>
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-4">
            <Button
              variant="outline"
              onClick={() => setIsDeployModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              type="submit"
              loading={deployMutation.isPending}
            >
              Deploy
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
