from .start import start_handler, text_handler, photo_handler
from .profile import profile_handler, profile_actions_handler, edit_choice_handler
from .settings import settings_handler, settings_actions_handler
from .search import search_handler, search_actions_handler
from .matches import matches_handler, matches_actions_handler
from .notifications import notification_actions_handler

all_handlers = [
    start_handler,

    profile_handler,
    profile_actions_handler,
    edit_choice_handler,

    settings_handler,
    settings_actions_handler,
    matches_handler,
    search_handler,

    notification_actions_handler,
    search_actions_handler,
    matches_actions_handler,

    photo_handler,
    text_handler,
]