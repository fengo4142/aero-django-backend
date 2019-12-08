from django.utils.translation import ugettext_lazy as _

# Form status constants
DRAFT = 0
PUBLISHED = 1
EXPIRED = 2
# These are the possible status for a form
STATUS = (
    (DRAFT, _("Draft")),
    (PUBLISHED, _("Published")),
    (EXPIRED, _("Expired")),
)