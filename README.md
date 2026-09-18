# ISL Generation System

An end-to-end system that translates natural language (English and Hindi) into **Indian Sign Language (ISL)**. The system provides two types of output: a stitched sequence of sign videos and raw 3D rotation data for rendering a virtual avatar.

## 🚀 Overview

This project leverages Large Language Models (LLMs) and semantic embeddings to bridge the gap between spoken/written language and ISL grammar. It doesn't just translate word-for-word but applies specific ISL grammatical rules (like Topic-Comment structure and Time-First ordering) to ensure the output is meaningful to the Deaf community.

## 🏗️ Architecture

### 1. Pipeline Flow
The system follows a multi-stage pipeline to transform a natural language sentence into ISL:

**Input** $\rightarrow$ **Translation** $\rightarrow$ **Vocab Resolution** $\rightarrow$ **ISL Grammar Mapping** $\rightarrow$ **Output Generation**

- **Translation**: If the input is in Hindi, it is first translated to English using `googletrans`.
- **Vocab Resolution**: 
  - The system identifies key words and removes stopwords.
  - It performs a lookup in a specialized ISL dictionary.
  - If a word is missing, it uses **Semantic Similarity** (via `sentence-transformers`) to find the closest available sign in the vocabulary.
- **ISL Grammar Mapping**: 
  - A specialized LLM (`gemma3` via `ollama`) acts as the ISL Grammar Agent.
  - Guided by a set of strict rules (defined in `soul.md`), the LLM rearranges the vocabulary into correct ISL structure (e.g., "I will go tomorrow" $\rightarrow$ "TOMORROW I GO").
- **Output Generation**:
  - **Video Path**: Stitches together pre-recorded MP4 clips for each sign using `moviepy`.
  - **Avatar Path**: Extracts 3D joint rotation data for each sign to drive a VRM avatar in the frontend.

### 2. Key Components

#### Backend (`/backend`)
- **FastAPI Server**: Handles requests for video generation and rotation data.
- **Embedding Engine**: Manages the ISL dictionary and performs cosine similarity searches for word mapping.
- **Grammar Agent**: Integrates with Ollama to ensure the output adheres to ISL linguistic standards.
- **Video Processor**: Dynamically concatenates video clips based on the generated ISL sequence.

#### Frontend (`/client`)
- **React Application**: Provides a user interface for entering sentences.
- **Avatar Renderer**: A 3D renderer that uses the rotation data to animate a VRM avatar in real-time.

#### Dataset Processing (`/dataset_processing`)
- Tools for processing raw sign videos, extracting landmarks using **MediaPipe**, and generating vector embeddings for the lookup engine.

## 🛠️ Tech Stack

- **Language**: Python (Backend), JavaScript/React (Frontend)
- **API Framework**: FastAPI
- **AI/ML**: 
  - `Ollama` (LLM for grammar)
  - `Sentence-Transformers` (all-MiniLM-L6-v2 for semantic lookup)
  - `MediaPipe` (for landmark extraction)
- **Video Processing**: `MoviePy`
- **3D Rendering**: VRM / Three.js (in client)

## 📦 Installation & Setup

### Backend Setup
1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure `ollama` is installed and the `gemma3:27b-cloud` model is pulled:
   ```bash
   ollama pull gemma3:27b-cloud
   ```
4. Run the server:
   ```bash
   python main.py
   ```

### Frontend Setup
1. Navigate to the client folder:
   ```bash
   cd client
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm start
   ```

## 📖 ISL Grammar Rules Applied
The system follows these core ISL principles:
- **Topic-Comment**: Subject/Topic comes first, followed by the action/comment.
- **Time-First**: Temporal markers (Today, Tomorrow, Yesterday) are placed at the beginning of the sentence.
- **Function Word Removal**: Words like "is", "am", "the", "a" are stripped out.
- **Base Forms**: Verbs are converted to their simplest base form.
