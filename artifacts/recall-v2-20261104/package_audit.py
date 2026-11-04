from pathlib import Path
import json, os, subprocess, sys, tarfile, zipfile
root=Path('artifacts/recall-v2-20261104')
wheel=next((root/'package').glob('*.whl'))
sdist=next((root/'package').glob('*.tar.gz'))
with zipfile.ZipFile(wheel) as archive: wheel_names=archive.namelist()
with tarfile.open(sdist) as archive: source_names=archive.getnames()
assert 'toruk_lm/source_spans.py' in wheel_names
assert not any('docs/internal/' in n.replace('\\','/') or n.endswith(('.pt','.safetensors')) for n in wheel_names+source_names)
target=(root/'wheel-install').resolve()
assert not target.exists()
subprocess.run([sys.executable,'-m','pip','install','--no-deps','--target',str(target),str(wheel)],check=True)
env=dict(os.environ,PYTHONPATH=str(target))
code="from pathlib import Path; import toruk_lm.source_spans as s; print(s.__file__); assert Path(s.__file__).resolve().is_relative_to(Path(__import__('os').environ['PYTHONPATH']))"
subprocess.run([sys.executable,'-c',code],env=env,check=True)
subprocess.run([sys.executable,'-m','toruk_lm','--help'],env=env,check=True,capture_output=True)
(root/'package-audit.json').write_text(json.dumps({'wheel':str(wheel),'sdist':str(sdist),'private_and_weights_excluded':True,'installed_import_and_cli':'PASS'},indent=2)+'\n')
print('Package privacy, installed import and CLI: PASS')
