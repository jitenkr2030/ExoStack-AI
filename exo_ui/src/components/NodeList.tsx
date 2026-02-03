import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { NodeStatus } from '../types/node';
import { NodeCard } from './NodeCard';
import { Modal } from './common/Modal';
import { Button } from './common/Button';
import { updateNodeStatus, deleteNode } from '../api/nodes';

interface NodeListProps {
  nodes: any[];
}

export const NodeList: React.FC<NodeListProps> = ({ nodes }) => {
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const queryClient = useQueryClient();

  const updateStatusMutation = useMutation({
    mutationFn: updateNodeStatus,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systemStatus'] });
      setIsModalOpen(false);
    },
  });

  const deleteNodeMutation = useMutation({
    mutationFn: deleteNode,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systemStatus'] });
      setIsModalOpen(false);
    },
  });

  const handleNodeAction = (node: any, action: string) => {
    setSelectedNode(node);
    setIsModalOpen(true);
  };

  const handleConfirmAction = async () => {
    if (!selectedNode) return;

    try {
      if (selectedNode.status === NodeStatus.ONLINE) {
        await updateStatusMutation.mutateAsync({
          nodeId: selectedNode.id,
          status: NodeStatus.MAINTENANCE,
        });
      } else if (selectedNode.status === NodeStatus.OFFLINE) {
        await deleteNodeMutation.mutateAsync(selectedNode.id);
      }
    } catch (error) {
      console.error('Error performing node action:', error);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Node Management
        </h2>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => queryClient.invalidateQueries({ queryKey: ['systemStatus'] })}
          >
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {nodes.map((node) => (
          <NodeCard
            key={node.id}
            node={node}
            onAction={handleNodeAction}
          />
        ))}
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Confirm Action"
      >
        <div className="p-6">
          <p className="text-gray-700 dark:text-gray-300 mb-4">
            Are you sure you want to {selectedNode?.status === NodeStatus.ONLINE
              ? 'put this node into maintenance mode'
              : 'remove this node'}?
          </p>
          <div className="flex justify-end gap-4">
            <Button
              variant="outline"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleConfirmAction}
              loading={updateStatusMutation.isPending || deleteNodeMutation.isPending}
            >
              Confirm
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
