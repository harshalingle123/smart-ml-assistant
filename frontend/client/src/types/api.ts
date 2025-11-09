export interface User {
  _id?: string;
  id?: string;
  email: string;
  name: string;
  username?: string;
  current_plan: string;
  queries_used?: number;
  fine_tune_jobs?: number;
  datasets_count?: number;
  billing_cycle?: string | null;
}

export interface UserCreate {
  username: string;
  password: string;
}

export interface UserLogin {
  username: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Chat {
  id: string;
  user_id: string;
  title: string;
  model_id?: string | null;
  dataset_id?: string | null;
  last_updated: string;
}

export interface ChatCreate {
  title: string;
  model_id?: string | null;
  dataset_id?: string | null;
}

export interface ChatUpdate {
  title?: string;
  model_id?: string | null;
  dataset_id?: string | null;
}

export interface Message {
  id: string;
  chat_id: string;
  role: string;
  content: string;
  query_type?: string | null;
  charts?: any;
  timestamp: string;
}

export interface MessageCreate {
  role: string;
  content: string;
  query_type?: string | null;
  charts?: any;
}

export interface Model {
  id: string;
  user_id: string;
  name: string;
  base_model: string;
  version: string;
  accuracy?: string | null;
  f1_score?: string | null;
  loss?: string | null;
  status: string;
  dataset_id?: string | null;
  created_at: string;
}

export interface ModelCreate {
  name: string;
  base_model: string;
  version: string;
  dataset_id?: string | null;
}

export interface Dataset {
  id: string;
  user_id: string;
  name: string;
  file_name: string;
  row_count: number;
  column_count: number;
  file_size: number;
  status: string;
  preview_data?: any;
  uploaded_at: string;
}

export interface DatasetCreate {
  name: string;
  file_name: string;
  row_count: number;
  column_count: number;
  file_size: number;
}

export interface FineTuneJob {
  id: string;
  user_id: string;
  model_id?: string | null;
  dataset_id: string;
  base_model: string;
  status: string;
  progress: number;
  current_step?: string | null;
  logs?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface FineTuneJobCreate {
  dataset_id: string;
  base_model: string;
}

export interface ApiKey {
  id: string;
  user_id: string;
  model_id: string;
  key: string;
  name: string;
  created_at: string;
}

export interface ApiKeyCreate {
  model_id: string;
  name: string;
}
