import { useState, useRef, useEffect } from "react";
import "./App.css";

export default function Home() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sendStatus, setSendStatus] = useState("");
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
      
    } catch (err) {
      console.error("Error accessing microphone:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob) => {
    try {
      const apiKey = "YOUR_DEEPGRAM_API_KEY";
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

    try {
      const response = await fetch("http://localhost:8000/rotation", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: transcript }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      setSendStatus("Sent");
      console.log("Backend response:", data);
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

  return (
    <>
      <nav className="navbar">
        <div className="logo">Rocky</div>
      </nav>

      <div className="container">
        <div className="left-panel">
          <div className="left-box"></div>
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