import traceback as traceback_module

from pulp.server.db.model.base import Model
from pulp.server.db.model.reaper_base import ReaperMixin
import pulp.common.dateutils as dateutils


class RepoContentUnit(Model):
    """
    Each instance represents a mapping between a content unit and a repo. The
    unit's metadata is stored in its appropriate type collection. A content
    unit is uniquely identified by its type (says which collection it is stored
    in) and its ID within the type collection.

    Not every content unit will have a mapping document in this collection. The
    same content unit may be mapped to multiple repos, in which case there will
    be multiple documents in this collection that reference the same unit.

    There may be multiple associations between a unit and a repository. For
    instance, associated by an importer during a sync or by a user during
    a unit copy or upload. The owner variables are used to distinguish between
    them. Queries should take this into account since in most cases the query
    will only want to know if it's associated at all, not how many times.

    @ivar repo_id: identifies the repo
    @type repo_id: str

    @ivar unit_id: ID (_id) of the content unit in its type collection
    @type unit_id: str

    @ivar unit_type_id: identifies the type of content unit being associated
    @type unit_type_id: str

    @ivar created: iso8601 formatted timestamp indicating when the association was first created
    @type created: str

    @ivar updated: iso8601 formatted timestamp indicating the last time the association was
                   updated (effectively when it was attempted to be created but already existed)
    @type updated: str
    """

    collection_name = 'repo_content_units'

    # Make sure you understand how the order of these affects mongo before
    # modifying the following index
    unique_indices = (('repo_id', 'unit_type_id', 'unit_id'),)
    search_indices = (('repo_id', 'unit_type_id'),
                      # default sort order on get_units query, do not remove
                      ('unit_type_id', 'created'),
                      'unit_id')

    OWNER_TYPE_IMPORTER = 'importer'
    OWNER_TYPE_USER = 'user'

    def __init__(self, repo_id, unit_id, unit_type_id):
        super(RepoContentUnit, self).__init__()

        # Mapping Identity Information
        self.repo_id = repo_id
        self.unit_id = unit_id
        self.unit_type_id = unit_type_id

        # store time in UTC
        utc_timestamp = dateutils.now_utc_timestamp()
        self.created = dateutils.format_iso8601_utc_timestamp(utc_timestamp)
        self.updated = self.created


class RepoSyncResult(Model, ReaperMixin):
    """
    Stores the results of a repo sync.

    The documents in this collection may be reaped, so it inherits from ReaperMixin.
    """

    collection_name = 'repo_sync_results'

    RESULT_SUCCESS = 'success'
    RESULT_FAILED = 'failed'
    RESULT_ERROR = 'error'
    RESULT_CANCELED = 'canceled'

    @classmethod
    def error_result(cls, repo_id, importer_id, importer_type_id, started, completed, exception,
                     traceback):
        """
        Creates a new history entry for a failed sync. The details of the error
        raised from the plugin are captured.

        @param repo_id: identifies the repo
        @type  repo_id: str

        @param importer_id: identifies the repo's importer
        @type  importer_id: str

        @param importer_type_id: identifies the type of importer that did the sync
        @type  importer_type_id: str

        @param started: iso8601 formatted timestamp when the sync was begun
        @type  started: str

        @param completed: iso8601 formatted timestamp when the sync completed
        @type  completed: str

        @param exception: exception instance raised from the plugin
        @type  exception: L{Exception}

        @param traceback: traceback in the plugin that caused the exception
        @type  traceback: traceback
        """

        r = RepoSyncResult(repo_id, importer_id, importer_type_id, started, completed,
                           RepoSyncResult.RESULT_ERROR)
        r.error_message = str(exception)
        r.exception = repr(exception)
        r.traceback = traceback_module.format_tb(traceback)

        return r

    @classmethod
    def expected_result(cls, repo_id, importer_id, importer_type_id, started, completed,
                        added_count, updated_count, removed_count, summary, details, result_code):
        """
        Creates a new history entry for a successful sync.

        @param repo_id: identifies the repo
        @type  repo_id: str

        @param importer_id: identifies the repo's importer
        @type  importer_id: str

        @param importer_type_id: identifies the type of importer that did the sync
        @type  importer_type_id: str

        @param started: iso8601 formatted timestamp when the sync was begun
        @type  started: str

        @param completed: iso8601 formatted timestamp when the sync completed
        @type  completed: str

        @param added_count: number of new units added during the sync
        @type  added_count: int

        @param updated_count: number of units updated during the sync
        @type  updated_count: int

        @param removed_count: number of units removed from the repo during the sync
        @type  removed_count: int

        @param summary: short log output from the plugin of the sync
        @type  summary: any serializable

        @param details: long log output from the plugin of the sync
        @type  details: any serializable

        @param result_code: one of the RESULT_* constants in this class
        @type  result_code: str
        """

        r = RepoSyncResult(repo_id, importer_id, importer_type_id, started, completed, result_code)
        r.added_count = added_count
        r.updated_count = updated_count
        r.removed_count = removed_count
        r.summary = summary
        r.details = details

        return r

    def __init__(self, repo_id, importer_id, importer_type_id, started, completed, result):
        """
        Describes the results of a single completed (potentially errored) sync.
        Rather than directory instantiating instances, use one of the above
        factory methods to make sure all the necessary fields are specified.
        """
        super(RepoSyncResult, self).__init__()

        self.repo_id = repo_id
        self.importer_id = importer_id
        self.importer_type_id = importer_type_id
        self.started = started
        self.completed = completed
        self.result = result

        # Include the success/error specific fields so they appear in all cases
        self.error_message = None
        self.exception = None
        self.traceback = None

        self.added_count = None
        self.updated_count = None
        self.removed_count = None
        self.summary = None
        self.details = None


class RepoPublishResult(Model, ReaperMixin):
    """
    Stores the results of a repo publish.

    The documents in this collection may be reaped, so it inherits from ReaperMixin.
    """

    collection_name = 'repo_publish_results'

    RESULT_SUCCESS = 'success'
    RESULT_FAILED = 'failed'
    RESULT_ERROR = 'error'

    @classmethod
    def error_result(cls, repo_id, distributor_id, distributor_type_id, started, completed,
                     exception, traceback):
        """
        Creates a new history entry for a failed publish. The details of the error
        raised from the plugin are captured.

        @param repo_id: identifies the repo
        @type  repo_id: str

        @param distributor_id: identifies the repo's distributor
        @type  distributor_id: str

        @param distributor_type_id: identifies the type of distributor that did the publish
        @type  distributor_type_id: str

        @param started: iso8601 formatted timestamp when the publish was begun
        @type  started: str

        @param completed: iso8601 formatted timestamp when the publish completed
        @type  completed: str

        @param exception: exception instance raised from the plugin
        @type  exception: L{Exception}

        @param traceback: traceback in the plugin that caused the exception
        @type  traceback: traceback
        """

        r = cls(repo_id, distributor_id, distributor_type_id, started, completed, cls.RESULT_ERROR)
        r.error_message = str(exception)
        r.exception = repr(exception)
        r.traceback = traceback_module.format_tb(traceback)

        return r

    @classmethod
    def expected_result(cls, repo_id, distributor_id, distributor_type_id, started,
                        completed, summary, details, result_code):
        """
        Creates a new history entry for a successful publish.

        @param repo_id: identifies the repo
        @type  repo_id: str

        @param distributor_id: identifies the repo's distributor
        @type  distributor_id: str

        @param distributor_type_id: identifies the type of distributor that did the publish
        @type  distributor_type_id: str

        @param started: iso8601 formatted timestamp when the publish was begun
        @type  started: str

        @param completed: iso8601 formatted timestamp when the publish completed
        @type  completed: str

        @param summary: short log output from the plugin of the publish
        @type  summary: any serializable

        @param details: long log output from the plugin of the publish
        @type  details: any serializable

        @param result_code: one of the RESULT_* constants in this class
        @type  result_code: str
        """

        r = cls(repo_id, distributor_id, distributor_type_id, started, completed, result_code)
        r.summary = summary
        r.details = details

        return r

    @classmethod
    def failed_result(cls, repo_id, distributor_id, distributor_type_id, started, completed,
                      summary, details):
        """
        Creates a new history entry for a gracefully failed publish.

        @param repo_id: identifies the repo
        @type  repo_id: str

        @param distributor_id: identifies the repo's distributor
        @type  distributor_id: str

        @param distributor_type_id: identifies the type of distributor that did the publish
        @type  distributor_type_id: str

        @param started: iso8601 formatted timestamp when the publish was begun
        @type  started: str

        @param completed: iso8601 formatted timestamp when the publish completed
        @type  completed: str

        @param summary: short log output from the plugin of the publish
        @type  summary: any serializable

        @param details: long log output from the plugin of the publish
        @type  details: any serializable
        """

        r = cls(repo_id, distributor_id, distributor_type_id, started, completed, cls.RESULT_FAILED)
        r.summary = summary
        r.details = details

        return r

    def __init__(self, repo_id, distributor_id, distributor_type_id, started, completed, result):
        """
        Describes the results of a single completed (potentially errored) publish.
        Rather than directory instantiating instances, use one of the above
        factory methods to make sure all the necessary fields are specified.
        """
        super(RepoPublishResult, self).__init__()

        self.repo_id = repo_id
        self.distributor_id = distributor_id
        self.distributor_type_id = distributor_type_id
        self.started = started
        self.completed = completed
        self.result = result

        # Include the success/error specific fields so they appear in all cases
        self.error_message = None
        self.exception = None
        self.traceback = None

        self.summary = None
        self.details = None
