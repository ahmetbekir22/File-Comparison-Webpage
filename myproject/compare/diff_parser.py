import difflib

class DiffCode:
    SIMILAR = 0  # starts with '  '
    RIGHTONLY = 1  # starts with '+ '
    LEFTONLY = 2  # starts with '- '
    CHANGED = 3  # either three or four lines with the prefixes ('-', '+', '?'), ('-', '?', '+') or ('-', '?', '+', '?') respectively

class DifflibParser:
    def __init__(self, text1, text2):
        self.__text1 = text1
        self.__text2 = text2
        self.__diff = list(difflib.ndiff(self.__text1, self.__text2))
        self.__currentLineno = 0
        self.__left_line_no = 0
        self.__right_line_no = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.__currentLineno >= len(self.__diff):
            raise StopIteration

        result = {}
        currentLine = self.__diff[self.__currentLineno]
        code = currentLine[:2]
        line = currentLine[2:]

        result['line'] = line
        result['left_line_no'] = self.__left_line_no if code in ('  ', '- ') else "-"
        result['right_line_no'] = self.__right_line_no if code in ('  ', '+ ') else "-"

        if code == '  ':
            result['code'] = DiffCode.SIMILAR
            self.__left_line_no += 1
            self.__right_line_no += 1
        elif code == '- ':
            incrementalChange = self.__tryGetIncrementalChange(self.__currentLineno)
            if not incrementalChange:
                result['code'] = DiffCode.LEFTONLY
                self.__left_line_no += 1
            else:
                result['code'] = DiffCode.CHANGED
                result['leftchanges'] = incrementalChange['left'] if 'left' in incrementalChange else None
                result['rightchanges'] = incrementalChange['right'] if 'right' in incrementalChange else None
                result['newline'] = incrementalChange['newline']
                self.__currentLineno += incrementalChange['skiplines']
                self.__left_line_no += 1
                self.__right_line_no += 1
        elif code == '+ ':
            result['code'] = DiffCode.RIGHTONLY
            self.__right_line_no += 1

        self.__currentLineno += 1
        return result

    next = __next__  # for Python 2

    def __tryGetIncrementalChange(self, lineno):
        lineOne = self.__diff[lineno] if lineno < len(self.__diff) else None
        lineTwo = self.__diff[lineno + 1] if lineno + 1 < len(self.__diff) else None
        lineThree = self.__diff[lineno + 2] if lineno + 2 < len(self.__diff) else None
        lineFour = self.__diff[lineno + 3] if lineno + 3 < len(self.__diff) else None

        changes = {}
        # ('-', '?', '+', '?') case
        if lineOne and lineOne[:2] == '- ' and \
                lineTwo and lineTwo[:2] == '? ' and \
                lineThree and lineThree[:2] == '+ ' and \
                lineFour and lineFour[:2] == '? ':
            changes['left'] = [i for (i, c) in enumerate(lineTwo[2:]) if c in ['-', '^']]
            changes['right'] = [i for (i, c) in enumerate(lineFour[2:]) if c in ['+', '^']]
            changes['newline'] = lineThree[2:]
            changes['skiplines'] = 3
            return changes
        # ('-', '+', '?')
        elif lineOne and lineOne[:2] == '- ' and \
                lineTwo and lineTwo[:2] == '+ ' and \
                lineThree and lineThree[:2] == '? ':
            changes['right'] = [i for (i, c) in enumerate(lineThree[2:]) if c in ['+', '^']]
            changes['left'] = []
            changes['newline'] = lineTwo[2:]
            changes['skiplines'] = 2
            return changes
        # ('-', '?', '+')
        elif lineOne and lineOne[:2] == '- ' and \
                lineTwo and lineTwo[:2] == '? ' and \
                lineThree and lineThree[:2] == '+ ':
            changes['right'] = []
            changes['left'] = [i for (i, c) in enumerate(lineTwo[2:]) if c in ['-', '^']]
            changes['newline'] = lineThree[2:]
            changes['skiplines'] = 2
            return changes
        # no incremental change
        else:
            return None
