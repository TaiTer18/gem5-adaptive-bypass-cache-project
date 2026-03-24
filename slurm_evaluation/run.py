import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
from uuid import UUID, uuid4
import zipfile

class gem5Run:
    """This class holds all of the info required to run gem5."""

    _id: UUID
    hash: str
    type: str
    name: str
    gem5_binary: Path
    run_script: Path
    params: Tuple[str, ...]
    timeout: int

    gem5_name: str
    script_name: str
    linux_name: str
    disk_name: str
    string: str

    outdir: Path

    linux_binary: Path
    disk_image: Path

    command: List[str]

    running: bool
    enqueue_time: float
    start_time: float
    end_time: float
    return_code: int
    kill_reason: str
    status: str
    pid: int
    task_id: Any

    @classmethod
    def _create(cls,
                name: str,
                gem5_binary: Path,
                run_script: Path,
                outdir: Path,
                params: Tuple[str, ...],
                timeout: int) -> 'gem5Run':
        run = cls()
        run.name = name
        run.gem5_binary = gem5_binary
        run.run_script = run_script
        run.params = params
        run.timeout = timeout

        run._id = uuid4()
        run.outdir = outdir.resolve()

        run.gem5_name = run.gem5_binary.parent.name
        run.script_name = run.run_script.stem

        run.running = False
        run.enqueue_time = time.time()
        run.start_time = 0.0
        run.end_time = 0.0
        run.return_code = 0
        run.kill_reason = ''
        run.status = "Created"
        run.pid = 0
        run.task_id = None
        run.results = None

        return run

    @classmethod
    def createSERun(cls,
                    name: str,
                    gem5_binary: str,
                    run_script: str,
                    outdir: str,
                    *params: str,
                    timeout: int = 60*60*4, # 4 Hours default per benchmark
                    ) -> 'gem5Run':
        """
        Creates a GEM5 SE Mode Run Object. Unpacks any added *params to the subprocess array.
        """
        run = cls._create(name, Path(gem5_binary), Path(run_script),
                          Path(outdir), params, timeout)

        run.string = f"{run.gem5_name} {run.script_name}"
        run.string += ' '.join(run.params)

        run.command = [
            str(run.gem5_binary),
            '-re', f'--outdir={run.outdir}',
            str(run.run_script)]
        run.command += list(params)
        
        run.hash = run._getHash()
        run.type = 'gem5 run'

        os.makedirs(run.outdir, exist_ok=True)
        run.dumpJson('info.json')

        return run

    def checkKernelPanic(self) -> bool:
        term_path = self.outdir / 'system.pc.com_1.device'
        if not term_path.exists():
            return False
        with open(term_path, 'rb') as f:
            try:
                f.seek(-1000, os.SEEK_END)
            except OSError:
                return False
            last = f.readlines()[-1].decode()
            if 'Kernel panic' in last:
                return True
            else:
                return False

    def _getSerializable(self) -> Dict[str, Union[str, UUID]]:
        d = vars(self).copy()
        for k,v in d.items():
            if isinstance(v, Path):
                d[k] = str(v)
        return d

    def _getHash(self) -> str:
        to_hash = []
        to_hash.append(str(self.run_script).encode())
        to_hash.append(' '.join(self.params).encode())
        return hashlib.md5(b''.join(to_hash)).hexdigest()

    @classmethod
    def _convertForJson(cls, d: Dict[str, Any]) -> Dict[str, str]:
        for k,v in d.items():
            if isinstance(v, UUID):
                d[k] = str(v)
        return d

    def dumpJson(self, filename: str) -> None:
        d = self._convertForJson(self._getSerializable())
        with open(self.outdir / filename, 'w') as f:
            json.dump(d, f)

    def dumpsJson(self) -> str:
        d = self._convertForJson(self._getSerializable())
        return json.dumps(d)

    def run(self, task: Any = None, cwd: str = '.') -> None:
        self.status = "Begin run"
        self.dumpJson('info.json')
        self.status = "Spawning"
        self.start_time = time.time()
        self.dumpJson('info.json')

        stderr_path = self.outdir / 'gem5_stderr.txt'
        stderr_file = open(stderr_path, 'w')
        proc = subprocess.Popen(self.command, cwd = cwd,
                                stderr=stderr_file)

        def handler(signum, frame):
            proc.kill()
            self.kill_reason = 'sigterm'
            self.dumpJson('info.json')

        signal.signal(signal.SIGTERM, handler)

        while proc.poll() is None:
            self.status = "Running"
            self.current_time = time.time()
            self.pid = proc.pid
            self.running = True

            if self.current_time - self.start_time > self.timeout:
                proc.kill()
                self.kill_reason = 'timeout'

            if self.checkKernelPanic():
                proc.kill()
                self.kill_reason = 'kernel panic'

            self.dumpJson('info.json')
            time.sleep(5)

        print("Done running {}".format(' '.join(self.command)))

        self.running = False
        self.end_time = time.time()
        self.return_code = proc.returncode
        stderr_file.close()

        if self.return_code == 0:
            self.status = "Finished"
        else:
            self.status = "Failed"
            # Print stderr contents so we can see the error in SLURM output
            try:
                with open(stderr_path, 'r') as f:
                    stderr_content = f.read()
                if stderr_content:
                    print(f"STDERR for {self.name}:\n{stderr_content}")
                else:
                    print(f"STDERR for {self.name}: (empty)")
            except Exception:
                pass

        self.dumpJson('info.json')

        print("Done storing the results of {}".format(' '.join(self.command)))

    def saveResults(self) -> None:
        with zipfile.ZipFile(self.outdir / 'results.zip', 'w',
                             zipfile.ZIP_DEFLATED) as zipf:
            for path in self.outdir.glob("**/*"):
                if path.name == 'results.zip': continue
                zipf.write(path, path.relative_to(self.outdir.parent))

    def __str__(self) -> str:
        return  self.string + ' -> ' + self.status
