from italianswirls.server import LS

if __name__ == "__main__":
    import logging
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(logging.FileHandler("/tmp/a.log"))
    LS.start_io()
