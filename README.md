# 🤖 AI Support Agent

An intelligent support agent framework built in Python for handling user queries, classifying intents, generating responses, and managing conversation flow. This modular setup is ideal for integrating AI assistance into customer support platforms or internal tools.

## 🚀 Getting Started

### 1. Clone and Install

```bash
git clone https://github.com/ariel11212321/ai-support-agent.git
cd ai-support-agent
pip install -r requirements.txt
```

### 2. Run the Agent

**Interactive Mode**
```bash
python main.py
```

**Single Question**
```bash
python main.py -q "Why was my account suspended?"
```

**Batch Mode**
```bash
python main.py -batch "Where's my order?,I need help with billing" -d
```

### 3. Input Validation

- Question must be 3–5000 characters
- Avoid code or suspicious patterns
- Only standard characters accepted

## 🧠 Features

- 🔍 **Input validation & sanitization**
- 📂 **Support category classification**
- 🧠 **AI-based response generation**
- 🚨 **Escalation detection**
- 📈 **Processing metrics & logging**
- 🧵 **Parallel processing with worker pool**
- 🛠️ **Modular and extendable**


Built by [Ariel](https://github.com/ariel11212321)