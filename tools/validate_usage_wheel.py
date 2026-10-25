"""Run existing wheel checks in an external, runtime-dependencies-only venv."""

import argparse
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pix-commit", help="Caller-declared wheel source commit")
    args = parser.parse_args()
    wheel, output = args.wheel.resolve(), args.output.resolve()
    source = Path(__file__).resolve().parents[1]
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pix-wheel-") as folder:
        outside = Path(folder)
        environment = outside / "venv"
        venv.EnvBuilder(with_pip=False).create(environment)
        python = environment / (
            "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
        )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "--python",
                str(python),
                "install",
                str(wheel),
            ],
            cwd=outside,
            check=True,
        )
        site = subprocess.check_output(
            [
                str(python),
                "-I",
                "-c",
                "import sysconfig; print(sysconfig.get_path('purelib'))",
            ],
            cwd=outside,
            text=True,
        ).strip()
        for checker in ("check_mining_wheel.py", "check_visualization_wheel.py"):
            subprocess.run(
                [
                    str(python),
                    "-I",
                    str(source / "tools" / checker),
                    "--wheel",
                    str(wheel),
                    "--site-packages",
                    site,
                    "--source-root",
                    str(source),
                    "--output",
                    str(output / checker.removesuffix(".py")),
                ],
                cwd=outside,
                check=True,
            )

        # Copy examples and inputs out too: no checkout import or runtime needed.
        fixture = outside / "pi_hub"
        shutil.copytree(source / "tests/fixtures/pi_hub", fixture)
        for name in ("chat_handover_demo.py", "adapter_contract_demo.py"):
            script = outside / name
            shutil.copy2(source / "examples" / name, script)
            command = [
                str(python),
                "-I",
                str(script),
                "--output",
                str(output / name.removesuffix(".py")),
            ]
            if name == "adapter_contract_demo.py":
                command += ["--fixture", str(fixture), "--wheel", str(wheel)]
                if args.pix_commit is not None:
                    command += ["--pix-commit", args.pix_commit]
            subprocess.run(command, cwd=outside, check=True)


if __name__ == "__main__":
    main()
