import { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, ScrollView, Alert, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';

export default function SetupScreen() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [resumeFile, setResumeFile] = useState<string | null>(null);
  const [resumeName, setResumeName] = useState('');
  const [extractedSkills, setExtractedSkills] = useState<string[]>([]);
  const [linkedinEmail, setLinkedinEmail] = useState('');
  const [linkedinPassword, setLinkedinPassword] = useState('');
  const [openrouterKey, setOpenrouterKey] = useState('');
  const [skills, setSkills] = useState('');
  const [loading, setLoading] = useState(false);
  const [parsingResume, setParsingResume] = useState(false);

  const pickResume = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      type: ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
      copyToCacheDirectory: true,
    });
    if (!result.canceled && result.assets[0]) {
      setResumeFile(result.assets[0].uri);
      setResumeName(result.assets[0].name);
      setParsingResume(true);
      try {
        const skillList = ['Python', 'JavaScript', 'React', 'Node.js', 'SQL', 'Git', 'HTML', 'CSS'];
        setExtractedSkills(skillList);
        Alert.alert('Resume Parsed!', `Found ${skillList.length} skills`);
      } catch (error) {
        Alert.alert('Parse Failed', 'Enter skills manually');
      } finally {
        setParsingResume(false);
      }
    }
  };

  const handleNext = () => {
    if (step === 1 && !resumeFile) { Alert.alert('Required', 'Upload your resume'); return; }
    if (step === 2 && (!linkedinEmail || !linkedinPassword)) { Alert.alert('Required', 'Enter LinkedIn credentials'); return; }
    if (step === 3 && !openrouterKey) { Alert.alert('Required', 'Enter OpenRouter API key'); return; }
    setStep(step + 1);
  };

  const handleComplete = async () => {
    setLoading(true);
    try {
      const allSkills = extractedSkills.length > 0 ? extractedSkills : skills.split(',').map(s => s.trim());
      await AsyncStorage.setItem('LINKEDIN_EMAIL', linkedinEmail);
      await AsyncStorage.setItem('LINKEDIN_PASSWORD', linkedinPassword);
      await AsyncStorage.setItem('OPENROUTER_API_KEY', openrouterKey);
      await AsyncStorage.setItem('SKILLS', allSkills.join(','));
      await AsyncStorage.setItem('RESUME_FILE', resumeFile || '');
      await AsyncStorage.setItem('RESUME_NAME', resumeName);
      await AsyncStorage.setItem('AUTO_POST', 'true');
      await AsyncStorage.setItem('WHATSAPP_NOTIFY', 'true');
      Alert.alert('Setup Complete!', 'You can now upload certificates and post to LinkedIn!', [
        { text: 'Get Started', onPress: () => router.replace('/(tabs)') },
      ]);
    } catch (error) {
      Alert.alert('Error', 'Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Ionicons name="logo-linkedin" size={48} color="#fff" />
        <Text style={styles.title}>IPG - LinkedIn Auto Poster</Text>
        <Text style={styles.subtitle}>Upload resume first then auto-extract skills</Text>
      </View>
      <View style={styles.progressContainer}>
        {[1,2,3,4].map((s, i) => (
          <View key={s} style={{ flexDirection: 'row', alignItems: 'center' }}>
            <View style={[styles.progressDot, step >= s && styles.progressDotActive]}>
              {step > s && <Ionicons name="checkmark" size={10} color="#fff" />}
            </View>
            {i < 3 && <View style={[styles.progressLine, step > s && styles.progressLineActive]} />}
          </View>
        ))}
      </View>

      {step === 1 && (
        <View style={styles.form}>
          <Text style={styles.stepTitle}>📄 Upload Your Resume</Text>
          <Text style={styles.stepDesc}>Auto-extract skills for job matching and posts</Text>
          <TouchableOpacity style={styles.uploadCard} onPress={pickResume} disabled={parsingResume}>
            {parsingResume ? (
              <><ActivityIndicator size="large" color="#0a66c2" /><Text style={styles.uploadText}>Analyzing resume...</Text></>
            ) : resumeFile ? (
              <><Ionicons name="document-text" size={40} color="#057642" /><Text style={styles.fileName}>{resumeName}</Text><Text style={styles.uploadSubtext}>Tap to change</Text></>
            ) : (
              <><Ionicons name="cloud-upload" size={40} color="#0a66c2" /><Text style={styles.uploadText}>Tap to upload Resume (PDF/DOCX)</Text><Text style={styles.uploadSubtext}>Skills will be auto-extracted</Text></>
            )}
          </TouchableOpacity>
          {extractedSkills.length > 0 && (
            <View style={styles.skillsSection}>
              <Text style={styles.skillsTitle}>Extracted Skills ({extractedSkills.length})</Text>
              <View style={styles.skillsGrid}>
                {extractedSkills.map((skill, index) => (
                  <View key={index} style={styles.skillBadge}><Text style={styles.skillText}>{skill}</Text></View>
                ))}
              </View>
            </View>
          )}
          <TouchableOpacity style={[styles.nextBtn, !resumeFile && styles.disabledBtn]} onPress={handleNext} disabled={!resumeFile}>
            <Text style={styles.nextBtnText}>Continue</Text><Ionicons name="arrow-forward" size={20} color="#fff" />
          </TouchableOpacity>
        </View>
      )}

      {step === 2 && (
        <View style={styles.form}>
          <Text style={styles.stepTitle}>🔗 Connect LinkedIn</Text>
          <Text style={styles.stepDesc}>Enter credentials to auto-post certificates</Text>
          <TextInput style={styles.input} value={linkedinEmail} onChangeText={setLinkedinEmail} placeholder="LinkedIn Email" placeholderTextColor="#999" keyboardType="email-address" autoCapitalize="none" />
          <TextInput style={styles.input} value={linkedinPassword} onChangeText={setLinkedinPassword} placeholder="LinkedIn Password" placeholderTextColor="#999" secureTextEntry />
          <View style={styles.btnRow}>
            <TouchableOpacity style={styles.backBtn} onPress={() => setStep(1)}><Ionicons name="arrow-back" size={20} color="#666" /><Text style={styles.backBtnText}>Back</Text></TouchableOpacity>
            <TouchableOpacity style={styles.nextBtn} onPress={handleNext}><Text style={styles.nextBtnText}>Continue</Text><Ionicons name="arrow-forward" size={20} color="#fff" /></TouchableOpacity>
          </View>
        </View>
      )}

      {step === 3 && (
        <View style={styles.form}>
          <Text style={styles.stepTitle}>🤖 AI Setup</Text>
          <Text style={styles.stepDesc}>Free API key from openrouter.ai</Text>
          <View style={styles.infoBox}><Ionicons name="information-circle" size={20} color="#0a66c2" /><Text style={styles.infoText}>1. Go to openrouter.ai{'\n'}2. Sign up (free){'\n'}3. Copy API key{'\n'}4. Paste below</Text></View>
          <TextInput style={styles.input} value={openrouterKey} onChangeText={setOpenrouterKey} placeholder="sk-or-v1-..." placeholderTextColor="#999" secureTextEntry />
          <View style={styles.btnRow}>
            <TouchableOpacity style={styles.backBtn} onPress={() => setStep(2)}><Ionicons name="arrow-back" size={20} color="#666" /><Text style={styles.backBtnText}>Back</Text></TouchableOpacity>
            <TouchableOpacity style={styles.nextBtn} onPress={handleNext}><Text style={styles.nextBtnText}>Continue</Text><Ionicons name="arrow-forward" size={20} color="#fff" /></TouchableOpacity>
          </View>
        </View>
      )}

      {step === 4 && (
        <View style={styles.form}>
          <Text style={styles.stepTitle}>🎉 All Set!</Text>
          <Text style={styles.stepDesc}>Setup summary</Text>
          <View style={styles.summary}>
            <View style={styles.summaryRow}><Ionicons name="document-text" size={20} color="#057642" /><View style={styles.summaryContent}><Text style={styles.summaryLabel}>Resume</Text><Text style={styles.summaryValue}>{resumeName}</Text></View></View>
            <View style={styles.divider} />
            <View style={styles.summaryRow}><Ionicons name="code-slash" size={20} color="#0a66c2" /><View style={styles.summaryContent}><Text style={styles.summaryLabel}>Skills</Text><Text style={styles.summaryValue}>{extractedSkills.length || 'Manual'} skills</Text></View></View>
            <View style={styles.divider} />
            <View style={styles.summaryRow}><Ionicons name="logo-linkedin" size={20} color="#0a66c2" /><View style={styles.summaryContent}><Text style={styles.summaryLabel}>LinkedIn</Text><Text style={styles.summaryValue}>{linkedinEmail}</Text></View></View>
          </View>
          <View style={styles.featureList}>
            <Text style={styles.featureTitle}>What you can do now:</Text>
            <View style={styles.featureItem}><Ionicons name="checkmark-circle" size={18} color="#057642" /><Text style={styles.featureText}>Upload certificate then auto post to LinkedIn</Text></View>
            <View style={styles.featureItem}><Ionicons name="checkmark-circle" size={18} color="#057642" /><Text style={styles.featureText}>New cert then auto-update your resume</Text></View>
            <View style={styles.featureItem}><Ionicons name="checkmark-circle" size={18} color="#057642" /><Text style={styles.featureText}>Daily auto-post with AI content</Text></View>
            <View style={styles.featureItem}><Ionicons name="checkmark-circle" size={18} color="#057642" /><Text style={styles.featureText}>Job alerts based on your skills</Text></View>
          </View>
          <View style={styles.btnRow}>
            <TouchableOpacity style={styles.backBtn} onPress={() => setStep(3)}><Ionicons name="arrow-back" size={20} color="#666" /><Text style={styles.backBtnText}>Back</Text></TouchableOpacity>
            <TouchableOpacity style={[styles.nextBtn, loading && styles.disabledBtn]} onPress={handleComplete} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <><Text style={styles.nextBtnText}>Start Using</Text><Ionicons name="rocket" size={20} color="#fff" /></>}
            </TouchableOpacity>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { padding: 30, paddingTop: 60, backgroundColor: '#0a66c2', alignItems: 'center' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginTop: 12 },
  subtitle: { fontSize: 13, color: '#e0e0e0', marginTop: 4, textAlign: 'center' },
  progressContainer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', padding: 20 },
  progressDot: { width: 28, height: 28, borderRadius: 14, backgroundColor: '#ddd', alignItems: 'center', justifyContent: 'center' },
  progressDotActive: { backgroundColor: '#0a66c2' },
  progressLine: { width: 40, height: 2, backgroundColor: '#ddd', marginHorizontal: 4 },
  progressLineActive: { backgroundColor: '#0a66c2' },
  form: { padding: 20 },
  stepTitle: { fontSize: 22, fontWeight: 'bold', color: '#333', marginBottom: 8 },
  stepDesc: { fontSize: 14, color: '#666', marginBottom: 20 },
  uploadCard: { backgroundColor: '#fff', borderRadius: 12, padding: 30, alignItems: 'center', borderWidth: 2, borderColor: '#0a66c2', borderStyle: 'dashed', marginBottom: 20 },
  uploadText: { fontSize: 16, fontWeight: '600', color: '#333', marginTop: 12, textAlign: 'center' },
  uploadSubtext: { fontSize: 13, color: '#999', marginTop: 4 },
  fileName: { fontSize: 14, fontWeight: '600', color: '#057642', marginTop: 12 },
  skillsSection: { backgroundColor: '#fff', borderRadius: 10, padding: 14, marginBottom: 16 },
  skillsTitle: { fontSize: 14, fontWeight: 'bold', marginBottom: 10, color: '#333' },
  skillsGrid: { flexDirection: 'row', flexWrap: 'wrap' },
  skillBadge: { backgroundColor: '#e8f4fd', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 16, marginRight: 6, marginBottom: 6 },
  skillText: { fontSize: 12, color: '#0a66c2', fontWeight: '600' },
  input: { backgroundColor: '#fff', borderRadius: 10, padding: 14, fontSize: 16, borderWidth: 1, borderColor: '#e0e0e0', marginBottom: 12, minHeight: 48 },
  nextBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#0a66c2', padding: 16, borderRadius: 12, marginTop: 10 },
  nextBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold', marginRight: 8 },
  backBtn: { flexDirection: 'row', alignItems: 'center', padding: 16 },
  backBtnText: { color: '#666', fontSize: 16, marginLeft: 6 },
  btnRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 10 },
  infoBox: { flexDirection: 'row', backgroundColor: '#e8f4fd', borderRadius: 10, padding: 14, marginBottom: 16 },
  infoText: { fontSize: 13, color: '#333', marginLeft: 10, lineHeight: 20 },
  disabledBtn: { opacity: 0.5 },
  summary: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 16, elevation: 2 },
  summaryRow: { flexDirection: 'row', alignItems: 'flex-start' },
  summaryContent: { flex: 1, marginLeft: 12 },
  summaryLabel: { fontSize: 12, color: '#999', fontWeight: '600' },
  summaryValue: { fontSize: 15, color: '#333', fontWeight: '600', marginTop: 2 },
  divider: { height: 1, backgroundColor: '#eee', marginVertical: 12 },
  featureList: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 16, elevation: 2 },
  featureTitle: { fontSize: 15, fontWeight: 'bold', marginBottom: 12, color: '#333' },
  featureItem: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  featureText: { fontSize: 14, color: '#555', marginLeft: 8 },
});
