"""Worker local: executa uma única triagem e publica progresso em JSON."""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager

from report_contract import output_prefix
from scientific_pdf_report import gerar_relatorio_cientifico_pdf
from triage_jobs import CONFIG_FILE, STATUS_FILE, read_json, read_status, write_json_atomic


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
NOTEBOOK_PATH = APP_DIR / "notebook_disciplina_triagem_virtual_fluxo_proposto.ipynb"
LOCK_PATH = PROJECT_ROOT / "outputs" / ".catailab_triagem.lock"
STAGES = [
    "Preparando dados e configuração", "Consultando fontes disponíveis",
    "Calculando descritores", "Avaliando candidatos", "Construindo o ranking",
    "Executando análise de incerteza", "Gerando figuras e arquivos",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def update(job_dir: Path, state: str, stage: str, progress: int, **extra) -> None:
    current = read_status(job_dir)
    payload = {**current, **extra, "state": state, "stage": stage,
               "progress": max(0, min(100, int(progress))), "updated_at": now_iso()}
    write_json_atomic(job_dir / STATUS_FILE, payload)


def earliest_queued(base_dir: Path) -> Path | None:
    candidates = []
    for path in base_dir.glob("execucao_*"):
        status = read_status(path)
        if status.get("state") == "queued":
            candidates.append((status.get("created_at", ""), path.resolve()))
    return min(candidates, default=(None, None), key=lambda item: (item[0], str(item[1])))[1]


def acquire_lock(job_dir: Path) -> None:
    base_dir = job_dir.parent
    while True:
        if earliest_queued(base_dir) != job_dir.resolve():
            update(job_dir, "queued", "Na fila local; aguardando a execução anterior", 0)
            time.sleep(2)
            continue
        try:
            descriptor = os.open(str(LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump({"job_dir": str(job_dir.resolve()), "pid": os.getpid(), "created_at": now_iso()}, stream)
            return
        except FileExistsError:
            try:
                if time.time() - LOCK_PATH.stat().st_mtime > 35 * 60:
                    LOCK_PATH.unlink(missing_ok=True)
                    continue
            except OSError:
                pass
            update(job_dir, "queued", "Na fila local; uma triagem está em execução", 0)
            time.sleep(2)


def configuration_cell(config: dict, output_dir: Path) -> str:
    reaction, metals, promoter = config["reaction"], config["metals"], config.get("promoter", "")
    return f"""
import json, os, sys, subprocess, time, math, re, html, base64, requests
from getpass import getpass
from pathlib import Path
import numpy as np
import pandas as pd
CWD = Path.cwd()
PROJECT_ROOT = CWD.parent if CWD.name.lower() == "triagem" else CWD
PROJECT_DATA_DIR = PROJECT_ROOT / "outputs"
MP_API_KEY_SALVA = os.environ.get("MP_API_KEY", "").strip()
OUTPUT_DIR = Path({str(output_dir)!r}).expanduser().resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RANKING_FILE = PROJECT_DATA_DIR / "ranking_multicriterio_v2_incerteza_explicabilidade.csv"
reacao_usuario = {reaction!r}
n_metais_usuario = {len(metals)}
metais_usuario = {metals!r}
promotor_usuario = {promoter!r}
GARANTIR_METAIS_NOS_100_VIAVEIS = {bool(config.get('ensure_metals', True))!r}
print("Reação:", reacao_usuario)
print("Metais ativos:", metais_usuario)
print("Promotor:", promotor_usuario)
""".strip()


def prepare_notebook(config: dict, output_dir: Path):
    notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
    replaced_config = replaced_input = False
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        if "pasta_saida_usuario = input" in cell.source:
            cell.source = configuration_cell(config, output_dir)
            replaced_config = True
        elif "reacao_usuario = perguntar" in cell.source:
            cell.source = "# Entradas definidas pela interface Streamlit."
            replaced_input = True
    if not replaced_config or not replaced_input:
        raise RuntimeError("Não foi possível parametrizar o notebook base.")
    return notebook


def result_paths(output_dir: Path, reaction: str) -> dict[str, Path]:
    prefix = f"disciplina_fluxo_{reaction}"
    matches = []
    for summary in output_dir.glob("catailab_*_resumo.json"):
        metadata = read_json(summary)
        if metadata.get("reacao") == reaction and metadata.get("prefixo_arquivos"):
            matches.append(metadata["prefixo_arquivos"])
    if len(matches) == 1:
        prefix = matches[0]
    elif len(matches) > 1:
        raise RuntimeError("A execução produziu mais de um resumo incompatível.")
    return {name: output_dir / f"{prefix}_{suffix}" for name, suffix in {
        "prioritarios": "prioritarios_sintese.csv", "ranking": "ranking_condicoes.csv",
        "metricas": "metricas_triagem.csv", "monte_carlo": "monte_carlo_ranking.csv",
        "figuras": "figuras_geradas.csv", "dominio": "dominio_aplicabilidade.csv",
        "excel": "resultados.xlsx", "html": "relatorio.html",
        "pdf": "relatorio_cientifico.pdf", "resumo": "resumo.json",
    }.items()}


def execute_notebook(job_dir: Path, config: dict) -> Path:
    notebook = prepare_notebook(config, job_dir)
    total = max(1, len(notebook.cells))

    def cell_started(**kwargs):
        index = int(kwargs.get("cell_index", 0))
        fraction = index / total
        stage = STAGES[min(len(STAGES) - 1, int(fraction * len(STAGES)))]
        update(job_dir, "running", stage, 8 + int(78 * fraction))

    kernels = KernelSpecManager().find_kernel_specs()
    kernel_name = "python3" if "python3" in kernels else next(iter(kernels), None)
    if not kernel_name:
        raise RuntimeError("Nenhum kernel Jupyter Python está disponível para executar a triagem.")
    client = NotebookClient(notebook, timeout=1800, kernel_name=kernel_name,
                            resources={"metadata": {"path": str(APP_DIR)}}, on_cell_start=cell_started)
    client.execute()
    paths = result_paths(job_dir, config["reaction"])
    for key in ("resumo", "html", "prioritarios", "ranking", "excel"):
        if not paths[key].is_file():
            raise RuntimeError(f"Arquivo obrigatório ausente: {key}")
    update(job_dir, "running", "Gerando relatório científico em PDF", 92)
    gerar_relatorio_cientifico_pdf(paths, config["reaction"], config["metals"], config.get("promoter", ""))
    notebook_path = job_dir / f"{output_prefix(config['reaction'], config['metals'], config.get('promoter', ''))}_notebook_executado.ipynb"
    nbformat.write(notebook, notebook_path)
    return notebook_path


def main(job_dir: Path) -> int:
    config = read_json(job_dir / CONFIG_FILE)
    acquire_lock(job_dir)
    try:
        update(job_dir, "running", "Preparando a execução", 3, started_at=now_iso(), pid=os.getpid())
        if config.get("reaction") not in {"metanacao", "reforma", "rwgs"}:
            raise ValueError("Reação não suportada por esta plataforma.")
        artifact = execute_notebook(job_dir, config)
        update(job_dir, "completed", "Triagem concluída", 100, completed_at=now_iso(), artifact=str(artifact))
        return 0
    except Exception as error:
        update(job_dir, "failed", "A triagem não foi concluída", 100,
               completed_at=now_iso(), error=str(error), traceback="".join(traceback.format_exception(error))[-6000:])
        return 1
    finally:
        lock = read_json(LOCK_PATH)
        if lock.get("job_dir") == str(job_dir.resolve()):
            LOCK_PATH.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]).resolve()))
