from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import subprocess

import os
import requests

from dotenv import load_dotenv
load_dotenv()

def create_github_repo(repo_name: str, private: bool = False) -> dict:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN no configurado en variables de entorno")

    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "name": repo_name,
        "private": private,
        "auto_init": False  
    }

    r = requests.post(url, headers=headers, json=payload)
    if r.status_code >= 300:
        raise ValueError(f"Error creando repo en GitHub: {r.status_code} {r.text}")
    return r.json()


def _run_git(repo: Path, args: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=str(repo),
        capture_output=True,
        text=True
    )

def _ensure_repo(repo: Path):
    if not repo.exists():
        raise ValueError(f"La ruta no existe: {repo}")
    cp = _run_git(repo, ["rev-parse", "--git-dir"])
    if cp.returncode != 0:
        raise ValueError(f"No es un repositorio git: {repo} ({cp.stderr.strip()})")

def init_repo(repo_path: Path, state: Dict[str, Any]) -> None:
    repo = Path(repo_path).expanduser().resolve()
    _ensure_repo(repo)
    state["repo"] = repo

def tool_git_create_branch(repo: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    branch = args["branch"]
    cp = _run_git(repo, ["checkout", "-b", branch])
    return {
        "repo": str(repo),
        "branch": branch,
        "stdout": cp.stdout.strip(),
        "stderr": cp.stderr.strip()
    }


def tool_git_init(_: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    repo_arg = args["repo_path"]
    repo_path = Path(repo_arg).expanduser()

    if not repo_path.is_absolute() and "/" not in repo_arg:
        base = Path.home() / "repos"
        base.mkdir(parents=True, exist_ok=True)
        repo_path = base / repo_arg

    repo_path = repo_path.resolve()
    repo_path.mkdir(parents=True, exist_ok=True)

    cp_init = _run_git(repo_path, ["init", "-b", "main"])


    return {
        "repo": str(repo_path),
        "stdout": cp_init.stdout.strip(),
        "stderr": cp_init.stderr.strip()
    }




def tool_git_create_file(repo: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    file_path = (repo / args["path"]).resolve()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(args["content"], encoding="utf-8")
    return {"repo": str(repo), "file": str(file_path), "status": "created"}


def tool_git_add(repo: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    cp = _run_git(repo, ["add"] + args["paths"])
    return {"repo": str(repo), "stdout": cp.stdout.strip(), "stderr": cp.stderr.strip()}


def tool_git_commit(repo: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    message = args["message"]
    author = args.get("author")
    cmd = ["commit", "-m", message]
    if author:
        name, email = author.split("<")
        email = email.strip(">").strip()
        cmd = ["-c", f"user.name={name.strip()}", "-c", f"user.email={email}"] + cmd
    cp = _run_git(repo, cmd)

    cp_branch = _run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
    if cp_branch.stdout.strip() == "master":
        _run_git(repo, ["branch", "-m", "main"])

    return {"repo": str(repo), "stdout": cp.stdout.strip(), "stderr": cp.stderr.strip()}



def tool_git_status(repo: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    cp = _run_git(repo, ["status", "--short"])
    return {"repo": str(repo), "status": cp.stdout.strip()}

# ---------- Tools de lectura ----------
def tool_git_list_branches(repo: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    remote = bool(args.get("remote", False))
    cp = _run_git(repo, ["branch", "-a"] if remote else ["branch"])
    if cp.returncode != 0:
        return {"error": cp.stderr.strip()}
    branches = [line.strip().lstrip("* ").strip() for line in cp.stdout.splitlines()]
    return {"repo": str(repo), "remote": remote, "branches": branches}

def tool_git_commits(repo: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    branch = args.get("branch") or "HEAD"
    limit = int(args.get("limit", 10))
    fmt = "%H|%an|%ad|%s"
    cp = _run_git(repo, ["log", branch, f"-{limit}", f"--pretty=format:{fmt}", "--date=iso"])
    if cp.returncode != 0:
        return {"error": cp.stderr.strip()}
    commits = []
    for line in cp.stdout.splitlines():
        h, an, ad, s = line.split("|", 3)
        commits.append({"hash": h, "author": an, "date": ad, "subject": s})
    return {"repo": str(repo), "branch": branch, "commits": commits}

def tool_git_show_file(repo: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    rev = args.get("rev") or "HEAD"
    path = args["path"]
    cp = _run_git(repo, ["show", f"{rev}:{path}"])
    if cp.returncode != 0:
        return {"error": cp.stderr.strip(), "rev": rev, "path": path}
    return {"repo": str(repo), "rev": rev, "path": path, "content": cp.stdout}

def tool_git_diff(repo: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    rev_a, rev_b = args["rev_a"], args["rev_b"]
    path = args.get("path")
    cmd = ["diff", rev_a, rev_b]
    if path:
        cmd += ["--", path]
    cp = _run_git(repo, cmd)
    return {"repo": str(repo), "rev_a": rev_a, "rev_b": rev_b, "diff": cp.stdout}

def tool_git_grep(repo: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    pattern = args["pattern"]
    rev = args.get("rev") or "HEAD"
    cp = _run_git(repo, ["grep", "-n", pattern, rev])
    if cp.returncode not in (0, 1):
        return {"error": cp.stderr.strip()}
    hits = []
    for line in cp.stdout.splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3:
            hits.append({"path": parts[0], "line": int(parts[1]), "match": parts[2]})
    return {"repo": str(repo), "rev": rev, "pattern": pattern, "matches": hits}


def tool_git_set_remote(repo: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    remote_url = args["remote_url"]  # ej: git@github.com:usuario/repo.git
    repo_name = remote_url.split("/")[-1].replace(".git", "")

    # Crear repo en GitHub si no existe
    try:
        created = create_github_repo(repo_name)
    except Exception as e:
        return {"error": f"No se pudo crear repo en GitHub: {e}"}

    # Configurar remoto en local
    cp = _run_git(repo, ["remote", "add", "origin", remote_url])
    return {
        "repo": str(repo),
        "remote_url": remote_url,
        "github_url": created.get("html_url"),
        "stdout": cp.stdout.strip(),
        "stderr": cp.stderr.strip()
    }



def tool_git_push(repo: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    branch = args.get("branch", "main")
    cp = _run_git(repo, ["push", "-u", "origin", branch])
    return {"repo": str(repo), "branch": branch, "stdout": cp.stdout.strip(), "stderr": cp.stderr.strip()}