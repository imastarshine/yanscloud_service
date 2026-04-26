from enum import IntEnum


class ExitCode(IntEnum):
    OK = 0
    ERROR = 1
    LOCKED_NOW = 45
    ALREADY_LOCKED = 46
    DISK_UNAVAILABLE = 47
    PROVIDER_UNAVAILABLE = 48
