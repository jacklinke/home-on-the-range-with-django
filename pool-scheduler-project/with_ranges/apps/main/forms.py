from apps.main.date_utils import get_datetime_range_from_string_list
from apps.main.models import (
    Closure,
    Lane,
    LaneReservation,
    Locker,
    LockerReservation,
    Pool,
)
from django import forms
from django.contrib.postgres.forms import (
    DateRangeField,
    DateTimeRangeField,
    DecimalRangeField,
    IntegerRangeField,
)
from django.core.exceptions import ValidationError


class DateTimeRangeForm(forms.Form):

    datetimerange_input = forms.CharField(
        label="DateTime Range to Filter",
        widget=forms.TextInput(
            attrs={
                "class": "datetime_rangepicker",
                #
                # Following functionality was moved into Lane/Locker views to keep the form generic for use with both
                # "hx-post": reverse_lazy("main:the_view_to_post_to"),
                "hx-target": "#outputDiv",
                "hx-trigger": "range_change",
                "onchange": "htmx.trigger(this, 'range_change')",
            }
        ),
    )

    def clean_datetimerange_input(self):
        """
        Take the string from the form field, splits it into a list of 2 strings, and then returns a
             DateTimeTZRange containing the resulting lower and upper datetime values of the range.
        """
        raw_string_list = self.cleaned_data["datetimerange_input"].split(" - ", 1)
        if len(raw_string_list) != 2:
            raise ValidationError("Incorrect datetime range input!")

        try:
            data = get_datetime_range_from_string_list(raw_string_list)
        except ValueError as e:
            raise ValidationError(e)

        return data


class DateTimeRangeFieldForm(forms.Form):

    datetimerange_input = DateTimeRangeField(
        label="DateTime Range to Filter",
    )


class DateRangeForm(forms.Form):

    daterange_input = forms.CharField(
        label="Date Range to Filter",
        widget=forms.TextInput(
            attrs={
                "class": "datetime_rangepicker",
                #
                # Following functionality was moved into Lane/Locker views to keep the form generic for use with both
                # "hx-post": reverse_lazy("main:the_view_to_post_to"),
                "hx-target": "#outputDiv",
                "hx-trigger": "range_change",
                "onchange": "htmx.trigger(this, 'range_change')",
            }
        ),
    )

    def clean_daterange_input(self):
        """
        Take the string from the form field, splits it into a list of 2 strings, and then returns a
             DateTimeTZRange containing the resulting lower and upper datetime values of the range.
        """
        raw_string_list = self.cleaned_data["datetimerange_input"].split(" - ", 1)
        if len(raw_string_list) != 2:
            raise ValidationError("Incorrect datetime range input!")

        try:
            data = get_datetime_range_from_string_list(raw_string_list)
        except ValueError as e:
            raise ValidationError(e)

        return data


class DateTimeForm(forms.Form):

    datetime_input = forms.DateTimeField(
        label="DateTime to Filter",
        widget=forms.DateTimeInput(
            attrs={
                "class": "datetime_rangepicker",
                #
                # Following functionality was moved into Lane/Locker views to keep the form generic for use with both
                # "hx-post": reverse_lazy("main:the_view_to_post_to"),
                "hx-target": "#outputDiv",
                "hx-trigger": "range_change",
                "onchange": "htmx.trigger(this, 'range_change')",
            }
        ),
    )

    def clean_datetime_input(self):
        """
        Take the string from the form field, splits it into a list of 2 strings, and then returns a
             DateTimeTZRange containing the resulting lower and upper datetime values of the range.
        """
        raw_string_list = self.cleaned_data["datetimerange_input"].split(" - ", 1)
        if len(raw_string_list) != 2:
            raise ValidationError("Incorrect datetime range input!")

        try:
            data = get_datetime_range_from_string_list(raw_string_list)
        except ValueError as e:
            raise ValidationError(e)

        return data


class DateForm(forms.Form):

    date_input = forms.DateField(
        label="Date to Filter",
        widget=forms.TextInput(
            attrs={
                "class": "datetime_rangepicker",
                #
                # Following functionality was moved into Lane/Locker views to keep the form generic for use with both
                # "hx-post": reverse_lazy("main:the_view_to_post_to"),
                "hx-target": "#outputDiv",
                "hx-trigger": "range_change",
                "onchange": "htmx.trigger(this, 'range_change')",
            }
        ),
    )

    def clean_date_input(self):
        """
        Take the string from the form field, splits it into a list of 2 strings, and then returns a
             DateTimeTZRange containing the resulting lower and upper datetime values of the range.
        """
        raw_string_list = self.cleaned_data["datetimerange_input"].split(" - ", 1)
        if len(raw_string_list) != 2:
            raise ValidationError("Incorrect datetime range input!")

        try:
            data = get_datetime_range_from_string_list(raw_string_list)
        except ValueError as e:
            raise ValidationError(e)

        return data
