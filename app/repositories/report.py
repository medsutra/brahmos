from app.query_models.report import ReportStatus
from ..models.report import Report
from ..schemas.report import Report as ReportSchema


class ReportRepository:

    @classmethod
    def add_report(cls, db, user_id):
        report = Report(
            status=ReportStatus.PROCESSING,
            user_id=user_id,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return ReportSchema.model_validate(report)

    @classmethod
    def set_report_failed(cls, db, report_id):
        report = cls.get_report_by_id(db, report_id)
        if report:
            report.status = ReportStatus.FAILED
            db.commit()
            db.refresh(report)
            return report
        return None

    @classmethod
    def get_report_by_id(cls, db, report_id):
        return db.query(Report).filter(Report.id == report_id).first()

    @classmethod
    def get_reports_by_user_id(cls, db, user_id):
        return db.query(Report).filter(Report.user_id == user_id).all()

    @classmethod
    def populate_report(
        cls, db, report_id, title, description, status=ReportStatus.PROCESSING
    ):
        report = cls.get_report_by_id(db, report_id)
        if report:
            report.title = title
            report.description = description
            report.status = status
            db.commit()
            db.refresh(report)
            return report
        return None

    @classmethod
    def update_report_status(cls, db, report_id, status):
        report = cls.get_report_by_id(db, report_id)
        if report:
            report.status = status
            db.commit()
            db.refresh(report)
            return report
        return None

    @classmethod
    def delete_report(cls, db, report_id):
        report = cls.get_report_by_id(db, report_id)
        if report:
            db.delete(report)
            db.commit()
            return True
        return False

    @classmethod
    def get_all_reports(cls, db):
        return db.query(Report).all()
