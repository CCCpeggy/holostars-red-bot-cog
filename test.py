from datetime import datetime
class Time:
    @staticmethod
    def add_timezone(time: datetime) -> datetime:
        import pytz
        return pytz.utc.localize(time)

    @staticmethod
    def to_datetime(datetime_text: str) -> datetime:
        from dateutil.parser import parse as parse_time
        time = parse_time(datetime_text)
        return Time.add_timezone(time)

    @staticmethod
    def to_standard_time_str(time: datetime) -> str:
        return time.isoformat()

    @staticmethod
    def get_specified_timezone_str(time: datetime, timezone: str='Asia/Taipei') -> str:
        if time.tzinfo == None:
            time = Time.add_timezone(time)
        import pytz
        return time.astimezone(pytz.timezone(timezone))

    @staticmethod
    def get_now():
        from datetime import timezone
        return datetime.now(timezone.utc)

    @staticmethod
    def get_diff_from_now_total_sec(time: datetime) -> int:
        return (time - Time.get_now()).total_seconds()

    @staticmethod
    def is_time_in_future_range(time: datetime, months=0, weeks=0, days=0, hours=0, minutes=0, seconds=0) -> bool:
        if time.tzinfo == None:
            time = Time.add_timezone(time)
        from dateutil.relativedelta import relativedelta
        delta_time = relativedelta(months=months, weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds) 
        return (Time.get_now() + delta_time) > time

