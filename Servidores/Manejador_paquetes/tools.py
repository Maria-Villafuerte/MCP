from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import os
import shutil


def tool_fs_list_dir(base: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    path = (base / args.get("path", ".")).resolve()
    if not path.exists() or not path.is_dir():
        return {"error": f"No es un directorio válido: {path}"}
    files = []
    for f in path.iterdir():
        files.append({
            "name": f.name,
            "is_dir": f.is_dir(),
            "size": f.stat().st_size
        })
    return {"path": str(path), "files": files}


def tool_fs_read_file(base: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    path = (base / args["path"]).resolve()
    if not path.exists():
        return {"error": f"No existe: {path}"}
    if not path.is_file():
        return {"error": f"No es un archivo: {path}"}
    return {
        "path": str(path),
        "content": path.read_text(encoding="utf-8")
    }


def tool_fs_write_file(base: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    path = (base / args["path"]).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(args["content"], encoding="utf-8")
    return {"path": str(path), "status": "written"}


def tool_fs_delete(base: Path, args: Dict[str, Any]) -> Dict[str, Any]:
    path = (base / args["path"]).resolve()
    if not path.exists():
        return {"error": f"No existe: {path}"}
    if path.is_dir():
        shutil.rmtree(path)
        return {"path": str(path), "status": "directory deleted"}
    else:
        path.unlink()
        return {"path": str(path), "status": "file deleted"}