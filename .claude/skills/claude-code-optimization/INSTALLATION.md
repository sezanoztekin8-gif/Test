# Installation & Usage Guide

## Prerequisites
- Claude Code installed on your machine
- Access to the file system where Claude Code can load skills

## Installation Steps

### Step 1: Locate Your Skills Directory

Claude Code looks for skills in specific directories. Find yours:

```bash
# Check if a skills directory already exists
ls -la ~/.claude-code/skills  # Linux/Mac
# or
dir %USERPROFILE%\.claude-code\skills  # Windows

# If it doesn't exist, create it
mkdir -p ~/.claude-code/skills  # Linux/Mac
# or
mkdir %USERPROFILE%\.claude-code\skills  # Windows
```

Alternatively, you can store skills anywhere and reference them explicitly.

### Step 2: Install the Optimizer Skill

**Option A: Copy to default skills directory**
```bash
# Copy the skill directory
cp -r /path/to/claude-code-optimizer ~/.claude-code/skills/

# Verify installation
ls ~/.claude-code/skills/claude-code-optimizer/SKILL.md
```

**Option B: Use a custom location**
```bash
# Create a dedicated skills folder
mkdir -p ~/claude-skills
cp -r /path/to/claude-code-optimizer ~/claude-skills/

# You'll reference this path when starting Claude Code
```

### Step 3: Verify Installation

Check that the SKILL.md file is accessible:
```bash
cat ~/.claude-code/skills/claude-code-optimizer/SKILL.md
# Should display the skill content
```

## Usage

### Starting Claude Code with the Optimizer

**If installed in default location:**
```bash
# Claude Code should auto-detect skills in ~/.claude-code/skills
claude-code
```

**If using custom location:**
```bash
# Specify the skills directory
claude-code --skills ~/claude-skills/claude-code-optimizer

# Or specify multiple skills
claude-code --skills ~/claude-skills/claude-code-optimizer,~/claude-skills/other-skill
```

**Environment variable approach:**
```bash
# Set the skills path in your shell profile
export CLAUDE_CODE_SKILLS="$HOME/claude-skills/claude-code-optimizer"

# Then just run
claude-code
```

### Verifying the Skill is Active

At the start of your Claude Code session, ask:
```
Are you using the Token Optimizer skill?
```

Claude should confirm and can reference the optimization principles.

### Toggling the Skill On/Off

**During a session:**
```
Please temporarily ignore the Token Optimizer skill for this task - I need detailed explanations.
```

**Between sessions:**
```bash
# Run without skills
claude-code --no-skills

# Or remove from the skills directory temporarily
mv ~/.claude-code/skills/claude-code-optimizer ~/.claude-code/skills/claude-code-optimizer.disabled
```

## Running the Tests

### Quick Test (5 minutes)
Run just Test 1 (bug fix) to verify basic functionality:

```bash
# 1. Create test file
cat > calculator.py << 'EOF'
def add(a, b):
    return a + b

def divide(a, b):
    return a / b
EOF

# 2. Run WITHOUT skill (baseline)
claude-code --no-skills

# In Claude Code session:
# "Fix the zero division bug in calculator.py"
# Note the response length and style

# 3. Run WITH skill (optimized)  
claude-code --skills ~/.claude-code/skills/claude-code-optimizer

# In Claude Code session:
# "Fix the zero division bug in calculator.py"
# Compare response length and style
```

### Full Test Suite (30-60 minutes)
Follow the complete TEST_HARNESS.md procedures for comprehensive validation.

## Measuring Impact

### Method 1: Manual Observation
- Compare response lengths visually
- Note reduction in explanatory text
- Track subjective "time to completion"

### Method 2: Token Counting (Recommended)
Enable Claude Code debug logging:

```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export CLAUDE_CODE_DEBUG=1
export CLAUDE_CODE_LOG_LEVEL=debug

# Then run Claude Code
claude-code --skills ~/.claude-code/skills/claude-code-optimizer

# Check logs for token usage
tail -f ~/.claude-code/logs/$(ls -t ~/.claude-code/logs/ | head -1)
```

### Method 3: API Dashboard
1. Visit https://console.anthropic.com/
2. Navigate to Usage or API Keys section
3. Compare token usage before/after enabling skill
4. Filter by time periods corresponding to your test runs

### Method 4: Programmatic Analysis
Create a simple token counter:

```python
# token_analyzer.py
import json
import sys

def analyze_log(log_file):
    total_input = 0
    total_output = 0
    
    with open(log_file) as f:
        for line in f:
            if 'usage' in line.lower():
                # Parse API response logs
                try:
                    data = json.loads(line)
                    if 'usage' in data:
                        total_input += data['usage'].get('input_tokens', 0)
                        total_output += data['usage'].get('output_tokens', 0)
                except:
                    pass
    
    print(f"Input tokens: {total_input}")
    print(f"Output tokens: {total_output}")
    print(f"Total tokens: {total_input + total_output}")
    
    # Calculate cost (as of January 2025 pricing)
    input_cost = total_input / 1_000_000 * 3.00   # $3 per million
    output_cost = total_output / 1_000_000 * 15.00  # $15 per million
    print(f"Estimated cost: ${input_cost + output_cost:.4f}")

if __name__ == "__main__":
    analyze_log(sys.argv[1])
```

Usage:
```bash
python token_analyzer.py ~/.claude-code/logs/session-baseline.log
python token_analyzer.py ~/.claude-code/logs/session-optimized.log
```

## Troubleshooting

### Skill Not Loading
```bash
# Check Claude Code version
claude-code --version

# Verify skill file syntax
cat ~/.claude-code/skills/claude-code-optimizer/SKILL.md

# Check for error messages
claude-code --skills ~/.claude-code/skills/claude-code-optimizer --verbose
```

### Skill Seems Inactive
1. Explicitly ask Claude if the skill is active
2. Give it a task that should trigger optimization (simple file edit)
3. Check if response is concise vs. verbose
4. Review Claude Code documentation for skill loading changes

### Inconsistent Behavior
- Skills may be context-dependent
- Complex tasks may naturally require more tokens
- The skill includes "Strategic Verbosity" rules - sometimes verbose is correct

## Productization Preparation

### What's Needed for Public Release

1. **Documentation**
   - ✅ SKILL.md (core functionality)
   - ✅ TEST_HARNESS.md (validation)
   - ✅ INSTALLATION.md (this file)
   - ⬜ README.md (marketing/overview)
   - ⬜ CHANGELOG.md (version tracking)
   - ⬜ LICENSE (choose appropriate license)

2. **Testing & Validation**
   - ⬜ Run full test suite
   - ⬜ Document actual token savings
   - ⬜ Collect user feedback (start with your team)
   - ⬜ Test across different project types
   - ⬜ Validate with different Claude models

3. **Distribution**
   - ⬜ GitHub repository setup
   - ⬜ Package as installable artifact (npm, pip, or similar)
   - ⬜ CI/CD for automated testing
   - ⬜ Version tagging strategy

4. **Community & Support**
   - ⬜ Create issues template
   - ⬜ Contributing guidelines
   - ⬜ Example use cases
   - ⬜ Video demo or GIFs
   - ⬜ Discord/Slack community (optional)

5. **Integration Options**
   - ⬜ Submit to Anthropic's skill marketplace (if exists)
   - ⬜ MCP server version for broader compatibility
   - ⬜ VS Code extension wrapper
   - ⬜ API proxy service for enterprise

### Next Steps for Production

After validating token savings:

1. **Create Public Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial release of Claude Code Token Optimizer"
   git remote add origin https://github.com/yourusername/claude-code-optimizer
   git push -u origin main
   ```

2. **Add Installation Script**
   ```bash
   # install.sh
   #!/bin/bash
   SKILLS_DIR="${CLAUDE_CODE_SKILLS:-$HOME/.claude-code/skills}"
   mkdir -p "$SKILLS_DIR"
   cp -r claude-code-optimizer "$SKILLS_DIR/"
   echo "✅ Claude Code Token Optimizer installed to $SKILLS_DIR"
   ```

3. **Create npm/pip Package** (optional)
   For easier installation:
   ```bash
   npx install-claude-skill claude-code-optimizer
   # or
   pip install claude-code-optimizer
   ```

4. **Evangelize & Iterate**
   - Share on Twitter/LinkedIn with results
   - Post to r/ClaudeAI, Anthropic forums
   - Write blog post about token optimization
   - Gather feedback and refine

### Monetization Paths (Future)

- Free open-source version (community building)
- Premium version with advanced analytics
- Enterprise support contracts
- MCP server hosting service
- Integration with Recurly for usage-based billing 😉

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review TEST_HARNESS.md for validation procedures
3. File an issue on GitHub (once published)
4. Contact: [your contact method]

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-23  
**Compatible with**: Claude Code (latest)
