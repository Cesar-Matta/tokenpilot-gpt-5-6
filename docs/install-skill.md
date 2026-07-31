# Install only the TokenPilot skill

This installation is for people who want routing guidance inside Codex without running the TokenPilot server.

## What gets installed

Copy only this self-contained directory:

```text
skills/tokenpilot-router/
├── SKILL.md
├── agents/openai.yaml
└── references/default-policy.md
```

You do not need:

- `OPENAI_API_KEY`
- Python or FastAPI
- Docker
- `.env`
- the `app/` or `config/` server directories

## Install for your Codex user

Codex loads personal skills from `$HOME/.agents/skills`. A personal installation is available in Codex App, Codex CLI, and the Codex IDE extension.

### Windows PowerShell

Run these commands from the cloned TokenPilot repository:

```powershell
$target = Join-Path $HOME ".agents\skills\tokenpilot-router"
New-Item -ItemType Directory -Force -Path $target
Copy-Item -Recurse -Force -Path "skills\tokenpilot-router\*" -Destination $target
```

### macOS or Linux

```bash
mkdir -p "$HOME/.agents/skills/tokenpilot-router"
cp -R skills/tokenpilot-router/. "$HOME/.agents/skills/tokenpilot-router/"
```

Codex normally detects skill changes automatically. Restart Codex if the skill does not appear.

## Install for one repository only

Copy the same folder to:

```text
YOUR_REPOSITORY/.agents/skills/tokenpilot-router/
```

This keeps the skill limited to that repository and its subdirectories.

## Verify it

In Codex CLI or the Codex IDE extension, type `$` or open `/skills` and confirm that `tokenpilot-router` appears. Then invoke:

```text
$tokenpilot-router Recommend the appropriate GPT-5.6 tier for this task.
```

## What standalone mode can and cannot do

The skill can:

- inspect task complexity, risk, confidence, context, and domain;
- recommend Luna, Terra, or Sol;
- explain the reasoning and expected cost profile;
- help design or review a routing policy.

The skill cannot:

- change the model powering the current Codex conversation;
- make automatic OpenAI API calls;
- enforce a real spending limit;
- execute fallback requests.

Those execution features belong to the separate, optional TokenPilot server.
