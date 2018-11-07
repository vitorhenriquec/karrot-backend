from django.conf import settings
from django.db import transaction
from django.utils.translation import ugettext as _
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from foodsaving.history.models import History, HistoryTypus
from foodsaving.history.utils import get_changed_data
from foodsaving.places.models import Place as PlaceModel, PlaceStatus


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceModel
        fields = [
            'id',
            'name',
            'description',
            'group',
            'address',
            'latitude',
            'longitude',
            'weeks_in_advance',
            'status',
        ]

        extra_kwargs = {
            'name': {
                'min_length': 3,
            },
            'description': {
                'trim_whitespace': False,
                'max_length': settings.DESCRIPTION_MAX_LENGTH,
            }
        }

    status = serializers.ChoiceField(
        choices=[status.value for status in PlaceStatus], default=PlaceModel.DEFAULT_STATUS
    )

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        place = super().create(validated_data)

        # TODO move into receiver
        History.objects.create(
            typus=HistoryTypus.STORE_CREATE,
            group=place.group,
            place=place,
            users=[
                self.context['request'].user,
            ],
            payload=self.initial_data,
        )
        place.group.refresh_active_status()
        return place

    def update(self, place, validated_data):
        changed_data = get_changed_data(place, validated_data)
        place = super().update(place, validated_data)

        if 'weeks_in_advance' in changed_data or \
                ('status' in changed_data and place.status == PlaceStatus.ACTIVE.value):
            with transaction.atomic():
                for series in place.series.all():
                    series.update_pickup_dates()

        if changed_data:
            History.objects.create(
                typus=HistoryTypus.STORE_MODIFY,
                group=place.group,
                place=place,
                users=[
                    self.context['request'].user,
                ],
                payload=changed_data,
            )
        place.group.refresh_active_status()
        return place

    def validate_group(self, group):
        if not group.is_member(self.context['request'].user):
            raise PermissionDenied(_('You are not a member of this group.'))
        if not group.is_editor(self.context['request'].user):
            raise PermissionDenied(_('You need to be a group editor'))
        return group

    def validate_weeks_in_advance(self, w):
        if w < 1:
            raise serializers.ValidationError(_('Set at least one week in advance'))
        return w
