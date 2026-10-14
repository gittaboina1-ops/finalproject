import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { studentService } from '../../services/api';
import MermaidDiagram from '../../components/MermaidDiagram';
import { LLMMessageRenderer } from '../../components/LLMMessageRenderer';
import { 
  Bot, 
  Send, 
  Sparkles, 
  BookOpen, 
  CheckCircle2, 
  AlertTriangle, 
  FileText, 
  Loader2, 
  Compass, 
  Image as ImageIcon,
  Check,
  ChevronDown,
  ChevronUp,
  Award,
  Layers,
  HelpCircle,
  BrainCircuit,
  Workflow
} from 'lucide-react';

const BACKEND_URL = `http://${window.location.hostname}:8000`;

const resolveImageUrl = (urlOrPath) => {
  if (!urlOrPath) return '';
  let str = urlOrPath;
  if (typeof urlOrPath === 'object') {
    str = urlOrPath.url || urlOrPath.path || urlOrPath.src || '';
  }
  if (!str || typeof str !== 'string') return '';
  if (str.startsWith('data:')) return str;
  if (str.startsWith('http://') || str.startsWith('https://')) return str;
  // Relative path like /images/... or /media/... — prepend backend host
  return `${BACKEND_URL}${str.startsWith('/') ? '' : '/'}${str}`;
};

const QuizCard = ({ 
  quiz, 
  quizId, 
  topic, 
  rawTopic, 
  subject, 
  quizMessage, 
  nextTopic,
  nextTopicName,
  nextTopicDescription,
  onQuizCompleted,
  onProceed,
  onSkip
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [evalResult, setEvalResult] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const [error, setError] = useState(null);
  const [isSkipped, setIsSkipped] = useState(false);
  const [skipping, setSkipping] = useState(false);

  if (!quiz || !Array.isArray(quiz) || quiz.length === 0) {
    return (
      <div className="pt-3 border-t border-slate-200">
        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-amber-500 shrink-0" />
          <span>{quizMessage || "Quiz could not be generated for this response. Please continue learning."}</span>
        </div>
      </div>
    );
  }

  const currentQ = quiz[currentStep] || quiz[0];
  const totalQuestions = quiz.length;
  const isLastQuestion = currentStep === totalQuestions - 1;

  const handleOptionSelect = (optIdx) => {
    setUserAnswers(prev => ({ ...prev, [currentStep]: optIdx }));
    setValidationError(null);
  };

  const handleNext = () => {
    if (userAnswers[currentStep] === undefined || userAnswers[currentStep] === null) {
      setValidationError("Please select an answer before continuing.");
      return;
    }
    setValidationError(null);
    if (!isLastQuestion) {
      setCurrentStep(prev => Math.min(totalQuestions - 1, prev + 1));
    } else {
      handleSubmit();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setValidationError(null);
      setCurrentStep(prev => Math.max(0, prev - 1));
    }
  };

  const handleSubmit = async () => {
    if (userAnswers[currentStep] === undefined || userAnswers[currentStep] === null) {
      setValidationError("Please select an answer before continuing.");
      return;
    }
    if (!quizId) return;

    setSubmitting(true);
    setError(null);
    setValidationError(null);
    try {
      const studentUser = JSON.parse(localStorage.getItem('pragtutor_user') || '{}');
      const studentId = studentUser.id || 'STU001';
      
      const answersArray = quiz.map((_, idx) => userAnswers[idx] !== undefined ? userAnswers[idx] : null);
      
      const result = await studentService.evaluateQuiz(quizId, answersArray, studentId, subject, topic);
      setEvalResult(result);

      if (result && result.passed && onQuizCompleted) {
        onQuizCompleted(topic);
      }
    } catch (err) {
      console.error('Quiz evaluation error:', err);
      setError("Failed to evaluate quiz answers. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const targetTopicName = topic || 'Operating System';

  // Topic recommendation resolved from evaluation result or initial query context
  const recTopicId = evalResult?.next_topic || nextTopic;
  const recTopicName = evalResult?.next_topic_name || nextTopicName || (recTopicId ? recTopicId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Next Topic');
  const recTopicDesc = evalResult?.next_topic_description || nextTopicDescription || '';

  const handleLaterClick = async () => {
    if (!recTopicId && !recTopicName) return;
    setSkipping(true);
    try {
      const studentUser = JSON.parse(localStorage.getItem('pragtutor_user') || '{}');
      const studentId = studentUser.id || 'STU001';
      const topicToSkip = recTopicId || recTopicName;
      await studentService.skipTopic(studentId, subject, topicToSkip);
      if (onSkip) {
        onSkip(topicToSkip);
      }
      setIsSkipped(true);
    } catch (err) {
      console.error('Failed to skip topic:', err);
    } finally {
      setSkipping(false);
    }
  };

  return (
    <div className="pt-4 border-t border-slate-200 space-y-4">
      {/* Quiz Header & Topic Title */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-amber-50 via-orange-50 to-amber-50 border border-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
        <div className="flex items-center gap-2.5">
          <span className="p-2.5 bg-amber-100 text-amber-700 rounded-xl border border-amber-200">
            <HelpCircle className="w-5 h-5" />
          </span>
          <div>
            <h3 className="text-sm font-bold text-amber-900 uppercase tracking-wide flex items-center gap-2">
              Test Your Understanding
            </h3>
            <p className="text-xs text-slate-600">
              Topic: <span className="text-amber-800 font-bold">{targetTopicName}</span>
            </p>
          </div>
        </div>

        {!evalResult && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-3 py-1.5 rounded-xl bg-white border border-amber-300 text-amber-800 shadow-xs">
              Question {currentStep + 1} of {totalQuestions}
            </span>
          </div>
        )}
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* BEFORE SUBMISSION: STEP-BY-STEP QUESTION VIEW (ONE QUESTION AT A TIME) */}
      {!evalResult ? (
        <div className="space-y-4">
          {/* Progress Bar */}
          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden border border-slate-200">
            <div 
              className="bg-gradient-to-r from-amber-500 to-orange-500 h-full rounded-full transition-all duration-300"
              style={{ width: `${((currentStep + 1) / totalQuestions) * 100}%` }}
            />
          </div>

          {/* Current Question Card */}
          <div className="p-5 bg-white rounded-2xl border border-slate-200 space-y-4 shadow-sm">
            <div className="text-sm font-semibold text-slate-900 flex items-start gap-2.5 leading-relaxed">
              <span className="px-2.5 py-0.5 rounded-lg bg-blue-50 text-blue-700 border border-blue-200 font-mono text-xs shrink-0 mt-0.5">
                Q{currentStep + 1}
              </span>
              <span>{currentQ.question}</span>
            </div>

            {/* 4 Selectable Option Buttons */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              {currentQ.options && currentQ.options.map((optText, optIdx) => {
                const isSelected = userAnswers[currentStep] === optIdx;
                const optionLabel = String.fromCharCode(65 + optIdx);
                return (
                  <button
                    key={optIdx}
                    type="button"
                    onClick={() => handleOptionSelect(optIdx)}
                    className={`p-3.5 rounded-xl text-xs text-left font-medium border transition-all flex items-center gap-3 cursor-pointer ${
                      isSelected
                        ? 'bg-blue-50 text-blue-900 border-blue-500 shadow-sm ring-2 ring-blue-500/20 font-semibold'
                        : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200 hover:border-slate-300 shadow-xs'
                    }`}
                  >
                    <span className={`w-6 h-6 rounded-full border text-[11px] font-bold flex items-center justify-center shrink-0 transition-colors ${
                      isSelected ? 'border-blue-600 bg-blue-600 text-white' : 'border-slate-300 text-slate-600 bg-slate-100'
                    }`}>
                      {optionLabel}
                    </span>
                    <span className="leading-snug flex-1">{optText}</span>
                  </button>
                );
              })}
            </div>

            {/* Validation Warning */}
            {validationError && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 font-medium flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>{validationError}</span>
              </div>
            )}
          </div>

          {/* Navigation Control Buttons */}
          <div className="flex items-center justify-between pt-1">
            <button
              type="button"
              onClick={handleBack}
              disabled={currentStep === 0 || submitting}
              className="px-5 py-2.5 rounded-xl bg-white hover:bg-slate-50 disabled:opacity-40 text-slate-700 hover:text-slate-900 border border-slate-200 text-xs font-semibold shadow-xs transition-all flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed"
            >
              <span>← Back</span>
            </button>

            <button
              type="button"
              onClick={isLastQuestion ? handleSubmit : handleNext}
              disabled={submitting}
              className={`px-6 py-2.5 rounded-xl font-bold text-xs shadow-sm transition-all flex items-center gap-2 cursor-pointer ${
                isLastQuestion
                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/20'
                  : 'bg-blue-600 hover:bg-blue-700 text-white shadow-blue-600/20'
              }`}
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Evaluating...</span>
                </>
              ) : isLastQuestion ? (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Finish Quiz</span>
                </>
              ) : (
                <>
                  <span>Next →</span>
                </>
              )}
            </button>
          </div>
        </div>
      ) : (
        /* AFTER SUBMISSION: RESULT VIEW & EXPLANATIONS */
        <div className="space-y-4">
          {/* Score Banner */}
          <div className={`p-5 rounded-2xl border space-y-3 shadow-sm ${
            evalResult.passed
              ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
              : 'bg-amber-50 border-amber-200 text-amber-950'
          }`}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <span className="text-[11px] font-mono uppercase tracking-wider text-slate-500 block mb-0.5">Quiz Completed</span>
                <h3 className="text-lg font-bold flex items-center gap-2">
                  {evalResult.passed ? <CheckCircle2 className="w-6 h-6 text-emerald-600" /> : <AlertTriangle className="w-6 h-6 text-amber-600" />}
                  <span>Score: {evalResult.score} / {evalResult.total} ({evalResult.percentage}%)</span>
                </h3>
              </div>
              <span className={`px-4 py-1.5 rounded-xl text-xs font-extrabold uppercase tracking-wide border shadow-xs ${
                evalResult.passed
                  ? 'bg-white text-emerald-800 border-emerald-300'
                  : 'bg-white text-rose-800 border-rose-300'
              }`}>
                {evalResult.passed ? '🎉 Topic Learned' : 'Topic Not Learned Yet'}
              </span>
            </div>

            <p className="text-xs text-slate-700 leading-relaxed bg-white/90 p-3 rounded-xl border border-slate-200">
              {evalResult.passed
                ? `You have successfully completed this topic '${targetTopicName}'.`
                : `Score is ${evalResult.percentage}% (requires > 70% to complete). Review the incorrect concepts below.`}
            </p>
          </div>

          {/* Detailed Question Review & Explanations */}
          <div className="space-y-3 pt-1">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-amber-600" />
              Review Your Answers
            </h4>

            {evalResult.results && evalResult.results.map((res, rIdx) => (
              <div key={rIdx} className={`p-4 rounded-2xl border space-y-2.5 transition-all shadow-xs ${
                res.is_correct
                  ? 'bg-emerald-50/50 border-emerald-200'
                  : 'bg-rose-50/50 border-rose-200'
              }`}>
                <div className="flex items-start justify-between gap-2 font-bold text-xs">
                  <span className="text-slate-900 leading-snug">
                    Question {rIdx + 1}: {res.question}
                  </span>
                  <span className={`px-2.5 py-0.5 rounded-md text-[11px] font-bold shrink-0 ${
                    res.is_correct ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' : 'bg-rose-100 text-rose-800 border border-rose-200'
                  }`}>
                    {res.is_correct ? '✓ Correct' : '✗ Incorrect'}
                  </span>
                </div>

                {!res.is_correct ? (
                  <div className="space-y-2 text-xs pt-2 border-t border-rose-200/60">
                    <div className="text-rose-900 font-medium bg-rose-100/70 p-2.5 rounded-xl border border-rose-200">
                      <span className="font-semibold text-rose-800">Your answer: </span>
                      {res.student_answer}
                    </div>
                    <div className="text-emerald-950 font-medium bg-emerald-100/70 p-2.5 rounded-xl border border-emerald-200">
                      <span className="font-semibold text-emerald-800">Correct answer: </span>
                      {res.correct_answer}
                    </div>
                    {res.explanation && (
                      <div className="p-3 bg-white rounded-xl border border-slate-200 text-slate-700 leading-relaxed shadow-xs">
                        <span className="font-bold text-blue-700">Explanation: </span>
                        {res.explanation}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-xs text-emerald-700 font-medium pt-1 border-t border-emerald-200/60">
                    ✓ Question {rIdx + 1} — Correct
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Next Topic Recommendation Section (Appears after quiz completion and answer review) */}
          <div className="mt-5 p-5 rounded-2xl bg-slate-50 border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center gap-2.5">
              <span className="p-2 bg-blue-100 text-blue-700 rounded-xl border border-blue-200">
                <Compass className="w-5 h-5" />
              </span>
              <div>
                <h4 className="text-sm font-bold text-slate-900 tracking-tight">
                  Next Topic Recommendation
                </h4>
                <p className="text-xs text-slate-500">
                  Recommended based on your course sequence & prerequisites
                </p>
              </div>
            </div>

            <div className="p-4 bg-white rounded-xl border border-slate-200 space-y-1.5 shadow-xs">
              <div className="text-xs text-slate-600 font-medium">
                Recommended topic: <span className="font-bold text-blue-700 text-sm">{recTopicName}</span>
              </div>
              {recTopicDesc && (
                <p className="text-xs text-slate-600 leading-relaxed pt-0.5">
                  {recTopicDesc}
                </p>
              )}
            </div>

            {/* Action Buttons: Proceed and Later */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
              <div className="flex items-center gap-2.5">
                <button
                  type="button"
                  onClick={() => onProceed && onProceed(recTopicName || recTopicId)}
                  className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm hover:shadow transition-all flex items-center gap-2 cursor-pointer"
                >
                  <span>Proceed</span>
                  <span>→</span>
                </button>

                <button
                  type="button"
                  onClick={handleLaterClick}
                  disabled={isSkipped || skipping}
                  className={`px-5 py-2.5 rounded-xl font-semibold text-xs border transition-all flex items-center gap-1.5 ${
                    isSkipped
                      ? 'bg-amber-50 text-amber-800 border-amber-300 cursor-default'
                      : 'bg-white hover:bg-slate-100 text-slate-700 hover:text-slate-900 border-slate-300 cursor-pointer shadow-xs'
                  }`}
                >
                  {isSkipped ? (
                    <>
                      <span>✓</span>
                      <span>Saved to Skipped Topics</span>
                    </>
                  ) : skipping ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-slate-500" />
                      <span>Saving...</span>
                    </>
                  ) : (
                    <>
                      <span>Later</span>
                    </>
                  )}
                </button>
              </div>

              {isSkipped && (
                <span className="text-[11px] text-amber-800 font-medium bg-amber-50 px-3 py-1.5 rounded-xl border border-amber-200">
                  Topic saved to Skipped Topics. Revisit anytime from your dashboard.
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export const AIChat = () => {
  const [searchParams] = useSearchParams();
  const initialSubject = searchParams.get('subject') || 'operating_systems';
  const initialQuery = searchParams.get('query') || '';

  const [subject, setSubject] = useState(initialSubject);
  const [query, setQuery] = useState(initialQuery);
  const [level, setLevel] = useState('beginner');
  const [attachedImages, setAttachedImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [showSourcesMap, setShowSourcesMap] = useState({});
  const [learnedTopics, setLearnedTopics] = useState(new Set());
  const [markingTopic, setMarkingTopic] = useState(null);
  const [previewImageModal, setPreviewImageModal] = useState(null);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const samplePrompts = [
    "What is a process?",
    "Show diagram of process states",
    "Explain CPU scheduling algorithms",
    "Show image of PCB structure",
    "What is virtual memory?"
  ];

  const subjectsList = [
    { id: 'operating_systems', name: 'Operating Systems' },
    { id: 'computer_networks', name: 'Computer Networks' },
    { id: 'data_structures', name: 'Data Structures' },
    { id: 'dbms', name: 'DBMS' },
    { id: 'software_engineering', name: 'Software Engineering' }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Load student's learned topics from MongoDB for current subject
  useEffect(() => {
    const studentUser = JSON.parse(localStorage.getItem('pragtutor_user') || '{}');
    const studentId = studentUser.id || 'STU001';
    studentService.getHistory(studentId, subject)
      .then(res => {
        if (res && res.known_topics) {
          setLearnedTopics(new Set(res.known_topics));
        } else if (res && res.completed_topics) {
          setLearnedTopics(new Set(res.completed_topics));
        }
      })
      .catch(e => console.warn('Could not load student progress:', e));
  }, [subject]);

  const handleImageSelect = (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = (event) => {
        setAttachedImages(prev => [...prev, {
          id: Date.now() + Math.random(),
          name: file.name,
          dataUri: event.target.result
        }]);
      };
      reader.readAsDataURL(file);
    });

    e.target.value = '';
  };

  const removeAttachedImage = (idToRemove) => {
    setAttachedImages(prev => prev.filter(img => img.id !== idToRemove));
  };

  const handleMarkLearned = async (msgId, topicKey, topicName) => {
    try {
      setMarkingTopic(topicKey || topicName);
      const studentUser = JSON.parse(localStorage.getItem('pragtutor_user') || '{}');
      const studentId = studentUser.id || 'STU001';
      const topicToMark = topicKey || topicName;
      await studentService.markLearned(studentId, subject, topicToMark);
      setLearnedTopics(prev => new Set([...prev, topicToMark, topicName, topicToMark.toLowerCase(), topicToMark.replace('_', ' ')]));
    } catch (err) {
      console.error('Failed to mark topic as learned:', err);
    } finally {
      setMarkingTopic(null);
    }
  };

  const handleSend = async (customQuery = null) => {
    const textToSend = customQuery || query;
    if (!textToSend.trim() && attachedImages.length === 0) return;

    const studentUser = JSON.parse(localStorage.getItem('pragtutor_user') || '{}');
    const studentId = studentUser.id || 'STU001';

    const currentImages = [...attachedImages];

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: textToSend || "Analyzing attached image(s)...",
      attachedImages: currentImages.map(img => img.dataUri),
      level,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessage]);
    if (!customQuery) setQuery('');
    setAttachedImages([]);
    setLoading(true);

    try {
      const imgPayload = currentImages.length > 0 ? currentImages.map(img => img.dataUri) : null;
      const res = await studentService.queryTutor(textToSend || "Explain the attached image", subject, imgPayload, studentId, level);
      const isKbUnavailable = res.status === 'kb_unavailable';
      
      const botMessage = {
        id: Date.now() + 1,
        sender: 'tutor',
        isKbUnavailable,
        rawTopic: res.topic_id || res.topic || "general",
        topic: res.topic_name || res.topic || "General Concept",
        topicConfidence: Math.round((res.topic_confidence || 0.85) * 100),
        level: res.level || level,
        completedPrereqs: res.student_completed || [],
        missingPrereqs: res.missing_prerequisites || [],
        learningPath: res.learning_path || res.prerequisites_used || [],
        sources: res.sources || res.retrieved_content || [],
        images: res.retrieved_images || res.images || [],
        retrievedImages: res.retrieved_images || res.images || [],
        generatedVisual: res.generated_visual || null,
        quiz: res.quiz || null,
        quizId: res.quiz_id || null,
        quizMessage: res.quiz_message || null,
        nextTopic: res.next_topic || null,
        nextTopicName: res.next_topic_name || null,
        nextTopicDescription: res.next_topic_description || null,
        answer: isKbUnavailable 
          ? (res.message || "PDFs have not been uploaded by your teachers for this subject yet.") 
          : (res.answer || res.llm_response || "Explanation generated."),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error(error);
      const errorMsg = {
        id: Date.now() + 1,
        sender: 'tutor',
        isKbUnavailable: false,
        answer: "I apologize, but I encountered an error processing your query. Please check your network or try again.",
        topic: "System Notice",
        topicConfidence: 100,
        level,
        completedPrereqs: [],
        missingPrereqs: [],
        learningPath: [],
        sources: [],
        images: [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSources = (msgId) => {
    setShowSourcesMap(prev => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  return (
    <div className="w-full min-h-[calc(100vh-65px)] bg-white text-slate-800">
      <div className="flex flex-col h-[calc(100vh-65px)] max-w-6xl mx-auto p-4 md:p-6 space-y-4">
        {/* Header Bar */}
        <div className="p-4 rounded-2xl border border-slate-200 bg-white shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shadow-xs">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-900 flex items-center gap-2">
                PragTutor Interactive AI Session
              </h1>
              <p className="text-xs text-slate-500">RAG Knowledge Retrieval & Adaptive Prerequisite Engine</p>
            </div>
          </div>

          {/* Subject Selector */}
          <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl text-xs">
            <BookOpen className="w-4 h-4 text-amber-500" />
            <span className="text-slate-500 font-medium">Subject:</span>
            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="bg-transparent text-slate-800 font-semibold focus:outline-none cursor-pointer"
            >
              {subjectsList.map(s => (
                <option key={s.id} value={s.id} className="bg-white text-slate-900">
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto space-y-6 pr-2">
          {messages.length === 0 && (
            <div className="p-8 rounded-3xl border border-slate-200 bg-slate-50/60 shadow-sm text-center space-y-6 my-auto max-w-2xl mx-auto mt-12">
              <div className="w-16 h-16 rounded-2xl bg-blue-50 border border-blue-200 text-blue-600 mx-auto flex items-center justify-center shadow-xs">
                <Bot className="w-8 h-8" />
              </div>
              <div className="space-y-2">
                <h2 className="text-xl font-bold text-slate-900">Ask PragTutor Anything</h2>
                <p className="text-xs text-slate-600">
                  PragTutor uses RAG to pull context from your course PDFs, analyzes your prerequisite knowledge state, and designs a custom step-by-step explanation.
                </p>
              </div>

              {/* Quick Sample Prompts */}
              <div className="space-y-2 text-left">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                  Recommended Questions:
                </span>
                <div className="flex flex-wrap gap-2">
                  {samplePrompts.map((promptText, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSend(promptText)}
                      className="px-3.5 py-2 rounded-xl bg-white hover:bg-blue-50 border border-slate-200 hover:border-blue-300 text-xs text-slate-700 hover:text-blue-700 shadow-xs transition-all text-left flex items-center gap-1.5 cursor-pointer"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                      {promptText}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} space-y-2`}>
              
              {/* USER BUBBLE */}
              {msg.sender === 'user' && (
                <div className="max-w-2xl bg-blue-600 text-white rounded-2xl rounded-tr-none px-5 py-3.5 text-sm shadow-sm space-y-2">
                  <p>{msg.text}</p>
                  {msg.attachedImages && msg.attachedImages.length > 0 && (
                    <div className="flex flex-wrap gap-2 pt-1 border-t border-blue-400/30">
                      {msg.attachedImages.map((imgUri, idx) => (
                        <img
                          key={idx}
                          src={imgUri}
                          alt="Attached upload"
                          onClick={() => setPreviewImageModal(imgUri)}
                          className="w-24 h-24 object-cover rounded-lg border border-white/30 cursor-pointer hover:opacity-90 transition-opacity"
                        />
                      ))}
                    </div>
                  )}
                  <div className="text-[10px] text-blue-100 text-right mt-1 font-mono">{msg.timestamp}</div>
                </div>
              )}

              {/* TUTOR RESPONSE BUBBLE */}
              {msg.sender === 'tutor' && (
                msg.isKbUnavailable ? (
                  <div className="w-full rounded-3xl border border-amber-200 bg-amber-50/60 p-6 space-y-4 shadow-sm">
                    <div className="flex items-center gap-3 text-amber-700">
                      <AlertTriangle className="w-6 h-6 shrink-0" />
                      <div>
                        <h3 className="text-base font-bold text-amber-900">Knowledge Base Not Available</h3>
                        <p className="text-xs text-amber-700">Subject: {subject.replace('_', ' ').toUpperCase()}</p>
                      </div>
                    </div>
                    <div className="text-sm text-slate-800 font-medium leading-relaxed bg-white p-4 rounded-2xl border border-amber-200 shadow-xs">
                      {msg.answer}
                    </div>
                  </div>
                ) : (
                  <div className="w-full rounded-3xl border border-slate-200 bg-white p-6 space-y-6 shadow-sm">
                    
                    {/* 1. TOPIC & CONFIDENCE BADGE */}
                    <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-2xl bg-slate-50 border border-slate-200">
                      <div className="flex items-center gap-3">
                        <span className="p-2 bg-blue-50 text-blue-600 border border-blue-200 rounded-xl">
                          <BrainCircuit className="w-5 h-5" />
                        </span>
                        <div>
                          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Identified Course Topic</div>
                          <div className="text-sm font-bold text-slate-900 flex items-center gap-2">
                            {msg.topic}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-xl border border-slate-200 shadow-xs">
                        <span className="text-xs text-slate-500 font-medium">Confidence:</span>
                        <span className="text-xs font-mono font-bold text-emerald-700">{msg.topicConfidence}%</span>
                        <div className="w-16 h-2 bg-slate-200 rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${msg.topicConfidence}%` }}></div>
                        </div>
                        <span className="ml-2 text-[11px] font-semibold uppercase px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200">
                          {msg.level || 'beginner'}
                        </span>
                      </div>
                    </div>

                    {/* 2. PREREQUISITE ANALYSIS BOX */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Completed Prerequisites */}
                      <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200 space-y-2">
                        <span className="text-xs font-bold text-emerald-800 flex items-center gap-1.5">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                          Completed Prerequisites (Mastered)
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.completedPrereqs.length > 0 ? (
                            msg.completedPrereqs.map((p, i) => (
                              <span key={i} className="px-2.5 py-1 rounded-lg bg-emerald-100 text-emerald-800 text-xs font-medium border border-emerald-300">
                                ✓ {p.replace('_', ' ')}
                              </span>
                            ))
                          ) : (
                            <span className="text-xs text-slate-500">All basic requirements verified.</span>
                          )}
                        </div>
                      </div>

                      {/* Missing Prerequisites */}
                      <div className="p-4 rounded-2xl bg-amber-50/60 border border-amber-200 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-amber-800 flex items-center gap-1.5">
                            <AlertTriangle className="w-4 h-4 text-amber-600" />
                            Missing Prerequisites (Click to mark learned)
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.missingPrereqs.length > 0 ? (
                            msg.missingPrereqs.map((p, i) => {
                              const isLearned = learnedTopics.has(p) || learnedTopics.has(p.toLowerCase()) || learnedTopics.has(p.replace('_', ' '));
                              return (
                                <button
                                  key={i}
                                  onClick={() => !isLearned && handleMarkLearned(msg.id, p, p)}
                                  title={isLearned ? "Already learned and saved to database" : "Click to mark as learned in your database"}
                                  className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-all flex items-center gap-1 cursor-pointer ${
                                    isLearned
                                      ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                                      : 'bg-white hover:bg-amber-100/70 text-amber-800 border-amber-300 shadow-xs'
                                  }`}
                                >
                                  {isLearned ? '✓' : '⚠'} {p.replace('_', ' ')} {isLearned ? '(Learned)' : '(Click to complete)'}
                                </button>
                              );
                            })
                          ) : (
                            <span className="text-xs text-slate-500">No missing prerequisites detected!</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* 3. PERSONALIZED LEARNING PATH CARD */}
                    {msg.learningPath.length > 0 && (
                      <div className="p-4 rounded-2xl bg-indigo-50/60 border border-indigo-200 space-y-3">
                        <span className="text-xs font-bold text-indigo-900 flex items-center gap-1.5">
                          <Compass className="w-4 h-4 text-indigo-600" />
                          Personalized Learning Sequence
                        </span>
                        <div className="flex flex-wrap items-center gap-2 text-xs">
                          {msg.learningPath.map((step, idx) => (
                            <React.Fragment key={idx}>
                              <span className="px-3 py-1 rounded-xl bg-white text-indigo-900 border border-indigo-200 font-medium shadow-xs">
                                {idx + 1}. {step.replace('_', ' ').toUpperCase()}
                              </span>
                              {idx < msg.learningPath.length - 1 && (
                                <span className="text-indigo-400 font-bold">→</span>
                              )}
                            </React.Fragment>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 3.5 RETRIEVED DIAGRAMS & IMAGES CARD WITH SOURCE CITATIONS */}
                    {msg.retrievedImages && msg.retrievedImages.length > 0 && (
                      <div className="p-4 rounded-2xl bg-purple-50/60 border border-purple-200 space-y-3">
                        <span className="text-xs font-bold text-purple-900 flex items-center gap-1.5">
                          <ImageIcon className="w-4 h-4 text-purple-600" />
                          Relevant Course Material Figures ({msg.retrievedImages.length} Image{msg.retrievedImages.length > 1 ? 's' : ''})
                        </span>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {msg.retrievedImages.map((imgObj, idx) => (
                            <div 
                              key={idx} 
                              onClick={() => setPreviewImageModal(resolveImageUrl(imgObj.url || imgObj.path || imgObj))}
                              className="p-2.5 bg-white rounded-xl border border-slate-200 hover:border-purple-300 cursor-pointer space-y-2 group transition-all shadow-xs"
                            >
                              <img 
                                src={resolveImageUrl(imgObj.url || imgObj.path || imgObj)} 
                                alt={imgObj.caption || "Course Diagram"} 
                                className="w-full h-44 object-contain bg-slate-50 rounded-lg group-hover:scale-[1.02] transition-transform" 
                              />
                              <div className="space-y-1 text-left px-1">
                                <div className="text-[11px] font-semibold text-slate-800 line-clamp-1">
                                  {imgObj.caption || `Diagram ${idx + 1}`}
                                </div>
                                <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono bg-slate-50 px-2 py-1 rounded border border-slate-200">
                                  <span>📄 {imgObj.source || 'Course Material'}</span>
                                  <span>Unit {imgObj.unit || '1'} • Page {imgObj.page || 1}</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 3.6 GENERATED EDUCATIONAL FLOWCHART / DIAGRAM */}
                    {msg.generatedVisual && msg.generatedVisual.enabled && msg.generatedVisual.content && (
                      <div className="space-y-2 p-3 bg-slate-50 rounded-2xl border border-slate-200">
                        <MermaidDiagram chart={msg.generatedVisual.content} />
                      </div>
                    )}

                    {/* 4. MAIN LLM TUTOR EXPLANATION */}
                    <div className="space-y-3 pt-2">
                      <div className="font-bold text-base text-slate-900 flex items-center gap-2 border-b border-slate-200 pb-2">
                        <Bot className="w-5 h-5 text-blue-600" />
                        Personalized AI Explanation ({msg.level ? msg.level.toUpperCase() : 'BEGINNER'})
                      </div>
                      <LLMMessageRenderer content={msg.answer} />
                    </div>

                    {/* 4.5 5-QUESTION PERSONALIZED QUIZ (APPEARS AFTER LLM EXPLANATION) */}
                    {!msg.isKbUnavailable && (
                      <QuizCard
                        quiz={msg.quiz}
                        quizId={msg.quizId}
                        topic={msg.topic}
                        rawTopic={msg.rawTopic}
                        subject={subject}
                        quizMessage={msg.quizMessage}
                        nextTopic={msg.nextTopic}
                        nextTopicName={msg.nextTopicName}
                        nextTopicDescription={msg.nextTopicDescription}
                        onQuizCompleted={(completedTopic) => {
                          setLearnedTopics(prev => new Set([...prev, completedTopic, msg.rawTopic, completedTopic.toLowerCase(), completedTopic.replace('_', ' ')]));
                        }}
                        onProceed={(recTopic) => {
                          handleSend(recTopic.toLowerCase().startsWith('explain ') ? recTopic : `Explain ${recTopic}`);
                        }}
                        onSkip={(topicSkipped) => {
                          // Topic recorded as skipped
                        }}
                      />
                    )}

                    {/* 5. CITED SOURCES ACCORDION */}
                    {msg.sources.length > 0 && (
                      <div className="pt-3 border-t border-slate-200 space-y-3">
                        <button
                          onClick={() => toggleSources(msg.id)}
                          className="w-full flex items-center justify-between text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors cursor-pointer"
                        >
                          <span className="flex items-center gap-1.5">
                            <FileText className="w-4 h-4 text-amber-600" />
                            Retrieved Course References ({msg.sources.length} Sources from ChromaDB)
                          </span>
                          {showSourcesMap[msg.id] ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </button>

                        {showSourcesMap[msg.id] && (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                            {msg.sources.map((src, idx) => (
                              <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5 text-xs shadow-xs">
                                <div className="flex items-center justify-between font-mono text-[11px] text-amber-700">
                                  <span>📄 {src.source_file || src.metadata?.source || 'Course Document'}</span>
                                  <span>Unit {src.unit || '1'} • Page {src.page || '1'}</span>
                                </div>
                                <p className="text-[11px] text-slate-600 italic line-clamp-3 bg-white p-2 rounded border border-slate-200">
                                  "{src.content || src.text}"
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* 6. MARK AS LEARNED BUTTON */}
                    <div className="pt-4 border-t border-slate-200 flex items-center justify-between">
                      <div className="text-xs text-slate-500">
                        Learned topic <span className="font-semibold text-slate-800">{msg.topic}</span>?
                      </div>
                      <button
                        onClick={() => handleMarkLearned(msg.id, msg.rawTopic, msg.topic)}
                        disabled={learnedTopics.has(msg.rawTopic) || learnedTopics.has(msg.topic) || markingTopic === (msg.rawTopic || msg.topic)}
                        className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                          learnedTopics.has(msg.rawTopic) || learnedTopics.has(msg.topic)
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-300 cursor-default'
                            : 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow cursor-pointer'
                        }`}
                      >
                        {learnedTopics.has(msg.rawTopic) || learnedTopics.has(msg.topic) ? (
                          <>
                            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                            Learned ✓ (Saved to DB)
                          </>
                        ) : markingTopic === (msg.rawTopic || msg.topic) ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Saving to Database...
                          </>
                        ) : (
                          <>
                            <Award className="w-4 h-4" />
                            Mark as Learned
                          </>
                        )}
                      </button>
                    </div>

                  </div>
                )
              )}
            </div>
          ))}

          {loading && (
            <div className="p-6 rounded-3xl border border-slate-200 bg-slate-50 flex items-center gap-4 text-slate-700 text-sm shadow-sm">
              <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
              <div>
                <div className="font-bold text-slate-900">Analyzing query & searching ChromaDB ({level.toUpperCase()} level)...</div>
                <div className="text-xs text-slate-500">Running topic classifier, checking prerequisites, and generating AI tutor response.</div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Box with Level Selector */}
        <div className="p-3.5 rounded-2xl border border-slate-200 bg-white shadow-sm shrink-0 space-y-2.5">
          {/* 3-Option Level Selector: Beginner, Intermediate, Advance */}
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              <span className="text-xs font-bold text-slate-700">Explanation Level:</span>
            </div>
            <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl border border-slate-200">
              <button
                type="button"
                onClick={() => setLevel('beginner')}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  level === 'beginner'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Beginner
              </button>
              <button
                type="button"
                onClick={() => setLevel('intermediate')}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  level === 'intermediate'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Intermediate
              </button>
              <button
                type="button"
                onClick={() => setLevel('advance')}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  level === 'advance' || level === 'advanced'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Advance
              </button>
            </div>
          </div>

          {/* Attached Images Preview Chips */}
          {attachedImages.length > 0 && (
            <div className="flex flex-wrap gap-2 p-2 bg-slate-50 rounded-xl border border-slate-200">
              {attachedImages.map(img => (
                <div key={img.id} className="relative group shrink-0">
                  <img src={img.dataUri} alt="Attached preview" className="w-16 h-16 object-cover rounded-lg border border-slate-300" />
                  <button
                    type="button"
                    onClick={() => removeAttachedImage(img.id)}
                    className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-rose-600 hover:bg-rose-500 text-white rounded-full text-xs font-bold flex items-center justify-center shadow-xs"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}

          <form 
            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            className="flex items-center gap-2"
          >
            <input
              type="file"
              ref={fileInputRef}
              accept="image/*"
              multiple
              onChange={handleImageSelect}
              className="hidden"
            />

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              title="Attach image(s) to your question"
              className="p-3 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 hover:border-blue-400 text-slate-700 hover:text-blue-600 transition-all flex items-center gap-1 text-xs shrink-0 cursor-pointer shadow-xs"
            >
              <ImageIcon className="w-4 h-4 text-blue-600" />
              <span className="hidden sm:inline">Image</span>
            </button>

            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={`Ask a question or upload image in ${subject.replace('_', ' ')} (${level.toUpperCase()} mode)...`}
              className="flex-1 bg-transparent px-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none"
            />

            <button
              type="submit"
              disabled={loading || (!query.trim() && attachedImages.length === 0)}
              className="p-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-sm hover:shadow disabled:opacity-50 transition-all flex items-center gap-1.5 text-xs shrink-0 cursor-pointer"
            >
              <span>Send</span>
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>

        {/* Fullscreen Image Lightbox Modal */}
        {previewImageModal && (
          <div 
            onClick={() => setPreviewImageModal(null)}
            className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
          >
            <div className="relative max-w-4xl max-h-[90vh] bg-white p-2 rounded-2xl border border-slate-300 shadow-2xl overflow-hidden flex flex-col items-center">
              <button
                onClick={() => setPreviewImageModal(null)}
                className="absolute top-3 right-3 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-bold z-10 shadow-sm"
              >
                ✕ Close
              </button>
              <img src={previewImageModal} alt="Enlarged Diagram Preview" className="max-w-full max-h-[82vh] object-contain rounded-xl" />
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
