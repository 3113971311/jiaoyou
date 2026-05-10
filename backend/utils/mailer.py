import smtplib
from email.mime.text import MIMEText

def get_smtp_config():
    from database import SessionLocal
    from models import SiteConfig
    db = SessionLocal()
    configs = {}
    for c in db.query(SiteConfig).filter(SiteConfig.config_key.like('smtp_%')).all():
        configs[c.config_key] = c.config_value
    db.close()
    port = int(configs.get('smtp_port', '465'))
    return {
        'host': configs.get('smtp_host', 'smtp.qq.com'),
        'port': port,
        'user': configs.get('smtp_user', ''),
        'pass': configs.get('smtp_pass', ''),
    }

def send_mail(to: str, subject: str, body: str):
    cfg = get_smtp_config()
    if not cfg['user']: return
    try:
        msg = MIMEText(body, "html", "utf-8")
        msg["From"] = cfg["user"]
        msg["To"] = to; msg["Subject"] = subject
        if cfg['port'] == 587:
            with smtplib.SMTP(cfg['host'], cfg['port']) as s:
                s.starttls()
                s.login(cfg['user'], cfg['pass'])
                s.sendmail(cfg['user'], [to], msg.as_string())
        else:
            with smtplib.SMTP_SSL(cfg['host'], cfg['port']) as s:
                s.login(cfg['user'], cfg['pass'])
                s.sendmail(cfg['user'], [to], msg.as_string())
    except Exception as e:
        raise e
