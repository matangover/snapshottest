import six
import os
import shutil
from .sorted_dict import SortedDict
from .generic_repr import GenericRepr
from LANDR.Utilities.CompareAudio import main as compareAudio

def trepr(s):
    text = '\n'.join([repr(line).lstrip('u')[1:-1] for line in s.split('\n')])
    quotes, dquotes = "'''", '"""'
    if quotes in text:
        if dquotes in text:
            text = text.replace(quotes, "\\'\\'\\'")
        else:
            quotes = dquotes
    return "%s%s%s" % (quotes, text, quotes)


class Formatter(object):
    def __init__(self, imports=None):
        self.types = {}
        self.htchar = ' '*4
        self.lfchar = '\n'
        self.indent = 0
        self.imports = imports

    def set_formater(self, obj, callback):
        self.types[obj] = callback

    def __call__(self, value, **args):
        return self.format(value, self.indent)

    def format(self, value, indent):
        from .diff import PrettyDiff
        if value is None:
            return 'None'
        if isinstance(value, PrettyDiff):
            return self.format(value.obj, indent)
        if isinstance(value, dict):
            return self.format_dict(value, indent)
        elif isinstance(value, tuple):
            return self.format_tuple(value, indent)
        elif isinstance(value, list):
            return self.format_list(value, indent)
        elif isinstance(value, six.string_types):
            return self.format_str(value, indent)
        elif isinstance(value, (int, float, complex, bool, bytes, set, frozenset, GenericRepr)):
            return self.format_std_type(value, indent)
        elif isinstance(value, AudioSnapshot):
            if self.imports:
                self.imports['snapshottest.formatter'].add('AudioSnapshot')
                self.imports['os.path'].add('dirname')
                self.imports['os.path'].add('join')
            return repr(value)

        return self.format_object(value, indent)

    def format_str(self, value, indent):
        if '\n' in value:
            # Is a multiline string, so we use '''{}''' for the repr
            return trepr(value)

        # Snapshots are saved with `from __future__ import unicode_literals`,
        # so the `u'...'` repr is unnecessary, even on Python 2
        return repr(value).lstrip('u')

    def format_std_type(self, value, indent):
        return repr(value)

    def format_object(self, value, indent):
        if self.imports:
            self.imports['snapshottest'].add('GenericRepr')
        return repr(GenericRepr(value))

    def format_dict(self, value, indent):
        value = SortedDict(**value)
        items = [
            self.lfchar + self.htchar * (indent + 1) + self.format(key, indent) + ': ' +
            self.format(value[key], indent + 1)
            for key in value
        ]
        return '{%s}' % (','.join(items) + self.lfchar + self.htchar * indent)

    def format_list(self, value, indent):
        items = [
            self.lfchar + self.htchar * (indent + 1) + self.format(item, indent + 1)
            for item in value
        ]
        return '[%s]' % (','.join(items) + self.lfchar + self.htchar * indent)

    def format_tuple(self, value, indent):
        items = [
            self.lfchar + self.htchar * (indent + 1) + self.format(item, indent + 1)
            for item in value
        ]
        return '(%s)' % (','.join(items) + self.lfchar + self.htchar * indent)

musicEngineconfigFilePath = "/Users/Matan/Documents/code/MasteringEngineWorker/PythonMusicEngine/Config/mastering.engine_local.config"
class AudioSnapshot(object):
    def __init__(self, filename):
        self.filename = filename
        self.storedFilename = None

    def __repr__(self):
        return "AudioSnapshot(join(dirname(__file__), \"{}\"))".format(self.storedFilename)

    def __eq__(self, other):
        args = ["CompareAudio.py", self.filename, other.filename, "-c",
            musicEngineconfigFilePath, '-ie', os.path.splitext(self.filename)[1]]
        numDiffs = compareAudio(args)
        return sum(numDiffs) == 0

    def store(self, module, test_name):
        snapshotDir = os.path.splitext(module.filepath)[0]
        if not os.path.exists(snapshotDir):
            os.makedirs(snapshotDir)
        snapshotFile = os.path.join(snapshotDir, test_name)
        shutil.copy(self.filename, snapshotFile)
        self.storedFilename = snapshotFile