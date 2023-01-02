from logging import handlers, Logger
import logging
import os


class LogMessage():
    def __init__(self, save_path: str, tile):
        self.__save_path = save_path
        self.__filetitle = tile
        self.__log_format = '%(asctime)s [%(levelname)s] <%(module)s %(funcName)s %(lineno)d>\n%(message)s'
        self.logger = logging.getLogger(__name__)

    def __set_logger(self):
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(self.__log_format)
        if not os.path.exists(self.__save_path):
            os.makedirs(self.__save_path)
        # create file handler which logs even debug messages

        rh = logging.handlers.TimedRotatingFileHandler(
            os.path.join(self.__save_path, self.__filetitle), when="midnight", backupCount=5
        )

        rh.setFormatter(formatter)
        stream = logging.StreamHandler()
        # add the handlers to logger
        self.logger.addHandler(rh)
        self.logger.addHandler(stream)


    def get_logger(self) -> Logger:
        self.__set_logger()
        return self.logger


if __name__ == "__main__":
    log = LogMessage("./buy_sell_log","test.txt")

    a_log = log.get_logger()