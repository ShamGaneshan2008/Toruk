"""Local offline repository verification only. No research fit or new model answers."""
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lifetime_job import controller_record
from lifetime_job_v2 import verify_seal

def main():
    output=RUN/"verification/execution"
    with controller_record(output):
        env=dict(os.environ);env["MYPYPATH"]=str(ROOT/"src")
        py=sys.executable
        commands=[
            ("ruff-lint",[py,"-B","-m","ruff","check","--no-cache","."]),
            ("ruff-format",[py,"-B","-m","ruff","format","--check","--no-cache","src","tests","scripts"]),
            ("mypy",[py,"-B","-m","mypy","--follow-imports=silent","--cache-dir",
                     str(RUN/"preflight-mypy"),"scripts/value_start_dev.py"]),
            ("frozen-sources",[py,"-B","scripts/check_frozen_sources.py"]),
            ("dependencies",[py,"-B","-m","pip","check"]),
            ("diff-check",["git","diff","--check"]),
            ("staged-diff-check",["git","diff","--cached","--check"]),
        ]
        checks=[]
        for name,command in commands:
            p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
            for suffix,text in (("stdout",p.stdout),("stderr",p.stderr)):
                with (output/f"{name}.{suffix}.log").open("x",encoding="utf-8",newline="\n") as f:
                    f.write(text)
            checks.append(dict(name=name,command=command,returncode=p.returncode))
            if p.returncode:
                break
        audit_path=RUN/"independent-audit.json"
        a=json.loads(audit_path.read_text())
        assert a["measurement_integrity"]=="PASS" and a["new_model_forwards"]==0
        verify_seal(RUN/"independent-audit-execution",expected_seal_sha256=
                    "21168c1e8de41321d2de2e19f0b201a6f0ad87400fecb8d82547784466037208")
        with (output/"independent-audit-copy.json").open("xb") as f:
            f.write(audit_path.read_bytes())
        tree=ast.parse((ROOT/"scripts/value_start_dev.py").read_text())
        imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        assert not any(m and any(b in m for b in ("transformers","ollama","chat_foundation","requests")) for m in imports)
        assert "toruk_lm.owned_lm" in imports
        assert "24 passed" in (RUN/"phase1-tests/output.log").read_text()
        assert "8 passed" in (RUN/"preparation/contracts/output.log").read_text()
        result=dict(status="PASS" if len(checks)==len(commands) and all(c["returncode"]==0 for c in checks) else "FAIL",
            commands=checks,python_type_lookup="MYPYPATH=D:/Toruk/src",
            focused_tests=dict(disposable_process_tests=24,new_numerical_data_gate_tests=8,
                               research_optimizer_updates_in_tests=0),
            independent_measurement_integrity="PASS",scientific_quality_decision=a["decision"],
            hosted_ci="NOT_RUN: uncommitted/unpushed new study; local checks only",
            complete_verify_py="NOT_RUN: installs, trains and generates unrelated research outputs",
            known_scope_exception="Pre-freeze native-shell search broadened; no held-out evaluation or experimental held-out inputs, but unrelated search access cannot be certified zero.",
            new_model_forwards=0,new_generated_answers=0)
        with (RUN/"checks.json").open("x",encoding="utf-8",newline="\n") as f:
            json.dump(result,f,indent=2);f.write("\n")
        print(json.dumps(result,indent=2))
        assert result["status"]=="PASS"

if __name__=="__main__":
    main()
