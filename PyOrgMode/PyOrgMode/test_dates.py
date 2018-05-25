
import PyOrgMode
import unittest


class TestDates(unittest.TestCase):
    """Test the org file parser with several date formats"""

    def test_baredate(self):
        """
        Tests parsing dates without time.
        """
        datestr = '<2013-11-20 Wed>'
        date = PyOrgMode.OrgDate(datestr)
        self.assertEqual(tuple(date.value), (2013, 11, 20, 0, 0, 0, 2, 324, -1))
        self.assertEqual(date.get_value(), datestr)

    def test_datetime(self):
        """
        Tests parsing dates with time.
        """
        datestr = '<2011-12-12 Mon 09:00>'
        date = PyOrgMode.OrgDate(datestr)
        self.assertEqual(tuple(date.value), (2011, 12, 12, 9, 0, 0, 0, 346, -1))
        self.assertEqual(date.get_value(), datestr)

    def test_datenoweekday(self):
        """
        Tests parsing simple dates without weekdays.
        """
        datestr = '<2013-11-20>'
        date = PyOrgMode.OrgDate(datestr)
        self.assertEqual(tuple(date.value), (2013, 11, 20, 0, 0, 0, 2, 324, -1))
        self.assertEqual(date.get_value(), datestr)

    def test_localizeddatetime_unicode(self):
        """
        Tests parsing dates with localized weekday name that uses non-ASCII.
        """
        datestr = '<2011-12-12 Пнд 09:00>' # Понедельник = Monday (Russian)
        date = PyOrgMode.OrgDate(datestr)
        self.assertEqual(tuple(date.value), (2011, 12, 12, 9, 0, 0, 0, 346, -1))
        self.assertEqual(date.get_value(), '<2011-12-12 Mon 09:00>')

    def test_localizeddatetime_dot(self):
        """
        Tests parsing dates with localized weekday name that includes a dot.
        """
        datestr = '<2011-12-12 al. 09:00>' # astelehena = Monday (Basque)
        date = PyOrgMode.OrgDate(datestr)
        self.assertEqual(tuple(date.value), (2011, 12, 12, 9, 0, 0, 0, 346, -1))
        self.assertEqual(date.get_value(), '<2011-12-12 Mon 09:00>')

    def test_timerange(self):
        """
        Tests parsing time ranges on the same day.
        """
        datestr = '<2012-06-28 Thu 12:00-13:00>'
        date = PyOrgMode.OrgDate(datestr)
        self.assertEqual(tuple(date.value), (2012, 6, 28, 12, 0, 0, 3, 180, -1))
        self.assertEqual(tuple(date.end), (2012, 6, 28, 13, 0, 0, 3, 180, -1))
        self.assertEqual(date.get_value(), datestr)

    def test_daterange(self):
        """
        Tests parsing date ranges.
        """
        datestr = '<2012-07-20 Fri>--<2012-07-31 Tue>'
        date = PyOrgMode.OrgDate(datestr)
        self.assertEqual(tuple(date.value), (2012, 7, 20, 0, 0, 0, 4, 202, -1))
        self.assertEqual(tuple(date.end), (2012, 7, 31, 0, 0, 0, 1, 213, -1))
        self.assertEqual(date.get_value(), datestr)

    def test_daterangewithtimes(self):
        """
        Tests parsing date ranges with times.
        """
        datestr = '<2012-07-20 Fri 09:00>--<2012-07-31 Tue 14:00>'
        date = PyOrgMode.OrgDate(datestr)
        self.assertEqual(tuple(date.value), (2012, 7, 20, 9, 0, 0, 4, 202, -1))
        self.assertEqual(tuple(date.end), (2012, 7, 31, 14, 0, 0, 1, 213, -1))
        self.assertEqual(date.get_value(), datestr)

if __name__ == '__main__':
    unittest.main()
