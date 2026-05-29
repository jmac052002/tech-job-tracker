import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { JobApplication } from '../types';

// Status colors — visual at a glance
const STATUS_COLORS: Record<string, string> = {
  applied: '#4f9eff',
  interviewing: '#f59e0b',
  offer: '#10b981',
  rejected: '#ef4444',
  withdrawn: '#6b7280',
};

interface JobCardProps {
  job: JobApplication;
  onPress: () => void;
}

export default function JobCard({ job, onPress }: JobCardProps) {
  const statusColor = STATUS_COLORS[job.status] ?? '#6b7280';

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.header}>
        <Text style={styles.company} numberOfLines={1}>{job.company}</Text>
        <View style={[styles.statusBadge, { backgroundColor: statusColor + '22' }]}>
          <Text style={[styles.statusText, { color: statusColor }]}>
            {job.status}
          </Text>
        </View>
      </View>
      <Text style={styles.position} numberOfLines={1}>{job.position}</Text>
      <Text style={styles.date}>Applied: {job.date_applied}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1a1a1a',
    borderRadius: 10,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  company: { fontSize: 16, fontWeight: '600', color: '#fff', flex: 1, marginRight: 8 },
  statusBadge: { borderRadius: 12, paddingHorizontal: 10, paddingVertical: 3 },
  statusText: { fontSize: 12, fontWeight: '600', textTransform: 'capitalize' },
  position: { fontSize: 14, color: '#aaa', marginBottom: 6 },
  date: { fontSize: 12, color: '#666' },
});
