import React, { useState, useEffect, useLayoutEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { router, useLocalSearchParams, useNavigation } from 'expo-router';
import { jobsService } from '../../../src/services/jobsService';
import { JobApplication, JOB_STATUSES, JobStatus } from '../../../src/types';

export default function JobDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const navigation = useNavigation();
  const [job, setJob] = useState<JobApplication | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const [company, setCompany] = useState('');
  const [position, setPosition] = useState('');
  const [status, setStatus] = useState<JobStatus>('applied');
  const [dateApplied, setDateApplied] = useState('');
  const [notes, setNotes] = useState('');

  useLayoutEffect(() => {
    navigation.setOptions({ title: 'Job Details' });
  }, [navigation]);

  useEffect(() => {
    fetchJob();
  }, [id]);

  async function fetchJob() {
    try {
      const data = await jobsService.getById(Number(id));
      setJob(data);
      setCompany(data.company);
      setPosition(data.position);
      setStatus(data.status as JobStatus);
      setDateApplied(data.date_applied);
      setNotes(data.notes ?? '');
    } catch {
      Alert.alert('Error', 'Failed to load job details');
      router.back();
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSave() {
    if (!company.trim() || !position.trim()) {
      Alert.alert('Error', 'Company and position are required');
      return;
    }

    setIsSaving(true);
    try {
      await jobsService.update(Number(id), {
        company: company.trim(),
        position: position.trim(),
        status,
        date_applied: dateApplied,
        notes: notes.trim() || undefined,
      });
      Alert.alert('Saved', 'Job application updated');
      router.back();
    } catch {
      Alert.alert('Error', 'Failed to update job application');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete() {
    Alert.alert(
      'Delete Application',
      `Delete ${company} \u2014 ${position}? This cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await jobsService.delete(Number(id));
              router.back();
            } catch {
              Alert.alert('Error', 'Failed to delete job application');
            }
          },
        },
      ]
    );
  }

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#4f9eff" size="large" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.label}>Company *</Text>
      <TextInput style={styles.input} value={company} onChangeText={setCompany} placeholderTextColor="#555" />

      <Text style={styles.label}>Position *</Text>
      <TextInput style={styles.input} value={position} onChangeText={setPosition} placeholderTextColor="#555" />

      <Text style={styles.label}>Status</Text>
      <View style={styles.statusRow}>
        {JOB_STATUSES.map((s) => (
          <TouchableOpacity
            key={s}
            style={[styles.statusChip, status === s && styles.statusChipActive]}
            onPress={() => setStatus(s)}
          >
            <Text style={[styles.statusChipText, status === s && styles.statusChipTextActive]}>
              {s}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.label}>Date Applied (YYYY-MM-DD)</Text>
      <TextInput style={styles.input} value={dateApplied} onChangeText={setDateApplied} placeholderTextColor="#555" />

      <Text style={styles.label}>Notes</Text>
      <TextInput
        style={[styles.input, styles.textArea]}
        value={notes}
        onChangeText={setNotes}
        multiline
        numberOfLines={4}
        placeholderTextColor="#555"
      />

      <TouchableOpacity
        style={[styles.button, isSaving && styles.buttonDisabled]}
        onPress={handleSave}
        disabled={isSaving}
      >
        {isSaving ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Save Changes</Text>}
      </TouchableOpacity>

      <TouchableOpacity style={styles.deleteButton} onPress={handleDelete}>
        <Text style={styles.deleteText}>Delete Application</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0a' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0a0a0a' },
  content: { padding: 20 },
  label: { color: '#aaa', fontSize: 13, fontWeight: '600', marginBottom: 6, marginTop: 16, textTransform: 'uppercase', letterSpacing: 0.5 },
  input: {
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#2a2a2a',
    borderRadius: 8,
    padding: 14,
    color: '#fff',
    fontSize: 16,
  },
  textArea: { height: 100, textAlignVertical: 'top' },
  statusRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  statusChip: {
    borderWidth: 1,
    borderColor: '#2a2a2a',
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 7,
    backgroundColor: '#1a1a1a',
  },
  statusChipActive: { borderColor: '#4f9eff', backgroundColor: '#4f9eff22' },
  statusChipText: { color: '#888', fontSize: 13, textTransform: 'capitalize' },
  statusChipTextActive: { color: '#4f9eff', fontWeight: '600' },
  button: {
    backgroundColor: '#4f9eff',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginTop: 28,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#fff', fontWeight: '600', fontSize: 16 },
  deleteButton: {
    borderWidth: 1,
    borderColor: '#ef444433',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginTop: 12,
  },
  deleteText: { color: '#ef4444', fontWeight: '600', fontSize: 16 },
});
