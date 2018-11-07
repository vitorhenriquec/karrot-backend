import datetime
import pytz

from foodsaving.tests.utils import TestMigrations
from foodsaving.utils.tests.fake import faker


class TestExtractPickupsFromPlacesApp(TestMigrations):
    migrate_from = [('groups', '0016_auto_20171101_0840'), ('users', '0016_user_language'),
                    ('places', '0027_auto_20171031_0942')]
    migrate_to = [('groups', '0016_auto_20171101_0840'), ('users', '0016_user_language'),
                  ('places', '0028_extract_pickups_app'), ('pickups', '0001_initial')]

    def setUpBeforeMigration(self, apps):
        User = apps.get_model('users', 'User')
        Group = apps.get_model('groups', 'Group')
        Place = apps.get_model('places', 'Place')
        PickupDateSeries = apps.get_model('places', 'PickupDateSeries')
        PickupDate = apps.get_model('places', 'PickupDate')
        Feedback = apps.get_model('places', 'Feedback')

        self.email = faker.email()
        self.now = datetime.datetime.now(tz=pytz.utc)
        self.date = faker.date_time_between(start_date='now', end_date='+24h', tzinfo=pytz.utc)
        self.group_name = 'Group ' + faker.name()
        self.place_name = 'Place ' + faker.name()

        user = User.objects.create(email=self.email, display_name='Peter')
        group = Group.objects.create(name=self.group_name)
        place = Place.objects.create(name=self.place_name, group=group)
        pickup_date_series = PickupDateSeries.objects.create(place=place, start_date=self.now)
        pickup_date = PickupDate.objects.create(series=pickup_date_series, place=place, date=self.date)
        pickup_date.collectors.add(user)
        Feedback.objects.create(given_by=user, about=pickup_date)

    def test_extract_pickups_from_places_app(self):
        User = self.apps.get_model('users', 'User')
        Group = self.apps.get_model('groups', 'Group')
        Place = self.apps.get_model('places', 'Place')
        PickupDateSeries = self.apps.get_model('pickups', 'PickupDateSeries')
        PickupDate = self.apps.get_model('pickups', 'PickupDate')
        Feedback = self.apps.get_model('pickups', 'Feedback')

        user = User.objects.filter(email=self.email).first()
        group = Group.objects.filter(name=self.group_name).first()
        place = Place.objects.filter(name=self.place_name).first()
        pickup_date_series = PickupDateSeries.objects.filter(start_date=self.now).first()
        pickup_date = PickupDate.objects.filter(date=self.date).first()
        feedback = Feedback.objects.filter(given_by=user).first()

        self.assertEqual(place.group, group)
        self.assertEqual(pickup_date_series.place, place)
        self.assertEqual(pickup_date_series.start_date, self.now)
        self.assertTrue(pickup_date in pickup_date_series.pickup_dates.all())
        self.assertEqual(feedback.about, pickup_date)
