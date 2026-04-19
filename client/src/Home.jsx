import { useState, useRef, useEffect } from "react";
import "./App.css";
import AvatarRenderer from "./components/AvatarRenderer.jsx";
import { COUNT_ANIMATION, NAMASTE_ANIMATION, WAVE_ANIMATION } from "./lib/animationData.js";

export default function Home() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sendStatus, setSendStatus] = useState("");
  const [sequence, setSequence] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const chunksRef = useRef([]);

  useEffect(() => {
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      
      source.connect(analyser);
      analyser.fftSize = 256;
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        await transcribeAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start(100);
      setIsRecording(true);
      console.log('🎙️ Speech Event: Started recording audio...');
      
    } catch (err) {
      console.error("Error accessing microphone:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      console.log('🛑 Speech Event: Recording stopped, processing audio transcript...');
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob) => {
    try {
      const apiKey = "01945e333d4532e1b2a664c1da3f2b684408ba22";
      const url = "https://api.deepgram.com/v1/listen?smart_format=true&model=nova-2&language=en-US";
      
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Authorization": `Token ${apiKey}`,
          "Content-Type": "audio/webm",
        },
        body: audioBlob,
      });
      
      if (!response.ok) {
        throw new Error(`Deepgram API error: ${response.status}`);
      }
      
      const data = await response.json();
      const transcription = data.results?.channels?.[0]?.alternatives?.[0]?.transcript;
      
      if (transcription) {
        setTranscript((prev) => prev + (prev ? " " : "") + transcription);
      }
    } catch (err) {
      console.error("Transcription error:", err);
    }
  };

  const sendToBackend = async () => {
    if (!transcript.trim()) {
      setSendStatus("No text");
      return;
    }

    setIsSending(true);
    setSendStatus("");
    setSequence(null);
    console.log('📡 API Flow: Requesting 3D rotation data for transcript --->', transcript);

    try {
      const response = await fetch("http://localhost:8000/main", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ sentence: transcript, lang: "en" }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      setSendStatus("Sent");
      console.log('✅ API Flow: Received VRM gesture instructions from backend!');
      if (data.rotations && data.rotations.length > 0) {
        setSequence(data.rotations);
      } else {
        console.warn('⚠️ API Flow: No rotations found in backend response');
      }
    } catch (err) {
      console.error("Error sending to backend:", err);
      setSendStatus("Failed");
    } finally {
      setIsSending(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleTranscriptChange = (e) => {
    setTranscript(e.target.value);
  };

  const clearTranscript = () => {
    setTranscript("");
    setSendStatus("");
  };

  const playDemoCounter = () => {
    console.log("🎬 UI Event: Manually triggering the count-to-5 animation flow...");
    setSequence(COUNT_ANIMATION);
  };

  const playNamaste = () => {
    console.log("🎬 UI Event: Manually triggering the namaste animation flow...");
    setSequence(NAMASTE_ANIMATION);
  };

  const playWave = () => {
    console.log("🎬 UI Event: Manually triggering the wave animation flow...");
    setSequence(WAVE_ANIMATION);
  };

  return (
    <>
      <nav className="navbar">
        <div className="logo">Rocky</div>
      </nav>

      <div className="container">
        <div className="left-panel">
          <AvatarRenderer dynamicAnimData={sequence} onSequenceEnd={() => setSequence(null)} />
        </div>

        <div className="right-panel">
          <div className="record-section">
            <button 
              className={`record-btn ${isRecording ? "recording" : ""}`}
              onClick={toggleRecording}
              disabled={isSending}
            >
              {isRecording ? "Tap to end" : "Tap to speak"}
            </button>
            <button 
              className="record-btn"
              onClick={playDemoCounter}
              style={{ marginTop: "12px", background: "var(--background)", borderColor: "var(--border)" }}
              disabled={isSending || isRecording}
            >
              ✋ Play Count-to-5 Demo
            </button>
            <button 
              className="record-btn"
              onClick={playNamaste}
              style={{ marginTop: "8px", background: "var(--background)", borderColor: "var(--border)" }}
              disabled={isSending || isRecording}
            >
              🙏 Play Namaste
            </button>
            <button 
              className="record-btn"
              onClick={playWave}
              style={{ marginTop: "8px", background: "var(--background)", borderColor: "var(--border)" }}
              disabled={isSending || isRecording}
            >
              👋 Play Full Body Wave
            </button>
            
            {isRecording && (
              <div className="recording-indicator">
                <span className="recording-dot"></span>
                <span>Recording...</span>
              </div>
            )}
          </div>

          <div className="transcript-section">
            <label className="transcript-label">Transcription</label>
            <textarea
              className="transcript-textarea"
              value={transcript}
              onChange={handleTranscriptChange}
              placeholder="Your transcribed text will appear here..."
              disabled={isSending}
            />
            <div className="transcript-footer">
              <span className="char-count">{transcript.length} chars</span>
              <div className="footer-actions">
                <button className="send-btn" onClick={sendToBackend} disabled={isSending || !transcript.trim()}>
                  Send
                </button>
                <button className="clear-btn" onClick={clearTranscript} disabled={isSending}>
                  Clear
                </button>
              </div>
            </div>
            {sendStatus && (
              <div className={`send-status ${sendStatus === "Failed" ? "error" : ""}`}>
                {sendStatus}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}