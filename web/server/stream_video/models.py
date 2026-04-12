import uuid
from django.db import models
from django.utils import timezone

class Session(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exercise_type = models.CharField(max_length=50)
    overall_score = models.FloatField(default=0.0)
    consistency_score = models.FloatField(default=0.0)
    fatigue_index = models.FloatField(default=0.0)
    most_frequent_error = models.CharField(max_length=255, null=True, blank=True)
    accuracy_trend = models.CharField(max_length=50, null=True, blank=True)
    best_set = models.IntegerField(default=1)
    worst_set = models.IntegerField(default=1)
    total_reps = models.IntegerField(default=0)
    session_deviation = models.FloatField(default=0.0)
    total_sets = models.IntegerField(default=1)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Session {self.session_id} - {self.exercise_type}"


class SessionSet(models.Model):
    session = models.ForeignKey(Session, related_name='sets', on_delete=models.CASCADE)
    exercise_type = models.CharField(max_length=50)
    set_number = models.IntegerField()
    raw_report_json = models.TextField()
    # Normalized Universal Metrics
    normalized_accuracy = models.FloatField(default=0.0)
    normalized_deviation = models.FloatField(default=0.0)
    normalized_stability = models.FloatField(default=0.0)
    normalized_range_of_motion = models.FloatField(default=0.0)
    normalized_rep_validity = models.FloatField(default=0.0)
    set_score = models.FloatField(default=0.0)
    total_errors = models.IntegerField(default=0)
    rep_count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['set_number']
        unique_together = ('session', 'set_number')

    def __str__(self):
        return f"{self.session.session_id} - Set {self.set_number}"
