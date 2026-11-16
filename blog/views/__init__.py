"""Blog views, split by area. Re-exported so `blog.urls` can use `views.<name>`."""
from .posts import (  # noqa: F401
    BlogListView,
    BlogDetailView,
    category_posts,
    tag_posts,
)
from .interactions import (  # noqa: F401
    bookmark_post,
    like_post,
    add_comment,
)
from .dashboard import (  # noqa: F401
    dashboard,
    saved_posts,
    profile_view,
    my_posts,
)
from .authoring import (  # noqa: F401
    create_post,
    update_post,
    delete_post,
)
from .moderation import (  # noqa: F401
    manage_categories,
    manage_tags,
    manage_comments,
)
from .activity import (  # noqa: F401
    notifications,
    liked_posts,
    commented_posts,
)
from .users import (  # noqa: F401
    manage_users,
)
