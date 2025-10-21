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
SUPPORTED_EXTENSIONS="${SUPPORTED_EXTENSIONS:-.py .js .ts .go .java .rb .sh .yaml .yml .json .tf .tsx .jsx}"
DRY_RUN="${DRY_RUN:-false}"

# ============================================================================
# Logging utilities
# ============================================================================
log_info() { echo "[INFO] $*" >&2; }
log_warn() { echo "[WARN] $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }
log_fatal() { log_error "$@"; exit 1; }

# ============================================================================
# Usage information
# ============================================================================
usage() {
    cat >&2 <<EOF
Usage: $0 [OPTIONS] [BRANCH_NAME]

Automated code review using LLM for pull requests.

OPTIONS:
    -h, --help              Show this help message
    -d, --dry-run           Generate template report without actual review
    -b, --base BRANCH       Base branch to compare against (default: main)
    -m, --model MODEL       LLM model to use (default: ai/granite-4.0-h-micro:3B)
    -o, --output FILE       Output report file (default: model_review.md)

ARGUMENTS:
    BRANCH_NAME            PR branch to review (optional, auto-detected in CI)

ENVIRONMENT VARIABLES:
    GITHUB_HEAD_REF                     GitHub Actions PR branch
    CI_MERGE_REQUEST_SOURCE_BRANCH_NAME GitLab CI PR branch
    BASE_BRANCH                         Base branch (default: main)
    DRY_RUN                             Set to 'true' for dry-run mode
    REPORT_FILE                         Output file path
    MODEL                               LLM model identifier

EXAMPLES:
    # Review specific branch
    $0 feature/new-api

    # GitHub Actions (auto-detects PR branch)
    $0

    # GitLab CI with custom base
    BASE_BRANCH=develop $0

    # Dry-run mode
    $0 --dry-run

    # Custom model and output
    $0 --model ai/custom:latest --output review.txt feature/bugfix
EOF
    exit 1
}

# ============================================================================
# Parse command-line arguments
# ============================================================================
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -b|--base)
                BASE_BRANCH="$2"
                shift 2
                ;;
            -m|--model)
                MODEL="$2"
                shift 2
                ;;
            -o|--output)
                REPORT_FILE="$2"
                shift 2
                ;;
            -*)
                log_error "Unknown option: $1"
                usage
                ;;
            *)
                # Positional argument (branch name)
                echo "$1"
                return
                ;;
        esac
    done
    echo ""
}

# ============================================================================
# Preflight checks
# ============================================================================
preflight_checks() {
    command -v git >/dev/null 2>&1 || log_fatal "git is not installed or not in PATH"
    git rev-parse --git-dir >/dev/null 2>&1 || log_fatal "Not inside a git repository"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        command -v docker >/dev/null 2>&1 || log_fatal "docker is not installed or not in PATH"
    fi
}

# ============================================================================
# Detect PR context
# ============================================================================
detect_pr_context() {
    local explicit_branch="${1:-}"
    local pr_branch=""
    local context_type="none"
    
    # Priority 1: Explicit argument
    if [[ -n "$explicit_branch" ]]; then
        pr_branch="$explicit_branch"
        context_type="explicit"
        log_info "Using explicitly provided branch: $pr_branch"
    
    # Priority 2: GitHub Actions
    elif [[ -n "${GITHUB_HEAD_REF:-}" ]]; then
        pr_branch="$GITHUB_HEAD_REF"
        context_type="github-actions"
        log_info "Detected GitHub Actions PR context"
        log_info "  PR Branch: $GITHUB_HEAD_REF"
        log_info "  Base Branch: ${GITHUB_BASE_REF:-unknown}"
        log_info "  Repository: ${GITHUB_REPOSITORY:-unknown}"
        log_info "  PR Number: ${GITHUB_REF##*/}"
        
        # Override base branch if provided by GitHub
        if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
            BASE_BRANCH="$GITHUB_BASE_REF"
            log_info "Using GitHub base branch: $BASE_BRANCH"
        fi
    
    # Priority 3: GitLab CI
    elif [[ -n "${CI_MERGE_REQUEST_SOURCE_BRANCH_NAME:-}" ]]; then
        pr_branch="$CI_MERGE_REQUEST_SOURCE_BRANCH_NAME"
        context_type="gitlab-ci"
        log_info "Detected GitLab CI PR context"
        log_info "  PR Branch: $CI_MERGE_REQUEST_SOURCE_BRANCH_NAME"
        log_info "  Target Branch: ${CI_MERGE_REQUEST_TARGET_BRANCH_NAME:-unknown}"
        log_info "  Project: ${CI_PROJECT_PATH:-unknown}"
        log_info "  MR IID: ${CI_MERGE_REQUEST_IID:-unknown}"
        
        # Override base branch if provided by GitLab
        if [[ -n "${CI_MERGE_REQUEST_TARGET_BRANCH_NAME:-}" ]]; then
            BASE_BRANCH="$CI_MERGE_REQUEST_TARGET_BRANCH_NAME"
            log_info "Using GitLab target branch: $BASE_BRANCH"
        fi
    
    # Priority 4: Current branch (fallback - requires warning)
    else
        pr_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
        if [[ -z "$pr_branch" || "$pr_branch" == "HEAD" ]]; then
            log_fatal "Could not determine branch name (detached HEAD?)"
        fi
        context_type="fallback"
        log_warn "⚠️  NO PR CONTEXT DETECTED"
        log_warn "  Using current branch: $pr_branch"
        log_warn "  This may produce incorrect results if not in a PR"
        log_warn "  Consider providing branch explicitly: $0 $pr_branch"
    fi
    
    # Validate branch name
    [[ -n "$pr_branch" ]] || log_fatal "Branch name is empty after detection"
    
    # Output context information
    echo "$pr_branch|$context_type"
}

# ============================================================================
# Checkout branch
# ============================================================================
checkout_branch() {
    local pr_branch="$1"
    local context_type="$2"
    
    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
    
    # Skip checkout if already on target branch
    if [[ "$current_branch" == "$pr_branch" ]]; then
        log_info "Already on branch: $pr_branch"
        return 0
    fi
    
    # Skip checkout in fallback mode (already on the branch)
    if [[ "$context_type" == "fallback" ]]; then
        log_warn "Skipping checkout in fallback mode"
        return 0
    fi
    
    # In CI environments, we're often already on the PR branch (detached HEAD or direct checkout)
    # Check if current HEAD matches the PR branch
    local current_commit
    current_commit=$(git rev-parse HEAD 2>/dev/null || echo "")
    
    # Try to resolve the PR branch commit (may not exist locally yet)
    local pr_branch_commit
    pr_branch_commit=$(git rev-parse "origin/$pr_branch" 2>/dev/null || \
                       git rev-parse "$pr_branch" 2>/dev/null || echo "")
    
    if [[ -n "$current_commit" && "$current_commit" == "$pr_branch_commit" ]]; then
        log_info "Already at PR branch commit (detached HEAD or direct checkout)"
        log_info "Current HEAD: $current_commit"
        return 0
    fi
    
    # Perform checkout
    log_info "Checking out branch: $pr_branch"
    
    # First, try direct checkout (branch exists locally)
    if git checkout "$pr_branch" 2>/dev/null; then
        log_info "Successfully checked out local branch: $pr_branch"
        return 0
    fi
    
    # Branch doesn't exist locally, try fetching from origin
    log_info "Branch not found locally, fetching from origin..."
    
    # Fetch the specific branch with full history
    if git fetch origin "$pr_branch:$pr_branch" 2>/dev/null; then
        log_info "Fetched branch from origin"
        if git checkout "$pr_branch" 2>/dev/null; then
            log_info "Successfully checked out: $pr_branch"
            return 0
        fi
    fi
    
    # Alternative: Create tracking branch from origin
    log_info "Attempting to create tracking branch from origin/$pr_branch"
    if git checkout -b "$pr_branch" "origin/$pr_branch" 2>/dev/null; then
        log_info "Created and checked out tracking branch: $pr_branch"
        return 0
    fi
    
    # Last resort: Check if we're already on the right commit (CI often does this)
    if [[ -n "$pr_branch_commit" && "$current_commit" == "$pr_branch_commit" ]]; then
        log_warn "Could not checkout branch name, but already at correct commit"
        log_info "Proceeding with current HEAD: $current_commit"
        return 0
    fi
    
    log_fatal "Failed to checkout or locate branch '$pr_branch'"
}

# ============================================================================
# Compute diff range
# ============================================================================
compute_diff_range() {
    local base_branch="$1"
    local pr_branch="$2"
    local context_type="$3"
    
    # Validate base branch exists
    if ! git rev-parse --verify "refs/heads/$base_branch" >/dev/null 2>&1 &&
       ! git rev-parse --verify "origin/$base_branch" >/dev/null 2>&1; then
        log_warn "Base branch '$base_branch' not found locally"
        log_info "Attempting to fetch from origin..."
        if ! git fetch origin "$base_branch:$base_branch" 2>/dev/null; then
            log_error "Failed to fetch base branch '$base_branch'"
            log_warn "Falling back to HEAD^ comparison"
            local latest_commit
            latest_commit=$(git rev-parse HEAD)
            local prev_commit
            prev_commit=$(git rev-parse "$latest_commit^" 2>/dev/null || echo "")
            [[ -n "$prev_commit" ]] || log_fatal "Cannot determine previous commit"
            echo "$prev_commit..$latest_commit|fallback"
            return
        fi
    fi
    
    # Fetch latest base branch for accurate comparison
    if git fetch origin "$base_branch" 2>/dev/null; then
        log_info "Successfully fetched latest '$base_branch' from origin"
    else
        log_warn "Could not fetch origin/$base_branch, using local ref"
    fi
    
    # Find merge-base (common ancestor)
    local merge_base
    local base_ref
    
    # Try origin first, then local
    if git rev-parse --verify "origin/$base_branch" >/dev/null 2>&1; then
        base_ref="origin/$base_branch"
    else
        base_ref="$base_branch"
    fi
    
    merge_base=$(git merge-base "$base_ref" "$pr_branch" 2>/dev/null || echo "")
    
    if [[ -z "$merge_base" ]]; then
        log_warn "Could not find merge-base between '$base_ref' and '$pr_branch'"
        
        # Self-comparison detection (critical issue)
        if [[ "$base_branch" == "$pr_branch" ]]; then
            log_error "⚠️  BASE AND PR BRANCHES ARE IDENTICAL"
            log_error "  This will produce an empty diff!"
            log_error "  Please specify a different base branch with --base or BASE_BRANCH"
            echo "SELF|error"
            return
        fi
        
        log_warn "Falling back to HEAD^ comparison"
        local latest_commit
        latest_commit=$(git rev-parse HEAD)
        local prev_commit
        prev_commit=$(git rev-parse "$latest_commit^" 2>/dev/null || echo "")
        [[ -n "$prev_commit" ]] || log_fatal "Cannot determine previous commit"
        echo "$prev_commit..$latest_commit|fallback"
    else
        local merge_base_short
        merge_base_short=$(git rev-parse --short "$merge_base")
        log_info "Found merge-base: $merge_base_short"
        log_info "Comparing: $base_ref ($merge_base_short) -> $pr_branch (HEAD)"
        echo "$merge_base..HEAD|merge-base"
    fi
}

# ============================================================================
# Get changed files with filtering
# ============================================================================
get_changed_files() {
    local diff_range="$1"
    
    # Handle self-comparison error
    if [[ "$diff_range" == "SELF" ]]; then
        echo ""
        return
    fi
    
    local files
    files=$(git diff --name-only --diff-filter=ACM "$diff_range" 2>/dev/null || echo "")
    
    if [[ -z "$files" ]]; then
        log_warn "No files changed in diff range: $diff_range"
        echo ""
        return
    fi
    
    # Filter by extension and size
    local filtered_files=""
    local skipped_count=0
    
    while IFS= read -r file; do
        # Check file exists
        if [[ ! -f "$file" ]]; then
            log_warn "File no longer exists: $file"
            continue
        fi
        
        # Check extension
        local ext="${file##*.}"
        if [[ ! " $SUPPORTED_EXTENSIONS " =~ " .$ext " ]]; then
            log_info "Skipping unsupported file type: $file"
            ((skipped_count++))
            continue
        fi
        
        # Check file size
        local size_kb
        size_kb=$(du -k "$file" | cut -f1)
        if [[ "$size_kb" -gt "$MAX_FILE_SIZE_KB" ]]; then
            log_warn "Skipping large file ($size_kb KB > $MAX_FILE_SIZE_KB KB): $file"
            ((skipped_count++))
            continue
        fi
        
        filtered_files+="$file"$'\n'
    done <<< "$files"
    
    if [[ $skipped_count -gt 0 ]]; then
        log_info "Skipped $skipped_count files due to size/type filters"
    fi
    
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
        'BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY'
    )
    
    # Load custom patterns if provided
    if [[ -n "$SECRET_PATTERNS_FILE" && -f "$SECRET_PATTERNS_FILE" ]]; then
        mapfile -t custom_patterns < "$SECRET_PATTERNS_FILE"
        patterns+=("${custom_patterns[@]}")
        log_info "Loaded ${#custom_patterns[@]} custom secret patterns"
    fi
    
    log_info "Scanning for secrets with ${#patterns[@]} patterns"
    
    while IFS= read -r file; do
        [[ -n "$file" ]] || continue
        for pattern in "${patterns[@]}"; do
            local matches
            matches=$(grep -inE "$pattern" "$file" 2>/dev/null || echo "")
            if [[ -n "$matches" ]]; then
                findings+="🔴 **$file** - Potential secret detected (pattern: \`${pattern:0:50}...\`)"$'\n'
                findings+="   Lines: $(echo "$matches" | cut -d: -f1 | paste -sd,)"$'\n\n'
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
        
        # Get file extension for syntax highlighting
        local ext="${file##*.}"
        
        aggregated+="\n\n### File: $file\n\`\`\`$ext\n$content\n\`\`\`"
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
$( [[ -n "$secret_findings" ]] && echo "$secret_findings" || echo "✅ No potential secrets detected in automated scan" )

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
    log_info "Invoking LLM (timeout: 300s)..."
    if ! response=$(timeout 300s docker model run "$MODEL" "$prompt" 2>&1); then
        local exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            log_fatal "LLM execution timed out after 300 seconds"
        else
            log_fatal "LLM execution failed with exit code $exit_code"
        fi
    fi
    
    log_info "LLM review completed successfully"
    echo "$response"
}

# ============================================================================
# Generate dry-run report
# ============================================================================
generate_dry_run_report() {
    local pr_branch="$1"
    local context_type="$2"
    
    cat > "$REPORT_FILE" <<EOF
# LLM Code Review - Dry Run Template

**Mode:** Dry Run (no actual review performed)  
**Current Branch:** \`$pr_branch\`  
**Context Type:** \`$context_type\`  
**Generated:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")

---

## 🔍 Dry Run Information

This is a template report generated in dry-run mode. No actual code review was performed.

### To perform a real review:

1. **In a PR context (GitHub Actions):**
   \`\`\`yaml
   - name: Run code review
     run: ./review.sh
   \`\`\`

2. **With explicit branch:**
   \`\`\`bash
   ./review.sh feature/my-branch
   \`\`\`

3. **With custom base branch:**
   \`\`\`bash
   BASE_BRANCH=develop ./review.sh feature/my-branch
   \`\`\`

---

## 📋 Current Configuration

- **Base Branch:** \`$BASE_BRANCH\`
- **Model:** \`$MODEL\`
- **Output File:** \`$REPORT_FILE\`
- **Max File Size:** ${MAX_FILE_SIZE_KB}KB
- **Supported Extensions:** $SUPPORTED_EXTENSIONS

---

## ⚙️ Environment Status

### Git Repository
- **Current Branch:** \`$pr_branch\`
- **Repository:** \`$(git config --get remote.origin.url 2>/dev/null || echo "unknown")\`
- **Latest Commit:** \`$(git rev-parse --short HEAD)\`

### CI Context
- **GitHub Actions:** $( [[ -n "${GITHUB_HEAD_REF:-}" ]] && echo "✅ Detected" || echo "❌ Not detected" )
- **GitLab CI:** $( [[ -n "${CI_MERGE_REQUEST_SOURCE_BRANCH_NAME:-}" ]] && echo "✅ Detected" || echo "❌ Not detected" )

---

## 🚀 Next Steps

Remove the \`--dry-run\` flag or unset \`DRY_RUN=false\` to perform an actual review.

\`\`\`bash
# Perform actual review
./review.sh feature/my-branch

# Or in CI (auto-detects)
./review.sh
\`\`\`
EOF
    
    log_info "Dry-run report written to: $REPORT_FILE"
}

# ============================================================================
# Write full report
# ============================================================================
write_report() {
    local pr_branch="$1"
    local context_type="$2"
    local diff_range="$3"
    local diff_method="$4"
    local files="$5"
    local secret_findings="$6"
    local llm_response="$7"
    
    # Generate context warning if fallback mode
    local context_warning=""
    if [[ "$context_type" == "fallback" ]]; then
        context_warning=$(cat <<EOF

## ⚠️ Context Warning

**No PR context detected.** This review was run on the current branch without explicit PR information.

### Recommendations:
- If this is a PR, run the script with the branch name: \`./review.sh $pr_branch\`
- In CI/CD, ensure PR environment variables are available:
  - GitHub Actions: \`GITHUB_HEAD_REF\`, \`GITHUB_BASE_REF\`
  - GitLab CI: \`CI_MERGE_REQUEST_SOURCE_BRANCH_NAME\`, \`CI_MERGE_REQUEST_TARGET_BRANCH_NAME\`
- Consider using \`--base\` flag to specify comparison branch explicitly

EOF
)
    fi
    
    # Generate diff method info
    local diff_info=""
    case "$diff_method" in
        merge-base)
            diff_info="✅ Accurate merge-base comparison"
            ;;
        fallback)
            diff_info="⚠️ Fallback mode (HEAD^..HEAD) - may miss changes"
            ;;
        error)
            diff_info="❌ Self-comparison detected - empty diff"
            ;;
    esac
    
    cat > "$REPORT_FILE" <<EOF
# LLM Code Review Summary

**Branch:** \`$pr_branch\`  
**Base Branch:** \`$BASE_BRANCH\`  
**Context Type:** \`$context_type\`  
**Diff Range:** \`$diff_range\`  
**Diff Method:** $diff_info  
**Generated:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")
$context_warning
---

## Files Reviewed

$( [[ -n "$files" ]] && echo "\`\`\`" && echo "$files" | sed '/^$/d' && echo "\`\`\`" || echo "_No files to review_" )

---

## 🔐 Security Pre-Scan

$( [[ -n "$secret_findings" ]] && echo "$secret_findings" || echo "✅ No potential secrets detected" )

---

## 🤖 LLM Review

$llm_response

---

**Review completed successfully**  
_Model: \`$MODEL\`_
EOF
    
    log_info "Report written to: $REPORT_FILE"
}

# ============================================================================
# Write empty report (no changes)
# ============================================================================
write_empty_report() {
    local pr_branch="$1"
    local context_type="$2"
    local diff_range="$3"
    local reason="$4"
    
    cat > "$REPORT_FILE" <<EOF
# No Changes to Review

**Branch:** \`$pr_branch\`  
**Base Branch:** \`$BASE_BRANCH\`  
**Context Type:** \`$context_type\`  
**Diff Range:** \`$diff_range\`  
**Generated:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")

---

## Status

$reason

### Possible Causes:
- No commits on the PR branch yet
- All changes are to unsupported file types
- Files exceed size limits (max: ${MAX_FILE_SIZE_KB}KB)
- Base and PR branches are identical

### Troubleshooting:
1. Verify branch has commits: \`git log $pr_branch --oneline\`
2. Check diff manually: \`git diff $BASE_BRANCH...$pr_branch\`
3. Ensure supported file types: $SUPPORTED_EXTENSIONS
4. Use \`--base\` flag if comparing against wrong branch

---

**No review performed**
EOF
    
    log_info "Empty review report written to: $REPORT_FILE"
}

# ============================================================================
# Main execution
# ============================================================================
main() {
    log_info "🚀 Starting LLM Code Review"
    log_info "Configuration: base=$BASE_BRANCH, model=$MODEL, dry-run=$DRY_RUN"
    
    # Parse arguments
    local explicit_branch
    explicit_branch=$(parse_args "$@")
    
    # Preflight checks
    preflight_checks
    
    # Dry-run mode
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Running in DRY-RUN mode"
        local context_info
        context_info=$(detect_pr_context "$explicit_branch")
        IFS='|' read -r pr_branch context_type <<< "$context_info"
        generate_dry_run_report "$pr_branch" "$context_type"
        log_info "✅ Dry-run completed"
        exit 0
    fi
    
    # 1. Detect PR context
    local context_info
    context_info=$(detect_pr_context "$explicit_branch")
    IFS='|' read -r pr_branch context_type <<< "$context_info"
    
    # 2. Checkout branch
    checkout_branch "$pr_branch" "$context_type"
    
    # 3. Compute diff range
    local diff_info
    diff_info=$(compute_diff_range "$BASE_BRANCH" "$pr_branch" "$context_type")
    IFS='|' read -r diff_range diff_method <<< "$diff_info"
    
    # Handle self-comparison error
    if [[ "$diff_method" == "error" ]]; then
        write_empty_report "$pr_branch" "$context_type" "N/A" \
            "❌ **Base and PR branches are identical** (\`$BASE_BRANCH\` == \`$pr_branch\`)  
Cannot compute diff when comparing a branch to itself.  
Please specify a different base branch using \`--base\` or \`BASE_BRANCH\` environment variable."
        log_error "Cannot proceed: self-comparison detected"
        exit 1
    fi
    
    log_info "Using diff range: $diff_range ($diff_method)"
    
    # 4. Get changed files
    local files
    files=$(get_changed_files "$diff_range")
    
    if [[ -z "$files" ]]; then
        write_empty_report "$pr_branch" "$context_type" "$diff_range" \
            "ℹ️ No reviewable files found in diff range: \`$diff_range\`"
        log_warn "No files to review"
        exit 0
    fi
    
    log_info "Files to review:"
    echo "$files" | while IFS= read -r f; do [[ -n "$f" ]] && log_info "  - $f"; done
    
    # 5. Scan for secrets
    log_info "Running security pre-scan..."
    local secret_findings
    secret_findings=$(scan_for_secrets "$files")
    if [[ -n "$secret_findings" ]]; then
        log_error "🔴 Potential secrets detected!"
        echo "$secret_findings" >&2
    fi
    
    # 6. Aggregate code
    log_info "Aggregating code for LLM..."
    local aggregated_code
    aggregated_code=$(aggregate_code "$files")
    
    # 7. Generate prompt
    local prompt
    prompt=$(generate_prompt "$aggregated_code" "$secret_findings")
    
    # 8. Run LLM review
    local llm_response
    llm_response=$(run_llm_review "$prompt")
    
    # 9. Write report
    write_report "$pr_branch" "$context_type" "$diff_range" "$diff_method" \
        "$files" "$secret_findings" "$llm_response"
    
    log_info "✅ Review completed successfully"
}

# Run main function
main "$@"
