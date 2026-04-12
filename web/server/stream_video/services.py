import json
import numpy as np
from .models import Session, SessionSet

class NormalizedMetricExtractor:
    @staticmethod
    def extract(exercise_type, raw_json):
        """
        Extracts normalized Layer 2 metrics from Layer 1 raw responses.
        Handles both old flat format and new fallback structure.
        """
        if isinstance(raw_json, str):
            report = json.loads(raw_json)
        else:
            report = raw_json

        # Handle new structure: { 'details': [], 'is_estimated': bool, 'motion_score': float }
        if 'details' in report and isinstance(report['details'], list):
            details = report['details']
        else:
            details = report if isinstance(report, list) else []

        total_errors = len(details)
        
        # Normalized reps logic based on the counter
        rep_count = 0
        counter = report.get('counter') if isinstance(report, dict) else None
        
        # If counter is not in report, it might be the second element of the tuple from handle_detected_results
        # But MultiSetSessionManager passes the raw_report which is the result of handle_detected_results
        # which I updated to return (final_results, rep_count) in the detectors.
        # Wait, I need to check how main.py calls it.
        # processed_results = exercise_detection.handle_detected_results(...)
        # return processed_results
        # In detectors, I changed it to return (results_dict, counter).
        
        if isinstance(counter, int):
            rep_count = counter
        elif isinstance(counter, dict):
            rep_count = counter.get('left_counter', 0) + counter.get('right_counter', 0)
        elif not counter and isinstance(report, dict) and 'is_estimated' in report:
            # This is the new structure, the counter was passed separately in handle_detected_results return
            # but MultiSetSessionManager might need adjustment.
            # Let's assume rep_count is passed in later or extracted.
            pass

        # For now, let's extract rep_count if it's buried in the report or passed as a sibling
        # Actually, let's look at MultiSetSessionManager.save_set
        # It calls NormalizedMetricExtractor.extract(exercise_type, raw_report)
        # raw_report is processed_results from main.py
        
        # To make it robust, let's check if 'rep_count' was injected into the report dict
        rep_count = report.get('rep_count', rep_count)

        normalized_accuracy = max(0.0, 100.0 - (total_errors * 10.0))
        normalized_deviation = float(total_errors) * 0.5
        normalized_stability = max(0.0, 100.0 - (total_errors * 5.0))
        normalized_range_of_motion = 100.0 if total_errors == 0 else 85.0
        normalized_rep_validity = 100.0 if rep_count > 0 and total_errors == 0 else 0.0
        set_score = normalized_accuracy

        return {
            'normalized_accuracy': normalized_accuracy,
            'normalized_deviation': normalized_deviation,
            'normalized_stability': normalized_stability,
            'normalized_range_of_motion': normalized_range_of_motion,
            'normalized_rep_validity': normalized_rep_validity,
            'set_score': set_score,
            'total_errors': total_errors,
            'rep_count': rep_count
        }


class ReportAggregator:
    @staticmethod
    def aggregate(session):
        """
        Aggregates multiple SessionSets into a final Session report.
        Redesigned to ALWAYS compute metrics, even with 1 set.
        """
        sets = list(session.sets.all().order_by('set_number'))
        if not sets:
            return
        
        # We no longer filter out sets. Every set is valid for aggregation.
        total_set_count = len(sets)
        total_reps = sum(s.rep_count for s in sets)
        
        # Weighted Accuracy
        if total_reps > 0:
            weighted_accuracy = sum(s.set_score * s.rep_count for s in sets) / total_reps
        else:
            weighted_accuracy = sum(s.set_score for s in sets) / total_set_count

        # Best / Worst
        best_set_obj = max(sets, key=lambda s: s.set_score)
        best_set = best_set_obj.set_number
        
        worst_set_obj = min(sets, key=lambda s: s.set_score)
        worst_set = worst_set_obj.set_number

        # Metrics: Fatigue, Consistency & Trend
        if total_set_count >= 2:
            scores = [s.set_score for s in sets]
            # Consistency: 100 - variance (clamped)
            variance = float(np.var(scores))
            consistency_score = max(0.0, 100.0 - variance)
            
            # Fatigue: Difference between start and end
            fatigue_index = sets[0].set_score - sets[-1].set_score
            
            # Trend
            if sets[-1].set_score > sets[0].set_score + 2: # 2 point buffer
                accuracy_trend = "Improving"
            elif sets[-1].set_score < sets[0].set_score - 2:
                accuracy_trend = "Declining"
            else:
                accuracy_trend = "Stable"
        else:
            # Single set baselines
            consistency_score = 100.0
            fatigue_index = 0.0
            accuracy_trend = "Baseline established"

        # Most Frequent Error
        error_counts = {}
        for s in sets:
            try:
                report_raw = json.loads(s.raw_report_json)
                # Handle both list and dict-wrapped results
                details = report_raw.get('details', []) if isinstance(report_raw, dict) else report_raw
                for error in details:
                    stage = error.get('stage', 'unknown')
                    error_counts[stage] = error_counts.get(stage, 0) + 1
            except Exception:
                pass
        most_frequent_error = max(error_counts, key=error_counts.get) if error_counts else "None"
        
        session_deviation = sum(s.normalized_deviation for s in sets) / total_set_count
            
        # Update session
        session.overall_score = float(weighted_accuracy)
        session.consistency_score = float(consistency_score)
        session.fatigue_index = float(fatigue_index)
        session.best_set = int(best_set)
        session.worst_set = int(worst_set)
        session.total_reps = int(total_reps)
        session.session_deviation = float(session_deviation)
        session.most_frequent_error = most_frequent_error
        session.accuracy_trend = accuracy_trend
        session.total_sets = total_set_count
        session.save()


class DatabaseService:
    @staticmethod
    def get_session(session_id):
        """
        Strict session fetch — session MUST have been pre-created by start_session.
        """
        try:
            return Session.objects.get(session_id=str(session_id))
        except Session.DoesNotExist:
            raise ValueError(f"Session {session_id} not found. Call /session/start first.")

    @staticmethod
    def create_session_set(session, set_number, raw_report, norms):
        return SessionSet.objects.create(
            session=session,
            exercise_type=session.exercise_type,
            set_number=set_number,
            raw_report_json=json.dumps(raw_report) if isinstance(raw_report, dict) else raw_report,
            **norms
        )


class MultiSetSessionManager:
    @staticmethod
    def save_set(session_id, exercise_type, set_number, raw_report):
        """
        Saves a single set. raw_report is the tuple (final_results, rep_count)
        returned by the detectors.
        """
        session = DatabaseService.get_session(session_id)
        
        # Unpack the new detector return structure
        if isinstance(raw_report, tuple) and len(raw_report) == 2:
            detection_data, rep_count = raw_report
        else:
            detection_data = raw_report
            # Robust extraction: check for metadata['counter'] first, then 'counter', then 'rep_count'
            if isinstance(raw_report, dict):
                meta = raw_report.get('metadata', {})
                rep_count = meta.get('counter') if isinstance(meta, dict) else None
                if rep_count is None:
                    rep_count = raw_report.get('counter', raw_report.get('rep_count', 0))
            else:
                rep_count = 0

        # Handle bicep curl dual-counter (dict type)
        if isinstance(rep_count, dict):
            final_reps = rep_count.get('left_counter', 0) + rep_count.get('right_counter', 0)
        else:
            final_reps = int(rep_count or 0)

        # Inject rep_count into detection_data for extraction
        if isinstance(detection_data, dict):
            detection_data['rep_count'] = final_reps
            
        norms = NormalizedMetricExtractor.extract(exercise_type, detection_data)
        
        SessionSet.objects.filter(session=session, set_number=set_number).delete()
        
        session_set = DatabaseService.create_session_set(session, set_number, detection_data, norms)
        print(f"[DEBUG] Saved Set {set_number} | session={session_id} | reps={final_reps} | score={norms['set_score']}")
        
        return {
            'status': 'success',
            'set_number': session_set.set_number,
            'rep_count': final_reps,
            'norms': norms
        }

    @staticmethod
    def finalize_session(session_id):
        try:
            session = Session.objects.get(session_id=str(session_id))
        except Session.DoesNotExist:
            return {'error': 'Session not found'}
            
        ReportAggregator.aggregate(session)
        
        sets = list(session.sets.all().order_by('set_number'))
        
        per_set_reps = [
            {
                'set': s.set_number, 
                'reps': s.rep_count, 
                'score': round(s.set_score, 2),
                'is_valid': True # All sets are valid now
            }
            for s in sets
        ]
        
        # We ALWAYS return success now. Aggregator sets the baseline labels.
        return {
            'status': 'success',
            'session_id': str(session.session_id),
            'overall_score': session.overall_score,
            'consistency_score': session.consistency_score,
            'fatigue_index': session.fatigue_index,
            # Use labels for UI clarity
            'fatigue_label': f"{session.fatigue_index:.1f}" if len(sets) >= 2 else "0.0 (Single set baseline)",
            'consistency_label': f"{session.consistency_score:.1f}" if len(sets) >= 2 else "100.0 (Baseline)",
            'most_frequent_error': session.most_frequent_error,
            'accuracy_trend': session.accuracy_trend,
            'best_set': session.best_set,
            'worst_set': session.worst_set,
            'total_reps': session.total_reps,
            'per_set_reps': per_set_reps,
            'session_deviation': session.session_deviation,
            'total_sets': len(sets),
            'valid_set_count': len(sets)
        }
