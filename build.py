import os
import platform
import shlex
import shutil
import subprocess
import sys

if __name__ == '__main__':
    iswin = platform.system() == 'Windows'
    appname = 'jeopy'
    srcpath = 'src/' # do not remove trailing forward slash
    buildpath = 'build'
    exepath = ''

    options = []
    options.append('--onefile')
    options.append('--out=%s' % buildpath)
    if iswin:
        options.append('--noconsole')

    cmd = 'pyinstaller %s %s' % (
        ' '.join(options), os.path.join(srcpath, '%s.py' % appname))
    print cmd
    retcode = subprocess.call(shlex.split(cmd), shell=iswin)

    if retcode == 0:
        exe = ('%s.exe' if iswin else '%s') % appname
        shutil.copy(
            os.path.join(buildpath, 'dist', exe), os.path.join(exepath, exe))
