import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Mic,
  MicOff,
  Sparkles,
  Save,
  CheckCircle2,
  AlertCircle,
  Clock,
  Globe,
  RefreshCw,
  FileText,
  ShieldCheck,
  Plus,
  HelpCircle,
  Info,
  Trash2,
  ArrowRight,
  Cpu,
} from 'lucide-react';
import { workersApi } from '../../api/workers.api';
import { Button } from '../ui/Button';
import { Alert } from '../ui/Alert';
import { formatDateTime } from '../../lib/date';

export function TellUsAboutYourWork({ standalone = false, onSaved }) {
  const queryClient = useQueryClient();
  const [text, setText] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('en-IN'); // 'en-IN' or 'hi-IN'
  const [isListening, setIsListening] = useState(false);
  const [interimText, setInterimText] = useState('');
  const [speechError, setSpeechError] = useState(null);
  const [isSpeechSupported, setIsSpeechSupported] = useState(true);
  const [saveSuccess, setSaveSuccess] = useState(null);
  const [saveError, setSaveError] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [skillsAddedMessage, setSkillsAddedMessage] = useState(null);

  const recognitionRef = useRef(null);
  const textareaRef = useRef(null);

  // Fetch current worker profile
  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ['my-profile'],
    queryFn: () => workersApi.getMyProfile(),
  });

  // Populate initial text from saved profile work_narrative or informal_work_description
  useEffect(() => {
    if (profile && !text) {
      const existing = profile.work_narrative || profile.informal_work_description || '';
      if (existing) {
        setText(existing);
      }
    }
  }, [profile]);

  // Initialize Web Speech API detection
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setIsSpeechSupported(false);
      setSpeechError('Voice dictation is not supported in this browser. Please type your experience in the text area below.');
    }
  }, []);

  // Cleanup speech recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // ignore
        }
      }
    };
  }, []);

  // Toggle Voice Recognition
  const toggleListening = () => {
    setSpeechError(null);
    setSaveSuccess(null);

    if (isListening) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {
          // ignore
        }
      }
      setIsListening(false);
      setInterimText('');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechError('Voice dictation is not supported in this browser. Please type your experience in the text area below.');
      setIsSpeechSupported(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = selectedLanguage;

      recognition.onstart = () => {
        setIsListening(true);
        setSpeechError(null);
      };

      recognition.onresult = (event) => {
        let finalChunk = '';
        let currentInterim = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const item = event.results[i];
          if (item.isFinal) {
            finalChunk += item[0].transcript;
          } else {
            currentInterim += item[0].transcript;
          }
        }

        if (finalChunk) {
          setText((prev) => {
            const trimmed = prev.trim();
            const chunkTrimmed = finalChunk.trim();
            if (!trimmed) return chunkTrimmed;
            return `${trimmed} ${chunkTrimmed}`;
          });
        }

        setInterimText(currentInterim);
      };

      recognition.onerror = (event) => {
        console.warn('Speech recognition event error:', event.error);
        if (event.error === 'not-allowed' || event.error === 'permission-denied') {
          setSpeechError(
            'Microphone access was denied. Please allow microphone permissions in your browser address bar to speak, or type manually below.'
          );
        } else if (event.error === 'no-speech') {
          setSpeechError('No speech was detected. Please speak into your microphone or type your experience.');
        } else if (event.error === 'audio-capture') {
          setSpeechError('No microphone detected. Please check your audio input hardware.');
        } else if (event.error === 'network') {
          setSpeechError('A network error occurred with the browser speech engine. You can continue typing manually.');
        } else if (event.error !== 'aborted') {
          setSpeechError(`Speech recognition notice (${event.error}). You can continue speaking or type directly.`);
        }
        setIsListening(false);
        setInterimText('');
      };

      recognition.onend = () => {
        setIsListening(false);
        setInterimText('');
      };

      recognition.start();
    } catch (err) {
      console.error('Failed to start speech recognition:', err);
      setSpeechError('Could not start microphone dictation. Please type directly into the text box.');
      setIsListening(false);
    }
  };

  // Save Narrative Mutation
  const saveMutation = useMutation({
    mutationFn: async (narrativeText) => {
      return await workersApi.saveNarrative(narrativeText);
    },
    onSuccess: (updatedWorker) => {
      setSaveSuccess('Work experience narrative saved successfully.');
      setSaveError(null);
      queryClient.invalidateQueries({ queryKey: ['my-profile'] });
      queryClient.invalidateQueries({ queryKey: ['worker-profile-me'] });
      if (onSaved) onSaved(updatedWorker);
    },
    onError: (err) => {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to save narrative. Please check your connection.';
      setSaveError(typeof msg === 'string' ? msg : JSON.stringify(msg));
      setSaveSuccess(null);
    },
  });

  const handleSave = (e) => {
    if (e) e.preventDefault();
    setSaveError(null);
    setSaveSuccess(null);

    const trimmed = text.trim();
    if (trimmed.length < 5) {
      setSaveError('Please provide at least a few words describing your work experience before saving.');
      return;
    }
    if (trimmed.length > 10000) {
      setSaveError('The narrative is too long (maximum 10,000 characters). Please condense your description.');
      return;
    }

    // If microphone is active, stop it
    if (isListening) {
      toggleListening();
    }

    saveMutation.mutate(trimmed);
  };

  // Analyze Narrative Handler
  const handleAnalyze = async () => {
    setSaveError(null);
    setSaveSuccess(null);
    setSkillsAddedMessage(null);

    const trimmed = text.trim();
    if (trimmed.length < 5) {
      setSaveError('Please enter a description of your work experience before analyzing skills.');
      return;
    }

    setIsAnalyzing(true);
    try {
      const lang = selectedLanguage === 'hi-IN' ? 'hi' : 'en';
      const result = await workersApi.analyzeNarrative({
        narrative: trimmed,
        language: lang,
      });
      setAnalysisResult(result);
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || 'Skill analysis could not be completed.';
      setSaveError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Add Extracted Skills to Profile
  const handleAddSkillsToProfile = async () => {
    if (!analysisResult?.extracted_skills?.length) return;
    try {
      const currentDeclared = profile?.declared_skills || [];
      const newSkills = analysisResult.extracted_skills.map((s) => s.skill_name);
      const merged = Array.from(new Set([...currentDeclared, ...newSkills]));

      await workersApi.updateMyProfile({ declared_skills: merged });
      queryClient.invalidateQueries({ queryKey: ['my-profile'] });
      setSkillsAddedMessage(`Successfully added ${newSkills.length} identified skill(s) to your declared skills profile.`);
    } catch (err) {
      setSaveError('Failed to update declared skills in profile.');
    }
  };

  const lastUpdated = profile?.updated_at || profile?.created_at;

  return (
    <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 specular-top-edge space-y-6">
      {/* 1. Header & Plain Language Copy */}
      <div className="space-y-2 border-b border-white/10 pb-4">
        <div className="flex items-center gap-2 font-mono text-xs text-zinc-400 uppercase tracking-widest">
          <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
          <span>Worker Voice &amp; Experience Entry</span>
        </div>
        <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight uppercase">
          Tell Us About Your Work
        </h2>
        <p className="text-zinc-300 text-xs sm:text-sm font-light leading-relaxed font-sans max-w-3xl">
          You have skills worth recognizing. Tell us what work you do, what tools you use, and what you have learned through experience. You can speak naturally or type in your own words.
        </p>
      </div>

      {/* 2. Feedback Alerts */}
      {saveSuccess && (
        <Alert variant="success" onClose={() => setSaveSuccess(null)}>
          <div className="flex items-center justify-between gap-2">
            <span>{saveSuccess}</span>
            {lastUpdated && (
              <span className="text-[10px] font-mono text-zinc-400">
                Last updated: {formatDateTime(lastUpdated)}
              </span>
            )}
          </div>
        </Alert>
      )}

      {saveError && (
        <Alert variant="error" onClose={() => setSaveError(null)}>
          {saveError}
        </Alert>
      )}

      {speechError && (
        <div className="p-3.5 bg-amber-950/30 border border-amber-600/40 text-amber-200 text-xs font-sans flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold font-mono text-[11px] uppercase tracking-wider block">
              Voice Dictation Notice
            </span>
            <span>{speechError}</span>
          </div>
        </div>
      )}

      {skillsAddedMessage && (
        <Alert variant="success" onClose={() => setSkillsAddedMessage(null)}>
          {skillsAddedMessage}
        </Alert>
      )}

      {/* 3. Input Controls Bar: Microphone, Language Selector, and Status */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-[#080808] border border-white/10">
        <div className="flex flex-wrap items-center gap-3">
          {/* Microphone Action Button */}
          <button
            type="button"
            onClick={toggleListening}
            disabled={!isSpeechSupported}
            className={`inline-flex items-center gap-2 px-4 py-2.5 font-mono text-xs font-bold uppercase tracking-wider transition-all cursor-pointer ${
              isListening
                ? 'bg-red-950 border border-red-500 text-red-200 shadow-[0_0_15px_rgba(239,68,68,0.3)] animate-pulse'
                : 'bg-white hover:bg-zinc-200 text-black border border-white disabled:opacity-50 disabled:cursor-not-allowed'
            }`}
            aria-label={isListening ? 'Stop listening to microphone' : 'Speak about your work using microphone'}
          >
            {isListening ? (
              <>
                <MicOff className="w-4 h-4 text-red-400" />
                <span>Stop Listening</span>
              </>
            ) : (
              <>
                <Mic className="w-4 h-4 text-black" />
                <span>Speak About Your Work</span>
              </>
            )}
          </button>

          {/* Language Selector */}
          <div className="flex items-center gap-1.5 bg-[#0f0f11] border border-white/15 px-3 py-1.5 text-xs font-mono">
            <Globe className="w-3.5 h-3.5 text-zinc-400" />
            <label htmlFor="voice-language-select" className="sr-only">
              Speech Recognition Language
            </label>
            <select
              id="voice-language-select"
              value={selectedLanguage}
              onChange={(e) => {
                setSelectedLanguage(e.target.value);
                if (isListening) {
                  // restart with new language
                  toggleListening();
                }
              }}
              className="bg-transparent text-white text-xs font-mono focus:outline-none cursor-pointer"
            >
              <option value="en-IN" className="bg-[#0a0a0a] text-white">English (India) · en-IN</option>
              <option value="hi-IN" className="bg-[#0a0a0a] text-white">हिंदी (भारत) · hi-IN</option>
            </select>
          </div>
        </div>

        {/* Live Status indicator */}
        <div className="flex items-center gap-2 text-xs font-mono">
          {isListening ? (
            <div className="flex items-center gap-2 text-emerald-400 font-bold">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping inline-block" />
              <span>Listening ({selectedLanguage === 'hi-IN' ? 'हिंदी' : 'English'})... Speak now</span>
            </div>
          ) : (
            <div className="text-zinc-500 text-[11px] font-mono flex items-center gap-1.5">
              <span>Ready for voice dictation or typing</span>
            </div>
          )}
        </div>
      </div>

      {/* 4. Editable Textarea & Live Transcription Preview */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
          <label htmlFor="work-experience-textarea" className="uppercase tracking-wider text-[11px]">
            Your Work Experience Narrative <span className="text-zinc-500">(Spoken or Typed)</span>
          </label>
          <div className="flex items-center gap-3 text-[11px]">
            <span>{text.length} characters</span>
            {text.length > 0 && (
              <button
                type="button"
                onClick={() => {
                  if (window.confirm('Clear your current narrative text?')) {
                    setText('');
                  }
                }}
                className="text-zinc-500 hover:text-red-400 flex items-center gap-1 cursor-pointer transition-colors"
                title="Clear text area"
              >
                <Trash2 className="w-3 h-3" />
                <span>Clear</span>
              </button>
            )}
          </div>
        </div>

        <div className="relative">
          <textarea
            id="work-experience-textarea"
            ref={textareaRef}
            rows={6}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="I have worked as an electrician for six years. I install domestic wiring, replace switches and fans, install MCBs, use a tester to find electrical faults, and repair wiring problems. I learned most of these skills while working with an experienced electrician..."
            className="w-full bg-[#080808] border border-white/20 p-4 text-xs sm:text-sm text-zinc-100 font-sans leading-relaxed focus:border-white focus:outline-none transition-colors resize-y"
          />

          {/* Interim transcript floating overlay */}
          {isListening && interimText && (
            <div className="p-2.5 bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 font-sans text-xs italic mt-1 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Transcribing: "{interimText}"</span>
            </div>
          )}
        </div>

        {/* Helpful guidance chips */}
        <div className="flex flex-wrap items-center gap-2 text-[11px] font-sans text-zinc-400 pt-1">
          <span className="text-zinc-500 font-mono text-[10px] uppercase">Tip:</span>
          <span>Mention your primary trade</span>
          <span>•</span>
          <span>Tools &amp; machines you operate</span>
          <span>•</span>
          <span>Years of site experience</span>
          <span>•</span>
          <span>Any formal or informal master mentors</span>
        </div>
      </div>

      {/* 5. Privacy Notice & Submission Action Row */}
      <div className="space-y-4 pt-4 border-t border-white/10">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            {/* Primary Action: Save Narrative */}
            <Button
              type="button"
              variant="primary"
              size="sm"
              onClick={handleSave}
              loading={saveMutation.isPending}
              disabled={saveMutation.isPending || isAnalyzing}
              className="font-mono text-xs font-bold uppercase tracking-wider"
            >
              <Save className="w-3.5 h-3.5 mr-1.5" />
              <span>Save My Experience</span>
            </Button>

            {/* Secondary Action: Analyze Skills */}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAnalyze}
              loading={isAnalyzing}
              disabled={saveMutation.isPending || isAnalyzing || text.trim().length < 5}
              className="font-mono text-xs font-bold uppercase tracking-wider border-teal-500/50 text-teal-300 hover:bg-teal-950/40"
            >
              <Sparkles className="w-3.5 h-3.5 mr-1.5 text-teal-400" />
              <span>Analyze My Skills (AI)</span>
            </Button>
          </div>

          {/* Save Status / Timestamp indicator */}
          <div className="text-[11px] font-mono text-zinc-500 flex items-center gap-2">
            <Clock className="w-3.5 h-3.5 text-zinc-400" />
            {lastUpdated ? (
              <span>Last saved: {formatDateTime(lastUpdated)}</span>
            ) : (
              <span>Not yet saved</span>
            )}
          </div>
        </div>

        {/* Privacy & Browser Notice */}
        <div className="p-3 bg-[#080808] border border-white/5 flex items-start gap-2.5 text-[11px] font-sans text-zinc-400 leading-normal">
          <Info className="w-4 h-4 text-zinc-400 flex-shrink-0 mt-0.5" />
          <div>
            <strong>Privacy &amp; Dictation Notice:</strong> Voice dictation uses your browser's built-in Web Speech API (supported in Chrome, Edge, and Safari). Voice data may be transcribed via your browser vendor's recognition service. KaushalTwin only stores the final text you choose to save. Raw audio is never uploaded or persisted.
          </div>
        </div>
      </div>

      {/* 6. AI Skill Analysis Results Panel */}
      {analysisResult && (
        <div className="p-6 bg-[#080808] border border-white/15 space-y-6 mt-6 specular-top-edge">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs font-mono font-bold text-teal-300 uppercase tracking-wider">
                <Sparkles className="w-4 h-4 text-teal-400" />
                <span>AI Skill Extraction &amp; Occupational Standards Analysis</span>
              </div>
              <p className="text-xs text-zinc-400 font-sans">
                Algorithmic extraction based on your narrative text for trade:{' '}
                <strong className="text-white uppercase font-mono">{analysisResult.trade || 'General'}</strong>.
              </p>
            </div>
            <span className="px-2 py-0.5 bg-amber-950/60 border border-amber-500/40 text-amber-300 text-[10px] font-mono uppercase tracking-wider">
              Advisory · Awaiting Assessor Review
            </span>
          </div>

          {/* Extracted Skills List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                1. Practical Skills Identified ({analysisResult.extracted_skills?.length || 0})
              </h3>
              {analysisResult.extracted_skills?.length > 0 && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleAddSkillsToProfile}
                  className="text-[10px] font-mono border-white/20 text-zinc-300 hover:text-white"
                >
                  <Plus className="w-3 h-3 mr-1" />
                  <span>Add Identified Skills to Profile</span>
                </Button>
              )}
            </div>

            {analysisResult.extracted_skills?.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {analysisResult.extracted_skills.map((skill, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 bg-[#050505] border border-white/10 space-y-1.5 font-mono text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-white font-bold truncate">{skill.skill_name}</span>
                      <span className="text-[10px] text-teal-400">
                        {Math.round((skill.confidence || 0.8) * 100)}% match
                      </span>
                    </div>
                    {skill.evidence_text && (
                      <p className="text-[10px] text-zinc-400 font-sans italic truncate">
                        Quote: "{skill.evidence_text}"
                      </p>
                    )}
                    <div className="flex items-center justify-between text-[9px] text-zinc-500 pt-1 border-t border-white/5">
                      <span>Trade: {skill.trade_context || analysisResult.trade}</span>
                      <span>Method: {skill.extraction_method || 'keyword'}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-zinc-500 font-sans italic">
                No specific practical skills were extracted from the current text. Try adding details about tools you use (e.g., multimeter, welding torch, pipe wrench) or specific installation tasks.
              </p>
            )}
          </div>

          {/* Suggested NOS Standards Mappings */}
          {analysisResult.nos_mappings?.length > 0 && (
            <div className="space-y-3 pt-4 border-t border-white/10">
              <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                2. Relevant National Occupational Standards (NOS) Matches
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {analysisResult.nos_mappings.map((mapping, idx) => {
                  const topCandidate = mapping.candidates?.[0];
                  if (!topCandidate) return null;
                  return (
                    <div
                      key={idx}
                      className="p-4 bg-[#050505] border border-white/10 space-y-2 font-mono"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-white font-bold text-xs">{topCandidate.nos_id}</span>
                        <span className="text-[10px] text-zinc-400">
                          Similarity: {Math.round((topCandidate.similarity || 0.5) * 100)}%
                        </span>
                      </div>
                      <div className="text-xs font-sans text-zinc-200 font-semibold">
                        {topCandidate.title}
                      </div>
                      <div className="text-[11px] font-sans text-zinc-400">
                        Mapped from: <span className="text-teal-300">"{mapping.skill?.skill_name}"</span>
                      </div>
                      {topCandidate.match_reasons?.length > 0 && (
                        <p className="text-[10px] font-sans text-zinc-500">
                          Reason: {topCandidate.match_reasons.join(' • ')}
                        </p>
                      )}
                      <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[9px] text-zinc-500">
                        <span>Status: Advisory Candidate</span>
                        <span className="text-amber-400">Assessor Review Required</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Governance Notice */}
          <div className="p-4 bg-teal-950/20 border border-teal-500/30 flex items-start gap-3 text-xs font-sans text-zinc-300 leading-relaxed">
            <ShieldCheck className="w-5 h-5 text-teal-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white font-mono uppercase text-[11px] block mb-0.5">
                RPL Assessment Principle
              </strong>
              {analysisResult.disclaimer ||
                'AI suggestions are strictly advisory and awaiting assessor review. These do not constitute verified competencies or certification. Your qualified human assessor will evaluate your skills during your practical RPL assessment.'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TellUsAboutYourWork;
