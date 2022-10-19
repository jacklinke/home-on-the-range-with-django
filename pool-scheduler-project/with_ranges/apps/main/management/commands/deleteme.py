import zoneinfo
from datetime import timedelta
from functools import reduce
from itertools import chain
from operator import or_

from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.contrib.postgres.fields.ranges import (
    IsEmpty,
    LowerInclusive,
    LowerInfinite,
    RangeBoundary,
    RangeEndsWith,
    RangeOperators,
    RangeStartsWith,
    UpperInclusive,
    UpperInfinite,
)
from django.contrib.postgres.validators import (
    RangeMaxValueValidator,
    RangeMinValueValidator,
)
from django.db import models
from django.db.models import F, OuterRef, Q, Subquery, Sum, Value, Window, fields
from django.db.models.functions import Coalesce, Lower, Upper
from django.utils import timezone
from django.utils.timezone import datetime, timedelta
from django.utils.translation import gettext_lazy as _
from psycopg2.extras import DateTimeRange, DateTimeTZRange, NumericRange

# import pytz
