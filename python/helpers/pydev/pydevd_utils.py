import traceback
import os

try:
    from urllib import quote
except:
    from urllib.parse import quote

import pydevd_constants

def to_number(x):
    if is_string(x):
        try:
            n = float(x)
            return n
        except ValueError:
            pass

        l = x.find('(')
        if l != -1:
            y = x[0:l-1]
            #print y
            try:
                n = float(y)
                return n
            except ValueError:
                pass
    return None

def compare_object_attrs(x, y):
    try:
        if x == y:
            return 0
        x_num = to_number(x)
        y_num = to_number(y)
        if x_num is not None and y_num is not None:
            if x_num - y_num<0:
                return -1
            else:
                return 1
        if '__len__' == x:
            return -1
        if '__len__' == y:
            return 1

        return x.__cmp__(y)
    except:
        if pydevd_constants.IS_PY3K:
            return (to_string(x) > to_string(y)) - (to_string(x) < to_string(y))
        else:
            return cmp(to_string(x), to_string(y))

def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K

def is_string(x):
    if pydevd_constants.IS_PY3K:
        return isinstance(x, str)
    else:
        return isinstance(x, basestring)

def to_string(x):
    if is_string(x):
        return x
    else:
        return str(x)

def print_exc():
    if traceback:
        traceback.print_exc()

def quote_smart(s, safe='/'):
    if pydevd_constants.IS_PY3K:
        return quote(s, safe)
    else:
        if isinstance(s, unicode):
            s =  s.encode('utf-8')

        return quote(s, safe)


def is_python(path):
    if path.endswith("'") or path.endswith('"'):
        path = path[1:len(path)-1]
    filename = os.path.basename(path)
    for name in ['python', 'jython', 'pypy']:
        if filename.find(name) != -1:
            return True

    return False

def patch_args(args):
    import sys
    new_args = []
    i = 0
    if len(args) == 0:
        return args

    if is_python(args[0]):
        new_args.append(args[0])
    else:
        return args

    i = 1
    while i < len(args):
        if args[i].startswith('-'):
            new_args.append(args[i])
        else:
            break
        i+=1

    for x in sys.original_argv:
        if sys.platform == "win32" and not x.endswith('"'):
            arg = '"%s"'%x
        else:
            arg = x
        new_args.append(arg)
        if x == '--file':
            break

    while i < len(args):
        new_args.append(args[i])
        i+=1

    return new_args

def new_spawnve(mode, file, args, env):
    import os
    return os.original_spawnve(mode, file, patch_args(args), env)

def new_fork():
    import os
    import sys
    child_process = os.original_fork()
    if child_process == 0:
        argv = sys.original_argv[:]
        import pydevd
        setup = pydevd.processCommandLine(argv)


#        pydevd.debugger.FinishDebuggingSession()
#        for t in pydevd.threadingEnumerate():
#            if hasattr(t, 'doKillPydevThread'):
#                t.killReceived = True
        import pydevd_tracing
        pydevd_tracing.RestoreSysSetTraceFunc()

        pydevd.dispatcher = pydevd.Dispatcher()
        pydevd.dispatcher.connect(setup)

        if pydevd.dispatcher.port is not None:
            port = pydevd.dispatcher.port
            pydevd.connected = False
            pydevd.settrace(setup['client'], port=port, suspend=False, overwrite_prev_trace=True)
    return child_process

def patch_new_process_functions():
    import os
    os.original_spawnve = os.spawnve
    os.spawnve = new_spawnve
    os.original_fork = os.fork
    os.fork = new_fork

