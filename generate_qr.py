import sys
from pathlib import Path
import qrcode

url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:3000/#gateway'
out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('public/assets/judge-gateway-qr.png')
out.parent.mkdir(parents=True, exist_ok=True)
img = qrcode.make(url)
img.save(out)
print(f'QR created for: {url}\nSaved to: {out}')
