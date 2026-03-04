import os, datetime, logging

LOGGERS : dict[str,logging.Logger] = dict()

def get_logger(name:str, level:int = logging.INFO, out_folder:str|None = None, filename:str|None = None) -> logging.Logger:
    global LOGGERS
    if name in LOGGERS.keys():
        return LOGGERS[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    terminal_handler = logging.StreamHandler()
    terminal_handler.setLevel(logging.DEBUG)
    terminal_handler.setFormatter(formatter)
    logger.addHandler(terminal_handler)

    if out_folder is not None:
        create_folder(out_folder)
        log_file = \
            (name+"_"+datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") if filename is None else filename) +".log"
        log_file_path = os.path.join(out_folder, log_file)
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    LOGGERS[name] = logger
    logger.info(f"############################### Logging {logger.name} Started ###############################")
    return logger

def create_folder(folder_path:str):
    import pathlib
    """Create a folder in the provided path

    Args:
        folder_path (str): Path of the desired folder
    """
    pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)
