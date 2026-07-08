"""
Management command to train the ML scorer from labelled hiring outcomes.

Before running this command, recruiters must mark MatchResult rows with
the outcome of each hiring decision (hired=True or hired=False).

At least 50 labelled rows are required. The more the better.

Usage:
    python manage.py train_scorer
    python manage.py train_scorer --min-samples 200
    python manage.py train_scorer --output path/to/model.joblib

After training, restart the Django server and Celery workers so the new
model is picked up (it is loaded once at process startup).
"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Train the ML scorer from MatchResult rows that have a hiring outcome recorded"

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-samples",
            type=int,
            default=50,
            help="Minimum number of labelled MatchResult rows required (default: 50)",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Path to save the trained model (default: ml/models/scorer.joblib)",
        )

    def handle(self, *args, **options):
        from ml.matching.trainer import MODEL_PATH, train_and_save

        output_path = Path(options["output"]) if options["output"] else MODEL_PATH
        min_samples = options["min_samples"]

        self.stdout.write("Training scorer model...")
        self.stdout.write(
            f"  Looking for MatchResult rows with hired=True or hired=False"
        )

        try:
            summary = train_and_save(min_samples=min_samples, output_path=output_path)
        except ValueError as exc:
            raise CommandError(str(exc))

        self.stdout.write(self.style.SUCCESS("\nTraining complete."))
        self.stdout.write(f"  Samples used    : {summary['n_samples']}")
        self.stdout.write(f"  Hired (positive): {summary['n_positive']}")
        self.stdout.write(f"  Not hired       : {summary['n_negative']}")
        if summary.get("cv_folds"):
            self.stdout.write(f"\n  Cross-validated ({summary['cv_folds']}-fold, stratified):")
            if summary.get("roc_auc_mean") is not None:
                self.stdout.write(
                    f"    ROC-AUC        : {summary['roc_auc_mean']:.4f} ± {summary['roc_auc_std']:.4f}"
                )
            if summary.get("pr_auc_mean") is not None:
                self.stdout.write(
                    f"    PR-AUC         : {summary['pr_auc_mean']:.4f} ± {summary['pr_auc_std']:.4f}"
                    "   (more informative than ROC-AUC under class imbalance)"
                )
            if summary.get("precision_mean") is not None:
                self.stdout.write(f"    Precision      : {summary['precision_mean']:.4f}")
            if summary.get("recall_mean") is not None:
                self.stdout.write(f"    Recall         : {summary['recall_mean']:.4f}")
            if summary.get("f1_mean") is not None:
                self.stdout.write(f"    F1             : {summary['f1_mean']:.4f}")
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\n  Too few samples per class for cross-validation -- "
                    "metrics are not statistically meaningful yet."
                )
            )
        self.stdout.write(f"\n  Model saved to  : {summary['model_path']}")
        self.stdout.write(
            "\nRestart the Django server and Celery workers to activate the new model."
        )
