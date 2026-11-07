from celery import shared_task


@shared_task
def process_device_payloads():
    """
    Beat task: turn new device result payloads (written to
    devices_devicepayload by the Go ingest service) into race runs.
    See races/device_results.py. A no-op unless DEVICE_RESULTS_ENABLED is on
    and DEVICE_RESULTS_SINCE is set.
    """
    from .device_results import process_pending
    return process_pending()
