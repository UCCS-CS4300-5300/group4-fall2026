
import secrets
import string

from django.db import models
from .AILocation import AIParser


def generate_invite_code():
    characters = string.ascii_uppercase + string.digits
    return "".join(
        secrets.choice(characters) for _ in range(8)
    )


class Trip(models.Model):

    name = models.CharField(max_length=120)

    invite_code = models.CharField(
        max_length=8,
        unique=True,
        default=generate_invite_code,
        editable=False,
    )

    users = models.ManyToManyField(
        "core.User",
        related_name="trips",
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True
    )

    ai_output = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def add_user(self, user):
        self.users.add(user)

    def remove_user(self, user):
        self.users.remove(user)

    def update_user(self, user, **updates):
        self._require_user(user)

        fields = {
            field.name
            for field in user._meta.concrete_fields
            if not field.primary_key
        }

        invalid_fields = updates.keys() - fields

        if invalid_fields:
            raise ValueError(
                f"Invalid user fields: {', '.join(sorted(invalid_fields))}"
            )

        for field, value in updates.items():
            setattr(user, field, value)

        if updates:
            user.save(update_fields=list(updates))

    def get_user_data(self, user, field_name):
        self._require_user(user)

        allowed_fields = {
            field.name
            for field in user._meta.concrete_fields
            if not field.primary_key
        }

        if field_name not in allowed_fields:
            raise ValueError(
                f"Invalid user field: {field_name}"
            )

        return getattr(user, field_name)

    def get_avg_budget(self):
        budgetList = []
        for i in self.users.all():
            userBudget = self.get_user_data(i, "budget")
            if userBudget == None:
                continue
            budgetList.append(float(userBudget))
        total = 0
        for i in budgetList:
            total += i
        if len(budgetList)>0:
            avg = total/len(budgetList)
            return avg
        else:
            return "IGNORE"

    def AIDest(self, parser:AIParser):
        if not isinstance(parser, AIParser):
            raise ValueError("AI Parser is of wrong type")
        if parser is None:
            raise ValueError("No AI parser passed")
        #Get the destination suggestions of the group

        destinations = []

        for user in self.users.all():
            destinations.extend(user.destinations)

        if not destinations:
            raise ValueError("No destination suggestions")
        #Get the budget of the group
        travelBudget = self.get_avg_budget()
        if travelBudget != "IGNORE":
            travelBudget *= .6
        return parser.giveLocation(destinations, travelBudget)

    def AIGetAct(self, parser:AIParser, inDest=None):
        if not isinstance(parser, AIParser):
            raise ValueError("AI Parser is of wrong type")
        if parser == None:
            raise ValueError("No AI parser passed")
        if inDest == None:
            if parser.location != "":
                inDest = parser.location
            else:
                raise ValueError("No input destination passed")
        activities = []
        for user in self.users.all():
            activities.extend(user.activities)
        if not activities:
            raise ValueError("No activity suggestions")
        actBudget = self.get_avg_budget()
        if actBudget != "IGNORE":
            actBudget *= .6
        return parser.giveActivities(inDest, activities, actBudget)

    def AIGetBudget(self, parser:AIParser, inDest=None, inAct=None, inBudget=None):
        if not isinstance(parser, AIParser):
            raise ValueError("AI Parser is of wrong type")
        if parser == None:
            raise ValueError("No AI parser passed")
        if inDest == None:
            if parser.location != "":
                inDest = parser.location
            else:
                raise ValueError("No input destination passed")
        if inAct == None:
            if parser.activities != []:
                inAct = parser.activities
            else:
                raise ValueError("No activities passed")
        if inBudget == None:
            inBudget = self.get_avg_budget()
        return parser.giveBudget(inDest, inAct, inBudget)

    def _require_user(self, user):
        if (
            user.pk is None
            or not self.users.filter(pk=user.pk).exists()
        ):
            raise ValueError(
                "User is not associated with this trip."
            )

    def __str__(self):
        return self.name


class AISuggestion(models.Model):

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="suggestions"
    )

    location = models.CharField(max_length=255)

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.location
