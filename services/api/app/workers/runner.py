"""DB-backed job runner entrypoint. Phase 0: idle loop (real runner lands in Phase 2)."""

import logging
import time

logger = logging.getLogger(__name__)

POLL_INTERVAL_S = 5


def main() -> None:
    logger.info("worker idle loop started (Phase 0 skeleton)")
    while True:
        time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
