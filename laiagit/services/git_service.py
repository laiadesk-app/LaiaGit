from __future__ import annotations

from pathlib import Path

from git import GitCommandError, InvalidGitRepositoryError
from git import Repo as GitRepo

from laiagit.models import (
    BranchInfo,
    Conflict,
    ConflictFile,
    FileChange,
    FileStatus,
    Repo,
    RepoStatus,
)


class GitError(Exception):
    pass


class GitService:
    """Wrapper around GitPython that returns LaiaGit domain models."""

    def open(self, path: Path) -> GitRepo:
        try:
            return GitRepo(str(path))
        except InvalidGitRepositoryError as exc:
            raise GitError(f"Not a git repository: {path}") from exc

    def hydrate(self, repo: Repo) -> Repo:
        try:
            git_repo = self.open(repo.path)
            repo.current_branch = self._current_branch(git_repo)
            repo.branches = self._branches(git_repo)
            repo.has_remote = bool(git_repo.remotes)
            repo.changes = self._changes(git_repo)
            repo.ahead, repo.behind = self._ahead_behind(git_repo)
            repo.status = self._compute_status(git_repo, repo)
            repo.error = None
        except GitError as exc:
            repo.status = RepoStatus.ERROR
            repo.error = str(exc)
        except Exception as exc:  # noqa: BLE001 — Git ops can raise many things
            repo.status = RepoStatus.ERROR
            repo.error = f"{type(exc).__name__}: {exc}"
        return repo

    def _current_branch(self, git_repo: GitRepo) -> str | None:
        try:
            return git_repo.active_branch.name
        except TypeError:
            # detached HEAD
            return None

    def _branches(self, git_repo: GitRepo) -> list[BranchInfo]:
        current = self._current_branch(git_repo)
        branches: list[BranchInfo] = []
        for head in git_repo.heads:
            upstream_name: str | None = None
            ahead = behind = 0
            tracking = head.tracking_branch()
            if tracking is not None:
                upstream_name = tracking.name
                try:
                    ahead = sum(1 for _ in git_repo.iter_commits(f"{tracking.name}..{head.name}"))
                    behind = sum(1 for _ in git_repo.iter_commits(f"{head.name}..{tracking.name}"))
                except GitCommandError:
                    ahead = behind = 0
            branches.append(
                BranchInfo(
                    name=head.name,
                    is_current=(head.name == current),
                    is_remote=False,
                    upstream=upstream_name,
                    ahead=ahead,
                    behind=behind,
                )
            )
        branches.sort(key=lambda b: (not b.is_current, b.name.lower()))
        return branches

    def _changes(self, git_repo: GitRepo) -> list[FileChange]:
        changes: list[FileChange] = []
        seen: set[tuple[str, bool]] = set()

        for entry in git_repo.index.diff(None):
            path = entry.b_path or entry.a_path
            if not path:
                continue
            status = self._diff_index_to_status(entry.change_type)
            key = (path, False)
            if key in seen:
                continue
            seen.add(key)
            changes.append(FileChange(path=path, status=status, staged=False))

        try:
            for entry in git_repo.index.diff("HEAD"):
                path = entry.b_path or entry.a_path
                if not path:
                    continue
                status = self._diff_index_to_status(entry.change_type)
                key = (path, True)
                if key in seen:
                    continue
                seen.add(key)
                changes.append(FileChange(path=path, status=status, staged=True))
        except (GitCommandError, ValueError):
            # No commits yet, or diff vs HEAD failed; ignore.
            pass

        for path in git_repo.untracked_files:
            key = (path, False)
            if key in seen:
                continue
            seen.add(key)
            changes.append(FileChange(path=path, status=FileStatus.UNTRACKED, staged=False))

        try:
            unmerged = git_repo.index.unmerged_blobs()
            for path in unmerged:
                key_unstaged = (path, False)
                key_staged = (path, True)
                changes = [c for c in changes if (c.path, c.staged) not in (key_unstaged, key_staged)]
                changes.append(FileChange(path=path, status=FileStatus.CONFLICTED, staged=False))
        except Exception:  # noqa: BLE001
            pass

        return changes

    def _diff_index_to_status(self, change_type: str) -> FileStatus:
        mapping = {
            "A": FileStatus.ADDED,
            "D": FileStatus.DELETED,
            "M": FileStatus.MODIFIED,
            "R": FileStatus.RENAMED,
            "T": FileStatus.MODIFIED,
        }
        return mapping.get(change_type, FileStatus.MODIFIED)

    def _ahead_behind(self, git_repo: GitRepo) -> tuple[int, int]:
        try:
            head = git_repo.active_branch
        except TypeError:
            return 0, 0
        tracking = head.tracking_branch()
        if tracking is None:
            return 0, 0
        try:
            ahead = sum(1 for _ in git_repo.iter_commits(f"{tracking.name}..{head.name}"))
            behind = sum(1 for _ in git_repo.iter_commits(f"{head.name}..{tracking.name}"))
            return ahead, behind
        except GitCommandError:
            return 0, 0

    def _compute_status(self, git_repo: GitRepo, repo: Repo) -> RepoStatus:
        if any(c.status == FileStatus.CONFLICTED for c in repo.changes):
            return RepoStatus.CONFLICT
        if repo.has_changes:
            return RepoStatus.PENDING
        if repo.ahead > 0:
            return RepoStatus.UNPUSHED
        if repo.behind > 0:
            return RepoStatus.BEHIND
        return RepoStatus.CLEAN

    def diff_for_file(self, path: Path, file_path: str, *, staged: bool = False) -> str:
        git_repo = self.open(path)
        try:
            if staged:
                return git_repo.git.diff("--cached", "--", file_path)
            return git_repo.git.diff("--", file_path)
        except GitCommandError as exc:
            raise GitError(str(exc)) from exc

    def full_diff(self, path: Path, *, staged_only: bool = False) -> str:
        git_repo = self.open(path)
        try:
            if staged_only:
                return git_repo.git.diff("--cached")
            staged = git_repo.git.diff("--cached")
            unstaged = git_repo.git.diff()
            return f"{staged}\n{unstaged}".strip()
        except GitCommandError as exc:
            raise GitError(str(exc)) from exc

    def stage(self, path: Path, files: list[str]) -> None:
        git_repo = self.open(path)
        try:
            git_repo.git.add("--", *files)
        except GitCommandError as exc:
            raise GitError(str(exc)) from exc

    def unstage(self, path: Path, files: list[str]) -> None:
        git_repo = self.open(path)
        try:
            git_repo.git.reset("HEAD", "--", *files)
        except GitCommandError as exc:
            raise GitError(str(exc)) from exc

    def commit(self, path: Path, message: str) -> str:
        if not message.strip():
            raise GitError("Commit message cannot be empty")
        git_repo = self.open(path)
        try:
            commit = git_repo.index.commit(message)
            return commit.hexsha
        except GitCommandError as exc:
            raise GitError(str(exc)) from exc

    def push(self, path: Path, remote: str = "origin", branch: str | None = None) -> str:
        git_repo = self.open(path)
        if not git_repo.remotes:
            raise GitError("Repository has no configured remote")
        if branch is None:
            try:
                branch = git_repo.active_branch.name
            except TypeError as exc:
                raise GitError("Cannot push from a detached HEAD") from exc
        try:
            push_info = git_repo.remote(remote).push(branch)
            messages = [pi.summary.strip() for pi in push_info if pi.summary]
            return "; ".join(messages) or "ok"
        except GitCommandError as exc:
            raise GitError(str(exc)) from exc

    def begin_merge(self, path: Path, source_branch: str) -> Conflict | None:
        """Run `git merge --no-commit --no-ff` for source_branch. Return Conflict if conflicts arise."""
        git_repo = self.open(path)
        try:
            target_branch = git_repo.active_branch.name
        except TypeError as exc:
            raise GitError("Cannot merge into detached HEAD") from exc
        try:
            git_repo.git.merge("--no-commit", "--no-ff", source_branch)
            return None
        except GitCommandError as exc:
            output = (exc.stderr or "") + (exc.stdout or "")
            if "CONFLICT" not in output and "conflict" not in output.lower():
                raise GitError(f"Merge failed: {output.strip()}") from exc
            return self._collect_conflict(git_repo, str(path), source_branch, target_branch)

    def abort_merge(self, path: Path) -> None:
        git_repo = self.open(path)
        try:
            git_repo.git.merge("--abort")
        except GitCommandError as exc:
            raise GitError(str(exc)) from exc

    def write_resolutions(self, path: Path, conflict: Conflict) -> None:
        for cf in conflict.files:
            if not cf.accepted or cf.resolution is None:
                continue
            target = path / cf.path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(cf.resolution.content, encoding="utf-8")

    def finalize_merge(self, path: Path, conflict: Conflict, message: str) -> str:
        git_repo = self.open(path)
        accepted_paths = [cf.path for cf in conflict.files if cf.accepted]
        if not accepted_paths:
            raise GitError("No accepted resolutions to commit")
        try:
            git_repo.git.add("--", *accepted_paths)
            commit = git_repo.index.commit(message)
            return commit.hexsha
        except GitCommandError as exc:
            raise GitError(str(exc)) from exc

    def _collect_conflict(
        self,
        git_repo: GitRepo,
        repo_path: str,
        source_branch: str,
        target_branch: str,
    ) -> Conflict:
        conflict = Conflict(
            repo_path=repo_path,
            source_branch=source_branch,
            target_branch=target_branch,
        )
        try:
            unmerged = git_repo.index.unmerged_blobs()
        except Exception as exc:  # noqa: BLE001
            raise GitError(f"Could not read conflict state: {exc}") from exc

        for file_path, stages in unmerged.items():
            head_content = ""
            incoming_content = ""
            base_content = ""
            for stage_no, blob in stages:
                try:
                    content = blob.data_stream.read().decode("utf-8", errors="replace")
                except Exception:  # noqa: BLE001
                    content = ""
                if stage_no == 1:
                    base_content = content
                elif stage_no == 2:
                    head_content = content
                elif stage_no == 3:
                    incoming_content = content
            conflict.files.append(
                ConflictFile(
                    path=file_path,
                    head_content=head_content,
                    incoming_content=incoming_content,
                    base_content=base_content,
                )
            )
        return conflict
