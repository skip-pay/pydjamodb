import multiprocessing
import os
import sys

import django
from django.db import connections
from django.test.runner import ParallelTestSuite, DiscoverRunner, setup_test_environment

from .connection import TestTableConnection
from .models import dynamodb_model_classes

try:
    from germanium.signals import set_up, tear_down

    def set_dynamodb_test_autoclean():
        set_up.connect(clean_dynamodb_database)
        tear_down.connect(clean_dynamodb_database)
except ImportError:
    def set_dynamodb_test_autoclean():
        pass


def init_pynamodb_test_prefix(prefix=None):
    for model_class in dynamodb_model_classes:
        model_class._connection = None
        model_class._connection = TestTableConnection(model_class._get_connection(), prefix)


def remove_pynamodb_table(model_class):
    if model_class.exists():
        model_class.delete_table(wait=True)


def recreate_pynamodb_table(model_class):
    remove_pynamodb_table(model_class)
    model_class.create_table(wait=True)


_worker_id = 0


def _init_worker(
    counter,
    initial_settings=None,
    serialized_contents=None,
    process_setup=None,
    process_setup_args=None,
    debug_mode=None,
):
    """
    Switch to databases dedicated to this worker.

    This helper lives at module-level because of the multiprocessing module's
    requirements.
    """

    global _worker_id

    with counter.get_lock():
        counter.value += 1
        _worker_id = counter.value

    start_method = multiprocessing.get_start_method()

    if start_method == "spawn":
        if process_setup and callable(process_setup):
            if process_setup_args is None:
                process_setup_args = ()
            process_setup(*process_setup_args)
        django.setup()
        setup_test_environment(debug=debug_mode)

    for alias in connections:
        connection = connections[alias]
        if start_method == "spawn":
            # Restore initial settings in spawned processes.
            connection.settings_dict.update(initial_settings[alias])
            if value := serialized_contents.get(alias):
                connection._test_serialized_contents = value
        connection.creation.setup_worker_connection(_worker_id)

    init_pynamodb_test_prefix(_worker_id)


class DynamoDBParallelTestSuite(ParallelTestSuite):

    init_worker = _init_worker


def clean_dynamodb_database(sender, **kwargs):
    for model_class in dynamodb_model_classes:
        model_class._connection.post_test_clean(model_class)


class DynamoDBTestSuiteMixin:

    parallel_test_suite = DynamoDBParallelTestSuite

    def log(self, msg, level=None):
        sys.stderr.write(msg + os.linesep)

    def _teardown_pynamodb_database(self, prefix=None):
        init_pynamodb_test_prefix(prefix)
        table_names = []
        for model_class in dynamodb_model_classes:
            table_names.append(model_class._connection.table_name)
            remove_pynamodb_table(model_class)
        self.log('Remove DynamoDB tables ({})...'.format(
            ', '.join("'{}'".format(table_name) for table_name in table_names))
        )

    def teardown_databases(self, old_config, **kwargs):
        super().teardown_databases(old_config, **kwargs)
        if self.parallel > 1:
            for i in range(self.parallel):
                self._teardown_pynamodb_database(str(i + 1))
        else:
            self._teardown_pynamodb_database()

    def _setup_pynamodb_database(self, prefix=None):
        init_pynamodb_test_prefix(prefix)
        set_dynamodb_test_autoclean()
        table_names = []
        for model_class in dynamodb_model_classes:
            table_names.append(model_class._connection.table_name)
            recreate_pynamodb_table(model_class)
        self.log('Setup DynamoDB tables ({})...'.format(
            ', '.join("'{}'".format(table_name) for table_name in table_names))
        )

    def setup_databases(self, **kwargs):
        databases = super().setup_databases(**kwargs)

        if self.parallel > 1:
            for i in range(self.parallel):
                self._setup_pynamodb_database(str(i + 1))
        else:
            self._setup_pynamodb_database()
        return databases


class DynamoDBTestDiscoverRunner(DynamoDBTestSuiteMixin, DiscoverRunner):
    pass
