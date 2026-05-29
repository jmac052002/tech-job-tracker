// JobApplication matches the backend JobApplicationResponse schema exactly
export interface JobApplication {
  id: number;
  user_id: number;
  company: string;
  position: string;
  status: string;
  date_applied: string;
  notes: string | null;
  follow_up_date: string | null;
}

export interface JobApplicationCreate {
  company: string;
  position: string;
  status: string;
  date_applied: string;
  notes?: string;
  follow_up_date?: string;
}

export interface JobApplicationUpdate {
  company?: string;
  position?: string;
  status?: string;
  date_applied?: string;
  notes?: string;
  follow_up_date?: string;
}

export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface RegisterResponse {
  user: User;
  token: AuthToken;
}

export const JOB_STATUSES = [
  'applied',
  'interviewing',
  'offer',
  'rejected',
  'withdrawn',
] as const;

export type JobStatus = (typeof JOB_STATUSES)[number];
