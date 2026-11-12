# Learning-Roadmap
 🗺️ AI Learning Roadmap Generator

A Streamlit app that builds a personalised, phase-by-phase learning roadmap using Google's Gemini Flash model.

## Features

- Enter any field or domain (e.g. Data Science, Web Development, Cybersecurity)
- Choose your skill level: Beginner, Intermediate or Advanced
- Set how long you have to learn (weeks or months) and your weekly study hours
- Get a roadmap with phases, topics, resources, hands-on projects and milestones
- Download the roadmap as a Markdown file

## Project structure

```
.
├── app.py             # Streamlit app
├── requirements.txt   # Python dependencies
└── README.md
```

## Run locally

1. Clone the repo and enter the folder:
   ```bash
   git clone https://github.com/<your-username>/<your-repo>.git
   cd <your-repo>
   ```
2. (Optional) create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Get a free API key from [Google AI Studio](https://aistudio.google.com/apikey).
5. Provide the key in one of these ways:
   - Create `.streamlit/secrets.toml`:
     ```toml
     GEMINI_API_KEY = "your-key-here"
     ```
   - or set an environment variable: `export GEMINI_API_KEY="your-key-here"`
   - or paste it into the sidebar when the app is running
6. Start the app:
   ```bash
   streamlit run app.py
   ```

## Configuration

| Setting          | Where                      | Default            |
|------------------|----------------------------|--------------------|
| `GEMINI_API_KEY` | secrets, env var or sidebar | none (required)    |
| `GEMINI_MODEL`   | secrets or env var         | `gemini-2.5-flash` |

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **Create app**, pick your repo and branch, and set the main file to `app.py`.
4. Open **Advanced settings → Secrets** and add:
   ```toml
   GEMINI_API_KEY = "your-key-here"
   ```
5. Click **Deploy**.

## Security

Never commit your API key. Keep `.streamlit/secrets.toml` out of Git (see `.gitignore`).

## Notes

AI-generated roadmaps can contain mistakes. Resource names are suggestions only, so verify them before relying on them.
