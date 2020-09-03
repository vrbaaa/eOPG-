from datetime import datetime, timedelta
class Config(object):
    TEMPLATES_AUTO_RELOAD = True
    SECRET_KEY = '5791628bb0b13ce0c676dfde280ba245'
    MONGO_URI = 'mongodb+srv://antonio:diehfwfksXAVZ8z@cluster0.lta3l.mongodb.net/opg?retryWrites=true&w=majority'
    CORS_HEADERS= 'Content-Type'
    ENV = 'development'
    RECAPTCHA_PUBLIC_KEY = '6LetNcUZAAAAAJ655ybKKhTj2o2PGuoJNozr4T14'
    RECAPTCHA_PRIVATE_KEY = '6LetNcUZAAAAANThAkBjYvQKGl7M661H1rIva9tI'
    DEBUG = False
    TESTING = False
    TRAJANJE_SESIJE_U_MINUTAMA = 1440
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=TRAJANJE_SESIJE_U_MINUTAMA) 

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True

    
class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
