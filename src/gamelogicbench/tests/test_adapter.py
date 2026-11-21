from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from gamelogicbench.adapter import GameLogicBenchAdapter


class PlatformTests(unittest.TestCase):
    def test_unsupported_task_is_rejected_before_creating_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = SimpleNamespace(harness=root/'harness', tasks=root/'tasks',
                                     unsupported_reason=lambda task: 'live object mutation')
            adapter = GameLogicBenchAdapter(source, root/'output', task_ids=['atom_live'])
            with self.assertRaisesRegex(ValueError, 'not supported by isolated verification'):
                adapter.run()
            self.assertFalse((root/'output').exists())

    def test_native_extension_pins_both_roles_without_affecting_plain_tasks(self):
        evaluation = {
            'cells': [None], 'timeout': {'wall': 180},
            'resources': {'cpus': 1, 'memory_mb': 1024},
            'deliverable_paths': ['res://logic/controller.gd'],
        }
        agent = {'timeout_sec': 3600, 'cpus': 2, 'memory_mb': 8192}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = SimpleNamespace(
                harness=root/'harness', tasks=root/'tasks', files={},
                copy_group=Mock(), instruction=Mock(return_value='Original prompt'),
            )
            def copy_group(task_id, group, target):
                target.mkdir(parents=True, exist_ok=True)
            source.copy_group.side_effect = copy_group
            for native in (False, True):
                task_id = 'repo_native' if native else 'atom_plain'
                (source.tasks/task_id).mkdir(parents=True)
                (source.tasks/task_id/'task.yaml').write_text('name: '+task_id)
                source.files[(task_id, 'game')] = [Path('addon.gdextension')] if native else []
                adapter = GameLogicBenchAdapter(source, root/'output', task_ids=[task_id])
                destination = root/'generated'/task_id
                adapter._write_task(destination, task_id, evaluation, agent)
                for role in ('environment', 'tests'):
                    dockerfile = (destination/role/'Dockerfile').read_text()
                    self.assertIn('COPY --from=engine', dockerfile)
                    self.assertNotIn('__GLB_RUNTIME_IMAGE__', dockerfile)
                    compose = destination/role/'docker-compose.yaml'
                    self.assertEqual(compose.exists(), native)
                    if native:
                        self.assertIn('platform: linux/amd64', compose.read_text())


if __name__ == '__main__':
    unittest.main()
