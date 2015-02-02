import logging
from logging import handlers

def setup_logger(name, log_dir):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] "
                                     "[%(levelname)-5.5s]  %(message)s")

    file_handler =\
        handlers.RotatingFileHandler(log_dir + '/' + name + '.log',
                                     maxBytes=1048576,
                                     backupCount=2,)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logFormatter)
    logger.addHandler(console_handler)
    return logger
