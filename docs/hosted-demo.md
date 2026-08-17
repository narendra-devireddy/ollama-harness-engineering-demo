# Hosted Demo Runbook

Use this when you cannot bring the development laptop and the office Mac restricts Python package installation.

## Recommendation

Run the demo in a hosted Linux environment and use the office Mac only as a browser or terminal viewer.

Best options:

1. GitHub Codespaces or VS Code Dev Containers.
2. Replit or another browser-based container workspace.
3. Small cloud VM such as EC2, Azure VM, GCP Compute Engine, or an internal Linux box.
4. Any machine with Docker installed.

Ollama Cloud runs the model inference. The hosted environment runs this repo, the harness, Strands, and the CLI.

```text
Office Mac browser/SSH
        ↓
Hosted container / VM / Codespace
        ↓
Harness demo code + Strands SDK
        ↓
Ollama Cloud model API
```

## Option A: Docker Anywhere

```bash
git clone <repo-url>
cd ollama-harness-engineering-demo
export OLLAMA_API_KEY=your_key

docker build -t harness-engineering-demo .
docker run --rm --env OLLAMA_API_KEY=$OLLAMA_API_KEY harness-engineering-demo
```

The default container command runs:

```bash
harness-demo compare --scenario incident-response
```

Run a single lane:

```bash
docker run --rm --env OLLAMA_API_KEY=$OLLAMA_API_KEY harness-engineering-demo   harness-demo run --scenario incident-response --lane strands-sdk
```

## Option B: GitHub Codespaces / Dev Container

Push this repo to GitHub, then create a Codespace. The repo includes `.devcontainer/devcontainer.json`, so the environment builds from the Dockerfile.

After it opens:

```bash
harness-demo compare --scenario incident-response
```

Add `OLLAMA_API_KEY` as a Codespaces secret before running live model calls.

## Option C: Cloud VM

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip

git clone <repo-url>
cd ollama-harness-engineering-demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

export OLLAMA_API_KEY=your_key
harness-demo compare --scenario incident-response
```

## What Runs Today

The current demo is deterministic and runs without API keys once dependencies are installed. This makes the management demo reliable.

The next implementation step is the live model lane:

```bash
harness-demo run --scenario incident-response --lane raw-strong --model gpt-oss:120b --live
harness-demo run --scenario incident-response --lane hand-built --model gpt-oss:20b --live
```

That live flag is not implemented yet. The repo is now packaged so we can add it without changing the deployment story.
