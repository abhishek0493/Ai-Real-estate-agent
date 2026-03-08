"""Models package — import all models so Alembic can discover them."""

from app.models.conversation import ConversationMessageModel
from app.models.lead import LeadModel
from app.models.prompt_version import PromptVersionModel
from app.models.property import PropertyModel
from app.models.tenant import TenantModel
from app.models.user import UserModel

__all__ = [
    "ConversationMessageModel",
    "LeadModel",
    "PromptVersionModel",
    "PropertyModel",
    "TenantModel",
    "UserModel",
]

