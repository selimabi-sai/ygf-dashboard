import json

# Credentials dosyasını oku
with open(r"C:\Users\PDS\Desktop\snap code\credentials.json", "r") as f:
    creds = json.load(f)

# Private key'deki gerçek newline'ları \\n olarak escape et
# TOML basic string'de \n = gerçek newline demek
# Biz literal \n istiyoruz ki Streamlit doğru okusun
pk = creds["private_key"]
pk_escaped = pk.replace("\n", "\\n")

toml = """[gcp_service_account]
type = "{type}"
project_id = "{project_id}"
private_key_id = "{private_key_id}"
private_key = "{private_key}"
client_email = "{client_email}"
client_id = "{client_id}"
auth_uri = "{auth_uri}"
token_uri = "{token_uri}"
auth_provider_x509_cert_url = "{auth_provider_x509_cert_url}"
client_x509_cert_url = "{client_x509_cert_url}"
universe_domain = "{universe_domain}"

[sheets]
sheet_id = "1RvQnrukTy8LVxWjskFYUzlpCOuAqEU9IH7YTFM2XJQI"
""".format(
    type=creds["type"],
    project_id=creds["project_id"],
    private_key_id=creds["private_key_id"],
    private_key=pk_escaped,
    client_email=creds["client_email"],
    client_id=creds["client_id"],
    auth_uri=creds["auth_uri"],
    token_uri=creds["token_uri"],
    auth_provider_x509_cert_url=creds["auth_provider_x509_cert_url"],
    client_x509_cert_url=creds["client_x509_cert_url"],
    universe_domain=creds.get("universe_domain", "googleapis.com"),
)

# Dosyaya yaz
with open(r"C:\Users\PDS\Desktop\claude\ygf\.streamlit\secrets.toml", "w", encoding="utf-8") as f:
    f.write(toml)

# Panoya kopyala
import subprocess
subprocess.run("clip", input=toml.encode("utf-8"), check=True)

print("TAMAM - secrets.toml yazildi ve panoya kopyalandi!")
print("Streamlit Secrets kutusuna Ctrl+V ile yapistir.")
