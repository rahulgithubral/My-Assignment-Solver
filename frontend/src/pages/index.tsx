import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Chat } from '../components/Chat';
import { Upload } from '../components/Upload';
import { PlanEditor } from '../components/PlanEditor';
import { Header } from '../components/Header';
import { Sidebar } from '../components/Sidebar';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { api } from '../lib/api';
import { Assignment, Plan } from '../types';

export default function Home() {
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [activeTab, setActiveTab] = useState<'chat' | 'upload' | 'plans'>('chat');
  
  const queryClient = useQueryClient();

  // Fetch assignments
  const { data: assignments, isLoading: assignmentsLoading, error: assignmentsError } = useQuery(
    'assignments',
    api.getAssignments,
    {
      refetchInterval: 5000, // Refetch every 5 seconds for real-time updates
    }
  );

  // Fetch plans for selected assignment
  const { data: plans, isLoading: plansLoading } = useQuery(
    ['plans', selectedAssignment?.id],
    () => api.getPlans(selectedAssignment?.id),
    {
      enabled: !!selectedAssignment?.id,
      refetchInterval: 5000,
    }
  );

  // Generate plan mutation
  const generatePlanMutation = useMutation(
    (assignmentId: string) => api.generatePlan(assignmentId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('assignments');
        queryClient.invalidateQueries(['plans', selectedAssignment?.id]);
      },
    }
  );

  // Execute plan mutation
  const executePlanMutation = useMutation(
    (planId: string) => api.executePlan(planId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['plans', selectedAssignment?.id]);
      },
    }
  );

  // Handle assignment selection
  const handleAssignmentSelect = (assignment: Assignment) => {
    setSelectedAssignment(assignment);
    setSelectedPlan(null);
    setActiveTab('chat');
  };

  // Handle plan selection
  const handlePlanSelect = (plan: Plan) => {
    setSelectedPlan(plan);
    setActiveTab('plans');
  };

  // Handle plan generation
  const handleGeneratePlan = async (assignmentId: string) => {
    try {
      await generatePlanMutation.mutateAsync(assignmentId);
    } catch (error) {
      console.error('Failed to generate plan:', error);
    }
  };

  // Handle plan execution
  const handleExecutePlan = async (planId: string) => {
    try {
      await executePlanMutation.mutateAsync(planId);
    } catch (error) {
      console.error('Failed to execute plan:', error);
    }
  };

  return (
    <>
      <Head>
        <title>Assignment Assistant Agent</title>
        <meta name="description" content="AI-powered agent for automating university assignment workflows" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        <Header />
        
        <div className="flex h-screen pt-16">
          {/* Sidebar */}
          <Sidebar
            assignments={assignments || []}
            selectedAssignment={selectedAssignment}
            onAssignmentSelect={handleAssignmentSelect}
            isLoading={assignmentsLoading}
            error={assignmentsError}
          />

          {/* Main Content */}
          <main className="flex-1 flex flex-col">
            {/* Tab Navigation */}
            <div className="border-b border-gray-200 bg-white">
              <nav className="flex space-x-8 px-6">
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'chat'
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Chat
                </button>
                <button
                  onClick={() => setActiveTab('upload')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'upload'
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Upload
                </button>
                <button
                  onClick={() => setActiveTab('plans')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'plans'
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Plans
                </button>
              </nav>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-hidden">
              {activeTab === 'chat' && (
                <Chat
                  assignment={selectedAssignment}
                  onGeneratePlan={handleGeneratePlan}
                  isGeneratingPlan={generatePlanMutation.isLoading}
                />
              )}
              
              {activeTab === 'upload' && (
                <Upload
                  onUploadSuccess={(assignment) => {
                    setSelectedAssignment(assignment);
                    setActiveTab('chat');
                    queryClient.invalidateQueries('assignments');
                  }}
                />
              )}
              
              {activeTab === 'plans' && (
                <PlanEditor
                  assignment={selectedAssignment}
                  plans={plans || []}
                  selectedPlan={selectedPlan}
                  onPlanSelect={handlePlanSelect}
                  onExecutePlan={handleExecutePlan}
                  isLoading={plansLoading}
                  isExecuting={executePlanMutation.isLoading}
                />
              )}
            </div>
          </main>
        </div>
      </div>
    </>
  );
}
