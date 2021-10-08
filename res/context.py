import sys
from pathlib import Path

res_root = Path(__file__).parent.absolute().resolve()
elida_root = res_root.parent

if not str(elida_root) in sys.path:
    sys.path.append(str(elida_root))
