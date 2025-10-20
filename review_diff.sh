#!/bin/bash
REPORT_FILE="model_review.md"
MODEL="ai/granite-4.0-h-micro:3B"
echo "# LLM Code Review Summary" > "$REPORT_FILE"
# Get the latest commit SHA that actually modified tracked files
LATEST_COMMIT=$(git log --pretty=format:"%H" -n 1)
# Double check with HEAD^ to form diff range
PREV_COMMIT=$(git rev-parse "$LATEST_COMMIT"^)
# Get changed files from the latest commit
FILES=$(git diff --name-only --diff-filter=ACM "$PREV_COMMIT" "$LATEST_COMMIT")
if [ -z "$FILES" ]; then
echo "No relevant files changed in the last commit ($LATEST_COMMIT)."
exit 0 # Don't proceed if nothing relevant changed
fi
echo "Files changed in last commit ($LATEST_COMMIT):"
echo "$FILES"
# Aggregate code for prompt
AGGREGATED_CODE=""
for FILE in $FILES; do
if [ -f "$FILE" ]; then
 FILE_CONTENT=$(cat "$FILE")
 AGGREGATED_CODE+="\n\n### File: $FILE\n\`\`\`\n$FILE_CONTENT\n\`\`\`"
fi
done
# Enhanced AI prompt
PROMPT="You are a senior software engineer performing a rigorous, production-focused code review. Analyze the provided code changes and deliver a detailed, professional review that prioritizes code health, correctness, and long-term maintainability. 
📋 Review Principles: 

    Be specific and actionable: Always reference exact line numbers and filenames. Avoid vague statements.
    Prioritize impact: Focus first on security flaws, critical bugs, and performance bottlenecks—not stylistic preferences.
    Provide concrete fixes: When suggesting improvements, include clear, idiomatic code examples.
    Think like a maintainer: Consider how this code will evolve, be debugged, or onboard new developers.
     

🔍 Review Dimensions: 

    Security – Data exposure, injection risks, authZ/authN gaps, secrets handling  
    Correctness – Logic errors, race conditions, unhandled edge cases, undefined behavior  
    Performance – Inefficient algorithms, unnecessary allocations, blocking I/O, scalability concerns  
    Design & Architecture – Modularity, separation of concerns, appropriate use of patterns  
    Readability – Clear naming, minimal cognitive load, useful comments/docs  
    Testing – Coverage gaps, flaky or missing tests, poor assertions, lack of edge-case validation  
    Maintainability – Technical debt, duplication, unclear abstractions, upgrade risks
     

📤 Output Structure (per file): 

    Summary: 1–2 sentences on the nature and overall quality of changes  
    Critical Issues (🚨): High-severity problems that could cause outages, breaches, or data loss  
    Improvement Suggestions (💡): Specific, prioritized recommendations with code snippets  
    Strengths (✅): Well-implemented patterns, thoughtful design choices, or exemplary clarity

📌 Input:
$AGGREGATED_CODE
Deliver a concise yet thorough review that enables the author to ship safe, efficient, and maintainable code. Focus on the highest-leverage feedback that prevents future incidents or rework.
"

# Run the model
RESPONSE=$(docker model run "$MODEL" "$PROMPT" 2>/dev/null)

# Write to review file
echo -e "$RESPONSE" >> "$REPORT_FILE"
