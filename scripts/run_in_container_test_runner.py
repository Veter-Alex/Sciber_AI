# Small runner to call the integration test function inside a container
import sys
sys.path.append('/app')
from tests.test_integration_watcher_celery import test_watcher_triggers_celery_and_db_record

if __name__ == '__main__':
    try:
        test_watcher_triggers_celery_and_db_record()
        print('SUCCESS')
    except AssertionError as e:
        print('FAIL', e)
    except Exception as e:
        print('ERROR', type(e), e)
