"""Unit tests for BazaarClient."""

from __future__ import unicode_literals

import os
import re
from hashlib import md5

import kgb

from rbtools.clients import RepositoryInfo
from rbtools.clients.bazaar import BazaarClient
from rbtools.clients.errors import (SCMClientDependencyError,
                                    TooManyRevisionsError)
from rbtools.clients.tests import FOO, FOO1, FOO2, FOO3, SCMClientTestCase
from rbtools.deprecation import RemovedInRBTools50Warning
from rbtools.utils.checks import check_install
from rbtools.utils.filesystem import make_tempdir
from rbtools.utils.process import execute


class BazaarClientStandaloneTests(SCMClientTestCase):
    """Unit tests for BazaarClient not requiring a working bzr tool."""

    scmclient_cls = BazaarClient

    def test_check_dependencies_with_bzr_found_as_bazaar(self):
        """Testing BazaarClient.check_dependencies with bzr (Bazaar) found"""
        self.spy_on(execute, op=kgb.SpyOpMatchAny([
            {
                'args': (['bzr', '--version'],),
                'op': kgb.SpyOpReturn('Bazaar 2.7.0'),
            },
        ]))

        self.spy_on(check_install, op=kgb.SpyOpMatchAny([
            {
                'args': (['brz', 'help'],),
                'op': kgb.SpyOpReturn(False),
            },
            {
                'args': (['bzr', 'help'],),
                'op': kgb.SpyOpReturn(True),
            },
        ]))

        client = self.build_client(setup=False,
                                   allow_dep_checks=True)
        client.check_dependencies()

        self.assertSpyCallCount(check_install, 2)
        self.assertSpyCalledWith(check_install, ['brz', 'help'])
        self.assertSpyCalledWith(check_install, ['bzr', 'help'])
        self.assertEqual(client.bzr, 'bzr')
        self.assertFalse(client.is_breezy)

    def test_check_dependencies_with_bzr_found_as_breezy(self):
        """Testing BazaarClient.check_dependencies with bzr (Breezy) found"""
        self.spy_on(execute, op=kgb.SpyOpMatchAny([
            {
                'args': (['bzr', '--version'],),
                'op': kgb.SpyOpReturn('Breezy 3.2.2'),
            },
        ]))

        self.spy_on(check_install, op=kgb.SpyOpMatchAny([
            {
                'args': (['brz', 'help'],),
                'op': kgb.SpyOpReturn(False),
            },
            {
                'args': (['bzr', 'help'],),
                'op': kgb.SpyOpReturn(True),
            },
        ]))

        client = self.build_client(setup=False,
                                   allow_dep_checks=True)
        client.check_dependencies()

        self.assertSpyCallCount(check_install, 2)
        self.assertSpyCalledWith(check_install, ['brz', 'help'])
        self.assertSpyCalledWith(check_install, ['bzr', 'help'])
        self.assertEqual(client.bzr, 'bzr')
        self.assertTrue(client.is_breezy)

    def test_check_dependencies_with_brz_found(self):
        """Testing BazaarClient.check_dependencies with brz found"""
        self.spy_on(check_install, op=kgb.SpyOpMatchAny([
            {
                'args': (['brz', 'help'],),
                'op': kgb.SpyOpReturn(True),
            },
            {
                'args': (['bzr', 'help'],),
                'op': kgb.SpyOpReturn(False),
            },
        ]))

        client = self.build_client(setup=False,
                                   allow_dep_checks=True)
        client.check_dependencies()

        self.assertSpyCallCount(check_install, 1)
        self.assertSpyCalledWith(check_install, ['brz', 'help'])
        self.assertEqual(client.bzr, 'brz')
        self.assertTrue(client.is_breezy)

    def test_check_dependencies_with_missing(self):
        """Testing BazaarClient.check_dependencies with dependencies missing"""
        self.spy_on(check_install, op=kgb.SpyOpReturn(False))

        client = self.build_client(setup=False,
                                   allow_dep_checks=True)

        message = "Command line tools (one of ('brz', 'bzr')) are missing."

        with self.assertRaisesMessage(SCMClientDependencyError, message):
            client.check_dependencies()

        self.assertSpyCallCount(check_install, 2)
        self.assertSpyCalledWith(check_install, ['brz', 'help'])
        self.assertSpyCalledWith(check_install, ['bzr', 'help'])

    def test_bzr_with_deps_missing(self):
        """Testing BazaarClient.bzr with dependencies missing"""
        # A False value is used just to ensure get_local_path() bails early,
        # and to minimize side-effects.
        self.spy_on(check_install, op=kgb.SpyOpReturn(False))

        client = self.build_client(setup=False,
                                   allow_dep_checks=True)

        self.assertFalse(client.has_dependencies())
        self.assertEqual(client.bzr, 'bzr')

        self.assertSpyCallCount(check_install, 2)
        self.assertSpyCalledWith(check_install, ['brz', 'help'])
        self.assertSpyCalledWith(check_install, ['bzr', 'help'])

    def test_bzr_with_deps_not_checked(self):
        """Testing BazaarClient.bzr with dependencies not checked"""
        # A False value is used just to ensure get_local_path() bails early,
        # and to minimize side-effects.
        self.spy_on(check_install, op=kgb.SpyOpReturn(False))

        client = self.build_client(setup=False,
                                   allow_dep_checks=True)

        message = re.escape(
            'Either BazaarClient.setup() or BazaarClient.has_dependencies() '
            'must be called before other functions are used. This will be '
            'required starting in RBTools 5.0.'
        )

        with self.assertWarnsRegex(RemovedInRBTools50Warning, message):
            bzr = client.bzr

        self.assertEqual(bzr, 'bzr')

        self.assertSpyCallCount(check_install, 2)
        self.assertSpyCalledWith(check_install, ['brz', 'help'])
        self.assertSpyCalledWith(check_install, ['bzr', 'help'])

    def test_is_breezy_with_deps_missing(self):
        """Testing BazaarClient.is_breezy with dependencies missing"""
        # A False value is used just to ensure get_local_path() bails early,
        # and to minimize side-effects.
        self.spy_on(check_install, op=kgb.SpyOpReturn(False))

        client = self.build_client(setup=False,
                                   allow_dep_checks=True)

        self.assertFalse(client.has_dependencies())
        self.assertFalse(client.is_breezy)

        self.assertSpyCallCount(check_install, 2)
        self.assertSpyCalledWith(check_install, ['brz', 'help'])
        self.assertSpyCalledWith(check_install, ['bzr', 'help'])

    def test_is_breezy_with_deps_not_checked(self):
        """Testing BazaarClient.is_breezy with dependencies not checked"""
        # A False value is used just to ensure get_local_path() bails early,
        # and to minimize side-effects.
        self.spy_on(check_install, op=kgb.SpyOpReturn(False))

        client = self.build_client(setup=False,
                                   allow_dep_checks=True)

        message = re.escape(
            'Either BazaarClient.setup() or BazaarClient.has_dependencies() '
            'must be called before other functions are used. This will be '
            'required starting in RBTools 5.0.'
        )

        with self.assertWarnsRegex(RemovedInRBTools50Warning, message):
            is_breezy = client.is_breezy

        self.assertFalse(is_breezy)

        self.assertSpyCallCount(check_install, 2)
        self.assertSpyCalledWith(check_install, ['brz', 'help'])
        self.assertSpyCalledWith(check_install, ['bzr', 'help'])

    def test_get_local_path_with_deps_missing(self):
        """Testing BazaarClient.get_local_path with dependencies missing"""
        self.spy_on(check_install, op=kgb.SpyOpReturn(False))
        self.spy_on(RemovedInRBTools50Warning.warn)

        client = self.build_client(setup=False,
                                   allow_dep_checks=True)

        # Make sure dependencies are checked for this test before we run
        # get_local_path(). This will be the expected setup flow.
        self.assertFalse(client.has_dependencies())

        with self.assertLogs(level='DEBUG') as ctx:
            local_path = client.get_local_path()

        self.assertIsNone(local_path)

        self.assertEqual(
            ctx.records[0].msg,
            'Unable to execute "brz help" or "bzr help": skipping Bazaar')
        self.assertSpyNotCalled(RemovedInRBTools50Warning.warn)

        self.assertSpyCallCount(check_install, 2)
        self.assertSpyCalledWith(check_install, ['brz', 'help'])
        self.assertSpyCalledWith(check_install, ['bzr', 'help'])

    def test_get_local_path_with_deps_not_checked(self):
        """Testing BazaarClient.get_local_path with dependencies not checked"""
        # A False value is used just to ensure get_local_path() bails early,
        # and to minimize side-effects.
        self.spy_on(check_install, op=kgb.SpyOpReturn(False))

        client = self.build_client(setup=False,
                                   allow_dep_checks=True)

        message = re.escape(
            'Either BazaarClient.setup() or BazaarClient.has_dependencies() '
            'must be called before other functions are used. This will be '
            'required starting in RBTools 5.0.'
        )

        with self.assertLogs(level='DEBUG') as ctx:
            with self.assertWarnsRegex(RemovedInRBTools50Warning, message):
                client.get_local_path()

        self.assertEqual(
            ctx.records[0].msg,
            'Unable to execute "brz help" or "bzr help": skipping Bazaar')

        self.assertSpyCallCount(check_install, 2)
        self.assertSpyCalledWith(check_install, ['brz', 'help'])
        self.assertSpyCalledWith(check_install, ['bzr', 'help'])

    def test_get_repository_info_with_deps_missing(self):
        """Testing BazaarClient.get_repository_info with dependencies missing
        """
        self.spy_on(check_install, op=kgb.SpyOpReturn(False))
        self.spy_on(RemovedInRBTools50Warning.warn)

        client = self.build_client(setup=False,
                                   allow_dep_checks=True)

        # Make sure dependencies are checked for this test before we run
        # get_repository_info(). This will be the expected setup flow.
        self.assertFalse(client.has_dependencies())

        with self.assertLogs(level='DEBUG') as ctx:
            repository_info = client.get_repository_info()

        self.assertIsNone(repository_info)

        self.assertEqual(
            ctx.records[0].msg,
            'Unable to execute "brz help" or "bzr help": skipping Bazaar')

        self.assertSpyCallCount(check_install, 2)
        self.assertSpyCalledWith(check_install, ['brz', 'help'])
        self.assertSpyCalledWith(check_install, ['bzr', 'help'])

    def test_get_repository_info_with_deps_not_checked(self):
        """Testing BazaarClient.get_repository_info with dependencies not
        checked
        """
        # A False value is used just to ensure get_repository_info() bails
        # early, and to minimize side-effects.
        self.spy_on(check_install, op=kgb.SpyOpReturn(False))

        client = self.build_client(setup=False,
                                   allow_dep_checks=True)

        message = re.escape(
            'Either BazaarClient.setup() or BazaarClient.has_dependencies() '
            'must be called before other functions are used. This will be '
            'required starting in RBTools 5.0.'
        )

        with self.assertLogs(level='DEBUG') as ctx:
            with self.assertWarnsRegex(RemovedInRBTools50Warning, message):
                client.get_repository_info()

        self.assertEqual(
            ctx.records[0].msg,
            'Unable to execute "brz help" or "bzr help": skipping Bazaar')

        self.assertSpyCallCount(check_install, 2)
        self.assertSpyCalledWith(check_install, ['brz', 'help'])
        self.assertSpyCalledWith(check_install, ['bzr', 'help'])


class BazaarClientTests(SCMClientTestCase):
    """Unit tests for BazaarClient."""

    scmclient_cls = BazaarClient

    @classmethod
    def setup_checkout(cls, checkout_dir):
        """Populate two Bazaar clones.

        This will create a clone of the sample Bazaar repository stored in
        the :file:`testdata` directory, and a child clone of that first
        clone.

        Args:
            checkout_dir (unicode):
                The top-level directory in which clones will be placed.

        Returns:
            The main clone directory, or ``None`` if :command:`bzr` isn't
            in the path.
        """
        original_branch = os.path.join(checkout_dir, 'orig')
        child_branch = os.path.join(checkout_dir, 'child')

        os.mkdir(checkout_dir, 0o700)
        os.mkdir(original_branch, 0o700)
        os.mkdir(child_branch, 0o700)

        cls.original_branch = original_branch
        cls.child_branch = child_branch

        # Figure out which command line tool we should use, if Bazaar/Breezy
        # is installed.
        scmclient = BazaarClient()

        if scmclient.has_dependencies():
            cls._bzr = scmclient.bzr

            try:
                cls._run_bzr(['init', '.'], cwd=original_branch)
                cls._bzr_add_file_commit(filename='foo.txt',
                                         data=FOO,
                                         msg='initial commit',
                                         cwd=original_branch)

                cls._run_bzr(['branch', '--use-existing-dir', original_branch,
                              child_branch],
                             cwd=original_branch)
            except Exception:
                # We couldn't set up the repository, so skip this. We'll skip
                # when setting up the client.
                pass
        else:
            cls._bzr = None

        return original_branch

    def setUp(self):
        super(BazaarClientTests, self).setUp()

        self.set_user_home(os.path.join(self.testdata_dir, 'homedir'))

    @classmethod
    def _run_bzr(cls, command, *args, **kwargs):
        """Run Bazaar/Breezy with the provided arguments.

        Args:
            command (list of unicode):
                The argument to pass to the command.

            *args (tuple):
                Additional positional arguments to pass to
                :py:func:`~rtools.utils.process.execute`.

            **kwargs (dict):
                Additional Keyword arguments to pass to
                :py:func:`~rtools.utils.process.execute`.

        Returns:
            object:
            The result of the :py:func:`~rtools.utils.process.execute` call.
        """
        return execute(
            [cls._bzr] + command,
            env={
                'BRZ_EMAIL': 'Test User <test@example.com>',
                'BZR_EMAIL': 'Test User <test@example.com>',
            },
            *args,
            **kwargs)

    @classmethod
    def _bzr_add_file_commit(cls, filename, data, msg, cwd=None, *args,
                             **kwargs):
        """Add a file to a Bazaar repository.

        Args:
            filename (unicode):
                The name of the file to add.

            data (bytes):
                The data to write to the file.

            msg (unicode):
                The commit message to use.

            cwd (unicode, optional):
                A working directory to use when running the bzr commands.

            *args (list):
                Positional arguments to pass through to
                :py:func:`rbtools.utils.process.execute`.

            **kwargs (dict):
                Keyword arguments to pass through to
                :py:func:`rbtools.utils.process.execute`.
        """
        if cwd is not None:
            filename = os.path.join(cwd, filename)

        with open(filename, 'wb') as f:
            f.write(data)

        cls._run_bzr(['add', filename], cwd=cwd, *args, **kwargs)
        cls._run_bzr(['commit', '-m', msg, '--author', 'Test User'],
                     cwd=cwd, *args, **kwargs)

    def _compare_diffs(self, filename, full_diff, expected_diff_digest,
                       change_type='modified'):
        """Compare expected metadata to a generated diff.

        Args:
            filename (unicode):
                The expected filename in the diff.

            full_diff (bytes):
                The generated diff content.

            expected_diff_digest (bytes):
                The expected MD5 digest of the diff, past the headers
                (starting on the 3rd line).

            change_type (unicode, optional):
                The expected change type listed in the header.

        Raises:
            AssertionError:
                One of the expectations failed.
        """
        filename = filename.encode('utf-8')
        change_type = change_type.encode('utf-8')

        diff_lines = full_diff.splitlines()

        self.assertEqual(diff_lines[0],
                         b"=== %s file '%s'" % (change_type, filename))
        self.assertTrue(diff_lines[1].startswith(b'--- %s\t' % filename))
        self.assertTrue(diff_lines[2].startswith(b'+++ %s\t' % filename))

        diff_body = b'\n'.join(diff_lines[3:])
        self.assertEqual(md5(diff_body).hexdigest(), expected_diff_digest)

    def _count_files_in_diff(self, diff):
        return len([
            line
            for line in diff.split(b'\n')
            if line.startswith(b'===')
        ])

    def test_get_repository_info_original_branch(self):
        """Testing BazaarClient get_repository_info with original branch"""
        client = self.build_client()
        os.chdir(self.original_branch)

        ri = client.get_repository_info()

        self.assertIsInstance(ri, RepositoryInfo)
        self.assertEqual(os.path.realpath(ri.path),
                         os.path.realpath(self.original_branch))

        self.assertEqual(ri.base_path, '/')

    def test_get_repository_info_child_branch(self):
        """Testing BazaarClient get_repository_info with child branch"""
        client = self.build_client()
        os.chdir(self.child_branch)

        ri = client.get_repository_info()

        self.assertIsInstance(ri, RepositoryInfo)
        self.assertEqual(os.path.realpath(ri.path),
                         os.path.realpath(self.child_branch))

        self.assertEqual(ri.base_path, '/')

    def test_get_repository_info_no_branch(self):
        """Testing BazaarClient get_repository_info, no branch"""
        client = self.build_client()
        self.chdir_tmp()

        ri = client.get_repository_info()
        self.assertIsNone(ri)

    def test_too_many_revisions(self):
        """Testing BazaarClient parse_revision_spec with too many revisions"""
        client = self.build_client()

        with self.assertRaises(TooManyRevisionsError):
            client.parse_revision_spec([1, 2, 3])

    def test_diff_simple(self):
        """Testing BazaarClient simple diff case"""
        client = self.build_client()
        os.chdir(self.child_branch)

        self._bzr_add_file_commit('foo.txt', FOO1, 'delete and modify stuff')

        revisions = client.parse_revision_spec([])
        result = client.diff(revisions)
        self.assertIsInstance(result, dict)
        self.assertIn('diff', result)

        self._compare_diffs('foo.txt', result['diff'],
                            'a6326b53933f8b255a4b840485d8e210')

    def test_diff_exclude(self):
        """Testing BazaarClient diff with file exclusion"""
        client = self.build_client()
        os.chdir(self.child_branch)

        self._bzr_add_file_commit('foo.txt', FOO1, 'commit 1')
        self._bzr_add_file_commit('exclude.txt', FOO2, 'commit 2')

        revisions = client.parse_revision_spec([])
        result = client.diff(revisions, exclude_patterns=['exclude.txt'])
        self.assertIsInstance(result, dict)
        self.assertIn('diff', result)

        self._compare_diffs('foo.txt', result['diff'],
                            'a6326b53933f8b255a4b840485d8e210')

        self.assertEqual(self._count_files_in_diff(result['diff']), 1)

    def test_diff_exclude_in_subdir(self):
        """Testing BazaarClient diff with file exclusion in a subdirectory"""
        client = self.build_client()
        os.chdir(self.child_branch)

        self._bzr_add_file_commit('foo.txt', FOO1, 'commit 1')

        os.mkdir('subdir')
        os.chdir('subdir')

        self._bzr_add_file_commit('exclude.txt', FOO2, 'commit 2')

        revisions = client.parse_revision_spec([])
        result = client.diff(revisions,
                             exclude_patterns=['exclude.txt', '.'])
        self.assertIsInstance(result, dict)
        self.assertIn('diff', result)

        self._compare_diffs('foo.txt', result['diff'],
                            'a6326b53933f8b255a4b840485d8e210')

        self.assertEqual(self._count_files_in_diff(result['diff']), 1)

    def test_diff_exclude_root_pattern_in_subdir(self):
        """Testing BazaarClient diff with file exclusion in the repo root"""
        client = self.build_client()
        os.chdir(self.child_branch)

        self._bzr_add_file_commit('exclude.txt', FOO2, 'commit 1')

        os.mkdir('subdir')
        os.chdir('subdir')

        self._bzr_add_file_commit('foo.txt', FOO1, 'commit 2')

        revisions = client.parse_revision_spec([])
        result = client.diff(
            revisions,
            exclude_patterns=[os.path.sep + 'exclude.txt',
                              os.path.sep + 'subdir'])

        self.assertIsInstance(result, dict)
        self.assertIn('diff', result)

        self._compare_diffs(os.path.join('subdir', 'foo.txt'), result['diff'],
                            '4deffcb296180fa166eddff2512bd0e4',
                            change_type='added')

    def test_diff_specific_files(self):
        """Testing BazaarClient diff with specific files"""
        client = self.build_client()
        os.chdir(self.child_branch)

        self._bzr_add_file_commit('foo.txt', FOO1, 'delete and modify stuff')
        self._bzr_add_file_commit('bar.txt', b'baz', 'added bar')

        revisions = client.parse_revision_spec([])
        result = client.diff(revisions, ['foo.txt'])
        self.assertIsInstance(result, dict)
        self.assertIn('diff', result)

        self._compare_diffs('foo.txt', result['diff'],
                            'a6326b53933f8b255a4b840485d8e210')

    def test_diff_simple_multiple(self):
        """Testing BazaarClient simple diff with multiple commits case"""
        client = self.build_client()
        os.chdir(self.child_branch)

        self._bzr_add_file_commit('foo.txt', FOO1, 'commit 1')
        self._bzr_add_file_commit('foo.txt', FOO2, 'commit 2')
        self._bzr_add_file_commit('foo.txt', FOO3, 'commit 3')

        revisions = client.parse_revision_spec([])
        result = client.diff(revisions)
        self.assertIsInstance(result, dict)
        self.assertIn('diff', result)

        self._compare_diffs('foo.txt', result['diff'],
                            '4109cc082dce22288c2f1baca9b107b6')

    def test_diff_parent(self):
        """Testing BazaarClient diff with changes only in the parent branch"""
        client = self.build_client()

        self._bzr_add_file_commit('foo.txt', FOO1, 'delete and modify stuff',
                                  cwd=self.child_branch)

        grand_child_branch = make_tempdir()
        self._run_bzr(['branch', '--use-existing-dir', self.child_branch,
                       grand_child_branch],
                      cwd=self.child_branch)
        os.chdir(grand_child_branch)

        revisions = client.parse_revision_spec([])
        self.assertEqual(
            client.diff(revisions),
            {
                'diff': None,
                'parent_diff': None,
            })

    def test_diff_grand_parent(self):
        """Testing BazaarClient diff with changes between a 2nd level
        descendant
        """
        # Requesting the diff between the grand child branch and its grand
        # parent:
        client = self.build_client(options={
            'parent_branch': self.original_branch,
        })

        self._bzr_add_file_commit('foo.txt', FOO1, 'delete and modify stuff',
                                  cwd=self.child_branch)

        grand_child_branch = make_tempdir()
        self._run_bzr(['branch', '--use-existing-dir', self.child_branch,
                       grand_child_branch],
                      cwd=self.child_branch)
        os.chdir(grand_child_branch)

        revisions = client.parse_revision_spec([])
        result = client.diff(revisions)
        self.assertIsInstance(result, dict)
        self.assertIn('diff', result)

        self._compare_diffs('foo.txt', result['diff'],
                            'a6326b53933f8b255a4b840485d8e210')

    def test_guessed_summary_and_description(self):
        """Testing BazaarClient guessing summary and description"""
        client = self.build_client(options={
            'guess_summary': True,
            'guess_description': True,
        })

        os.chdir(self.child_branch)

        self._bzr_add_file_commit('foo.txt', FOO1, 'commit 1')
        self._bzr_add_file_commit('foo.txt', FOO2, 'commit 2')
        self._bzr_add_file_commit('foo.txt', FOO3, 'commit 3')

        revisions = client.parse_revision_spec([])

        self.assertEqual(
            client.get_commit_message(revisions),
            {
                'description': (
                    'commit 2'
                    '\n\n\n'
                    'commit 1'
                ),
                'summary': 'commit 3',
            })

    def test_guessed_summary_and_description_in_grand_parent_branch(self):
        """Testing BazaarClient guessing summary and description for grand
        parent branch
        """
        # Requesting the diff between the grand child branch and its grand
        # parent:
        client = self.build_client(options={
            'guess_summary': True,
            'guess_description': True,
            'parent_branch': self.original_branch,
        })

        self._bzr_add_file_commit('foo.txt', FOO1, 'commit 1',
                                  cwd=self.child_branch)
        self._bzr_add_file_commit('foo.txt', FOO2, 'commit 2',
                                  cwd=self.child_branch)
        self._bzr_add_file_commit('foo.txt', FOO3, 'commit 3',
                                  cwd=self.child_branch)

        grand_child_branch = make_tempdir()
        self._run_bzr(['branch', '--use-existing-dir', self.child_branch,
                       grand_child_branch],
                      cwd=self.child_branch)
        os.chdir(grand_child_branch)

        revisions = client.parse_revision_spec([])

        self.assertEqual(
            client.get_commit_message(revisions),
            {
                'description': (
                    'commit 2'
                    '\n\n\n'
                    'commit 1'
                ),
                'summary': 'commit 3',
            })

    def test_guessed_summary_and_description_with_revision_range(self):
        """Testing BazaarClient guessing summary and description with a
        revision range
        """
        client = self.build_client(options={
            'guess_summary': True,
            'guess_description': True,
        })

        os.chdir(self.child_branch)

        self._bzr_add_file_commit('foo.txt', FOO1, 'commit 1')
        self._bzr_add_file_commit('foo.txt', FOO2, 'commit 2')
        self._bzr_add_file_commit('foo.txt', FOO3, 'commit 3')

        revisions = client.parse_revision_spec(['2..3'])

        self.assertEqual(
            client.get_commit_message(revisions),
            {
                'description': 'commit 2',
                'summary': 'commit 2',
            })

    def test_parse_revision_spec_no_args(self):
        """Testing BazaarClient.parse_revision_spec with no specified
        revisions
        """
        client = self.build_client()
        os.chdir(self.child_branch)

        base_commit_id = client._get_revno()
        self._bzr_add_file_commit('foo.txt', FOO1, 'commit 1')
        tip_commit_id = client._get_revno()

        self.assertEqual(
            client.parse_revision_spec(),
            {
                'base': base_commit_id,
                'tip': tip_commit_id,
            })

    def test_parse_revision_spec_one_arg(self):
        """Testing BazaarClient.parse_revision_spec with one specified
        revision
        """
        client = self.build_client()
        os.chdir(self.child_branch)

        base_commit_id = client._get_revno()
        self._bzr_add_file_commit('foo.txt', FOO1, 'commit 1')
        tip_commit_id = client._get_revno()

        self.assertEqual(
            client.parse_revision_spec([tip_commit_id]),
            {
                'base': base_commit_id,
                'tip': tip_commit_id,
            })

    def test_parse_revision_spec_one_arg_parent(self):
        """Testing BazaarClient.parse_revision_spec with one specified
        revision and a parent diff
        """
        client = self.build_client(options={
            'parent_branch': self.child_branch,
        })

        os.chdir(self.original_branch)

        parent_base_commit_id = client._get_revno()

        grand_child_branch = make_tempdir()
        self._run_bzr(['branch', '--use-existing-dir', self.child_branch,
                       grand_child_branch])
        os.chdir(grand_child_branch)

        base_commit_id = client._get_revno()
        self._bzr_add_file_commit('foo.txt', FOO2, 'commit 2')
        tip_commit_id = client._get_revno()

        self.assertEqual(
            client.parse_revision_spec([tip_commit_id]),
            {
                'base': base_commit_id,
                'parent_base': parent_base_commit_id,
                'tip': tip_commit_id,
            })

    def test_parse_revision_spec_one_arg_split(self):
        """Testing BazaarClient.parse_revision_spec with R1..R2 syntax"""
        client = self.build_client()
        os.chdir(self.child_branch)

        self._bzr_add_file_commit('foo.txt', FOO1, 'commit 1')
        base_commit_id = client._get_revno()
        self._bzr_add_file_commit('foo.txt', FOO2, 'commit 2')
        tip_commit_id = client._get_revno()

        self.assertEqual(
            client.parse_revision_spec([
                '%s..%s' % (base_commit_id, tip_commit_id),
            ]),
            {
                'base': base_commit_id,
                'tip': tip_commit_id,
            })

    def test_parse_revision_spec_two_args(self):
        """Testing BazaarClient.parse_revision_spec with two revisions"""
        client = self.build_client()
        os.chdir(self.child_branch)

        self._bzr_add_file_commit('foo.txt', FOO1, 'commit 1')
        base_commit_id = client._get_revno()
        self._bzr_add_file_commit('foo.txt', FOO2, 'commit 2')
        tip_commit_id = client._get_revno()

        self.assertEqual(
            client.parse_revision_spec([base_commit_id, tip_commit_id]),
            {
                'base': base_commit_id,
                'tip': tip_commit_id,
            })
