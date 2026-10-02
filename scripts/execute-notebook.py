"""用当前Python解释器启动独立内核，在临时目录从头执行入门Notebook。"""
from pathlib import Path
import sys,json,tempfile
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'notebooks/python-svm-start.ipynb'
nb=nbformat.read(source,as_version=4)
for cell in nb.cells:
    if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
with tempfile.TemporaryDirectory(prefix='svm-notebook-') as temporary:
    temp=Path(temporary);spec=temp/'kernels'/'svm-python';spec.mkdir(parents=True)
    (spec/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'SVM Python','language':'python'}),encoding='utf-8')
    manager=KernelManager(kernel_name='svm-python',kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(temp/'kernels')]))
    client=NotebookClient(nb,km=manager,timeout=120)
    try:
        client.execute(cwd=temporary)
    finally:
        if manager.has_kernel:manager.shutdown_kernel(now=True)
        manager.cleanup_resources()
nbformat.validate(nb)
assert all(cell.execution_count is not None for cell in nb.cells if cell.cell_type=='code')
assert not any(o.output_type=='error' for c in nb.cells if c.cell_type=='code' for o in c.outputs)
nbformat.write(nb,source)
print('Independent notebook executed and validated in a clean kernel and temporary directory.')
