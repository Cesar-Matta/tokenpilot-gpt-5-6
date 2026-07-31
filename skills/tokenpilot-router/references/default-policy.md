# Default TokenPilot policy

| Tier | Model | Use | Default reasoning |
|---|---|---|---|
| Luna | `gpt-5.6-luna` | High-volume extraction, classification, summaries, routine generation | `low` |
| Terra | `gpt-5.6-terra` | Technical nuance, ambiguity, long context, medium risk | `medium` |
| Sol | `gpt-5.6-sol` | Difficult reasoning, high risk, safety-sensitive tasks | `high` |

Protected domain floors: legal, medical, financial, and security use Terra or higher; safety uses Sol. The calling application owns its definition of risk and task-specific quality validation.
