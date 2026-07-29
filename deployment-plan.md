# Streamlit Deployment Plan: SecondSelf 🚀

This document outlines the detailed configuration, prerequisites, secrets management, and step-by-step procedure for deploying **SecondSelf** to **Streamlit Community Cloud**.

---

## 1. Prerequisites Checklist

Before initiating the deployment on the Streamlit Cloud Dashboard, ensure the following workspace files are configured:

1. **GitHub Repository**:
   - The project code must be pushed to a public or private GitHub repository.
2. **Requirements File (`requirements.txt`)**:
   - Outlines dependencies that Streamlit's serverless environment must install during build.
   - Verified dependencies list:
     ```text
     streamlit
     sentence-transformers
     groq
     numpy
     pyyaml
     requests
     beautifulsoup4
     scikit-learn
     ```
3. **Ignored Configuration (`.gitignore`)**:
   - Ensure you **do not** check in your local `.env` file or `.streamlit/secrets.toml` to GitHub to avoid exposing private API keys.

---

## 2. Secrets Management

Streamlit Community Cloud provides a secure vault to store secret key/value pairs which are injected as environment variables.

### App secrets configuration in Streamlit console:
When deploying, you will paste the following keys directly in the **Secrets** editor under the Advanced Settings pane:

```toml
# Streamlit Secrets (TOML format)
GROQ_API_KEY = "gsk_..."
HF_TOKEN = "hf_..." # Optional: to suppress Hugging Face rate-limit warnings
```

*Note: The application automatically pulls these variables via `os.environ` using our unified `lib/utils.py` loader.*

---

## 3. Deployment Procedure (Step-by-Step)

### Step 1: Push Code to GitHub
Ensure all code and folder structures are pushed to your target branch (e.g. `main`):
```bash
git init
git add .
git commit -m "Initialize SecondSelf Second Brain"
git branch -M main
git remote add origin https://github.com/your-username/secondself.git
git push -u origin main
```

### Step 2: Access Streamlit Cloud Dashboard
1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Sign in with your GitHub account.
3. Click on the **"New app"** button.

### Step 3: Configure Deployment Fields
- **Repository**: Choose your cloned repository (`your-username/secondself`).
- **Branch**: Select the deployment branch (`main`).
- **Main file path**: Point to the app entrypoint script: `app.py`.

### Step 4: Configure Advanced Secrets (Critical)
1. Click **"Advanced settings"** before deploying.
2. Under the **Secrets** text area, paste your TOML credentials (your Groq API key and optional Hugging Face token).
3. Click **"Save"**.

### Step 5: Boot & Verify
1. Click **"Deploy!"**.
2. Streamlit will launch a container, download your Python runtime dependencies, cache the SentenceTransformers model, and boot the application dashboard.
3. Once online, capture a note and test Q&A to confirm API key linkage works.

---

## 4. Architectural Constraints & Mitigations

### ⚠️ The Ephemeral Filesystem Challenge
Streamlit Community Cloud runs inside serverless Docker containers. This introduces a major constraint for local-first file operations:

- **Constraint**: Streamlit instances restart or shut down after inactivity. When this happens, the container is destroyed. Any raw staging files (`raw/`) or categorized markdown notes (`wiki/`) captured dynamically by users during the running session **will be permanently wiped**.
- **Result**: The app returns to its initial repository state (e.g. only containing files that were checked into git).

### Mitigation Solutions
Depending on your project's scaling goals, choose one of these mitigations:

#### Mitigation A: Read-Only Demo with Pre-populated Git Notes (Default Setup)
- Keep sample notes checked into GitHub (`wiki/` folder with seed data).
- Users can test capturing new items and observe the graph dynamically refresh during their session, accepting that session additions are temporary.

#### Mitigation B: Git-Backed Automation (Automated Commit Push)
- Update Python scripts to commit and push changes back to the GitHub repository when a note is captured.
- *Pros*: Completely free, persistent.
- *Cons*: Container needs write-access SSH keys to the GitHub repository.

#### Mitigation C: External Database Integration (Production Setup)
- Replace local file operations in `lib/utils.py` with an external database hook (e.g., Supabase, PostgreSQL, or a lightweight MongoDB cloud instance).
- Modify `load_all_notes` to fetch rows from a database table instead of reading directories.
- *Pros*: Secure, professional, scalable.
