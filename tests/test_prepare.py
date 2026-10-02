import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_missing_source_fails_before_changing_outputs():
    target=ROOT/'assets/models.json'
    before=target.stat().st_mtime_ns
    result=subprocess.run([sys.executable,str(ROOT/'scripts/prepare.py'),'--heart-source',str(ROOT/'data/not-a-source.csv')],capture_output=True)
    assert result.returncode != 0
    assert target.stat().st_mtime_ns == before
