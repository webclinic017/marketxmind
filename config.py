import os
from datetime import timedelta
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.urandom(24).hex()
    SALT_KEY='your-market-x-mind-salt'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:your-password@localhost/dbmarketxmind' 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'mail.your-domain.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'noresponse@your-domain.com'
    MAIL_PASSWORD = 'm4rketXm1nd'
    MAIL_DEFAULT_SENDER = ('MarketXmind', 'noresponse@your-domain.com')
    MAIL_DEFAULT_CC = ('MarketXmind', 'hello@your-domain.com')
    MAIL_DEFAULT_BCC = ('MarketXmind', 'support@your-domain.com')
    DATE_FORMAT = '%d-%m-%Y'
    UPLOAD_FOLDER = 'uploads'
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 1
    PDF_KIT_PATH =r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'    
    IMG_KIT_PATH =r'C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe'     
    #PDF_KIT_PATH ='/usr/bin/wkhtmltopdf'
    #IMG_KIT_PATH ='/usr/bin/wkhtmltoimage'
    SESSION_TYPE = 'filesystem'   
    SESSION_FILE_DIR = os.path.join(basedir, 'marketxmind_session')  
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    AIML_API_KEY="your-api-key" 
    AIML_MODEL_NAME="meta-llama/Meta-Llama-3-8B-Instruct" 
    AIML_MODEL_NAME_OPENAI="GPT-4o"
    AIML_ENDPOINT="https://api.aimlapi.com/v1"
    AIHF_KEY="your-hf-token"

