import apiClient from './apiClient';
import {
  JobApplication,
  JobApplicationCreate,
  JobApplicationUpdate,
} from '../types';

export const jobsService = {
  async getAll(): Promise<JobApplication[]> {
    const response = await apiClient.get<JobApplication[]>('/api/jobs');
    return response.data;
  },

  async getById(id: number): Promise<JobApplication> {
    const response = await apiClient.get<JobApplication>(`/api/jobs/${id}`);
    return response.data;
  },

  async create(job: JobApplicationCreate): Promise<JobApplication> {
    const response = await apiClient.post<JobApplication>('/api/jobs', job);
    return response.data;
  },

  async update(id: number, job: JobApplicationUpdate): Promise<JobApplication> {
    const response = await apiClient.put<JobApplication>(`/api/jobs/${id}`, job);
    return response.data;
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/api/jobs/${id}`);
  },
};
