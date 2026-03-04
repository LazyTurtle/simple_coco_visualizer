def print_progress_bar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """Call in a loop to create terminal progress bar

    Args:
        iteration (_type_): Required  : current iteration (Int)
        total (_type_): Required  : total iterations (Int)
        prefix (str, optional): Optional  : prefix string (Str)
        suffix (str, optional): Optional  : suffix string (Str)
        decimals (int, optional): Optional  : positive number of decimals in percent complete (Int)
        length (int, optional): Optional  : character length of bar (Int)
        fill (str, optional): Optional  : bar fill character (Str)
        printEnd (str, optional): Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()
