class DisallowedPath(Exception):
    """
    The path is not allowed by the robots.txt.
    """


class Unauthorized(Exception):
    """
    The user is not logged-in.
    """


class ParsingError(Exception):
    """
    An error occurred while parsing the page.
    """


class NonePage(ParsingError):
    """
    The parsed page is None.
    """


class NoTitle(ParsingError):
    """
    The parsed paged is missing a title.
    """


class NotFound(ParsingError):
    """
    The resource could not be found.
    """


class DisabledAccount(ParsingError):
    """
    The resource belongs to a disabled account.
    """


class ServerError(ParsingError):
    """
    The page contains a server error notice.
    """


class NoticeMessage(ParsingError):
    """
    A notice of unknown type was found in the page.
    """


def _raise_exception(err: BaseException):
    raise err
