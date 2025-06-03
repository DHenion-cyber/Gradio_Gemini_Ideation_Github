import logging
from trulens_eval import Tru
from trulens.dashboard.run import run_dashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Attempting to initialize TruLens and run the dashboard.")
tru = Tru()
logger.info("TruLens initialized. Attempting to run dashboard...")
run_dashboard(tru)
logger.info("TruLens dashboard function called.")