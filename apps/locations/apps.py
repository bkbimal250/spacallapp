from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save


class LocationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.locations"

    def ready(self):
        from apps.branches.models import Branch
        from apps.locations.models import (
            Area,
            AreaAlias,
            City,
            CityAlias,
            LocationGroup,
            LocationMatchIgnorePhrase,
            State,
        )
        from apps.locations.services.fuzzy_matcher import clear_location_candidate_cache
        from apps.doubletick.models import DoubleTickAreaAlias, DoubleTickLeadArea

        senders = [
            State,
            City,
            CityAlias,
            LocationGroup,
            Area,
            AreaAlias,
            LocationMatchIgnorePhrase,
            Branch,
            DoubleTickLeadArea,
            DoubleTickAreaAlias,
        ]
        for sender in senders:
            post_save.connect(
                clear_location_candidate_cache,
                sender=sender,
                weak=False,
                dispatch_uid=f"locations_clear_match_cache_save_{sender._meta.label_lower}",
            )
            post_delete.connect(
                clear_location_candidate_cache,
                sender=sender,
                weak=False,
                dispatch_uid=f"locations_clear_match_cache_delete_{sender._meta.label_lower}",
            )
