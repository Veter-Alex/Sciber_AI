import sys, os

if __name__ == '__main__':
	sys.path.append('/app')
	from app.tasks.core import enqueue_add_file
	from pathlib import Path
	fp = Path('/app/storage/base/integration_test_audio.mp3')
	print('file exists:', fp.exists(), 'size', fp.stat().st_size)
	rel_path = os.path.relpath(str(fp), '/app/storage')
	print('rel_path', rel_path)
	new_id = enqueue_add_file.run('integration_test_audio.mp3', 'BASE', rel_path, fp.stat().st_size, 'integration_test_audio.mp3', 1)
	print('enqueue_add_file.run returned', new_id)
