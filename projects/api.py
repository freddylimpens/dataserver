from django.core.urlresolvers import reverse
from django.conf.urls import url  # , patterns, include

from tastypie.resources import ModelResource
from tastypie import fields
from tastypie.paginator import Paginator
from tastypie.utils import trailing_slash

from .models import Project, ProjectProgressRange, ProjectProgress

from base.api import HistorizedModelResource
from graffiti.api import TaggedItemResource
from haystack.query import SearchQuerySet
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

    class Meta:
        object_class = Project
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

    def prepend_urls(self):
        """ URL override for permissions and search specials. """

        # get the one from HistorizedModelResource
        urls = super(ProjectResource, self).prepend_urls()

        return urls + [
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name,
                trailing_slash()), self.wrap_view('project_search'),
                name="api_project_search"),
        ]

    def project_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.throttle_check(request)
        self.is_authenticated(request)

        # Query params
        query = request.GET.get('q', '')
        selected_facets = request.GET.getlist('facet', None)

        sqs = SearchQuerySet().models(self.Meta.object_class).facet('tags')

        # narrow down QS with facets
        if selected_facets:
            for facet in selected_facets:
                sqs = sqs.narrow('tags:%s' % (facet))
        # launch query
        if query != "":
            sqs = sqs.auto_query(query)

        uri = reverse('api_project_search',
                      kwargs={'api_name': self.api_name,
                              'resource_name': self._meta.resource_name})
        paginator = Paginator(request.GET, sqs, resource_uri=uri)

        objects = []
        for result in paginator.page()['objects']:
            if result:
                bundle = self.build_bundle(obj=result.object, request=request)
                bundle = self.full_dehydrate(bundle)
                objects.append(bundle)
        object_list = {
            'meta': paginator.page()['meta'],
            'objects': objects,
        }

        self.log_throttled_access(request)
        return self.create_response(request, object_list)