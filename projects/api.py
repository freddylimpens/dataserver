from tastypie.resources import ModelResource
from tastypie import fields

from .models import Project, ProjectProgressRange, ProjectProgress

from base.api import HistorizedModelResource
from graffiti.api import TaggedItemResource
from scout.api import PlaceResource
from dataserver.authentication import AnonymousApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.constants import ALL_WITH_RELATIONS

# from accounts.api import ProfileResource


class ProjectProgressRangeResource(ModelResource):
    class Meta:
        queryset = ProjectProgressRange.objects.all()
        allowed_methods = ['get']

        filtering = {
            "slug": ('exact',),
        }


class ProjectProgressResource(ModelResource):
    range = fields.ToOneField(ProjectProgressRangeResource, "progress_range")

    class Meta:
        queryset = ProjectProgress.objects.all()
        allowed_methods = ['get']
        always_return_data = True

        filtering = {
            "range": ALL_WITH_RELATIONS,
        }


class ProjectHistoryResource(ModelResource):

    class Meta:
        queryset = Project.history.all()
        filtering = {'id': ALL_WITH_RELATIONS}


class ProjectResource(HistorizedModelResource):
    location = fields.ToOneField(PlaceResource, 'location',
                                 null=True, blank=True, full=True)
    progress = fields.ToOneField(ProjectProgressResource, 'progress',
                                 null=True, blank=True, full=True)
    tags = fields.ToManyField(TaggedItemResource, 'tagged_items', full=True, null=True)
    # TODO: 20150302 keep ?
    # tags = fields.ToManyField('graffiti.api.TagResource', 'tags',
    #                           full=True, null=True)

    class Meta:
        queryset = Project.objects.all()
        allowed_methods = ['get', 'post', 'put', 'patch']
        resource_name = 'project/project'
        always_return_data = True
        authentication = AnonymousApiKeyAuthentication()
        authorization = DjangoAuthorization()
        history_resource_class = ProjectHistoryResource
        filtering = {
            'slug': ('exact',),
            'id': ('exact', ),
            'location': ALL_WITH_RELATIONS,
        }
