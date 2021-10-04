

# def create_bag(search_collector):
#     """Create a bag."""
#     scol = self.search_collector.post_search(index, query, filters,
#                                              self.request.user,
#                                              self.kwargs.get('project'))
#     scol.filter_subjects(request.POST.getlist('subjects'), apply=True)
#     manifest = scol.get_manifest()
#     bag_metadata = {
#         'created_by': request.META['HTTP_HOST'],
#         'search_index': index,
#         'search_url': request.POST.get('search_url'),
#         'name': request.POST.get('bag_name'),
#         'files': len(manifest),
#     }
#     Bag.create_bag(request.user, index, manifest, bag_metadata,
#                    bag_metadata, request.POST.get('bag_name'),
#                    settings.MINID_TEST, query, scol.search_data)
