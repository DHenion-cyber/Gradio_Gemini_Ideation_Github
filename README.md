---
title: CHIP400 Ideation
emoji: 🚀
colorFrom: red
colorTo: red
sdk: docker
app_port: 8501
tags:
- streamlit
pinned: false
short_description: Guided digital health startup brainstorm
---

# Welcome to Streamlit!

Edit `/src/streamlit_app.py` to customize this app to your heart's desire. :heart:

If you have any questions, checkout our [documentation](https://docs.streamlit.io) and [community
forums](https://discuss.streamlit.io).

## 🚀 Deployment (Hugging Face Spaces)

This chatbot app can be deployed to [Hugging Face Spaces](https://huggingface.co/spaces) using Streamlit.

### 📁 Recommended Files
Make sure your project includes:
- `app.py` or `streamlit_app.py` (main entry point)
- `.streamlit/config.toml`
- `.env` (you’ll upload this manually during setup)
- `requirements.txt`
- `.gitignore` and `.env.example`

### ⚙️ Environment Variables
Create a `.env` file with your own API keys based on `.env.example`, then upload it directly in the Hugging Face Space UI under **Files → Add file → Upload**.

Example variables:
GEMINI_API_KEY=your-gemini-key
PERPLEXITY_API_KEY=your-perplexity-key


### 🚢 Steps to Deploy
1. Push your repo to Hugging Face using Git or upload via the web UI.
2. Set your Space **Runtime** to `Streamlit`.
3. Upload your `.env` file (not tracked by Git).
4. Click “Restart Space” to launch.

---

### ✅ Example Layout
Your file tree should look like:
/project-root
│
├── streamlit_app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── .streamlit/
│ └── config.toml
├── README.md
└── ...

---
## Recent Changes

- **2025-06-16:** Removed obsolete test file `tests/test_value_prop_workflow.py` and simulation script `scripts/simulate_user_session.py` due to incompatibilities with the current codebase (e.g., missing methods in mocked objects, incorrect function imports). This cleanup ensures the project contains only relevant and working auxiliary files.

### 🧪 Testing and Continuous Integration
This project includes basic pytest tests and a GitHub Actions workflow (.github/workflows/test.yml) that runs tests automatically on every push.

To run tests locally:

bash
pytest
Test files are located in the /tests directory and cover core modules like llm_utils, search_utils, and database.
