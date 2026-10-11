import contextlib
import pathlib
import runpy
import traceback

root = pathlib.Path(__file__).resolve().parent
with (root / 'probe-admin-output.txt').open('w', encoding='utf-8') as output:
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        try:
            runpy.run_path(str(root / 'probe_diag.py'), run_name='__main__')
        except BaseException:
            traceback.print_exc()
