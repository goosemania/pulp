from celery import shared_task

from pulp.app import models
from pulp.tasking.tasks import UserFacingTask


@shared_task(base=UserFacingTask)
def delete_publisher(repo_name, publisher_name):
    models.Publisher.objects.filter(name=publisher_name, repository__name=repo_name).delete()