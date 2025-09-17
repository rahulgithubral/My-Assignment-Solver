import React, { useState, useEffect, useRef } from 'react';
import { useMutation, useQuery } from 'react-query';
import { PaperAirplaneIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { api, handleApiError } from '../lib/api';
import { Assignment, ChatMessage } from '../types';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';

interface ChatProps {
  assignment?: Assignment | null;
  onGeneratePlan?: (assignmentId: string) => void;
  isGeneratingPlan?: boolean;
}

export const Chat: React.FC<ChatProps> = ({
  assignment,
  onGeneratePlan,
  isGeneratingPlan = false,
}) => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch chat history
  const { data: chatHistory, isLoading: isLoadingHistory } = useQuery(
    ['chatHistory', assignment?.id],
    () => api.getChatHistory(assignment?.id),
    {
      enabled: !!assignment?.id,
      onSuccess: (data) => {
        setMessages(data);
      },
    }
  );

  // Send message mutation
  const sendMessageMutation = useMutation(
    (messageText: string) => api.sendMessage(messageText, assignment?.id),
    {
      onSuccess: (newMessage) => {
        setMessages(prev => [...prev, newMessage]);
        setMessage('');
      },
      onError: (error) => {
        console.error('Failed to send message:', error);
      },
    }
  );

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || sendMessageMutation.isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setMessage('');

    try {
      await sendMessageMutation.mutateAsync(message.trim());
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleGeneratePlan = () => {
    if (assignment && onGeneratePlan) {
      onGeneratePlan(assignment.id);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Chat Assistant</h2>
            {assignment && (
              <p className="text-sm text-gray-500">
                Working on: {assignment.title}
              </p>
            )}
          </div>
          {assignment && assignment.status === 'uploaded' && (
            <button
              onClick={handleGeneratePlan}
              disabled={isGeneratingPlan}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGeneratingPlan ? (
                <LoadingSpinner size="sm" />
              ) : (
                <SparklesIcon className="w-4 h-4 mr-2" />
              )}
              {isGeneratingPlan ? 'Generating Plan...' : 'Generate Plan'}
            </button>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {isLoadingHistory ? (
          <div className="flex justify-center items-center h-full">
            <LoadingSpinner />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
              <SparklesIcon className="w-8 h-8 text-primary-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Welcome to Assignment Assistant
            </h3>
            <p className="text-gray-500 max-w-md">
              {assignment
                ? `I'm here to help you with "${assignment.title}". Ask me anything about your assignment!`
                : 'Upload an assignment file to get started, or ask me any questions about your project.'}
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  msg.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                <p
                  className={`text-xs mt-1 ${
                    msg.role === 'user' ? 'text-primary-100' : 'text-gray-500'
                  }`}
                >
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))
        )}
        
        {sendMessageMutation.isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-900 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <LoadingSpinner size="sm" />
                <span className="text-sm">Assistant is typing...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Message Input */}
      <div className="flex-shrink-0 px-6 py-4 border-t border-gray-200 bg-white">
        <form onSubmit={handleSubmit} className="flex space-x-4">
          <div className="flex-1">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={
                assignment
                  ? `Ask about "${assignment.title}"...`
                  : 'Type your message here...'
              }
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              disabled={sendMessageMutation.isLoading}
            />
          </div>
          <button
            type="submit"
            disabled={!message.trim() || sendMessageMutation.isLoading}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <PaperAirplaneIcon className="w-4 h-4" />
          </button>
        </form>
        
        {sendMessageMutation.error && (
          <ErrorMessage
            message={handleApiError(sendMessageMutation.error)}
            className="mt-2"
          />
        )}
      </div>
    </div>
  );
};
