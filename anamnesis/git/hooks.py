import os
import stat
from pathlib import Path
from typing import Optional
from anamnesis.git.inspector import GitInspector
from anamnesis.memory.client import MemoryClient
from anamnesis.config import load_config, save_config, find_project_root

HOOK_SCRIPT = """#!/usr/bin/env bash
# Anamnesis Git Pre-Commit Hook
# Evaluates staged changes against Cognee memory graph

if command -v anamnesis >/dev/null 2>&1; then
    anamnesis hook run --stage pre-commit
else
    # Fallback to python execution if anamnesis CLI is in virtualenv
    python -m anamnesis.cli hook run --stage pre-commit 2>/dev/null || true
fi
"""

class HookManager:
    """Manages git hooks installation and pre-commit memory recall execution."""

    @staticmethod
    def get_hooks_dir(repo_root: Optional[Path] = None) -> Optional[Path]:
        root = repo_root or find_project_root()
        git_dir = root / ".git"
        if not git_dir.exists():
            return None
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        return hooks_dir

    @classmethod
    def install_pre_commit_hook(cls, repo_root: Optional[Path] = None) -> bool:
        hooks_dir = cls.get_hooks_dir(repo_root)
        if not hooks_dir:
            return False

        hook_path = hooks_dir / "pre-commit"
        with open(hook_path, "w", encoding="utf-8") as f:
            f.write(HOOK_SCRIPT)

        # Make executable
        st = os.stat(hook_path)
        os.chmod(hook_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        config = load_config(repo_root)
        config["hooks_installed"] = True
        save_config(config, repo_root)
        return True

    @classmethod
    def uninstall_hooks(cls, repo_root: Optional[Path] = None) -> bool:
        hooks_dir = cls.get_hooks_dir(repo_root)
        if not hooks_dir:
            return False

        hook_path = hooks_dir / "pre-commit"
        if hook_path.exists():
            try:
                hook_path.unlink()
            except Exception:
                pass

        config = load_config(repo_root)
        config["hooks_installed"] = False
        save_config(config, repo_root)
        return True

    @classmethod
    def execute_pre_commit_check(cls, repo_root: Optional[Path] = None) -> Dict[str, Any]:
        """
        [COGNEE PRIMITIVE: recall]
        Extracts staged files & diffs and queries Cognee memory graph.
        """
        root = repo_root or find_project_root()
        staged_files = GitInspector.get_staged_files(root)
        staged_diff = GitInspector.get_staged_diff(root)
        
        client = MemoryClient(root)
        warnings = []

        if staged_files or staged_diff:
            query = f"staged files: {' '.join(staged_files)} {staged_diff[:300]}"
            for file_path in staged_files:
                recalled = client.recall(query=query, file_context=file_path, top_k=3)
                for mem in recalled:
                    if mem not in warnings:
                        warnings.append(mem)

        return {
            "staged_files": staged_files,
            "warnings": warnings
        }
