#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# ============================================================================
# Configuration
# ============================================================================
REPORT_FILE="${REPORT_FILE:-model_review.md}"
MODEL="${MODEL:-ai/granite-4.0-h-micro:3B}"
BASE_BRANCH="${BASE_BRANCH:-main}"
SECRET_PATTERNS_FILE="${SECRET_PATTERNS_FILE:-}"
MAX_FILE_SIZE_KB="${MAX_FILE_SIZE_KB:-500}"
SUPPORTED_EXTENSIONS="${SUPPORTED_EXTENSIONS:-.py .js .ts .go .java .rb .sh .yaml .yml .json .tf}"

# ============================================================================
# Logging utilities
# ============================================================================
log_info() { echo "[INFO] $*" >&2; }
log_warn() { echo "[WARN] $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }
log_fatal() { log_error "$@"; exit 1; }

# ============================================================================
# Preflight checks
# ============================================================================
command -v git >/dev/null 2>&1 || log_fatal "git is not installed or not in PATH"
command -v docker >/dev/null 2>&1 || log_fatal "docker is not installed or not in PATH"
git rev-parse --git-dir >/dev/null 2>&1 || log_fatal "Not inside a git repository"

# ============================================================================
# Branch detection and checkout
# ============================================================================
detect_and_checkout_branch() {
    local pr_branch=""
    
    # Priority 1: Explicit argument
    if [[ -n "${1:-}" ]]; then
        pr_branch="$1"
        log_info "Using branch from argument: $pr_branch"
    # Priority 2: GitHub Actions
    elif [[ -n "${GITHUB_HEAD_REF:-}" ]]; then
        pr_branch="$GITHUB_HEAD_REF"
        log_info "Detected GitHub Actions PR branch: $pr_branch"
    # Priority 3: GitLab CI
    elif [[ -n "${CI_MERGE_REQUEST_SOURCE_BRANCH_NAME:-}" ]]; then
        pr_branch="$CI_MERGE_REQUEST_SOURCE_BRANCH_NAME"
        log_info "Detected GitLab CI PR branch: $pr_branch"
    # Priority 4: Current branch (fallback)
    else
        pr_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
        if [[ -z "$pr_branch" || "$pr_branch" == "HEAD" ]]; then
            log_fatal "Could not determine branch name (detached HEAD?)"
        fi
        log_warn "No PR context detected, using current branch: $pr_branch"
    fi
    
    # Validate branch name is non-empty
    [[ -n "$pr_branch" ]] || log_fatal "Branch name is empty after detection"
    
    # Attempt checkout if not already on target branch
    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$current_branch" != "$pr_branch" ]]; then
        log_info "Checking out branch: $pr_branch"
        if ! git checkout "$pr_branch" 2>/dev/null; then
            log_fatal "Failed to checkout branch '$pr_branch'"
        fi
    else
        log_info "Already on branch: $pr_branch"
    fi
    
    echo "$pr_branch"
}

# ============================================================================
# Compute diff range
# ============================================================================
compute_diff_range() {
    local base_branch="$1"
    local pr_branch="$2"
    
    # Fetch latest base branch to ensure accurate comparison
    if ! git fetch origin "$base_branch" 2>/dev/null; then
        log_warn "Could not fetch origin/$base_branch, using local ref"
    fi
    
    # Find merge-base (common ancestor)
    local merge_base
    merge_base=$(git merge-base "origin/$base_branch" "$pr_branch" 2>/dev/null || \
                 git merge-base "$base_branch" "$pr_branch" 2>/dev/null || \
                 echo "")
    
    if [[ -z "$merge_base" ]]; then
        log_warn "Could not find merge-base, falling back to HEAD^ comparison"
        local latest_commit
        latest_commit=$(git rev-parse HEAD)
        local prev_commit
        prev_commit=$(git rev-parse "$latest_commit^" 2>/dev/null || echo "")
        [[ -n "$prev_commit" ]] || log_fatal "Cannot determine previous commit"
        echo "$prev_commit..$latest_commit"
    else
        log_info "Comparing against merge-base: $merge_base"
        echo "$merge_base..HEAD"
    fi
}

# ============================================================================
# Get changed files with filtering
# ============================================================================
get_changed_files() {
    local diff_range="$1"
    local files
    files=$(git diff --name-only --diff-filter=ACM "$diff_range" 2>/dev/null || echo "")
    
    if [[ -z "$files" ]]; then
        log_warn "No files changed in diff range: $diff_range"
        echo ""
        return
    fi
    
    # Filter by extension and size
    local filtered_files=""
    while IFS= read -r file; do
        # Check file exists
        [[ -f "$file" ]] || continue
        
        # Check extension
        local ext="${file##*.}"
        if [[ ! " $SUPPORTED_EXTENSIONS " =~ " .$ext " ]]; then
            log_info "Skipping unsupported file type: $file"
            continue
        fi
        
        # Check file size
        local size_kb
        size_kb=$(du -k "$file" | cut -f1)
        if [[ "$size_kb" -gt "$MAX_FILE_SIZE_KB" ]]; then
            log_warn "Skipping large file ($size_kb KB): $file"
            continue
        fi
        
        filtered_files+="$file"$'\n'
    done <<< "$files"
    
    echo "$filtered_files"
}

# ============================================================================
# Secret detection
# ============================================================================
scan_for_secrets() {
    local files="$1"
    local findings=""
    
    # Default patterns (basic regex for common secrets)
    local patterns=(
        'password\s*=\s*["\047][^"\047]{8,}["\047]'
        'api[_-]?key\s*=\s*["\047][A-Za-z0-9]{16,}["\047]'
        'secret\s*=\s*["\047][^"\047]{8,}["\047]'
        'token\s*=\s*["\047][A-Za-z0-9_-]{20,}["\047]'
        'AWS.*["\047][A-Z0-9]{20}["\047]'
        'sk_live_[0-9a-zA-Z]{24,}'
        'ghp_[0-9a-zA-Z]{36}'
        'PRIVATE\s+KEY'
    )
    
    # Load custom patterns if provided
    if [[ -n "$SECRET_PATTERNS_FILE" && -f "$SECRET_PATTERNS_FILE" ]]; then
        mapfile -t custom_patterns < "$SECRET_PATTERNS_FILE"
        patterns+=("${custom_patterns[@]}")
    fi
    
    while IFS= read -r file; do
        [[ -n "$file" ]] || continue
        for pattern in "${patterns[@]}"; do
            if grep -inE "$pattern" "$file" 2>/dev/null; then
                findings+="🔴 Potential secret in $file: matches pattern '$pattern'"$'\n'
            fi
        done
    done <<< "$files"
    
    echo "$findings"
}

# ============================================================================
# Aggregate code with proper escaping
# ============================================================================
aggregate_code() {
    local files="$1"
    local aggregated=""
    local file_count=0
    
    while IFS= read -r file; do
        [[ -n "$file" && -f "$file" ]] || continue
        
        # Read file with null byte handling
        local content
        content=$(cat "$file" | tr -d '\000')
        
        # Escape backticks for markdown
        content="${content//\`/\\\`}"
        
        aggregated+="\n\n### File: $file\n\`\`\`\n$content\n\`\`\`"
        ((file_count++))
    done <<< "$files"
    
    log_info "Aggregated $file_count files for review"
    echo "$aggregated"
}

# ============================================================================
# Generate LLM prompt
# ============================================================================
generate_prompt() {
    local aggregated_code="$1"
    local secret_findings="$2"
    
    cat <<EOF
You are a senior software engineer performing a rigorous, production-focused code review. Analyze the provided code changes and deliver a detailed, professional review that prioritizes code health, correctness, and long-term maintainability.

📋 Review Principles:
    • Be specific and actionable: Always reference exact line numbers and filenames. Avoid vague statements.
    • Prioritize impact: Focus first on security flaws, critical bugs, and performance bottlenecks—not stylistic preferences.
    • Provide concrete fixes: When suggesting improvements, include clear, idiomatic code examples.
    • Think like a maintainer: Consider how this code will evolve, be debugged, or onboard new developers.

🔍 Review Dimensions:
    • Security – Data exposure, injection risks, authZ/authN gaps, secrets handling
    • Correctness – Logic errors, race conditions, unhandled edge cases, undefined behavior
    • Performance – Inefficient algorithms, unnecessary allocations, blocking I/O, scalability concerns
    • Design & Architecture – Modularity, separation of concerns, appropriate use of patterns
    • Readability – Clear naming, minimal cognitive load, useful comments/docs
    • Testing – Coverage gaps, flaky or missing tests, poor assertions, lack of edge-case validation
    • Maintainability – Technical debt, duplication, unclear abstractions, upgrade risks

🔐 Pre-scan Results:
$secret_findings

📤 Output Structure (per file):
    • Summary: 1–2 sentences on the nature and overall quality of changes
    • Critical Issues (🚨): High-severity problems that could cause outages, breaches, or data loss
    • Improvement Suggestions (💡): Specific, prioritized recommendations with code snippets
    • Strengths (✅): Well-implemented patterns, thoughtful design choices, or exemplary clarity

📌 Input:
$aggregated_code

Deliver a concise yet thorough review that enables the author to ship safe, efficient, and maintainable code. Focus on the highest-leverage feedback that prevents future incidents or rework.
EOF
}

# ============================================================================
# Run LLM review
# ============================================================================
run_llm_review() {
    local prompt="$1"
    local response
    
    log_info "Running LLM model: $MODEL"
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        log_fatal "Docker daemon is not running"
    fi
    
    # Run model with timeout
    if ! response=$(timeout 300s docker model run "$MODEL" "$prompt" 2>&1); then
        log_fatal "LLM execution failed or timed out"
    fi
    
    echo "$response"
}

# ============================================================================
# Write report
# ============================================================================
write_report() {
    local pr_branch="$1"
    local diff_range="$2"
    local files="$3"
    local secret_findings="$4"
    local llm_response="$5"
    
    cat > "$REPORT_FILE" <<EOF
# LLM Code Review Summary

**Branch:** \`$pr_branch\`  
**Diff Range:** \`$diff_range\`  
**Generated:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")

---

## Files Reviewed
\`\`\`
$files
\`\`\`

---

## Security Pre-Scan
$( [[ -n "$secret_findings" ]] && echo "$secret_findings" || echo "✅ No potential secrets detected" )

---

## LLM Review
$llm_response

---

**Review completed successfully**
EOF
    
    log_info "Report written to: $REPORT_FILE"
}

# ============================================================================
# Main execution
# ============================================================================
main() {
    log_info "Starting PR code review"
    
    # 1. Detect and checkout branch
    local pr_branch
    pr_branch=$(detect_and_checkout_branch "${1:-}")
    
    # 2. Compute diff range
    local diff_range
    diff_range=$(compute_diff_range "$BASE_BRANCH" "$pr_branch")
    log_info "Using diff range: $diff_range"
    
    # 3. Get changed files
    local files
    files=$(get_changed_files "$diff_range")
    
    if [[ -z "$files" ]]; then
        log_warn "No reviewable files found in diff range"
        echo "# No Changes to Review" > "$REPORT_FILE"
        echo "**Branch:** \`$pr_branch\`" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        echo "No files were modified in the target diff range: \`$diff_range\`" >> "$REPORT_FILE"
        log_info "Empty review report written to: $REPORT_FILE"
        exit 0
    fi
    
    log_info "Files to review:"
    echo "$files" | while IFS= read -r f; do log_info "  - $f"; done
    
    # 4. Scan for secrets
    local secret_findings
    secret_findings=$(scan_for_secrets "$files")
    if [[ -n "$secret_findings" ]]; then
        log_error "Potential secrets detected!"
        echo "$secret_findings"
    fi
    
    # 5. Aggregate code
    local aggregated_code
    aggregated_code=$(aggregate_code "$files")
    
    # 6. Generate prompt
    local prompt
    prompt=$(generate_prompt "$aggregated_code" "$secret_findings")
    
    # 7. Run LLM review
    local llm_response
    llm_response=$(run_llm_review "$prompt")
    
    # 8. Write report
    write_report "$pr_branch" "$diff_range" "$files" "$secret_findings" "$llm_response"
    
    log_info "✅ Review completed successfully"
}

# Run main function
main "$@"
