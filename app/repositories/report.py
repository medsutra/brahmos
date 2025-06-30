

from models.report import Report


class ReportRepository:

    @classmethod
    def add_report(cls, db, report):
        """
        Adds a new report to the database.

        :param db: The database session.
        :param report: The report object to be added.
        :return: The added report object.
        """
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @classmethod
    def get_report_by_id(cls, db, report_id):
        """
        Retrieves a report by its ID.

        :param db: The database session.
        :param report_id: The ID of the report to retrieve.
        :return: The report object if found, otherwise None.
        """
        return db.query(Report).filter(Report.id == report_id).first()

    @classmethod
    def get_reports_by_user_id(cls, db, user_id):
        """
        Retrieves all reports for a specific user.

        :param db: The database session.
        :param user_id: The ID of the user whose reports are to be retrieved.
        :return: A list of report objects for the specified user.
        """
        return db.query(Report).filter(Report.user_id == user_id).all()

    @classmethod
    def update_report_status(cls, db, report_id, status):
        """
        Updates the status of a report.

        :param db: The database session.
        :param report_id: The ID of the report to update.
        :param status: The new status to set for the report.
        :return: The updated report object if found, otherwise None.
        """
        report = cls.get_report_by_id(db, report_id)
        if report:
            report.status = status
            db.commit()
            db.refresh(report)
            return report
        return None

    @classmethod
    def delete_report(cls, db, report_id):
        """
        Deletes a report by its ID.

        :param db: The database session.
        :param report_id: The ID of the report to delete.
        :return: True if the report was deleted, otherwise False.
        """
        report = cls.get_report_by_id(db, report_id)
        if report:
            db.delete(report)
            db.commit()
            return True
        return False

    @classmethod
    def get_all_reports(cls, db):
        """
        Retrieves all reports from the database.

        :param db: The database session.
        :return: A list of all report objects.
        """
        return db.query(Report).all()