"""
Print Job Simulator
Simulates print jobs for testing the print budget system
"""

from typing import Dict

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from src.services.print_validation_service import PrintValidationService
from src.utils.logger import get_logger


logger = get_logger(__name__)


class PrintJobSimulator(QObject):
    """Simulates print jobs for testing print budget system"""

    # Signals
    print_job_requested = pyqtSignal(int, int)  # black_white_pages, color_pages
    print_job_completed = pyqtSignal(int, int)  # black_white_pages, color_pages
    print_job_failed = pyqtSignal(str)  # error message

    def __init__(self, print_validation_service: PrintValidationService):
        super().__init__()
        self.print_validation_service = print_validation_service
        self.simulated_jobs = []

    def simulate_print_job(
        self, black_white_pages: int, color_pages: int, delay_seconds: int = 2
    ) -> Dict:
        """
        Simulate a print job with validation and budget deduction

        Args:
            black_white_pages: Number of black and white pages
            color_pages: Number of color pages
            delay_seconds: Delay before completing the job (simulate printing time)

        Returns:
            Dict with simulation result
        """
        try:
            logger.info(
                f"Simulating print job: {black_white_pages} B&W, "
                f"{color_pages} color pages"
            )

            # Emit print job requested signal
            self.print_job_requested.emit(black_white_pages, color_pages)

            # Validate print job
            validation_result = self.print_validation_service.validate_print_job(
                black_white_pages, color_pages
            )

            if not validation_result.get("success"):
                error_msg = f"Print validation failed: {validation_result.get('error')}"
                logger.error(error_msg)
                self.print_job_failed.emit(error_msg)
                return validation_result

            if not validation_result.get("can_print"):
                error_msg = (
                    f"Insufficient budget: "
                    f"{validation_result.get('message', 'Unknown error')}"
                )
                logger.warning(error_msg)
                self.print_job_failed.emit(error_msg)
                return validation_result

            # Simulate printing delay
            QTimer.singleShot(
                delay_seconds * 1000,
                lambda: self._complete_print_job(black_white_pages, color_pages),
            )

            return {
                "success": True,
                "message": f"Print job queued, will complete in "
                f"{delay_seconds} seconds",
                "validation": validation_result,
            }

        except Exception as e:
            error_msg = f"Error simulating print job: {str(e)}"
            logger.error(error_msg)
            self.print_job_failed.emit(error_msg)
            return {"success": False, "error": error_msg}

    def _complete_print_job(self, black_white_pages: int, color_pages: int):
        """Complete the print job and deduct budget"""
        try:
            logger.info(
                f"Completing print job: {black_white_pages} B&W, "
                f"{color_pages} color pages"
            )

            # Process successful print
            result = self.print_validation_service.process_successful_print(
                black_white_pages, color_pages
            )

            if result.get("success"):
                logger.info(
                    f"Print job completed successfully: {result.get('message')}"
                )
                self.print_job_completed.emit(black_white_pages, color_pages)
            else:
                error_msg = f"Failed to process print job: {result.get('error')}"
                logger.error(error_msg)
                self.print_job_failed.emit(error_msg)

        except Exception as e:
            error_msg = f"Error completing print job: {str(e)}"
            logger.error(error_msg)
            self.print_job_failed.emit(error_msg)

    def simulate_multiple_jobs(self, jobs: list, delay_between_jobs: int = 1) -> Dict:
        """
        Simulate multiple print jobs

        Args:
            jobs: List of tuples (black_white_pages, color_pages)
            delay_between_jobs: Delay between jobs in seconds

        Returns:
            Dict with simulation result
        """
        try:
            logger.info(f"Simulating {len(jobs)} print jobs")

            total_black_white = sum(job[0] for job in jobs)
            total_color = sum(job[1] for job in jobs)

            # Validate total job
            validation_result = self.print_validation_service.validate_print_job(
                total_black_white, total_color
            )

            if not validation_result.get("success") or not validation_result.get(
                "can_print"
            ):
                return validation_result

            # Queue jobs with delays
            for i, (bw_pages, color_pages) in enumerate(jobs):
                delay = i * delay_between_jobs
                QTimer.singleShot(
                    delay * 1000,
                    lambda bw=bw_pages, c=color_pages: self.simulate_print_job(
                        bw, c, 1
                    ),
                )

            return {
                "success": True,
                "message": f"Queued {len(jobs)} print jobs",
                "total_black_white": total_black_white,
                "total_color": total_color,
            }

        except Exception as e:
            logger.error(f"Error simulating multiple jobs: {e}")
            return {
                "success": False,
                "error": f"Error simulating multiple jobs: {str(e)}",
            }
