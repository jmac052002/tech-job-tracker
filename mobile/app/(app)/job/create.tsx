import React, { useState } from 'react';
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
import { router } from 'expo-router';
import { jobsService } from '../../../src/services/jobsService';
import { JOB_STATUSES, JobStatus } from '../../../src/types';

export default function CreateJobScreen() {
  const [company, setCompany] = useState('');
  const [position, setPosition] = useState('');
  const [status, setStatus] = useState<JobStatus>('applied');
  const [dateApplied, setDateApplied] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [notes, setNotes] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  async function handleCreate() {
    if (!company.trim() || !position.trim() || !dateApplied) {
      Alert.alert('Error', 'Company, position, and date applied are required');
      return;
    }

    setIsLoading(true);
    try {
      await jobsService.create({
        company: company.trim(),
        position: position.trim(),
        status,
        date_applied: dateApplied,
        notes: notes.trim() || undefined,
      });
      router.back();
    } catch {
      Alert.alert('Error', 'Failed to create job application');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.label}>Company *</Text>
      <TextInput
        style={styles.input}
        value={company}
        onChangeText={setCompany}
        placeholder="e.g. Amazon"
        placeholderTextColor="#555"
      />

      <Text style={styles.label}>Position *</Text>
      <TextInput
        style={styles.input}
        value={position}
        onChangeText={setPosition}
        placeholder="e.g. DevOps Engineer"
        placeholderTextColor="#555"
      />

      <Text style={styles.label}>Status *</Text>
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

      <Text style={styles.label}>Date Applied * (YYYY-MM-DD)</Text>
      <TextInput
        style={styles.input}
        value={dateApplied}
        onChangeText={setDateApplied}
        placeholder="2024-03-15"
        placeholderTextColor="#555"
      />

      <Text style={styles.label}>Notes</Text>
      <TextInput
        style={[styles.input, styles.textArea]}
        value={notes}
        onChangeText={setNotes}
        placeholder="Any notes about this application..."
        placeholderTextColor="#555"
        multiline
        numberOfLines={4}
      />

      <TouchableOpacity
        style={[styles.button, isLoading && styles.buttonDisabled]}
        onPress={handleCreate}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Save Application</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0a' },
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
});
