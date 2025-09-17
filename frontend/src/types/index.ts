// Type definitions for the Assignment Assistant Agent frontend

export interface Assignment {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  file_path?: string;
  status: AssignmentStatus;
  file_size?: number;
  file_type?: string;
  created_at: string;
  updated_at?: string;
}

export interface Plan {
  id: string;
  assignment_id: string;
  name: string;
  description?: string;
  tasks: Task[];
  status: PlanStatus;
  total_estimated_duration?: number;
  execution_started_at?: string;
  execution_completed_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface Task {
  id: string;
  task_type: string;
  description: string;
  dependencies: TaskDependency[];
  estimated_duration?: number;
  tool_requirements: string[];
  parameters: Record<string, any>;
  status: TaskStatus;
  result?: Record<string, any>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface TaskDependency {
  task_id: string;
  dependency_type: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface ExecutionResult {
  task_id: string;
  status: TaskStatus;
  output?: Record<string, any>;
  logs: string[];
  error_message?: string;
  execution_time?: number;
}

export interface FileUploadResponse {
  file_id: string;
  filename: string;
  file_size: number;
  file_type: string;
  upload_path: string;
  uploaded_at: string;
}

// Enums
export enum AssignmentStatus {
  UPLOADED = 'uploaded',
  PROCESSING = 'processing',
  PLANNED = 'planned',
  EXECUTING = 'executing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum PlanStatus {
  CREATED = 'created',
  VALIDATED = 'validated',
  EXECUTING = 'executing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum TaskStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  SUCCESS = 'success',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// Form types
export interface UploadFormData {
  file: File;
  title?: string;
  description?: string;
}

export interface ChatFormData {
  message: string;
  assignment_id?: string;
}

// UI State types
export interface UIState {
  selectedAssignment: Assignment | null;
  selectedPlan: Plan | null;
  activeTab: 'chat' | 'upload' | 'plans';
  isLoading: boolean;
  error: string | null;
}

// Component Props types
export interface ChatProps {
  assignment?: Assignment | null;
  onGeneratePlan?: (assignmentId: string) => void;
  isGeneratingPlan?: boolean;
}

export interface UploadProps {
  onUploadSuccess?: (assignment: Assignment) => void;
}

export interface PlanEditorProps {
  assignment?: Assignment | null;
  plans: Plan[];
  selectedPlan?: Plan | null;
  onPlanSelect?: (plan: Plan) => void;
  onExecutePlan?: (planId: string) => void;
  isLoading?: boolean;
  isExecuting?: boolean;
}

export interface SidebarProps {
  assignments: Assignment[];
  selectedAssignment?: Assignment | null;
  onAssignmentSelect?: (assignment: Assignment) => void;
  isLoading?: boolean;
  error?: Error | null;
}

// Error types
export interface ApiError {
  message: string;
  status: number;
  details?: Record<string, any>;
}

// Configuration types
export interface AppConfig {
  apiUrl: string;
  wsUrl?: string;
  maxFileSize: number;
  allowedFileTypes: string[];
}
