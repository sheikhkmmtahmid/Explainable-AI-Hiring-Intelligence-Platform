"""
Drops the partial token_blacklist tables created by the failed 0001_initial migration,
recreates them with the correct final schema using TiDB-compatible SQL (all constraints
at CREATE time), then fakes all token_blacklist migrations so Django considers them applied.
Run once after adding rest_framework_simplejwt.token_blacklist to INSTALLED_APPS.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder


CREATE_OUTSTANDING = """
CREATE TABLE token_blacklist_outstandingtoken (
    id          BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    jti         VARCHAR(255) NOT NULL,
    token       LONGTEXT NOT NULL,
    created_at  DATETIME(6) NULL,
    expires_at  DATETIME(6) NOT NULL,
    user_id     BIGINT NULL,
    UNIQUE KEY uq_outstanding_jti (jti),
    CONSTRAINT fk_outstanding_user
        FOREIGN KEY (user_id) REFERENCES accounts_user (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

CREATE_BLACKLISTED = """
CREATE TABLE token_blacklist_blacklistedtoken (
    id              BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    blacklisted_at  DATETIME(6) NOT NULL,
    token_id        BIGINT NOT NULL,
    UNIQUE KEY uq_blacklisted_token (token_id),
    CONSTRAINT fk_blacklisted_token
        FOREIGN KEY (token_id) REFERENCES token_blacklist_outstandingtoken (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

MIGRATIONS_TO_FAKE = [
    "0001_initial",
    "0002_outstandingtoken_jti_hex",
    "0003_auto_20171017_2007",
    "0004_auto_20171017_2013",
    "0005_remove_outstandingtoken_jti",
    "0006_auto_20171017_2113",
    "0007_auto_20171017_2214",
    "0008_migrate_to_bigautofield",
    "0010_fix_migrate_to_bigautofield",
    "0011_linearizes_history",
    "0012_alter_outstandingtoken_user",
]


class Command(BaseCommand):
    help = "Create token_blacklist tables for TiDB and fake the library migrations."

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Drop partial tables from the previously failed migration run
            cursor.execute("DROP TABLE IF EXISTS token_blacklist_blacklistedtoken")
            self.stdout.write("  dropped token_blacklist_blacklistedtoken (if existed)")
            cursor.execute("DROP TABLE IF EXISTS token_blacklist_outstandingtoken")
            self.stdout.write("  dropped token_blacklist_outstandingtoken (if existed)")

            cursor.execute(CREATE_OUTSTANDING)
            self.stdout.write("  created token_blacklist_outstandingtoken")
            cursor.execute(CREATE_BLACKLISTED)
            self.stdout.write("  created token_blacklist_blacklistedtoken")

        recorder = MigrationRecorder(connection)
        recorder.ensure_schema()
        already = {m for (a, m) in recorder.applied_migrations() if a == "token_blacklist"}
        for name in MIGRATIONS_TO_FAKE:
            if name not in already:
                recorder.record_applied("token_blacklist", name)
                self.stdout.write(f"  faked token_blacklist.{name}")
            else:
                self.stdout.write(f"  already recorded: {name}")

        self.stdout.write(self.style.SUCCESS("token_blacklist setup complete."))
