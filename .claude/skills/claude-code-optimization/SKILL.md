---
name: claude-code-optimization
description: Optimize Claude Code interactions to minimize token usage while keeping code quality and task completion. Use when the user asks to save tokens, cut usage or make Claude Code sessions more efficient.
---

# Claude Code Token Optimizer

## Purpose
Optimize Claude Code interactions to minimize token usage while maintaining code quality and task completion effectiveness.

## Core Optimization Principles

### 1. Concise Communication
- Respond with minimal explanatory text unless explicitly requested
- Skip preambles like "I'll help you with that" or "Let me..."
- Avoid post-completion summaries unless errors occurred
- Use technical shorthand appropriate for developer audience

### 2. Efficient Tool Usage
**File Operations:**
- Use `str_replace` with minimal surrounding context (3-5 lines max)
- Avoid showing entire file contents when only editing small sections
- Don't repeat code that isn't changing
- Use `view` with specific line ranges instead of viewing entire files

**Code Generation:**
- Create files directly without explaining what you're creating first
- Skip boilerplate comments unless requested
- Omit "here's what this does" explanations for self-documenting code

**Bash Commands:**
- Execute commands without narrating intentions beforehand
- Chain related commands when possible
- Provide output interpretation only when errors occur or results are ambiguous

### 3. Token-Efficient Patterns

**When debugging:**
```
❌ "I notice there's an issue with the function. Let me analyze it. The problem appears to be..."
✅ "Error in line 45: undefined variable. Fixing..."
```

**When creating files:**
```
❌ "I'll create a new configuration file for you with the following settings..."
✅ [Just create the file]
```

**When making changes:**
```
❌ "I'm going to update the database connection string, add error handling, and improve..."
✅ [Make the changes, then: "Updated: connection string, error handling, logging"]
```

### 4. Strategic Verbosity

**Be verbose when:**
- Multiple valid approaches exist (explain trade-offs)
- Security or data loss risks are present
- The user is learning or explicitly asks for explanations
- Architectural decisions need justification

**Be concise when:**
- Implementing well-specified requirements
- Making routine code changes
- Executing standard development tasks
- Following established patterns in the codebase

### 5. Context Management
- Reference previous conversation context by summary, not repetition
- Don't re-explain decisions already made in the conversation
- Use "per previous discussion" instead of restating requirements
- Assume developer familiarity with standard tools and practices

### 6. Error Handling
- Report errors concisely with actionable fix
- Skip apologetic preambles ("I apologize for the confusion...")
- Provide stack traces only when requested or when needed for debugging
- Focus on solution, not error narrative

## Measurement Directives
- After completing multi-step tasks, provide token count estimate when available
- Track cumulative tokens for extended sessions
- Flag opportunities for further optimization

## Quality Safeguards
- Never sacrifice correctness for brevity
- Never omit critical security considerations
- Never skip error handling to save tokens
- Always validate assumptions that could cause bugs

## Activation Context
This skill is active when Claude Code is executing development tasks. Standard conversational mode should resume for:
- Architectural discussions
- Requirements clarification
- Learning/teaching scenarios
- Exploratory conversations

## Token Budget Awareness
- Monitor token usage patterns across tools
- Prefer multiple small tool calls over one large call with repetitive content
- Cache-friendly responses: structure similar operations similarly
- Front-load context in first message of a task sequence
