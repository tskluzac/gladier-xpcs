
## Tabbed Project Templates

These templates are completely self-contained and can be easily added to your index. It contains
an index specific landing page, project page, and search page.

### Installation

You must have this directory structure to use these templates:

myindex/
  detail-overview.html
  search.html

In both files, add a hook to include the tabbed project content:

search.html
{% extends 'global/tabbed-project/search.html' %}

detail.html
{% extends 'global/tabbed-project/detail-overview.html' %}

For including components, ensure you copy the directory structure for the component you want to override:

myindex/
  detail-overview.html
  search.html
  global/
    tabbed-project/
      landing-page.html
      projects-page.html
      components/
        search-facets.html
        search-results.html
