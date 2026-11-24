"""Download public research assets; verify hashes and never overwrite files."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
REVISION = '590726b3765b1b90c5e53a17e3b1f77d92d3aa8a'

def fetch(url, path, expected):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        # Exclusive creation prevents overwriting another download. Interrupted
        # files are retained; subsequent runs detect the hash mismatch.
        with urlopen(url, timeout=120) as response, path.open('xb') as output:
            while chunk := response.read(1024*1024):
                output.write(chunk)
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != expected:
        raise ValueError(f'Hash mismatch for {path}. Move the file aside before retrying; it was not deleted.')
    print(f'Verified {path.name}')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', action='store_true', help='Also download the 1.1 GB Qwen model')
    args = parser.parse_args()
    report = json.loads((ROOT/'evaluation.json').read_text())
    for split, digest in report['sha256'].items():
        fetch(f'https://huggingface.co/datasets/ibm-research/argument_quality_ranking_30k/resolve/{REVISION}/{split}.csv', ROOT/'data'/f'{split}.csv', digest)
    if args.model:
        fetch('https://huggingface.co/unsloth/Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B-Q4_K_M.gguf',
              ROOT/'weights'/'Qwen3-1.7B-Q4_K_M.gguf',
              'b139949c5bd74937ad8ed8c8cf3d9ffb1e99c866c823204dc42c0d91fa181897')

if __name__ == '__main__':
    main()
