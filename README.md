# 🎬 Vyber – Movies That Match Your Vibe

Vyber is an AI-powered movie recommendation system that suggests movies based on your current mood.  
It uses emotion detection, genre filtering, similarity scoring, and contextual personalization to deliver tailored movie recommendations.

---

## 🚀 Features

### 🧠 Mood Detection
- Detects user emotion from free-text input using a pretrained HuggingFace model.
- Maps fine-grained emotions into 6 core moods:
  - Happy
  - Sad
  - Romantic
  - Action
  - Scary
  - Fantasy

### 🎭 Manual Mood Selection
- Users can directly select their current mood.

### 🎬 Smart Recommendations
- Combines:
  - Cosine similarity
  - Genre filtering
  - Average rating
- Generates natural-language explanations for each recommendation.

### 🎲 Surprise Me
- Provides a fresh recommendation using vibe clusters.

### 📊 Internal Analytics Dashboard
- Logs:
  - Mood detection
  - Recommendation requests
  - Surprise clicks
- Displays event distribution and usage metrics.

### ⚡ Personalization Module
- Context-aware ranking
- Boosts recommendations based on mood and contextual signals

---

## 🛠 Tech Stack

- Python
- Streamlit (Frontend UI)
- Pandas & NumPy
- HuggingFace Transformers
- Scikit-learn
- TF-IDF + Cosine Similarity
- Git-based feature branching workflow

---

## 🎯 Project Goal

Vyber demonstrates how AI can bridge emotion understanding with intelligent content recommendation, combining NLP, similarity modeling, and personalization into a user-friendly interactive system.
