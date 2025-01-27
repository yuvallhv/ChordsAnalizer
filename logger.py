
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def log(msg):
    print(msg)


def warning(msg):
    print(f"{bcolors.WARNING}WARNING: {msg}{bcolors.ENDC}")


def notice(msg):
    print(f"{bcolors.OKGREEN}notice: {msg}{bcolors.ENDC}")
