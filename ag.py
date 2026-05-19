from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END


# -----------------------------
# State Definition
# -----------------------------
class RepoState(TypedDict, total=False):
    repo_name: str
    repo_path: str
    dependencies: Dict[str, str]
    vulnerabilities: List[Dict[str, Any]]
    risk_level: str

    fix_plan: List[Dict[str, Any]]
    resolution_attempts: int

    build_ok: bool
    tests_ok: bool

    pr_url: Optional[str]
    status: str
    error: Optional[str]


# -----------------------------
# Node 1: Init / Fetch Repo
# -----------------------------
def c(state: RepoState) -> RepoState:
    """
    Clone or update the repository locally.
    """
    repo_name = state["repo_name"]

    # Placeholder logic
    repo_path = f"/tmp/repos/{repo_name}"

    return {"repo_path": repo_path, "status": "repo_fetched"}


# -----------------------------
# Node 2: Scan Dependencies
# -----------------------------
def scan_dependencies(state: RepoState) -> RepoState:
    """
    Parse pyproject.toml + lockfile to extract dependencies.
    """
    # Placeholder parsed output
    dependencies = {"requests": "2.28.0", "urllib3": "1.26.0"}

    return {"dependencies": dependencies, "status": "dependencies_scanned"}


# -----------------------------
# Node 3: Fetch Vulnerabilities
# -----------------------------
def fetch_vulnerabilities(state: RepoState) -> RepoState:
    """
    Query GitHub Dependabot / OSV for vulnerabilities.
    """
    vulnerabilities = [
        {"package": "urllib3", "severity": "HIGH", "affected": "<1.26.5"}
    ]

    return {"vulnerabilities": vulnerabilities, "status": "vulns_fetched"}


# -----------------------------
# Node 4: Evaluate Risk
# -----------------------------
def evaluate_risk(state: RepoState) -> RepoState:
    vulns = state.get("vulnerabilities", [])

    high_or_critical = [v for v in vulns if v["severity"] in ["HIGH", "CRITICAL"]]

    if not high_or_critical:
        return {"risk_level": "LOW", "status": "no_action"}

    return {"risk_level": "HIGH", "status": "needs_fix"}


# -----------------------------
# Node 5: Plan Fixes (LLM step)
# -----------------------------
def plan_fixes(state: RepoState) -> RepoState:
    """
    LLM generates safe upgrade plan.
    """
    vulns = state["vulnerabilities"]

    # Placeholder deterministic plan
    fix_plan = [{"package": "urllib3", "target_version": "1.26.18"}]

    return {"fix_plan": fix_plan, "status": "fix_planned"}


# -----------------------------
# Node 6: Resolve Dependencies
# -----------------------------
def resolve_dependencies(state: RepoState) -> RepoState:
    """
    Apply version upgrades and run dependency resolution.
    """
    attempts = state.get("resolution_attempts", 0) + 1

    # Simulated failure on first attempt
    if attempts < 2:
        return {"resolution_attempts": attempts, "status": "resolution_failed"}

    return {"resolution_attempts": attempts, "status": "resolution_ok"}


# -----------------------------
# Node 7: Validate Build
# -----------------------------
def validate_build(state: RepoState) -> RepoState:
    """
    Run install + build validation.
    """
    return {"build_ok": True, "status": "build_validated"}


# -----------------------------
# Node 8: Run Tests
# -----------------------------
def run_tests(state: RepoState) -> RepoState:
    """
    Execute test suite.
    """
    return {"tests_ok": True, "status": "tests_passed"}


# -----------------------------
# Node 9: Create PR
# -----------------------------
def create_pr(state: RepoState) -> RepoState:
    """
    Push branch and create GitHub PR.
    """
    pr_url = f"https://github.com/{state['repo_name']}/pull/123"

    return {"pr_url": pr_url, "status": "pr_created"}


# -----------------------------
# Node 10: Notify / End
# -----------------------------
def notify(state: RepoState) -> RepoState:
    """
    Final reporting node.
    """
    return {"status": "completed"}


# -----------------------------
# Conditional Routing Logic
# -----------------------------
def route_after_risk(state: RepoState):
    return "plan_fixes" if state.get("risk_level") == "HIGH" else "notify"


def route_after_resolution(state: RepoState):
    if state["status"] == "resolution_failed":
        return "resolve_dependencies"

    return "validate_build"


def route_after_tests(state: RepoState):
    return "create_pr" if state.get("tests_ok") else "resolve_dependencies"


# -----------------------------
# Build Graph
# -----------------------------
workflow = StateGraph(RepoState)

workflow.add_node("fetch_repo", fetch_repo)
workflow.add_node("scan_dependencies", scan_dependencies)
workflow.add_node("fetch_vulnerabilities", fetch_vulnerabilities)
workflow.add_node("evaluate_risk", evaluate_risk)

workflow.add_node("plan_fixes", plan_fixes)
workflow.add_node("resolve_dependencies", resolve_dependencies)
workflow.add_node("validate_build", validate_build)
workflow.add_node("run_tests", run_tests)

workflow.add_node("create_pr", create_pr)
workflow.add_node("notify", notify)


# -----------------------------
# Edges (linear flow first)
# -----------------------------
workflow.add_edge(START, "fetch_repo")
workflow.add_edge("fetch_repo", "scan_dependencies")
workflow.add_edge("scan_dependencies", "fetch_vulnerabilities")
workflow.add_edge("fetch_vulnerabilities", "evaluate_risk")

# Conditional branching
workflow.add_conditional_edges(
    "evaluate_risk", route_after_risk, {"plan_fixes": "plan_fixes", "notify": "notify"}
)

workflow.add_edge("plan_fixes", "resolve_dependencies")

workflow.add_conditional_edges(
    "resolve_dependencies",
    route_after_resolution,
    {
        "resolve_dependencies": "resolve_dependencies",
        "validate_build": "validate_build",
    },
)

workflow.add_edge("validate_build", "run_tests")

workflow.add_conditional_edges(
    "run_tests",
    route_after_tests,
    {"create_pr": "create_pr", "resolve_dependencies": "resolve_dependencies"},
)

workflow.add_edge("create_pr", "notify")
workflow.add_edge("notify", END)


# Compile graph
app = workflow.compile()
