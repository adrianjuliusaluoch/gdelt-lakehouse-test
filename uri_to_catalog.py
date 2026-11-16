from getpass import getpass
from urllib.parse import unquote, urlparse

u = urlparse(getpass("Paste the Neon URI (input is hidden): ").strip())
host = u.hostname.replace("-pooler", "")
print(f"host={host} port=5432 dbname={u.path.lstrip('/')} user={unquote(u.username)} "
      f"password={unquote(u.password)} sslmode=require")