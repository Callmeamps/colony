# Ubiquitous Language

## Nest (Memory)

| Term            | Definition                                                                 | Aliases to avoid          |
| --------------- | -------------------------------------------------------------------------- | ------------------------- |
| **Nest**        | The hybrid memory system combining vector and graph-based retrieval.       | DB, Vector store          |
| **NestNode**    | A single unit of information stored within the Nest.                       | Fact, snippet, record     |
| **Crystal**     | A high-strength, frequently accessed NestNode promoted to permanent status. | Persistent memory         |
| **Strength**    | A value (0.0-1.0) representing the current relevance/recall level of a node. | Score, priority, weight   |
| **Decay**       | The process of reducing a node's Strength over time.                       | Forgetting, fading        |
| **Trauma**      | A metric indicating adversarial or dangerous content within a node.         | Risk, bad score           |

## Council (Routing)

| Term            | Definition                                                                 | Aliases to avoid          |
| --------------- | -------------------------------------------------------------------------- | ------------------------- |
| **Council**     | The orchestration layer that routes tasks to Clones.                       | Router, manager           |
| **Satellite**   | A specialized module that evaluates a task to provide a Ballot.            | Evaluator, sensor         |
| **Ballot**      | A ranked list of preferred Clones produced by a Satellite.                  | Vote, preference          |
| **Shaka**       | The STV (Single Transferable Vote) election process for picking a winner.   | Election, selector        |
| **Dictator**    | An emergency override that forces a specific state or behavior.            | Override, force-mode      |
| **Antennae**    | The adaptive prefetch mechanism that prepares Nest context for Clones.      | Context loader, prefetch  |

## Workers (Inference)

| Term            | Definition                                                                 | Aliases to avoid          |
| --------------- | -------------------------------------------------------------------------- | ------------------------- |
| **Clone**       | A specific model instance (Code, Chat, Voice) that executes tasks.         | Model, worker, labourer   |
| **Scout**       | A small model used for rapid urgency classification and direct answering.  | Fertilizer, classifier    |
| **York**        | The RAM governor that enforces resource limits on Clones.                  | RAM guard, governor       |
| **Zep**         | The short-term session memory storage for conversation history.            | Session DB, buffer        |

## Evolution (Learning)

| Term            | Definition                                                                 | Aliases to avoid          |
| --------------- | -------------------------------------------------------------------------- | ------------------------- |
| **Raid**        | A distillation process where a larger model is used to teach a Clone.      | Distillation, scrape      |
| **Drone**       | A background process that spawns new LoRA variants of Clones.               | Trainer, variant-gen      |
| **Valkyrie**    | The judge that evaluates and promotes new Clone variants.                  | Evaluator, promoter       |

## Relationships

- A **Satellite** produces a **Ballot** for a given task.
- **Shaka** processes multiple **Ballots** to select a winning **Clone**.
- **York** can trigger a **Dictator** (Resource) if RAM thresholds are breached.
- **Crystals** represent the peak of **NestNode** evolution through high **Strength**.

## Example dialogue

> **Dev:** "Does the **Council** wait for all **Satellites** before starting **Shaka**?"
> **Domain expert:** "Yes, but there's a timeout. If **York** sees high RAM, it might trigger a **Dictator** before **Shaka** even finishes."
> **Dev:** "If the **Clone** finishes the task, does the **Archivist** increase the **Strength** of the **Crystals** used?"
> **Domain expert:** "Only if it wasn't already a **Crystal**. For normal **NestNodes**, it adds a delta to the **Strength** to delay **Decay**."
> **Dev:** "And if **Valkyrie** rejects a **Drone** variant?"
> **Domain expert:** "Then the **Raid** results are discarded, and the **Clone** keeps its current weights."

## Flagged ambiguities

- "Labourer" was used in older specs for **Clone** — **Clone** is now the canonical term for task-executing models.
- "Fertilizer" was an alias for **Scout** — **Scout** is preferred for the role of rapid classification and direct answering.
- "Memory" is too vague — use **Nest** for long-term storage or **Zep** for short-term session state.
