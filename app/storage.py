from app.models.IndexCollection import IndexCollection
from app.api.search import SearchEngine

app_index_collection = IndexCollection()
app_search = SearchEngine(app_index_collection)
