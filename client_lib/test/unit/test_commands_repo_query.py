import mock

from pulp.client.commands.repo.query import RepoSearchCommand
from pulp.client.extensions.core import TAG_DOCUMENT, TAG_TITLE
from pulp.common import constants
from pulp.devel.unit import base


class TestRepoSearchCommand(base.PulpClientTests):
    def setUp(self):
        super(TestRepoSearchCommand, self).setUp()
        self.command = RepoSearchCommand(self.context, 'fake_type')

    def test_run(self):
        # Setup
        repos = []
        for i in range(0, 4):
            r = {
                'repo_id': 'repo_%s' % i,
                'display_name': 'Repo %s' % i,
                'description': 'Description'}
            repos.append(r)

        self.server_mock.request.return_value = 200, repos

        # Test
        self.command.run()

        # Verify
        expected_tags = [TAG_TITLE]
        expected_tags += map(lambda x: TAG_DOCUMENT, range(0, 12))  # 3 fields * 4 repos
        self.assertEqual(expected_tags, self.prompt.get_write_tags())

    def test_criteria(self):
        mock_context = mock.MagicMock()

        RepoSearchCommand(mock_context, 'fake_type').run()

        expected = {'str-eq': [['notes.%s' % constants.REPO_NOTE_TYPE_KEY, 'fake_type']]}
        mock_context.server.repo_search.search.assert_called_once_with(**expected)
