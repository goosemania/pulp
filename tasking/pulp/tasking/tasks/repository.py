from celery import task

from pulp.tasking.base import UserFacingTask


@task(base=UserFacingTask)
def delete_publisher(repo_name, publisher_name):
    from pulp.app.models import Publisher
    Publisher.objects.filter(name=publisher_name, repository__name=repo_name).delete()