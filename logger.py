import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("mymodule.log")
streamHandler = logging.StreamHandler()
logger.addHandler(file_handler)
logger.addHandler(streamHandler)