import os
import sys

import pytest

from paste.cgiapp import CGIApplication, CGIError
from paste.fixture import TestApp

data_dir = os.path.join(os.path.dirname(__file__), 'cgiapp_data')

# these CGI scripts can't work on Windows or Jython
if sys.platform != 'win32' and not sys.platform.startswith('java'):

    # Ensure the CGI scripts are called with the same python interpreter. Put a
    # symlink to the interpreter executable into the path...
    def setup_module():
        global oldpath, pyexelink
        oldpath = os.environ.get('PATH', None)
        os.environ['PATH'] = data_dir + os.path.pathsep + oldpath
        pyexelink = os.path.join(data_dir, "python")
        try:
            os.unlink(pyexelink)
        except OSError:
            pass
        os.symlink(sys.executable, pyexelink)

    # ... and clean up again.
    def teardown_module():
        global oldpath, pyexelink
        os.unlink(pyexelink)
        if oldpath is not None:
            os.environ['PATH'] = oldpath
        else:
            del os.environ['PATH']

    def test_ok():
        app = TestApp(CGIApplication({}, script='ok.cgi', path=[data_dir]))
        res = app.get('')
        assert res.header('content-type') == 'text/html; charset=UTF-8'
        assert res.full_status == '200 Okay'
        assert 'This is the body' in res

    def test_form():
        app = TestApp(CGIApplication({}, script='form.cgi', path=[data_dir]))
        res = app.post('', params={'name': b'joe'},
                       upload_files=[('up', 'file.txt', b'x'*10000)])
        assert 'file.txt' in res
        assert 'joe' in res
        assert 'x'*10000 in res

    def test_error():
        app = TestApp(CGIApplication({}, script='error.cgi', path=[data_dir]))
        pytest.raises(CGIError, app.get, '', status=500)

    def test_stderr():
        app = TestApp(CGIApplication({}, script='stderr.cgi', path=[data_dir]))
        res = app.get('', expect_errors=True)
        assert res.status == 500
        assert 'error' in res
        assert 'some data' in res.errors
