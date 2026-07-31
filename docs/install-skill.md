# Codex skill installation

The TokenPilot Agent Skill packages the routing policy as a self-contained
Codex skill. It runs within the host agent's existing session and has no
dependency on the TokenPilot API Server.

## Package contents

```text
skills/tokenpilot-router/
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
`-- references/
    `-- default-policy.md
```

The directory can be copied independently from the rest of the repository.
It requires no credentials, Python packages, container runtime, or background
process.

## Installation scope

Codex discovers skills from standard filesystem locations:

| Scope | Destination | Availability |
|---|---|---|
| Personal | `$HOME/.agents/skills/tokenpilot-router` | All local Codex projects |
| Repository | `<repository>/.agents/skills/tokenpilot-router` | That repository and its subdirectories |

Personal skills are available to Codex App, Codex CLI, and the Codex IDE
extension. Repository scope is appropriate when the routing policy should be
versioned with a specific codebase.

## Personal installation

Run the relevant command from the root of a cloned TokenPilot repository.

### Windows PowerShell

```powershell
$destination = Join-Path $HOME ".agents\skills\tokenpilot-router"
New-Item -ItemType Directory -Force -Path $destination | Out-Null
Copy-Item "skills\tokenpilot-router\*" $destination -Recurse -Force
```

### macOS and Linux

```bash
destination="$HOME/.agents/skills/tokenpilot-router"
mkdir -p "$destination"
cp -R skills/tokenpilot-router/. "$destination/"
```

## Repository installation

Copy the package to the target repository:

```text
<repository>/.agents/skills/tokenpilot-router/
```

The destination must contain `SKILL.md` directly. Avoid introducing an extra
nested `tokenpilot-router/tokenpilot-router` directory.

## Verification

1. Open the Codex skill selector with `/skills` or type `$` in the composer.
2. Confirm that `tokenpilot-router` is listed.
3. Invoke a routing assessment:

```text
$tokenpilot-router Assess the appropriate GPT-5.6 tier for this task.
```

Codex detects skill changes automatically in most environments. Restart the
client if the installed skill is not discovered.

## Operating boundary

The standalone skill:

- evaluates complexity, risk, confidence, context, domain, and budget;
- recommends Luna, Terra, or Sol with an explanation;
- supports routing-policy design and review;
- does not transmit prompts to the TokenPilot API Server;
- does not require `OPENAI_API_KEY`;
- does not change the model assigned to the current Codex session.

Automatic provider execution, cost enforcement, retries, and fallback calls
are capabilities of the separate API Server.

## Update

Replace the installed directory contents with the contents of the newer
`skills/tokenpilot-router` release, then verify that the skill remains visible
in Codex.
